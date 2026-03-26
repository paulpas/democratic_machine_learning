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

import collections
import datetime
import json
import logging
import logging.handlers
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

from src.config import get_config

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# LLM AUDIT LOGGER
# Writes every prompt and response to logs/llm_calls.log (rotating, 50 MB max,
# 5 backups).  When PYTHONLOGGING=DEBUG the same content also goes to stdout.
# ──────────────────────────────────────────────────────────────────────────────


def _get_log_dir() -> Path:
    """Resolve the audit-log directory from config (honours legacy LLM_LOG_DIR too)."""
    cfg_dir = get_config().llm.log_dir
    if cfg_dir:
        return Path(cfg_dir)
    return Path(os.environ.get("LLM_LOG_DIR", Path(__file__).resolve().parents[2] / "logs"))


_LOG_DIR = _get_log_dir()
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOG_DIR / "llm_calls.log"

# True when PYTHONLOGGING=DEBUG is set in the environment
_DEBUG_TO_STDOUT: bool = os.environ.get("PYTHONLOGGING", "").upper() == "DEBUG"

# Module-level audit logger — one shared instance for the whole process.
# Guard against duplicate handlers when the module is imported multiple times
# within the same process (e.g. DecisionEngine creates its own LLMClient).
_audit_logger = logging.getLogger("llm.audit")
_audit_logger.setLevel(logging.DEBUG)
_audit_logger.propagate = False  # don't bubble up to root logger


def _has_handler(logger: logging.Logger, handler_type: type) -> bool:
    """Return True if logger already has a handler of exactly the given type.

    Uses exact type matching (type(h) is handler_type) not isinstance, because
    RotatingFileHandler is a subclass of StreamHandler and isinstance would
    incorrectly match the file handler when checking for a stdout StreamHandler.
    """
    return any(type(h) is handler_type for h in logger.handlers)


