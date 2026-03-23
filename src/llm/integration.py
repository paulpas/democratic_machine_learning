"""LLM integration for democratic machine learning.

This module provides LLM-based reasoning, analysis, and conjecture formation
using a llama.cpp endpoint at http://localhost:8080.

Production-grade implementation with:
- Concise prompts that produce real LLM responses
- Deep recursive investigation with geographic fan-out
- Full national/state/county representation
- Comprehensive stdout logging at every step
- Full prompt+response audit logging to file (logs/llm_calls.log)
  - Set PYTHONLOGGING=DEBUG to also mirror full content to stdout
"""

import json
import logging
import logging.handlers
import os
import re
import sys
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import urllib.request
import urllib.error

# ──────────────────────────────────────────────────────────────────────────────
# LLM AUDIT LOGGER
# Writes every prompt and response to logs/llm_calls.log (rotating, 50 MB max,
# 5 backups).  When PYTHONLOGGING=DEBUG the same content also goes to stdout.
# ──────────────────────────────────────────────────────────────────────────────

_LOG_DIR = Path(
    os.environ.get("LLM_LOG_DIR", Path(__file__).resolve().parents[2] / "logs")
)
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOG_DIR / "llm_calls.log"

# True when PYTHONLOGGING=DEBUG is set in the environment
_DEBUG_TO_STDOUT: bool = os.environ.get("PYTHONLOGGING", "").upper() == "DEBUG"

# Module-level audit logger — one shared instance for the whole process
_audit_logger = logging.getLogger("llm.audit")
_audit_logger.setLevel(logging.DEBUG)
_audit_logger.propagate = False  # don't bubble up to root logger

# Rotating file handler — always active
_file_handler = logging.handlers.RotatingFileHandler(
    _LOG_FILE,
    maxBytes=50 * 1024 * 1024,  # 50 MB per file
    backupCount=5,
    encoding="utf-8",
)
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s  %(levelname)-5s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)
_audit_logger.addHandler(_file_handler)

# Stdout handler — only active when PYTHONLOGGING=DEBUG
if _DEBUG_TO_STDOUT:
    _stdout_handler = logging.StreamHandler(sys.stdout)
    _stdout_handler.setLevel(logging.DEBUG)
    _stdout_handler.setFormatter(
        logging.Formatter(
            fmt="[DEBUG %(asctime)s] %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    _audit_logger.addHandler(_stdout_handler)


def _audit(msg: str) -> None:
    """Write a message to the audit log (and stdout if DEBUG mode)."""
    _audit_logger.debug(msg)


def _audit_call(
    call_number: int,
    label: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    endpoint: str,
) -> None:
    """Log the full outgoing LLM request to the audit file."""
    divider = "=" * 120
    _audit(divider)
    _audit(f"LLM CALL #{call_number}  |  {label}")
    _audit(f"  endpoint    : {endpoint}/completion")
    _audit(f"  max_tokens  : {max_tokens}")
    _audit(f"  temperature : {temperature}")
    _audit(f"  prompt_chars: {len(prompt)}")
    _audit(
        "── PROMPT ──────────────────────────────────────────────────────────────────────────────────────"
    )
    # Write the full prompt, indented for readability
    for line in prompt.splitlines():
        _audit(f"  {line}")
    _audit(
        "── END PROMPT ──────────────────────────────────────────────────────────────────────────────────"
    )


def _audit_response(
    call_number: int,
    label: str,
    content: str,
    tokens: int,
    cumulative_tokens: int,
    elapsed_ms: float,
) -> None:
    """Log the full LLM response to the audit file."""
    _audit(f"LLM RESPONSE #{call_number}  |  {label}")
    _audit(f"  tokens      : {tokens}")
    _audit(f"  cumulative  : {cumulative_tokens}")
    _audit(f"  elapsed_ms  : {elapsed_ms:.0f}")
    _audit(f"  content_chars: {len(content)}")
    _audit(
        "── RESPONSE ────────────────────────────────────────────────────────────────────────────────────"
    )
    for line in content.splitlines():
        _audit(f"  {line}")
    _audit(
        "── END RESPONSE ────────────────────────────────────────────────────────────────────────────────"
    )
    _audit("")


def _audit_error(call_number: int, label: str, error: Exception) -> None:
    """Log an LLM call error to the audit file."""
    _audit(f"LLM ERROR #{call_number}  |  {label}  |  {type(error).__name__}: {error}")
    _audit("")


# ──────────────────────────────────────────────────────────────────────────────
# US GEOGRAPHY DATA - All 50 states + representative counties
# ──────────────────────────────────────────────────────────────────────────────

US_STATES: Dict[str, Dict[str, Any]] = {
    "AL": {"name": "Alabama", "population": 5024279, "counties": 67},
    "AK": {"name": "Alaska", "population": 733391, "counties": 30},
    "AZ": {"name": "Arizona", "population": 7151502, "counties": 15},
    "AR": {"name": "Arkansas", "population": 3011524, "counties": 75},
    "CA": {"name": "California", "population": 39538223, "counties": 58},
    "CO": {"name": "Colorado", "population": 5773714, "counties": 64},
    "CT": {"name": "Connecticut", "population": 3605944, "counties": 8},
    "DE": {"name": "Delaware", "population": 989948, "counties": 3},
    "FL": {"name": "Florida", "population": 21538187, "counties": 67},
    "GA": {"name": "Georgia", "population": 10711908, "counties": 159},
    "HI": {"name": "Hawaii", "population": 1455271, "counties": 5},
    "ID": {"name": "Idaho", "population": 1839106, "counties": 44},
    "IL": {"name": "Illinois", "population": 12812508, "counties": 102},
    "IN": {"name": "Indiana", "population": 6785528, "counties": 92},
    "IA": {"name": "Iowa", "population": 3190369, "counties": 99},
    "KS": {"name": "Kansas", "population": 2937880, "counties": 105},
    "KY": {"name": "Kentucky", "population": 4505836, "counties": 120},
    "LA": {"name": "Louisiana", "population": 4657757, "counties": 64},
    "ME": {"name": "Maine", "population": 1362359, "counties": 16},
    "MD": {"name": "Maryland", "population": 6177224, "counties": 24},
    "MA": {"name": "Massachusetts", "population": 7029917, "counties": 14},
    "MI": {"name": "Michigan", "population": 10077331, "counties": 83},
    "MN": {"name": "Minnesota", "population": 5706494, "counties": 87},
    "MS": {"name": "Mississippi", "population": 2961279, "counties": 82},
    "MO": {"name": "Missouri", "population": 6154913, "counties": 115},
    "MT": {"name": "Montana", "population": 1084225, "counties": 56},
    "NE": {"name": "Nebraska", "population": 1961504, "counties": 93},
    "NV": {"name": "Nevada", "population": 3104614, "counties": 17},
    "NH": {"name": "New Hampshire", "population": 1377529, "counties": 10},
    "NJ": {"name": "New Jersey", "population": 9288994, "counties": 21},
    "NM": {"name": "New Mexico", "population": 2117522, "counties": 33},
    "NY": {"name": "New York", "population": 20201249, "counties": 62},
    "NC": {"name": "North Carolina", "population": 10439388, "counties": 100},
    "ND": {"name": "North Dakota", "population": 779094, "counties": 53},
    "OH": {"name": "Ohio", "population": 11799448, "counties": 88},
    "OK": {"name": "Oklahoma", "population": 3959353, "counties": 77},
    "OR": {"name": "Oregon", "population": 4237256, "counties": 36},
    "PA": {"name": "Pennsylvania", "population": 13002700, "counties": 67},
    "RI": {"name": "Rhode Island", "population": 1097379, "counties": 5},
    "SC": {"name": "South Carolina", "population": 5118425, "counties": 46},
    "SD": {"name": "South Dakota", "population": 886667, "counties": 66},
    "TN": {"name": "Tennessee", "population": 6910840, "counties": 95},
    "TX": {"name": "Texas", "population": 29145505, "counties": 254},
    "UT": {"name": "Utah", "population": 3271616, "counties": 29},
    "VT": {"name": "Vermont", "population": 643077, "counties": 14},
    "VA": {"name": "Virginia", "population": 8631393, "counties": 95},
    "WA": {"name": "Washington", "population": 7705281, "counties": 39},
    "WV": {"name": "West Virginia", "population": 1793716, "counties": 55},
    "WI": {"name": "Wisconsin", "population": 5893718, "counties": 72},
    "WY": {"name": "Wyoming", "population": 576851, "counties": 23},
}

US_NATIONAL_POPULATION = 331449281
US_TOTAL_COUNTIES = 3143

# Representative counties per region for geographic diversity
REPRESENTATIVE_COUNTIES: List[Dict[str, Any]] = [
    {
        "state": "CA",
        "name": "Los Angeles County",
        "population": 10014009,
        "type": "urban",
    },
    {"state": "TX", "name": "Harris County", "population": 4713325, "type": "urban"},
    {
        "state": "FL",
        "name": "Miami-Dade County",
        "population": 2716940,
        "type": "urban",
    },
    {"state": "NY", "name": "Kings County", "population": 2736074, "type": "urban"},
    {"state": "IL", "name": "Cook County", "population": 5275541, "type": "urban"},
    {
        "state": "PA",
        "name": "Philadelphia County",
        "population": 1603797,
        "type": "urban",
    },
    {"state": "TX", "name": "Bexar County", "population": 2009324, "type": "suburban"},
    {
        "state": "NC",
        "name": "Mecklenburg County",
        "population": 1115482,
        "type": "suburban",
    },
    {"state": "KY", "name": "Leslie County", "population": 10000, "type": "rural"},
    {"state": "MS", "name": "Holmes County", "population": 17010, "type": "rural"},
]

# Domain-specific subtopic seeds — used as fallback when LLM returns too few items
DOMAIN_SUBTOPICS: Dict[str, List[str]] = {
    "healthcare": [
        "Health Insurance Coverage and Access",
        "Healthcare Cost Control and Affordability",
        "Healthcare Quality and Outcomes",
        "Public Health Infrastructure and Prevention",
        "Health Equity and Social Determinants",
        "Mental Health and Substance Abuse",
        "Pharmaceutical Pricing and Drug Access",
        "Electronic Health Records and Data Privacy",
        "Rural Healthcare Access",
        "Workforce Shortages and Training",
    ],
    "economy": [
        "Job Creation and Employment",
        "Wage Growth and Income Inequality",
        "Small Business Support",
        "Trade Policy and International Commerce",
        "Tax Policy and Revenue",
        "Infrastructure Investment",
        "Technology and Innovation",
        "Social Safety Net Programs",
        "Housing Affordability",
        "Financial Regulation",
    ],
    "education": [
        "K-12 Funding Equity",
        "Teacher Recruitment and Retention",
        "Higher Education Affordability",
        "Early Childhood Education",
        "Curriculum Standards and Accountability",
        "School Choice and Charter Schools",
        "Special Education Services",
        "STEM Education",
        "Student Loan Debt",
        "Vocational and Trade Education",
    ],
    "immigration": [
        "Border Security and Management",
        "Legal Immigration Pathways",
        "Refugee and Asylum Policy",
        "Undocumented Immigrant Integration",
        "Visa Programs and Worker Permits",
        "Citizenship and Naturalization",
        "Deportation Policy",
        "Immigration Courts",
        "Community Integration Programs",
        "Economic Impacts of Immigration",
    ],
    "climate": [
        "Greenhouse Gas Emissions Reduction",
        "Renewable Energy Transition",
        "Carbon Pricing Mechanisms",
        "Climate Adaptation and Resilience",
        "Environmental Justice",
        "Clean Transportation",
        "Energy Efficiency Standards",
        "Forest and Land Conservation",
        "Coastal and Flood Management",
        "Green Jobs and Economic Transition",
    ],
    "infrastructure": [
        "Roads and Bridges Modernization",
        "Public Transit Expansion",
        "Broadband Internet Access",
        "Water Systems and Drinking Water",
        "Electrical Grid Modernization",
        "Airport and Port Improvements",
        "Cybersecurity for Infrastructure",
        "Rural Infrastructure Access",
        "Climate-Resilient Infrastructure",
        "Public-Private Partnerships",
    ],
}


def _log(msg: str, *, flush: bool = True) -> None:
    """Write to stdout immediately with timestamp."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=flush)


def _log_section(title: str, width: int = 80) -> None:
    _log("=" * width)
    _log(f"  {title}")
    _log("=" * width)


def _log_subsection(title: str, width: int = 80) -> None:
    _log("-" * width)
    _log(f"  {title}")
    _log("-" * width)


class LLMClient:
    """Production-grade client for LLM-based reasoning using llama.cpp endpoint."""

    def __init__(self, endpoint: Optional[str] = None, model: Optional[str] = None):
        """Initialize LLM client.

        Args:
            endpoint: Llama.cpp endpoint URL (default: http://localhost:8080)
            model: Model name to use (for logging purposes)
        """
        self.endpoint = endpoint or os.environ.get(
            "LLAMA_CPP_ENDPOINT", "http://localhost:8080"
        )
        self.model = model or os.environ.get("LLAMA_MODEL", "llama.cpp-model")
        self.timeout = int(os.environ.get("LLAMA_TIMEOUT", "900"))  # default 15 min
        self._call_count: int = 0
        self._total_tokens: int = 0

        self.available = self._test_connection()
        if self.available:
            _log(f"✅ LLM endpoint connected: {self.endpoint}")
        else:
            _log(f"⚠️  LLM endpoint unavailable: {self.endpoint} — using fallback")

    # ──────────────────────────────────────────────────────────────────────────
    # Connection test
    # ──────────────────────────────────────────────────────────────────────────

    def _test_connection(self) -> bool:
        """Test if the llama.cpp endpoint is available."""
        try:
            data = json.dumps(
                {"prompt": "Hi", "max_tokens": 5, "temperature": 0.0}
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{self.endpoint}/completion",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(
                req, timeout=30
            ) as response:  # 30s for connection test
                return response.getcode() == 200
        except Exception:
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Core LLM call — single responsibility, full logging
    # ──────────────────────────────────────────────────────────────────────────

    def _call_llm(
        self,
        prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        label: str = "",
    ) -> str:
        """
        Send a single prompt to the LLM endpoint and return the response text.

        Args:
            prompt:      The prompt string.
            max_tokens:  Token budget for the response.
            temperature: Sampling temperature.
            label:       Human-readable label for logging (domain/tier/subtopic).

        Returns:
            The generated text, or an empty string on failure.
        """
        if not self.available:
            _log(f"  ⚠️  LLM unavailable — skipping call [{label}]")
            _audit(f"LLM SKIPPED  |  {label}  |  endpoint unavailable")
            return ""

        self._call_count += 1
        _log("")
        _log(f"  🔄 LLM CALL #{self._call_count} | {label}")
        _log(
            f"     prompt_chars={len(prompt)}  max_tokens={max_tokens}  temp={temperature}"
        )
        _log(f"     endpoint={self.endpoint}/completion")

        # Full audit log — always written to file, stdout only in DEBUG mode
        _audit_call(
            call_number=self._call_count,
            label=label,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            endpoint=self.endpoint,
        )

        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        t_start = datetime.datetime.now()
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.endpoint}/completion",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result.get("content", "").strip()
                tokens = result.get("tokens_predicted", len(content.split()))
                elapsed_ms = (datetime.datetime.now() - t_start).total_seconds() * 1000
                self._total_tokens += tokens
                _log(
                    f"  ✅ RESPONSE  tokens={tokens}  cumulative={self._total_tokens}  elapsed={elapsed_ms / 1000:.1f}s"
                )
                preview = content[:120].replace("\n", " ")
                _log(f"     preview: {preview}{'…' if len(content) > 120 else ''}")
                # Full response to audit log
                _audit_response(
                    call_number=self._call_count,
                    label=label,
                    content=content,
                    tokens=tokens,
                    cumulative_tokens=self._total_tokens,
                    elapsed_ms=elapsed_ms,
                )
                return content
        except Exception as exc:
            elapsed_ms = (datetime.datetime.now() - t_start).total_seconds() * 1000
            _log(f"  ❌ LLM ERROR: {exc}")
            _audit_error(self._call_count, label, exc)
            return ""

    # ──────────────────────────────────────────────────────────────────────────
    # Public high-level methods
    # ──────────────────────────────────────────────────────────────────────────

    def investigate_domain_initial(
        self,
        domain: str,
        context: Dict[str, Any],
        principles: List[str],
    ) -> str:
        """Level-0 domain investigation — returns full reasoning text."""
        pop = context.get("population", US_NATIONAL_POPULATION)
        prompt = (
            f"You are a US policy expert. Analyze {domain} policy for the United States "
            f"(population {pop:,}). List the 5 most important subtopics as a numbered list, "
            f"then briefly explain each. Principles: {', '.join(principles[:5])}."
        )
        return self._call_llm(
            prompt,
            max_tokens=4096,
            label=f"domain={domain} tier=national depth=0",
        )

    def investigate_subtopic(
        self,
        domain: str,
        subtopic: str,
        tier: str,
        tier_label: str,
        tier_population: int,
        depth: int,
        principles: List[str],
        parent_context: str = "",
    ) -> str:
        """Investigate a subtopic at a specific geographic tier."""
        context_snippet = parent_context[:300] if parent_context else ""
        prompt = (
            f"You are a US {tier}-level policy expert. "
            f"Analyze '{subtopic}' as a subtopic of {domain} policy "
            f"for {tier_label} (population {tier_population:,}). "
            f"Provide: (1) current state, (2) key challenges, (3) best policy approaches, "
            f"(4) implementation steps, (5) expected outcomes. "
            f"Principles: {', '.join(principles[:5])}."
            + (f" Context: {context_snippet}" if context_snippet else "")
        )
        return self._call_llm(
            prompt,
            max_tokens=4096,
            label=f"domain={domain} subtopic={subtopic[:40]} tier={tier} depth={depth}",
        )

    def elaborate_subtopic(
        self,
        domain: str,
        subtopic: str,
        tier: str,
        tier_label: str,
        tier_population: int,
        depth: int,
        principles: List[str],
        prior_reasoning: str,
    ) -> str:
        """Deep elaboration on a subtopic — calls after initial investigation."""
        snippet = prior_reasoning[:400] if prior_reasoning else ""
        prompt = (
            f"Elaborate further on '{subtopic}' in {domain} policy at the {tier} level "
            f"({tier_label}, population {tier_population:,}). "
            f"Prior analysis: {snippet} "
            f"Provide: evidence for each approach, equity implications, "
            f"stakeholder concerns, and measurable success metrics."
        )
        return self._call_llm(
            prompt,
            max_tokens=4096,
            label=f"elaborate domain={domain} subtopic={subtopic[:40]} tier={tier} depth={depth}",
        )

    def form_conjecture(
        self,
        question: str,
        context: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        max_tokens: int = 4096,
        domain: str = "general",
    ) -> Dict[str, Any]:
        """Form a final conjecture synthesizing all evidence."""
        evidence_text = "\n".join(
            f"- [{e.get('tier', '?')} depth={e.get('depth', 0)}] "
            f"{e.get('finding', e.get('reasoning', ''))[:200]}"
            for e in evidence[:15]
        )
        prompt = (
            f"Based on the following evidence about {domain} policy, "
            f"answer: {question}\n\n"
            f"Evidence:\n{evidence_text}\n\n"
            f"Provide: (1) Conjecture statement, (2) Confidence 0-1, "
            f"(3) Top 3 supporting points, (4) Key contradictions."
        )
        raw = self._call_llm(
            prompt,
            max_tokens=max_tokens,
            temperature=0.6,
            label=f"conjecture domain={domain}",
        )
        return self._parse_conjecture(raw, question, evidence)

    def analyze_policy(
        self,
        topic: str,
        research_data: Dict[str, Any],
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """Analyze a policy topic using LLM."""
        context_text = " | ".join(
            f"{k}: {str(v)[:80]}" for k, v in list(research_data.items())[:5]
        )
        prompt = (
            f"Analyze {topic} policy. Context: {context_text}. "
            f"Provide: key findings, consensus level 0-1, top 3 recommendations, "
            f"implementation steps, expected outcomes."
        )
        raw = self._call_llm(
            prompt, max_tokens=max_tokens, label=f"analyze policy={topic}"
        )
        return self._parse_analysis(raw, topic)

    # ──────────────────────────────────────────────────────────────────────────
    # Deep recursive investigation — THE MAIN ENTRY POINT
    # ──────────────────────────────────────────────────────────────────────────

    def generate_reasoning_with_recursion(
        self,
        domain: str,
        initial_context: Dict[str, Any],
        max_depth: int = 4,
        subtopics_per_level: int = 5,
        principles: Optional[List[str]] = None,
        include_state_county_rep: bool = True,
    ) -> Dict[str, Any]:
        """
        Full deep-recursive LLM investigation with geographic fan-out.

        Architecture:
          Level 0 : Initial domain overview → extract top-N subtopics
          Level 1…N: For each subtopic:
                       - national investigation
                       - (if enabled) all 50 states
                       - (if enabled) representative counties
                       - elaborate on each finding
                       - extract sub-subtopics for next level
          Synthesis: form_conjecture from all elaborations
          Ranking:   rank solutions by score × geographic weight

        All stdout logging goes to terminal in real-time.
        """
        if principles is None:
            principles = [
                "Inclusivity",
                "Transparency",
                "Accountability",
                "Adaptability",
                "Equity",
                "Evidence-Based",
                "Context-Aware",
            ]

        started_at = datetime.datetime.now()

        _log("")
        _log_section(f"DEEP RECURSIVE LLM INVESTIGATION  |  domain={domain}")
        _log(f"  started        : {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        _log(f"  max_depth      : {max_depth}")
        _log(f"  subtopics/level: {subtopics_per_level}")
        _log(f"  geo_rep        : {include_state_county_rep}")
        _log(f"  endpoint       : {self.endpoint}")
        _log(f"  audit_log      : {_LOG_FILE}")
        _log("")

        _audit("=" * 120)
        _audit(f"SESSION START  domain={domain}  started={started_at.isoformat()}")
        _audit(
            f"  max_depth={max_depth}  subtopics_per_level={subtopics_per_level}  geo_rep={include_state_county_rep}"
        )
        _audit(f"  endpoint={self.endpoint}  log_file={_LOG_FILE}")
        _audit("=" * 120)
        _audit("")

        results: Dict[str, Any] = {
            "domain": domain,
            "max_depth": max_depth,
            "subtopics_per_level": subtopics_per_level,
            "include_state_county_rep": include_state_county_rep,
            "started_at": started_at.isoformat(),
            "recursive_analysis": {},
            "subtopics_by_level": {},
            "all_elaborations": [],
            "final_conjecture": {},
            "best_solutions": [],
        }

        context = {
            **initial_context,
            "domain": domain,
            "population": initial_context.get("population", US_NATIONAL_POPULATION),
        }

        # ── LEVEL 0: initial domain overview ──────────────────────────────────
        _log_section(f"LEVEL 0 | domain={domain} | tier=national | depth=0")

        level0_reasoning = self.investigate_domain_initial(domain, context, principles)
        if not level0_reasoning:
            level0_reasoning = f"Overview of {domain} policy for the United States."

        results["recursive_analysis"]["level_0"] = {
            "tier": "national",
            "depth": 0,
            "domain": domain,
            "reasoning": level0_reasoning,
        }

        # Extract initial subtopics from the LLM response, fall back to seeds
        current_subtopics = self._extract_subtopics_from_text(
            level0_reasoning, domain, subtopics_per_level
        )
        results["subtopics_by_level"]["level_0"] = current_subtopics
        _log(f"  subtopics extracted: {len(current_subtopics)}")
        for i, s in enumerate(current_subtopics, 1):
            _log(f"    {i}. {s}")

        # ── LEVELS 1..max_depth ───────────────────────────────────────────────
        for depth in range(1, max_depth + 1):
            if not current_subtopics:
                _log(f"  ⚠️  No subtopics for depth {depth}, ending early")
                break

            _log_section(
                f"LEVEL {depth}/{max_depth} | domain={domain} | "
                f"{len(current_subtopics)} subtopics"
            )

            level_elaborations: List[Dict[str, Any]] = []
            next_subtopics: List[str] = []

            for idx, subtopic in enumerate(current_subtopics[:subtopics_per_level], 1):
                _log("")
                _log_subsection(
                    f"SUBTOPIC {idx}/{min(len(current_subtopics), subtopics_per_level)} "
                    f"| depth={depth} | {subtopic}"
                )

                # ── national level ────────────────────────────────────────────
                _log(f"  🌐 NATIONAL  population={US_NATIONAL_POPULATION:,}")
                nat_reasoning = self.investigate_subtopic(
                    domain=domain,
                    subtopic=subtopic,
                    tier="national",
                    tier_label="United States",
                    tier_population=US_NATIONAL_POPULATION,
                    depth=depth,
                    principles=principles,
                    parent_context=level0_reasoning,
                )
                nat_elab = self.elaborate_subtopic(
                    domain=domain,
                    subtopic=subtopic,
                    tier="national",
                    tier_label="United States",
                    tier_population=US_NATIONAL_POPULATION,
                    depth=depth,
                    principles=principles,
                    prior_reasoning=nat_reasoning,
                )
                nat_entry: Dict[str, Any] = {
                    "domain": domain,
                    "subtopic": subtopic,
                    "tier": "national",
                    "tier_label": "United States",
                    "tier_population": US_NATIONAL_POPULATION,
                    "depth": depth,
                    "reasoning": nat_reasoning,
                    "elaboration": nat_elab,
                    "finding": (nat_reasoning + " " + nat_elab)[:600],
                }
                level_elaborations.append(nat_entry)
                results["all_elaborations"].append(nat_entry)

                # ── geographic fan-out ────────────────────────────────────────
                if include_state_county_rep:
                    state_entries, county_entries = self._geographic_fan_out(
                        domain=domain,
                        subtopic=subtopic,
                        depth=depth,
                        principles=principles,
                        prior_reasoning=nat_reasoning,
                    )
                    level_elaborations.extend(state_entries)
                    level_elaborations.extend(county_entries)
                    results["all_elaborations"].extend(state_entries)
                    results["all_elaborations"].extend(county_entries)

                    _log(
                        f"  ✅ Geo fan-out complete: {len(state_entries)} states, "
                        f"{len(county_entries)} counties"
                    )

                # Extract sub-subtopics for the next depth level
                sub_subtopics = self._extract_subtopics_from_text(
                    nat_reasoning, subtopic, max(2, subtopics_per_level // (depth + 1))
                )
                next_subtopics.extend(sub_subtopics)

            results["recursive_analysis"][f"level_{depth}"] = level_elaborations
            results["subtopics_by_level"][f"level_{depth}"] = next_subtopics

            # Deduplicate and cap for next level
            seen: set = set()
            deduped: List[str] = []
            for s in next_subtopics:
                key = s.lower().strip()
                if key not in seen:
                    seen.add(key)
                    deduped.append(s)
            current_subtopics = deduped[:subtopics_per_level]

            _log(
                f"  Level {depth} done — {len(level_elaborations)} elaborations, "
                f"{len(current_subtopics)} sub-subtopics queued"
            )

        # ── SYNTHESIS ─────────────────────────────────────────────────────────
        total_elab = len(results["all_elaborations"])
        _log("")
        _log_section(f"SYNTHESIS | domain={domain} | total_elaborations={total_elab}")

        final_question = (
            f"Based on all evidence, what are the optimal governance mechanisms "
            f"for {domain} policy in the United States, considering national, state, "
            f"and county perspectives?"
        )
        final_conjecture = self.form_conjecture(
            question=final_question,
            context=context,
            evidence=results["all_elaborations"][:20],
            domain=domain,
            max_tokens=700,
        )
        results["final_conjecture"] = final_conjecture

        _log(f"  conjecture confidence: {final_conjecture.get('confidence', 0):.2f}")
        _log(f"  statement: {final_conjecture.get('statement', '')[:100]}…")

        # ── RANKING ───────────────────────────────────────────────────────────
        _log("")
        _log_section(f"RANKING SOLUTIONS | domain={domain}")
        best_solutions = self._rank_solutions_with_geographic_weighting(
            all_elaborations=results["all_elaborations"],
            domain=domain,
        )
        results["best_solutions"] = best_solutions
        _log(f"  solutions ranked: {len(best_solutions)}")
        for i, sol in enumerate(best_solutions[:5], 1):
            _log(
                f"  {i}. score={sol['score']:.3f} tier={sol['tier']} | {sol['solution'][:80]}…"
            )

        # ── FINAL SUMMARY ─────────────────────────────────────────────────────
        elapsed = (datetime.datetime.now() - started_at).total_seconds()
        _log("")
        _log_section(f"INVESTIGATION COMPLETE | domain={domain}")
        _log(f"  elapsed       : {elapsed:.1f}s")
        _log(f"  llm_calls     : {self._call_count}")
        _log(f"  total_tokens  : {self._total_tokens}")
        _log(f"  elaborations  : {total_elab}")
        _log(f"  best_solutions: {len(best_solutions)}")
        _log(f"  confidence    : {final_conjecture.get('confidence', 0):.2f}")
        _log(f"  audit_log     : {_LOG_FILE}")
        _log("")

        _audit("=" * 120)
        _audit(f"SESSION END  domain={domain}  elapsed={elapsed:.1f}s")
        _audit(
            f"  llm_calls={self._call_count}  total_tokens={self._total_tokens}  elaborations={total_elab}"
        )
        _audit(f"  confidence={final_conjecture.get('confidence', 0):.2f}")
        _audit("=" * 120)
        _audit("")

        results["elapsed_seconds"] = elapsed
        results["llm_calls"] = self._call_count
        results["total_tokens"] = self._total_tokens
        return results

    # ──────────────────────────────────────────────────────────────────────────
    # Geographic fan-out
    # ──────────────────────────────────────────────────────────────────────────

    def _geographic_fan_out(
        self,
        domain: str,
        subtopic: str,
        depth: int,
        principles: List[str],
        prior_reasoning: str,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Investigate a subtopic across all 50 states and representative counties.

        Returns:
            Tuple of (state_elaborations, county_elaborations)
        """
        state_entries: List[Dict[str, Any]] = []
        county_entries: List[Dict[str, Any]] = []

        # ── All 50 states ─────────────────────────────────────────────────────
        for abbr, state_data in US_STATES.items():
            state_name = state_data["name"]
            state_pop = state_data["population"]
            _log(f"    🏛️  STATE {abbr} | {state_name} | pop={state_pop:,}")
            reasoning = self.investigate_subtopic(
                domain=domain,
                subtopic=subtopic,
                tier="state",
                tier_label=state_name,
                tier_population=state_pop,
                depth=depth,
                principles=principles,
                parent_context=prior_reasoning,
            )
            elab = self.elaborate_subtopic(
                domain=domain,
                subtopic=subtopic,
                tier="state",
                tier_label=state_name,
                tier_population=state_pop,
                depth=depth,
                principles=principles,
                prior_reasoning=reasoning,
            )
            entry: Dict[str, Any] = {
                "domain": domain,
                "subtopic": subtopic,
                "tier": "state",
                "tier_label": state_name,
                "state_abbr": abbr,
                "tier_population": state_pop,
                "depth": depth,
                "reasoning": reasoning,
                "elaboration": elab,
                "finding": (reasoning + " " + elab)[:600],
            }
            state_entries.append(entry)

        # ── Representative counties ───────────────────────────────────────────
        for county_data in REPRESENTATIVE_COUNTIES:
            county_name = county_data["name"]
            county_pop = county_data["population"]
            county_type = county_data.get("type", "mixed")
            _log(f"    🏘️  COUNTY {county_name} ({county_type}) | pop={county_pop:,}")
            reasoning = self.investigate_subtopic(
                domain=domain,
                subtopic=subtopic,
                tier="county",
                tier_label=county_name,
                tier_population=county_pop,
                depth=depth,
                principles=principles,
                parent_context=prior_reasoning,
            )
            elab = self.elaborate_subtopic(
                domain=domain,
                subtopic=subtopic,
                tier="county",
                tier_label=county_name,
                tier_population=county_pop,
                depth=depth,
                principles=principles,
                prior_reasoning=reasoning,
            )
            entry = {
                "domain": domain,
                "subtopic": subtopic,
                "tier": "county",
                "tier_label": county_name,
                "state_abbr": county_data["state"],
                "county_type": county_type,
                "tier_population": county_pop,
                "depth": depth,
                "reasoning": reasoning,
                "elaboration": elab,
                "finding": (reasoning + " " + elab)[:600],
            }
            county_entries.append(entry)

        return state_entries, county_entries

    # ──────────────────────────────────────────────────────────────────────────
    # Ranking
    # ──────────────────────────────────────────────────────────────────────────

    def _rank_solutions_with_geographic_weighting(
        self,
        all_elaborations: List[Dict[str, Any]],
        domain: str,
    ) -> List[Dict[str, Any]]:
        """Rank all elaborations by quality score × geographic tier weight."""
        tier_weights = {
            "national": 1.0,
            "state": 0.8,
            "county": 0.6,
        }
        solutions: List[Dict[str, Any]] = []
        for elab in all_elaborations:
            tier = elab.get("tier", "national")
            weight = tier_weights.get(tier, 0.5)
            text = elab.get("finding", elab.get("reasoning", ""))
            # Quality score: length (capped) × quality keywords × tier weight
            length_score = min(1.0, len(text) / 800)
            keywords = [
                "equit",
                "access",
                "afford",
                "implement",
                "evidence",
                "outcome",
                "stakeholder",
                "fund",
                "reform",
                "impact",
            ]
            kw_score = sum(0.1 for kw in keywords if kw in text.lower())
            score = (length_score + kw_score) * weight
            solutions.append(
                {
                    "solution": text[:300],
                    "tier": tier,
                    "tier_label": elab.get("tier_label", ""),
                    "domain": domain,
                    "subtopic": elab.get("subtopic", ""),
                    "depth": elab.get("depth", 0),
                    "score": round(score, 4),
                    "should_capture": score > 0.5,
                }
            )
        solutions.sort(key=lambda x: x["score"], reverse=True)
        return solutions

    # ──────────────────────────────────────────────────────────────────────────
    # Subtopic extraction
    # ──────────────────────────────────────────────────────────────────────────

    def _extract_subtopics_from_text(
        self,
        text: str,
        domain: str,
        count: int,
    ) -> List[str]:
        """
        Extract subtopic strings from LLM-generated text.

        Strategy:
          1. Look for numbered list items  (1. ... / 1) ...)
          2. Look for bold markdown (**Topic**)
          3. Look for bullet lines (- / * / •)
          4. Fall back to domain seed list
        """
        extracted: List[str] = []
        seen: set = set()

        patterns = [
            r"^\s*\d+[.)]\s+\*{0,2}([A-Z][^\n*]{4,80}?)\*{0,2}\s*$",  # numbered
            r"\*\*([A-Z][^*\n]{4,80}?)\*\*",  # bold
            r"^\s*[-*•]\s+([A-Z][^\n]{4,80}?)\s*$",  # bullets
        ]
        for pattern in patterns:
            for m in re.finditer(pattern, text, re.MULTILINE):
                candidate = m.group(1).strip(" .:,")
                key = candidate.lower()
                if key not in seen and len(candidate) > 5:
                    seen.add(key)
                    extracted.append(candidate)
                    if len(extracted) >= count:
                        return extracted

        # Fallback to domain seed list
        seeds = DOMAIN_SUBTOPICS.get(domain.lower(), [])
        for seed in seeds:
            key = seed.lower()
            if key not in seen:
                seen.add(key)
                extracted.append(seed)
                if len(extracted) >= count:
                    break

        return extracted[:count]

    # ──────────────────────────────────────────────────────────────────────────
    # Response parsers
    # ──────────────────────────────────────────────────────────────────────────

    def _parse_conjecture(
        self,
        response: str,
        question: str,
        evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Parse the conjecture response into a structured dict."""
        statement = ""
        confidence = 0.75
        supporting: List[str] = []
        contradicting: List[str] = []
        current_section: Optional[str] = None

        for raw_line in response.splitlines():
            line = raw_line.strip()
            if not line:
                current_section = None
                continue
            low = line.lower()
            if low.startswith(("conjecture:", "statement:", "1.")):
                current_section = "statement"
                after_colon = line.split(":", 1)[-1].strip() if ":" in line else line
                statement += (" " + after_colon).strip()
            elif low.startswith("confidence:"):
                m = re.search(r"([0-9]+\.?[0-9]*)", line)
                if m:
                    val = float(m.group(1))
                    confidence = val / 100 if val > 1.0 else val
            elif "support" in low and ":" in low:
                current_section = "supporting"
            elif "contradict" in low or "challenge" in low:
                current_section = "contradicting"
            elif line.startswith(("-", "*", "•")):
                item = line.lstrip("-*• ").strip()
                if current_section == "supporting":
                    supporting.append(item)
                elif current_section == "contradicting":
                    contradicting.append(item)
            elif current_section == "statement":
                statement += " " + line

        if not statement:
            # Use first non-empty substantial line
            for line in response.splitlines():
                if len(line.strip()) > 20:
                    statement = line.strip()
                    break
        if not statement:
            statement = f"Based on the evidence, optimal {question} requires multi-tiered governance."

        return {
            "statement": statement.strip()[:600],
            "confidence": max(0.0, min(1.0, confidence)),
            "supporting_evidence": supporting[:10],
            "contradicting_evidence": contradicting[:10],
            "update_reason": "LLM synthesis via llama.cpp",
            "evidence_count": len(evidence),
        }

    def _parse_analysis(
        self,
        response: str,
        topic: str,
    ) -> Dict[str, Any]:
        """Parse analysis response."""
        findings = response[:500] if response else f"Analysis of {topic}."
        recommendations: List[str] = []
        implementation: List[str] = []
        outcomes: List[str] = []
        consensus = 0.75
        current_section: Optional[str] = None

        for raw_line in response.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            low = line.lower()
            if "recommend" in low and ":" in low:
                current_section = "rec"
            elif "implement" in low and ":" in low:
                current_section = "impl"
            elif "outcome" in low and ":" in low:
                current_section = "out"
            elif "consensus" in low:
                m = re.search(r"([0-9]+\.?[0-9]*)", line)
                if m:
                    val = float(m.group(1))
                    consensus = val / 100 if val > 1.0 else val
            elif line.startswith(("-", "*", "•")):
                item = line.lstrip("-*• ").strip()
                if current_section == "rec":
                    recommendations.append(item)
                elif current_section == "impl":
                    implementation.append(item)
                elif current_section == "out":
                    outcomes.append(item)

        return {
            "findings": findings,
            "consensus": max(0.0, min(1.0, consensus)),
            "recommendations": recommendations or ["Phased implementation"],
            "implementation": implementation or ["Pilot → evaluate → scale"],
            "outcomes": outcomes or ["Improved governance"],
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Legacy compatibility shims
    # ──────────────────────────────────────────────────────────────────────────

    def generate_reasoning(
        self,
        context: Dict[str, Any],
        research_questions: List[str],
        principles: List[str],
        max_tokens: int = 4096,
        domain: str = "general",
        tier: str = "national",
        depth: int = 0,
        subtopic: str = "",
    ) -> str:
        """Legacy shim — calls _call_llm with a concise prompt."""
        pop = context.get("population", US_NATIONAL_POPULATION)
        q = research_questions[0] if research_questions else "key policy considerations"
        prompt = (
            f"You are a {tier}-level policy expert on {domain}. "
            f"Population: {pop:,}. "
            + (f"Subtopic: {subtopic}. " if subtopic else "")
            + f"Answer: {q} "
            f"Principles: {', '.join(principles[:4])}. "
            f"Be specific and practical."
        )
        return self._call_llm(
            prompt,
            max_tokens=max_tokens,
            label=f"domain={domain} tier={tier} depth={depth}"
            + (f" sub={subtopic[:30]}" if subtopic else ""),
        )

    def _generate_fallback_reasoning(
        self,
        context: Dict[str, Any],
        principles: List[str],
    ) -> str:
        """Fallback when LLM unavailable."""
        return (
            f"Governance principles: {', '.join(principles[:5])}. "
            f"Population: {context.get('population', 'N/A')}. "
            "Multi-tiered representation ensures democratic accountability."
        )

    def _form_fallback_conjecture(
        self,
        question: str,
        evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Fallback conjecture when LLM unavailable."""
        return {
            "statement": f"Based on evidence: {question}",
            "confidence": 0.6 if evidence else 0.4,
            "supporting_evidence": [e.get("finding", "")[:100] for e in evidence[:3]],
            "contradicting_evidence": [],
            "update_reason": "Fallback (LLM unavailable)",
            "evidence_count": len(evidence),
        }

    def _generate_fallback_analysis(
        self,
        topic: str,
        research_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Fallback analysis when LLM unavailable."""
        return {
            "findings": f"Analysis of {topic} based on available data.",
            "consensus": 0.6,
            "recommendations": ["Phased policy rollout", "Stakeholder consultation"],
            "implementation": ["Pilot program", "Evaluation", "Scale-up"],
            "outcomes": ["Improved outcomes", "Higher satisfaction"],
        }