# Rotating file handler — always active, added only once
if not _has_handler(_audit_logger, logging.handlers.RotatingFileHandler):
    _llm_cfg = get_config().llm
    _file_handler = logging.handlers.RotatingFileHandler(
        _LOG_FILE,
        maxBytes=_llm_cfg.log_max_bytes,
        backupCount=_llm_cfg.log_backup_count,
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

# Stdout handler is added lazily on first _audit() call when PYTHONLOGGING=DEBUG.
# This ensures it works even when the env var is set after module import.


def _audit(msg: str) -> None:
    """Write a message to the audit log (and stdout if DEBUG mode).

    PYTHONLOGGING=DEBUG is re-evaluated on every call so it can be set
    after module import (e.g. in tests or via env change at runtime).
    """
    _audit_logger.debug(msg)

    # Re-check DEBUG flag each call — ensures the stdout handler is added
    # even if the env var was set after the module was first imported.
    if os.environ.get("PYTHONLOGGING", "").upper() == "DEBUG":
        if not _has_handler(_audit_logger, logging.StreamHandler):
            _sh = logging.StreamHandler(sys.stdout)
            _sh.setLevel(logging.DEBUG)
            _sh.setFormatter(
                logging.Formatter(
                    fmt="[DEBUG %(asctime)s] %(message)s",
                    datefmt="%H:%M:%S",
                )
            )
            _audit_logger.addHandler(_sh)

    # Force immediate flush — no buffering lag on file or stdout
    for h in _audit_logger.handlers:
        h.flush()


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


def estimate_calls(
    max_depth: Optional[int] = None,
    subtopics_per_level: Optional[int] = None,
    geo_fan_out: Optional[bool] = None,
    domains: Optional[int] = None,
    combine_geo: Optional[bool] = None,
    progressive_synthesis: Optional[bool] = None,
) -> Dict[str, Any]:
    """Calculate the estimated total LLM calls for a given configuration.

    Call structure per domain:
      Level 0 : 1 call  (initial domain overview)
      Levels 1..max_depth, per subtopic:
        national investigate  : 1
        national elaborate    : 1
        state (combined)×50   : 50   ⎫ combine_geo=True  (was 100)
        county (combined)×10  : 10   ⎬
        intermediate subtopic : 1    ⎭ progressive_synthesis=True
      Per-level intermediate  : 1/level   progressive_synthesis=True
      Synthesis               : 1 call  (form_conjecture)

    Args:
        max_depth:             Recursion depth
        subtopics_per_level:   Subtopics per level
        geo_fan_out:           Include state/county fan-out
        domains:               Number of domains to run (default: 6)
        combine_geo:           Use combined investigate+elaborate for geo tiers
        progressive_synthesis: Use per-subtopic + per-level intermediate conjectures

    Returns:
        Dict with breakdown, calls_per_domain, total_calls, etc.
    """
    cfg = get_config()
    if max_depth is None:
        max_depth = cfg.llm.max_depth
    if subtopics_per_level is None:
        subtopics_per_level = cfg.llm.subtopics_per_level
    if geo_fan_out is None:
        geo_fan_out = cfg.voter_pool.prod_geo_fan_out
    if domains is None:
        domains = 6
    if combine_geo is None:
        combine_geo = cfg.llm.combine_geo_investigate_elaborate
    if progressive_synthesis is None:
        progressive_synthesis = cfg.llm.progressive_synthesis

    n_states = len(US_STATES)  # 50
    n_counties = len(REPRESENTATIVE_COUNTIES)  # 10

    # calls per one subtopic at any depth level
    if geo_fan_out:
        geo_calls = (n_states + n_counties) if combine_geo else (n_states + n_counties) * 2
        calls_per_subtopic = 2 + geo_calls  # 2 national + geo
    else:
        calls_per_subtopic = 2  # national only

    # intermediate conjecture calls per subtopic (progressive synthesis)
    intermediate_per_subtopic = 1 if (progressive_synthesis and geo_fan_out) else 0
    # intermediate conjecture calls per depth level
    intermediate_per_level = 1 if (progressive_synthesis and geo_fan_out) else 0

    calls_per_domain = (
        1  # level 0
        + max_depth * subtopics_per_level * (calls_per_subtopic + intermediate_per_subtopic)
        + max_depth * intermediate_per_level  # per-level
        + 1  # final synthesis
    )
    total_calls = calls_per_domain * domains

    geo_mode = "combined (1 call/tier)" if combine_geo else "separate (2 calls/tier)"
    if geo_fan_out:
        geo_note = (
            f"  geo breakdown : 2 national + {n_states} states + {n_counties} counties"
            f" ({geo_mode}) = {calls_per_subtopic} calls/subtopic"
        )
    else:
        geo_note = "  geo breakdown : 2 national only (geo_fan_out=false)"

    ps_note = (
        f"  progressive   : +{intermediate_per_subtopic}/subtopic + {intermediate_per_level}/level"
        if progressive_synthesis
        else "  progressive   : disabled"
    )

    calls_formula = (
        f"1 + {max_depth}×{subtopics_per_level}×({calls_per_subtopic}+{intermediate_per_subtopic})"
        f" + {max_depth}×{intermediate_per_level} + 1"
    )

    breakdown = "\n".join(
        [
            f"  max_depth           : {max_depth}",
            f"  subtopics_per_level : {subtopics_per_level}",
            f"  geo_fan_out         : {geo_fan_out}",
            f"  combine_geo         : {combine_geo}",
            f"  progressive_synth   : {progressive_synthesis}",
            geo_note,
            ps_note,
            f"  calls_per_subtopic  : {calls_per_subtopic} (+{intermediate_per_subtopic} intermediate)",
            f"  calls_per_domain    : {calls_formula} = {calls_per_domain}",
            f"  domains             : {domains}",
            "  ─────────────────────────────────────────────",
            f"  TOTAL ESTIMATED     : {total_calls:,} LLM calls",
        ]
    )

    return {
        "max_depth": max_depth,
        "subtopics_per_level": subtopics_per_level,
        "geo_fan_out": geo_fan_out,
        "combine_geo": combine_geo,
        "progressive_synthesis": progressive_synthesis,
        "n_states": n_states,
        "n_counties": n_counties,
        "calls_per_subtopic": calls_per_subtopic,
        "intermediate_per_subtopic": intermediate_per_subtopic,
        "intermediate_per_level": intermediate_per_level,
        "calls_per_domain": calls_per_domain,
        "total_calls": total_calls,
        "domains": domains,
        "breakdown": breakdown,
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
            endpoint: Llama.cpp endpoint URL.  Defaults to ``config.yaml``
                      ``llm.endpoint`` (or the legacy ``LLAMA_CPP_ENDPOINT`` env var).
            model: Model name label.  Defaults to ``config.yaml`` ``llm.model``.
        """
        _cfg = get_config().llm
        self.endpoint = endpoint or os.environ.get("LLAMA_CPP_ENDPOINT", "") or _cfg.endpoint
        self.model = model or os.environ.get("LLAMA_MODEL", "") or _cfg.model
        self.timeout = int(os.environ.get("LLAMA_TIMEOUT", "") or _cfg.timeout_seconds)
        self._cfg = _cfg  # keep reference for per-call token budgets etc.

        # Thread-safe counters (multiple threads share one LLMClient instance)
        self._lock = threading.Lock()
        self._call_count: int = 0  # resets each domain (for per-domain progress)
        self._lifetime_calls: int = 0  # never resets — true total across all domains
        self._total_tokens: int = 0
        self._total_calls_estimate: int = 0  # per-domain estimate (1 domain)
        self._lifetime_calls_estimate: int = 0  # total estimate across all domains
        # Rolling window of recent call durations (seconds) for ETA estimation.
        # Capped at 20 so ETA adapts to current model speed without ancient history skewing it.
        self._call_durations: Deque[float] = collections.deque(maxlen=20)

        # Singleton WebSearcher — created once, reused across all calls.
        # Creating a new WebSearcher per call would reinitialise Playwright 700+
        # times per domain run.  Closed via self.close().
        self._web_searcher: Optional[Any] = None
        if get_config().web_search.enabled:
            try:
                from src.llm.web_search import WebSearcher

                self._web_searcher = WebSearcher()
            except Exception as _ws_err:
                logger.warning(f"WebSearcher init failed: {_ws_err}")

        self.available = self._test_connection()
        if self.available:
            _log(f"✅ LLM endpoint connected: {self.endpoint}")
        else:
            _log(f"⚠️  LLM endpoint unavailable: {self.endpoint} — using fallback")

        # Determine worker count and set up the semaphore that caps concurrency
        self._workers: int = self._resolve_workers()
        self._semaphore = threading.Semaphore(self._workers)
        if self._workers > 1:
            _log(
                f"⚡ Parallel mode: {self._workers} concurrent slots "
                f"(llama-server --parallel {self._workers})"
            )
        else:
            _log("  Sequential mode: 1 worker (set llm.parallel_workers > 1 to enable parallel)")

    # ──────────────────────────────────────────────────────────────────────────
    # Connection test and worker-count resolution
    # ──────────────────────────────────────────────────────────────────────────

    def _test_connection(self) -> bool:
        """Test if the llama.cpp endpoint is available."""
        try:
            data = json.dumps({"prompt": "Hi", "max_tokens": 5, "temperature": 0.0}).encode("utf-8")
            req = urllib.request.Request(
                f"{self.endpoint}/completion",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            connect_timeout = self._cfg.connect_test_timeout
            with urllib.request.urlopen(req, timeout=connect_timeout) as response:
                return response.getcode() == 200
        except Exception:
            return False

    def _probe_server_slots(self) -> int:
        """Query llama.cpp /props to discover how many parallel slots are configured.

        llama-server exposes GET /props which returns JSON including
        ``"n_ctx_train"``, ``"total_slots"``, and (in newer builds) ``"n_parallel"``.
        We read ``total_slots`` first, then fall back to ``n_parallel``.

        Returns the slot count, or 1 if the endpoint is unavailable or doesn't
        support /props.
        """
        try:
            req = urllib.request.Request(
                f"{self.endpoint}/props",
                headers={"Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self._cfg.connect_test_timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                # newer llama.cpp: "total_slots" field
                if "total_slots" in data and isinstance(data["total_slots"], int):
                    return max(1, int(data["total_slots"]))
                # older builds: "n_parallel"
                if "n_parallel" in data and isinstance(data["n_parallel"], int):
                    return max(1, int(data["n_parallel"]))
        except Exception as exc:
            _log(f"  ℹ️  /props probe failed ({exc}); defaulting to 1 worker")
        return 1

    def _resolve_workers(self) -> int:
        """Determine how many parallel workers to use.

        Logic:
          - If ``llm.parallel_workers == 0``: auto-probe the server via /props.
          - If ``llm.parallel_workers >= 1``: use that value directly.
          - If server is unavailable: always 1.
        """
        if not self.available:
            return 1
        configured = self._cfg.parallel_workers
        if configured == 0:
            detected = self._probe_server_slots()
            _log(f"  🔍 Auto-detected {detected} parallel slot(s) from server /props")
            return detected
        return max(1, configured)

    def close(self) -> None:
        """Release resources held by this client (WebSearcher browser, etc.)."""
        if self._web_searcher is not None:
            try:
                self._web_searcher.close()
            except Exception:
                pass
            self._web_searcher = None

    def _eta_str(self, completed: int) -> str:
        """Return a human-readable ETA string based on recent call durations.

        Uses the rolling average of the last N call durations (self._call_durations)
        divided by the number of parallel workers to estimate wall-clock time
        remaining for the calls not yet completed.

        Args:
            completed: Number of calls completed so far (including this one).

        Returns:
            ETA string like 'ETA ~1h 23m' or 'ETA ~45m' or 'ETA ~30s',
            or '' if not enough data yet.
        """
        total = self._total_calls_estimate
        if not total or not self._call_durations:
            return ""
        remaining = max(0, total - completed)
        if remaining == 0:
            return "ETA done"
        avg_secs = sum(self._call_durations) / len(self._call_durations)
        # With N parallel workers each slot is busy avg_secs seconds, so wall
        # clock time per 'batch' is avg_secs / workers.
        eta_secs = avg_secs * remaining / max(1, self._workers)
        if eta_secs < 60:
            return f"ETA ~{eta_secs:.0f}s"
        elif eta_secs < 3600:
            return f"ETA ~{eta_secs / 60:.0f}m"
        else:
            h = int(eta_secs // 3600)
            m = int((eta_secs % 3600) // 60)
            return f"ETA ~{h}h {m:02d}m"

    # ──────────────────────────────────────────────────────────────────────────
    # Web search helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _derive_search_query_from_label(label: str) -> str:
        """Build a targeted web search query from a structured call label.

        Label examples:
          "domain=economy subtopic=Wage Growth tier=state:California depth=2"
          "conjecture domain=economy"
          "intermediate subtopic=Wage Growth depth=1 domain=economy"
          "domain=healthcare tier=national depth=0"

        Returns a short query string like:
          "economy Wage Growth California policy current"
          "economy governance United States optimal policy current"
        """
        year = datetime.datetime.now().year
        domain = ""
        subtopic = ""
        tier_label = ""
        call_type = "policy"

        # Extract domain
        m = re.search(r"domain=([a-zA-Z_]+)", label)
        if m:
            domain = m.group(1).replace("_", " ")

        # Extract subtopic
        m = re.search(r"subtopic=([^|]+?)(?:\s+tier=|\s+depth=|$)", label)
        if m:
            subtopic = m.group(1).strip()

        # Extract tier label (state/county name)
        m = re.search(r"tier=(?:state|county):([^|\s]+(?:\s+[^|\s]+)*?)(?:\s+depth=|$)", label)
        if m:
            tier_label = m.group(1).strip()

        # Determine call type for better query tailoring
        if "conjecture" in label:
            call_type = "governance optimal policy"
        elif "intermediate" in label and "subtopic" in label:
            call_type = "state variations policy implications"
        elif "intermediate" in label:
            call_type = "policy framework cross-cutting themes"
        elif "elaborate" in label:
            call_type = "policy evidence equity implementation"

        parts = [p for p in [domain, subtopic, tier_label, call_type, str(year)] if p]
        return " ".join(parts)

    def _fetch_web_context(self, query: str) -> str:
        """Run a web search and return formatted context string for prompt injection.

        Uses the singleton WebSearcher.  Returns empty string on any failure so
        callers can unconditionally prepend the result without error handling.
        """
        if not self._web_searcher or not query:
            return ""
        try:
            from src.llm.web_search import format_search_results_for_llm

            ws_cfg = get_config().web_search
            results = self._web_searcher.search(
                query,
                max_results=ws_cfg.max_results_in_prompt,
                use_cache=True,
            )
            if results:
                logger.info(f"✅ Web search: {len(results)} results for '{query[:60]}'")
                return format_search_results_for_llm(
                    results,
                    max_snippet_length=ws_cfg.max_snippet_length,
                    max_results=ws_cfg.max_results_in_prompt,
                )
            logger.debug(f"Web search returned no results for '{query[:60]}'")
        except Exception as exc:
            logger.warning(f"Web search failed for '{query[:60]}': {exc}")
        return ""

    # ──────────────────────────────────────────────────────────────────────────
    # Core LLM call — single responsibility, full logging
    # ──────────────────────────────────────────────────────────────────────────

    def _call_llm(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        label: str = "",
        search_query: Optional[str] = None,
    ) -> str:
        """
        Send a single prompt to the LLM endpoint and return the response text.

        Thread-safe: multiple threads may call this simultaneously up to
        ``self._workers`` concurrent requests.  Each attempt acquires the
        semaphore, fires the HTTP request, and releases the semaphore on exit.
        On 503 (slot busy) or transient errors the call is retried with
        exponential backoff up to ``llm.parallel_max_retries`` attempts.

        Args:
            prompt:      The prompt string.
            max_tokens:  Token budget for the response.
            temperature: Sampling temperature.
            label:       Human-readable label for logging (domain/tier/subtopic).

        Returns:
            The generated text, or an empty string on failure.
        """
        # Resolve defaults from config when callers pass None
        _cfg = self._cfg
        if max_tokens is None:
            max_tokens = _cfg.max_tokens_default
        if temperature is None:
            temperature = _cfg.temperature_default

        if not self.available:
            _log(f"  ⚠️  LLM unavailable — skipping call [{label}]")
            _audit(f"LLM SKIPPED  |  {label}  |  endpoint unavailable")
            return ""

        # Thread-safe call number allocation
        with self._lock:
            self._call_count += 1
            self._lifetime_calls += 1
            call_num = self._call_count
            lifetime_num = self._lifetime_calls

        _log("")
        if self._total_calls_estimate:
            progress = f"{call_num}/{self._total_calls_estimate}"
            pct = call_num / self._total_calls_estimate * 100
            eta = self._eta_str(call_num - 1)  # ETA before this call completes
            eta_part = f"  {eta}" if eta else ""
            # Show lifetime total when running multiple domains
            if (
                self._lifetime_calls_estimate
                and self._lifetime_calls_estimate != self._total_calls_estimate
            ):
                lifetime_part = f"  [total {lifetime_num}/{self._lifetime_calls_estimate}]"
            else:
                lifetime_part = ""
            _log(f"  🔄 LLM CALL {progress} ({pct:.1f}%){eta_part}{lifetime_part} | {label}")
        else:
            _log(f"  🔄 LLM CALL #{call_num} | {label}")
        _log(
            f"     prompt_chars={len(prompt)}  max_tokens={max_tokens}  "
            f"temp={temperature}  workers={self._workers}"
        )
        _log(f"     endpoint={self.endpoint}/completion")

        # ── Web search: inject real-time internet context into every call ──────
        # Auto-derive query from label when caller didn't supply one.
        # Uses the singleton WebSearcher so no browser is re-initialised per call.
        if get_config().web_search.enabled:
            _sq = search_query or self._derive_search_query_from_label(label)
            if _sq:
                logger.info(f"🔍 Web search: '{_sq[:80]}'")
                web_ctx = self._fetch_web_context(_sq)
                if web_ctx:
                    prompt = f"[Recent web information — {datetime.datetime.now().strftime('%Y-%m-%d')}]\n{web_ctx}\n\n{prompt}"

        _audit_call(
            call_number=call_num,
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
            # Sampling params must be explicit in the POST body — llama.cpp CLI
            # flags (--top-p, --min-p, --top-k, --seed) are NOT automatically
            # applied to API requests; they only set server-side defaults that
            # get overridden by whatever the client sends (or doesn't send).
            "top_p": _cfg.top_p,
            "min_p": _cfg.min_p,
            "top_k": _cfg.top_k,
            "seed": _cfg.seed,
        }

        max_retries = _cfg.parallel_max_retries
        base_wait = _cfg.parallel_retry_base_wait
        max_wait = _cfg.parallel_retry_max_wait

        for attempt in range(max_retries + 1):
            # Acquire a slot before sending — this is the concurrency gate.
            # At most `_workers` threads may be inside this block simultaneously.
            self._semaphore.acquire()
            released = False  # track whether we released early for a retry
            t_start = datetime.datetime.now()
            try:
                raw_data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    f"{self.endpoint}/completion",
                    data=raw_data,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    content = result.get("content", "").strip()
                    tokens = result.get("tokens_predicted", len(content.split()))
                    elapsed_ms = (datetime.datetime.now() - t_start).total_seconds() * 1000

                    with self._lock:
                        self._total_tokens += tokens
                        total_tok = self._total_tokens
                        self._call_durations.append(elapsed_ms / 1000)
                        eta_after = self._eta_str(call_num)

                    _log(
                        f"  ✅ RESPONSE #{call_num}  tokens={tokens}  "
                        f"elapsed={elapsed_ms / 1000:.1f}s  cumulative={total_tok}"
                        + (f"  {eta_after}" if eta_after else "")
                    )
                    _preview_len = _cfg.preview_chars
                    preview = content[:_preview_len].replace("\n", " ")
                    _log(f"     preview: {preview}{'…' if len(content) > _preview_len else ''}")
                    _audit_response(
                        call_number=call_num,
                        label=label,
                        content=content,
                        tokens=tokens,
                        cumulative_tokens=total_tok,
                        elapsed_ms=elapsed_ms,
                    )
                    return content

            except urllib.error.HTTPError as exc:
                # 503 = all slots busy; 429 = rate-limited — both are retryable
                if exc.code in (429, 503) and attempt < max_retries:
                    wait = min(max_wait, base_wait * (2**attempt))
                    _log(
                        f"  ⏳ HTTP {exc.code} on call #{call_num} "
                        f"(attempt {attempt + 1}/{max_retries + 1}) — "
                        f"retrying in {wait:.1f}s"
                    )
                    _audit(
                        f"RETRY  call={call_num}  label={label}  "
                        f"http={exc.code}  attempt={attempt + 1}  wait={wait:.1f}s"
                    )
                    self._semaphore.release()
                    released = True
                    time.sleep(wait)
                    continue
                _log(f"  ❌ HTTP ERROR #{call_num}: {exc}")
                _audit_error(call_num, label, exc)
                return ""

            except Exception as exc:
                # Retry on timeout / connection reset
                is_timeout = "timed out" in str(exc).lower() or "timeout" in str(exc).lower()
                if is_timeout and attempt < max_retries:
                    wait = min(max_wait, base_wait * (2**attempt))
                    _log(
                        f"  ⏳ TIMEOUT on call #{call_num} "
                        f"(attempt {attempt + 1}/{max_retries + 1}) — "
                        f"retrying in {wait:.1f}s"
                    )
                    self._semaphore.release()
                    released = True
                    time.sleep(wait)
                    continue
                _log(f"  ❌ LLM ERROR #{call_num}: {exc}")
                _audit_error(call_num, label, exc)
                return ""

            finally:
                if not released:
                    self._semaphore.release()

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
            max_tokens=self._cfg.max_tokens_domain_initial,
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
        search_query: Optional[str] = None,
    ) -> str:
        """Investigate a subtopic at a specific geographic tier."""
        context_snippet = (
            parent_context[: self._cfg.context_snippet_chars] if parent_context else ""
        )
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
            max_tokens=self._cfg.max_tokens_subtopic,
            label=f"domain={domain} subtopic={subtopic[:30]} tier={tier}:{tier_label[:20]} depth={depth}",
            search_query=search_query,
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
        search_query: Optional[str] = None,
    ) -> str:
        """Deep elaboration on a subtopic — calls after initial investigation."""
        snippet = prior_reasoning[: self._cfg.prior_snippet_chars] if prior_reasoning else ""
        prompt = (
            f"Elaborate further on '{subtopic}' in {domain} policy at the {tier} level "
            f"({tier_label}, population {tier_population:,}). "
            f"Prior analysis: {snippet} "
            f"Provide: evidence for each approach, equity implications, "
            f"stakeholder concerns, and measurable success metrics."
        )
        return self._call_llm(
            prompt,
            max_tokens=self._cfg.max_tokens_elaboration,
            label=f"elaborate domain={domain} subtopic={subtopic[:30]} tier={tier}:{tier_label[:20]} depth={depth}",
            search_query=search_query,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Combined investigate+elaborate for geo tiers (state / county)
    # ──────────────────────────────────────────────────────────────────────────

    def _investigate_and_elaborate_combined(
        self,
        domain: str,
        subtopic: str,
        tier: str,
        tier_label: str,
        tier_population: int,
        depth: int,
        principles: List[str],
        parent_context: str = "",
        search_query: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Single LLM call covering both investigation AND elaboration for a geo tier.

        Replaces two serial calls (investigate_subtopic + elaborate_subtopic) for
        state/county tiers, cutting geo fan-out calls by ~50%.

        Returns:
            Tuple of (reasoning, elaboration) strings.  If the model doesn't use
            the ## Part 2 delimiter the full response goes into reasoning.
        """
        context_snippet = (
            parent_context[: self._cfg.context_snippet_chars] if parent_context else ""
        )
        prompt = (
            f"You are a US {tier}-level policy expert analyzing '{subtopic}' "
            f"as part of {domain} policy for {tier_label} (population {tier_population:,}).\n\n"
            f"## Part 1 — Investigation\n"
            f"Provide: (1) current state, (2) key challenges, (3) best policy approaches, "
            f"(4) implementation steps, (5) expected outcomes.\n"
            f"Principles: {', '.join(principles[:5])}.\n"
            + (f"Context: {context_snippet}\n\n" if context_snippet else "\n")
            + f"## Part 2 — Elaboration\n"
            f"Provide: evidence for each approach, equity implications, "
            f"stakeholder concerns, and measurable success metrics specific to {tier_label}."
        )
        raw = self._call_llm(
            prompt,
            max_tokens=self._cfg.max_tokens_geo_combined,
            label=f"domain={domain} subtopic={subtopic[:30]} tier={tier}:{tier_label[:20]} depth={depth}",
            search_query=search_query,
        )
        # Split on the Part 2 delimiter; fall back gracefully
        split_markers = ["## Part 2", "## part 2", "**Part 2", "Part 2 —", "Part 2:"]
        reasoning, elaboration = raw, ""
        for marker in split_markers:
            if marker in raw:
                parts = raw.split(marker, 1)
                reasoning = parts[0].strip()
                elaboration = parts[1].strip() if len(parts) > 1 else ""
                break
        return reasoning, elaboration

    # ──────────────────────────────────────────────────────────────────────────
    # Progressive synthesis — intermediate conjectures
    # ──────────────────────────────────────────────────────────────────────────

    def _intermediate_conjecture_subtopic(
        self,
        domain: str,
        subtopic: str,
        depth: int,
        nat_entry: Dict[str, Any],
        state_entries: List[Dict[str, Any]],
        county_entries: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Synthesise ALL geo findings for one subtopic into a compact conjecture.

        The prompt includes the full national finding (reasoning + elaboration) plus
        truncated per-state and per-county findings so every geographic tier influences
        the result.  This replaces the old behaviour of passing only the first 20
        elaborations (in insertion order) to the final conjecture call.
        """
        _cfg = self._cfg
        sc = _cfg.intermediate_state_chars
        cc = _cfg.intermediate_county_chars

        nat_text = (nat_entry.get("reasoning", "") + " " + nat_entry.get("elaboration", "")).strip()

        state_lines = "\n".join(
            f"- {e.get('tier_label', '?')} (pop {e.get('tier_population', 0):,}): "
            f"{(e.get('reasoning', '') + ' ' + e.get('elaboration', '')).strip()[:sc]}"
            for e in state_entries
        )

        county_lines = "\n".join(
            f"- {e.get('tier_label', '?')} ({e.get('county_type', 'mixed')}, "
            f"pop {e.get('tier_population', 0):,}): "
            f"{(e.get('reasoning', '') + ' ' + e.get('elaboration', '')).strip()[:cc]}"
            for e in county_entries
        )

        year = datetime.datetime.now().year
        prompt = (
            f"You are synthesising all geographic evidence for '{subtopic}' "
            f"within {domain} policy (analysis year: {year}).\n\n"
            f"NATIONAL FINDINGS:\n{nat_text[:1000]}\n\n"
            f"STATE FINDINGS — unique needs per state that must be accommodated:\n"
            f"{state_lines}\n\n"
            f"COUNTY FINDINGS — unique needs per county type:\n"
            f"{county_lines}\n\n"
            f"Provide:\n"
            f"1. Conjecture: A policy framework for '{subtopic}' that explicitly "
            f"accommodates every state and county's unique context\n"
            f"2. Confidence: 0.0–1.0\n"
            f"3. State variations: Top 5 states with needs diverging most from the "
            f"national picture\n"
            f"4. County variations: Key urban/suburban/rural distinctions requiring "
            f"tailored implementation\n"
            f"5. Supporting evidence: 3 strongest cross-tier consensus points\n"
            f"6. Contradictions: 3 tensions between geographic tiers to resolve"
        )
        raw = self._call_llm(
            prompt,
            max_tokens=_cfg.max_tokens_intermediate_subtopic,
            temperature=_cfg.temperature_intermediate,
            label=f"intermediate subtopic={subtopic[:40]} depth={depth} domain={domain}",
        )
        result = self._parse_conjecture(raw, subtopic, state_entries + county_entries)
        result["subtopic"] = subtopic
        result["depth"] = depth
        result["tier_count"] = 1 + len(state_entries) + len(county_entries)
        # Extract state/county variation bullets from raw response
        result["state_variations"] = self._extract_section(raw, "State variations")
        result["county_variations"] = self._extract_section(raw, "County variations")
        return result

    def _intermediate_conjecture_level(
        self,
        domain: str,
        depth: int,
        subtopic_conjectures: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Unify all per-subtopic conjectures for one depth level.

        Receives the list of subtopic_conjecture dicts produced by
        _intermediate_conjecture_subtopic() at this depth.
        """
        _cfg = self._cfg
        year = datetime.datetime.now().year

        summaries = []
        for i, sc in enumerate(subtopic_conjectures, 1):
            summaries.append(
                f"{i}. '{sc.get('subtopic', '?')}':\n"
                f"   Conjecture: {sc.get('statement', '')[:300]}\n"
                f"   State variations: {sc.get('state_variations', '')[:200]}\n"
                f"   County variations: {sc.get('county_variations', '')[:200]}\n"
                f"   Confidence: {sc.get('confidence', 0):.2f}"
            )

        prompt = (
            f"You are synthesising {len(subtopic_conjectures)} subtopic analyses "
            f"for depth-{depth} of {domain} policy (year: {year}).\n\n"
            f"SUBTOPIC SUMMARIES:\n" + "\n\n".join(summaries) + "\n\n"
            "Provide:\n"
            "1. Unified policy framework addressing all subtopics at this depth level\n"
            "2. Cross-subtopic tensions and how to resolve them\n"
            "3. Confidence: 0.0–1.0\n"
            "4. Key state/county needs appearing across multiple subtopics\n"
            "5. Supporting evidence: 3 strongest cross-subtopic consensus points\n"
            "6. Contradictions: 3 unresolved cross-subtopic tensions"
        )
        raw = self._call_llm(
            prompt,
            max_tokens=_cfg.max_tokens_intermediate_level,
            temperature=_cfg.temperature_intermediate,
            label=f"intermediate level={depth} domain={domain}",
        )
        result = self._parse_conjecture(raw, f"depth-{depth} synthesis", subtopic_conjectures)
        result["depth"] = depth
        result["subtopic_count"] = len(subtopic_conjectures)
        result["cross_subtopic_needs"] = self._extract_section(raw, "state/county needs")
        return result

    @staticmethod
    def _extract_section(text: str, heading_keyword: str, max_chars: int = 300) -> str:
        """Extract a bullet-list section from LLM response by keyword match."""
        lines = text.splitlines()
        collecting = False
        collected: List[str] = []
        for line in lines:
            if heading_keyword.lower() in line.lower() and ":" in line:
                collecting = True
                continue
            if collecting:
                if line.strip().startswith(("-", "*", "•", "1", "2", "3", "4", "5")):
                    collected.append(line.strip().lstrip("-*• 0123456789.)").strip())
                elif line.strip() == "":
                    if collected:
                        break
                else:
                    break
        return "; ".join(collected)[:max_chars]

    def form_conjecture(
        self,
        question: str,
        context: Dict[str, Any],
        evidence: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        domain: str = "general",
        use_level_conjectures: bool = False,
    ) -> Dict[str, Any]:
        """Form a final conjecture synthesizing all evidence.

        When ``use_level_conjectures=True`` the evidence list is treated as a
        list of level-conjecture dicts (from progressive synthesis) and a richer
        prompt is built that explicitly asks the model to accommodate all 50
        states and county-level diversity.
        """
        _cfg = self._cfg
        if max_tokens is None:
            max_tokens = _cfg.max_tokens_conjecture
        year = datetime.datetime.now().year

        if use_level_conjectures and evidence:
            # Build a rich prompt from per-level intermediate conjectures
            level_summaries = "\n\n".join(
                f"Depth-{e.get('depth', i + 1)} findings "
                f"({e.get('subtopic_count', '?')} subtopics):\n"
                f"  {e.get('statement', '')[:400]}\n"
                f"  State/county needs: {e.get('cross_subtopic_needs', '')[:200]}"
                for i, e in enumerate(evidence)
            )
            prompt = (
                f"Based on {len(evidence)} depth-level investigations of {domain} policy "
                f"(year: {year}), synthesise a final governance conjecture.\n\n"
                f"DEPTH-LEVEL SUMMARIES:\n{level_summaries}\n\n"
                f"Answer: {question}\n\n"
                f"Provide:\n"
                f"1. Conjecture statement: A final governance framework for {domain} policy "
                f"in the United States that explicitly accommodates all 50 states and "
                f"county-level diversity\n"
                f"2. Confidence: 0.0–1.0\n"
                f"3. Supporting evidence: Top 5 cross-tier consensus points\n"
                f"4. Contradictions: Key unresolved tensions between geographic tiers"
            )
        else:
            # Fallback: plain evidence list (used when progressive_synthesis=False)
            evidence_limit = _cfg.conjecture_evidence_limit
            evidence_text = "\n".join(
                f"- [{e.get('tier', '?')} depth={e.get('depth', 0)}] "
                f"{e.get('finding', e.get('reasoning', ''))[:200]}"
                for e in evidence[:evidence_limit]
            )
            prompt = (
                f"Based on the following evidence about {domain} policy (year: {year}), "
                f"answer: {question}\n\n"
                f"Evidence:\n{evidence_text}\n\n"
                f"Provide: (1) Conjecture statement, (2) Confidence 0-1, "
                f"(3) Top 3 supporting points, (4) Key contradictions."
            )
        raw = self._call_llm(
            prompt,
            max_tokens=max_tokens,
            temperature=_cfg.temperature_conjecture,
            label=f"conjecture domain={domain}",
        )
        return self._parse_conjecture(raw, question, evidence)

    def analyze_policy(
        self,
        topic: str,
        research_data: Dict[str, Any],
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Analyze a policy topic using LLM."""
        _cfg = self._cfg
        if max_tokens is None:
            max_tokens = _cfg.max_tokens_policy_analysis
        context_text = " | ".join(
            f"{k}: {str(v)[:80]}"
            for k, v in list(research_data.items())[: _cfg.analysis_context_limit]
        )
        prompt = (
            f"Analyze {topic} policy. Context: {context_text}. "
            f"Provide: key findings, consensus level 0-1, top 3 recommendations, "
            f"implementation steps, expected outcomes."
        )
        raw = self._call_llm(prompt, max_tokens=max_tokens, label=f"analyze policy={topic}")
        return self._parse_analysis(raw, topic)

    # ──────────────────────────────────────────────────────────────────────────
    # Deep recursive investigation — THE MAIN ENTRY POINT
    # ──────────────────────────────────────────────────────────────────────────

    def generate_reasoning_with_recursion(
        self,
        domain: str,
        initial_context: Dict[str, Any],
        max_depth: Optional[int] = None,
        subtopics_per_level: Optional[int] = None,
        principles: Optional[List[str]] = None,
        include_state_county_rep: bool = True,
        search_query: Optional[str] = None,
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
        # Resolve None defaults from config
        _cfg = self._cfg
        if max_depth is None:
            max_depth = _cfg.max_depth
        if subtopics_per_level is None:
            subtopics_per_level = _cfg.subtopics_per_level
        subtopics_per_level_int: int = subtopics_per_level

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
        principles_list: List[str] = principles

        started_at = datetime.datetime.now()

        # Reset per-domain counters so progress/ETA are relative to this domain,
        # not accumulated across all domains in a multi-domain run.
        with self._lock:
            self._call_count = 0
            self._call_durations.clear()

        # Pre-compute call estimate so every _call_llm can show X/total progress
        est = estimate_calls(
            max_depth=max_depth,
            subtopics_per_level=subtopics_per_level,
            geo_fan_out=include_state_county_rep,
            domains=1,
        )
        self._total_calls_estimate = est["calls_per_domain"]

        _log("")
        _log_section(f"DEEP RECURSIVE LLM INVESTIGATION  |  domain={domain}")
        _log(f"  started        : {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        _log(f"  max_depth      : {max_depth}")
        _log(f"  subtopics/level: {subtopics_per_level}")
        _log(f"  geo_rep        : {include_state_county_rep}")
        _log(
            f"  search_query   : {search_query[:50] + '...' if search_query and len(search_query) > 50 else search_query}"
        )
        _log(f"  endpoint       : {self.endpoint}")
        _log(f"  audit_log      : {_LOG_FILE}")
        _log(f"  est. LLM calls : ~{self._total_calls_estimate:,} for this domain")
        _log("")

        _audit("=" * 120)
        _audit(f"SESSION START  domain={domain}  started={started_at.isoformat()}")
        _audit(
            f"  max_depth={max_depth}  subtopics_per_level={subtopics_per_level}  geo_rep={include_state_county_rep}  search_query={search_query}"
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
            "subtopic_conjectures": {},  # {level_N: [subtopic_conjecture, ...]}
            "level_conjectures": [],  # [level_conjecture, ...] — fed to final synthesis
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
                f"LEVEL {depth}/{max_depth} | domain={domain} | {len(current_subtopics)} subtopics"
            )

            active_subtopics = current_subtopics[:subtopics_per_level]

            def _process_one_subtopic(
                idx_subtopic: Tuple[int, str],
                _domain: str = domain,
                _depth: int = depth,
                _principles: List[str] = principles_list,
                _level0: str = level0_reasoning,
                _include_geo: bool = include_state_county_rep,
                _spl: int = subtopics_per_level_int,
                search_query: Optional[str] = None,
            ) -> Tuple[List[Dict[str, Any]], List[str], Optional[Dict[str, Any]]]:
                """Process a single subtopic (national + optional geo fan-out).

                Returns (elaborations_list, sub_subtopics_list, subtopic_conjecture).
                subtopic_conjecture is None when progressive_synthesis=False.
                Designed to run in a thread.
                """
                idx, subtopic = idx_subtopic
                _log("")
                _log_subsection(
                    f"SUBTOPIC {idx}/{len(active_subtopics)} | depth={_depth} | {subtopic}"
                )

                # ── national level ────────────────────────────────────────────
                _log(f"  🌐 NATIONAL  population={US_NATIONAL_POPULATION:,}")
                nat_reasoning = self.investigate_subtopic(
                    domain=_domain,
                    subtopic=subtopic,
                    tier="national",
                    tier_label="United States",
                    tier_population=US_NATIONAL_POPULATION,
                    depth=_depth,
                    principles=_principles,
                    parent_context=_level0,
                    search_query=search_query,
                )
                nat_elab = self.elaborate_subtopic(
                    domain=_domain,
                    subtopic=subtopic,
                    tier="national",
                    tier_label="United States",
                    tier_population=US_NATIONAL_POPULATION,
                    depth=_depth,
                    principles=_principles,
                    prior_reasoning=nat_reasoning,
                    search_query=search_query,
                )
                nat_entry: Dict[str, Any] = {
                    "domain": _domain,
                    "subtopic": subtopic,
                    "tier": "national",
                    "tier_label": "United States",
                    "tier_population": US_NATIONAL_POPULATION,
                    "depth": _depth,
                    "reasoning": nat_reasoning,
                    "elaboration": nat_elab,
                    "finding": (nat_reasoning + " " + nat_elab)[:600],
                }
                elab_list: List[Dict[str, Any]] = [nat_entry]
                st_entries: List[Dict[str, Any]] = []
                co_entries: List[Dict[str, Any]] = []

                # ── geographic fan-out ────────────────────────────────────────
                if _include_geo:
                    st_entries, co_entries = self._geographic_fan_out(
                        domain=_domain,
                        subtopic=subtopic,
                        depth=_depth,
                        principles=_principles,
                        prior_reasoning=nat_reasoning,
                        search_query=search_query,
                    )
                    elab_list.extend(st_entries)
                    elab_list.extend(co_entries)
                    _log(
                        f"  ✅ Geo fan-out complete: {len(st_entries)} states, "
                        f"{len(co_entries)} counties"
                    )

                # ── progressive synthesis: per-subtopic intermediate conjecture ─
                subtopic_conj: Optional[Dict[str, Any]] = None
                if self._cfg.progressive_synthesis:
                    _log(f"  🔬 Intermediate synthesis: subtopic='{subtopic}' depth={_depth}")
                    subtopic_conj = self._intermediate_conjecture_subtopic(
                        domain=_domain,
                        subtopic=subtopic,
                        depth=_depth,
                        nat_entry=nat_entry,
                        state_entries=st_entries,
                        county_entries=co_entries,
                    )
                    _log(
                        f"  ✅ Subtopic conjecture confidence={subtopic_conj.get('confidence', 0):.2f}"
                    )

                sub_subs = self._extract_subtopics_from_text(
                    nat_reasoning, subtopic, max(2, _spl // (_depth + 1))
                )
                return elab_list, sub_subs, subtopic_conj

            # ── dispatch subtopics (parallel if workers > 1) ──────────────────
            level_elaborations: List[Dict[str, Any]] = []
            next_subtopics: List[str] = []
            level_subtopic_conjectures: List[Dict[str, Any]] = []

            if self._workers == 1:
                # Sequential — preserves original deterministic ordering
                for idx, subtopic in enumerate(active_subtopics, 1):
                    elab_list, sub_subs, sub_conj = _process_one_subtopic(
                        (idx, subtopic), search_query=search_query
                    )
                    level_elaborations.extend(elab_list)
                    results["all_elaborations"].extend(elab_list)
                    next_subtopics.extend(sub_subs)
                    if sub_conj is not None:
                        level_subtopic_conjectures.append(sub_conj)
            else:
                # Parallel subtopics — each subtopic tree runs concurrently.
                # The semaphore inside _call_llm caps actual HTTP concurrency.
                n_sub_threads = min(len(active_subtopics), self._workers)
                _log(
                    f"  ⚡ Parallel subtopics: {len(active_subtopics)} items "
                    f"| threads={n_sub_threads}"
                )
                sub_futures: List[Tuple[int, Future]] = []
                with ThreadPoolExecutor(
                    max_workers=n_sub_threads, thread_name_prefix="subtopic"
                ) as ex:
                    for idx, subtopic in enumerate(active_subtopics, 1):
                        f = ex.submit(
                            _process_one_subtopic, (idx, subtopic), search_query=search_query
                        )
                        sub_futures.append((idx, f))

                # Collect in submission order to keep output deterministic
                for idx, f in sub_futures:
                    try:
                        elab_list, sub_subs, sub_conj = f.result()
                        level_elaborations.extend(elab_list)
                        results["all_elaborations"].extend(elab_list)
                        next_subtopics.extend(sub_subs)
                        if sub_conj is not None:
                            level_subtopic_conjectures.append(sub_conj)
                    except Exception as exc:
                        _log(f"  ❌ Subtopic #{idx} error: {exc}")

            results["recursive_analysis"][f"level_{depth}"] = level_elaborations
            results["subtopics_by_level"][f"level_{depth}"] = next_subtopics
            results["subtopic_conjectures"][f"level_{depth}"] = level_subtopic_conjectures

            # ── progressive synthesis: per-level intermediate conjecture ──────
            if _cfg.progressive_synthesis and level_subtopic_conjectures:
                _log(
                    f"  🔬 Intermediate level synthesis: depth={depth} "
                    f"subtopics={len(level_subtopic_conjectures)}"
                )
                level_conj = self._intermediate_conjecture_level(
                    domain=domain,
                    depth=depth,
                    subtopic_conjectures=level_subtopic_conjectures,
                )
                results["level_conjectures"].append(level_conj)
                _log(f"  ✅ Level conjecture confidence={level_conj.get('confidence', 0):.2f}")

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
        level_conjs = results["level_conjectures"]
        _log("")
        _log_section(
            f"SYNTHESIS | domain={domain} | elaborations={total_elab} "
            f"| level_conjectures={len(level_conjs)}"
        )

        final_question = (
            f"Based on all evidence, what are the optimal governance mechanisms "
            f"for {domain} policy in the United States, considering national, state, "
            f"and county perspectives?"
        )

        use_progressive = _cfg.progressive_synthesis and bool(level_conjs)
        if use_progressive:
            _log(f"  Using progressive synthesis ({len(level_conjs)} level conjectures)")
            evidence_for_final: List[Dict[str, Any]] = level_conjs
        else:
            _log(f"  Using flat synthesis (first {_cfg.synthesis_evidence_limit} elaborations)")
            evidence_for_final = results["all_elaborations"][: _cfg.synthesis_evidence_limit]

        final_conjecture = self.form_conjecture(
            question=final_question,
            context=context,
            evidence=evidence_for_final,
            domain=domain,
            max_tokens=_cfg.max_tokens_synthesis,
            use_level_conjectures=use_progressive,
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
            _log(f"  {i}. score={sol['score']:.3f} tier={sol['tier']} | {sol['solution'][:80]}…")

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

    # ──────────────────────────────────────────────────────────────────────────
    # Geographic fan-out helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _investigate_one_state(
        self,
        abbr: str,
        state_data: Dict[str, Any],
        domain: str,
        subtopic: str,
        depth: int,
        principles: List[str],
        prior_reasoning: str,
        search_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Investigate + elaborate a single state.  Called from a thread pool."""
        state_name = state_data["name"]
        state_pop = state_data["population"]
        _log(f"    🏛️  STATE {abbr} | {state_name} | pop={state_pop:,}")
        if self._cfg.combine_geo_investigate_elaborate:
            reasoning, elab = self._investigate_and_elaborate_combined(
                domain=domain,
                subtopic=subtopic,
                tier="state",
                tier_label=state_name,
                tier_population=state_pop,
                depth=depth,
                principles=principles,
                parent_context=prior_reasoning,
                search_query=search_query,
            )
        else:
            reasoning = self.investigate_subtopic(
                domain=domain,
                subtopic=subtopic,
                tier="state",
                tier_label=state_name,
                tier_population=state_pop,
                depth=depth,
                principles=principles,
                parent_context=prior_reasoning,
                search_query=search_query,
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
                search_query=search_query,
            )
        return {
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

    def _investigate_one_county(
        self,
        county_data: Dict[str, Any],
        domain: str,
        subtopic: str,
        depth: int,
        principles: List[str],
        prior_reasoning: str,
        search_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Investigate + elaborate a single county.  Called from a thread pool."""
        county_name = county_data["name"]
        county_pop = county_data["population"]
        county_type = county_data.get("type", "mixed")
        _log(f"    🏘️  COUNTY {county_name} ({county_type}) | pop={county_pop:,}")
        if self._cfg.combine_geo_investigate_elaborate:
            reasoning, elab = self._investigate_and_elaborate_combined(
                domain=domain,
                subtopic=subtopic,
                tier="county",
                tier_label=county_name,
                tier_population=county_pop,
                depth=depth,
                principles=principles,
                parent_context=prior_reasoning,
                search_query=search_query,
            )
        else:
            reasoning = self.investigate_subtopic(
                domain=domain,
                subtopic=subtopic,
                tier="county",
                tier_label=county_name,
                tier_population=county_pop,
                depth=depth,
                principles=principles,
                parent_context=prior_reasoning,
                search_query=search_query,
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
                search_query=search_query,
            )
        return {
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

    def _geographic_fan_out(
        self,
        domain: str,
        subtopic: str,
        depth: int,
        principles: List[str],
        prior_reasoning: str,
        search_query: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Investigate a subtopic across all 50 states and representative counties.

        When ``self._workers > 1`` the state and county work items are submitted
        to a ``ThreadPoolExecutor`` so that up to ``_workers`` HTTP calls run
        concurrently.  The semaphore inside ``_call_llm`` ensures we never exceed
        the server's parallel-slot capacity.

        Returns:
            Tuple of (state_elaborations, county_elaborations) in stable order.
        """
        workers = self._workers

        if search_query and get_config().web_search.search_on_fanout:
            from src.data.social_narrative_collector import SocialNarrativeCollector
            from src.llm.web_search import WebSearcher, format_search_results_for_llm

            # Try web search first for up-to-date factual information
            logger.info(f"🔍 Geographic fan-out web search: '{search_query}'")
            web_searcher = WebSearcher()
            web_results = web_searcher.search(
                search_query,
                max_results=get_config().web_search.max_results_in_prompt,
                use_cache=True,
            )
            web_searcher.close()

            if web_results:
                logger.info(f"✅ Geographic fan-out search returned {len(web_results)} results")
                search_text = format_search_results_for_llm(
                    web_results,
                    max_snippet_length=get_config().web_search.max_snippet_length,
                    max_results=get_config().web_search.max_results_in_prompt,
                )
                prior_reasoning = (
                    f"Recent information and facts:\n{search_text}\n\n{prior_reasoning}"
                )
            else:
                logger.warning("⚠️ Geographic fan-out web search returned no results")
                # Fall back to social narrative if web search fails
                collector = SocialNarrativeCollector()
                search_results = collector.search_public_opinion(
                    search_query,
                    domain=domain,
                    max_results=get_config().web_search.max_results_per_search,
                )
                if search_results:
                    search_text = "\n".join(
                        f"[{i + 1}] {r.get('text', '')[:200]}"
                        for i, r in enumerate(
                            search_results[: get_config().web_search.max_results_in_prompt]
                        )
                    )
                    prior_reasoning = f"Public opinion context:\n{search_text}\n\n{prior_reasoning}"

        # Build the full work list: states first, counties second.
        # Each item is (callable, args) so we can dispatch uniformly.
        state_items = list(US_STATES.items())  # [(abbr, state_data), ...]
        county_items = list(REPRESENTATIVE_COUNTIES)  # [county_data, ...]

        if workers == 1:
            # ── Sequential path (original behaviour) ─────────────────────────
            state_entries: List[Dict[str, Any]] = []
            county_entries: List[Dict[str, Any]] = []
            for abbr, state_data in state_items:
                state_entries.append(
                    self._investigate_one_state(
                        abbr,
                        state_data,
                        domain,
                        subtopic,
                        depth,
                        principles,
                        prior_reasoning,
                        search_query,
                    )
                )
            for county_data in county_items:
                county_entries.append(
                    self._investigate_one_county(
                        county_data,
                        domain,
                        subtopic,
                        depth,
                        principles,
                        prior_reasoning,
                        search_query,
                    )
                )
            return state_entries, county_entries

        # ── Parallel path ─────────────────────────────────────────────────────
        # We use more threads than workers so the executor queue stays full while
        # the semaphore gates actual HTTP concurrency.
        # max_workers = 2 × parallel_workers to keep the queue saturated.
        n_threads = min(len(state_items) + len(county_items), workers * 2)
        _log(
            f"    ⚡ Parallel geo fan-out: {len(state_items)} states + "
            f"{len(county_items)} counties | threads={n_threads} slots={workers}"
        )

        # We store futures in submission order to preserve output ordering.
        state_futures: List[Future] = []
        county_futures: List[Future] = []

        with ThreadPoolExecutor(max_workers=n_threads, thread_name_prefix="geo_fan") as ex:
            for abbr, state_data in state_items:
                f = ex.submit(
                    self._investigate_one_state,
                    abbr,
                    state_data,
                    domain,
                    subtopic,
                    depth,
                    principles,
                    prior_reasoning,
                    search_query,
                )
                state_futures.append(f)

            for county_data in county_items:
                f = ex.submit(
                    self._investigate_one_county,
                    county_data,
                    domain,
                    subtopic,
                    depth,
                    principles,
                    prior_reasoning,
                    search_query,
                )
                county_futures.append(f)

        # Collect results in original submission order (futures preserve order)
        state_entries = []
        for f in state_futures:
            try:
                state_entries.append(f.result())
            except Exception as exc:
                _log(f"    ❌ State fan-out error: {exc}")

        county_entries = []
        for f in county_futures:
            try:
                county_entries.append(f.result())
            except Exception as exc:
                _log(f"    ❌ County fan-out error: {exc}")

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
        _cfg = get_config().llm
        tier_weights = {
            "national": _cfg.tier_weight_national,
            "state": _cfg.tier_weight_state,
            "county": _cfg.tier_weight_county,
        }
        capture_threshold = _cfg.solution_capture_threshold
        length_norm = _cfg.ranking_length_norm
        solutions: List[Dict[str, Any]] = []
        for elab in all_elaborations:
            tier = elab.get("tier", "national")
            weight = tier_weights.get(tier, 0.5)
            text = elab.get("finding", elab.get("reasoning", ""))
            # Quality score: length (capped) × quality keywords × tier weight
            length_score = min(1.0, len(text) / length_norm)
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
                    "should_capture": score > capture_threshold,
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
        confidence = get_config().llm.default_confidence
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
            statement = (
                f"Based on the evidence, optimal {question} requires multi-tiered governance."
            )

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
        consensus = get_config().llm.default_confidence
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
        max_tokens: Optional[int] = None,
        domain: str = "general",
        tier: str = "national",
        depth: int = 0,
        subtopic: str = "",
    ) -> str:
        """Legacy shim — calls _call_llm with a concise prompt."""
        if max_tokens is None:
            max_tokens = get_config().llm.max_tokens_legacy
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
        _cfg = get_config().llm
        confidence = (
            _cfg.fallback_confidence_with_evidence if evidence else _cfg.fallback_confidence_empty
        )
        return {
            "statement": f"Based on evidence: {question}",
            "confidence": confidence,
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
