# Democratic Machine Learning System

A production-grade AI-augmented democratic governance framework for the United States.
It simulates multi-tiered decision-making (county → state → national), applies adaptive
trust-weighted voting, collects live social data from Reddit and Google News, performs
real-time web search for up-to-date information, runs deep recursive policy analysis
through a local LLM (llama.cpp), and produces final governance **thesis documents**
across any policy topic you choose.

Comes pre-configured for six major US policy domains. An **interactive profile menu**
(`just menu`) lets you define entirely new topics — "opioid crisis", "AI governance",
"housing affordability" — and run the same PhD-quality analysis on them without touching
any code.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Profile System — Choose Your Topic](#profile-system--choose-your-topic)
3. [Where Output Lives](#where-output-lives)
4. [Requirements](#requirements)
5. [Installation](#installation)
6. [LLM Setup (llama.cpp)](#llm-setup-llamacpp)
7. [Quick Start — just recipes](#quick-start--just-recipes)
8. [Configuration](#configuration)
9. [Running Without just](#running-without-just)
10. [Repository Structure](#repository-structure)
11. [Key Concepts](#key-concepts)
12. [Documentation Index](#documentation-index)

---

## What It Does

For any policy topic you define — the six built-in domains **economy, healthcare,
education, immigration, climate, infrastructure** or any custom topic you create — the
system:

1. **Collects real-time web information** — Uses DuckDuckGo API with optional Playwright
   JavaScript rendering for up-to-date factual information (no API keys required)
2. **Collects real social data** — Reddit opinions and Google News narratives via free APIs
3. **Builds a synthetic voter pool** — domain experts, state delegates, county delegates,
   and the general public with trust-weighted preferences
4. **Runs a deep recursive LLM investigation** — the LLM fans out from a national overview
   through all 50 states and representative counties at configurable depth, elaborating on
   each finding and synthesising evidence into a final conjecture
5. **Makes a democratic decision** — trust-weighted voting with fairness constraints,
   anti-pattern detection, and feedback-loop adaptation
6. **Writes a thesis document** — a PhD/scientific-paper-grade markdown report with
   Abstract, Methodology, Evidence Base, National/State/County Findings, Principal Thesis,
   Policy Recommendations, Democratic Deliberation record, and Conclusions

---

## Profile System — Choose Your Topic

The **profile system** decouples *what* to analyse from *how* to analyse it. Each profile
is a YAML file in `config/profiles/` that specifies topics, recursion depth, geographic
scope, and LLM budgets.

### Launch the interactive menu

```bash
just menu
```

The menu lets you:

| Action | What happens |
|--------|-------------|
| **Select & run** | Pick any saved profile → confirm settings → analysis begins immediately |
| **Create** | 4-step wizard: name → description → topics (checkbox + free-text) → depth |
| **Edit** | Modify depth, geo scope, description, or topics for an existing profile |
| **Delete** | Remove custom profiles (the `default` profile is protected) |
| **View** | Inspect any profile in a formatted table |
| **List** | See all profiles with their domain list, depth, and geo setting |

### Built-in default profile

`config/profiles/default.yaml` — the six production domains at full depth:

```yaml
name: "default"
domains: [economy, healthcare, education, immigration, climate, infrastructure]
depth: 4
subtopics_per_level: 5
geo_fan_out: true          # all 50 US states + representative counties
```

### Custom topics

When creating a profile you can mix built-in domains with any free-text topic:

```
Built-in checkboxes:  ☑ economy  ☑ climate  ☐ healthcare  …
Free-text additions:  opioid crisis, AI governance, housing affordability
```

The LLM investigation and 50-state fan-out work identically for custom topics —
there is no restriction on what you can analyse.

### Profile output isolation

Every profile writes its reports to its own sub-directory:

```
output/default/us_economy_governance_model.md
output/default/us_climate_governance_model.md
output/my-ai-profile/us_ai-governance_governance_model.md
output/my-ai-profile/session_summary.json
```

This means multiple profiles can coexist without overwriting each other.

See **[PROFILES_WALKTHROUGH.md](PROFILES_WALKTHROUGH.md)** for a step-by-step guide
covering every menu action with example output.

---

## Where Output Lives

All generated artifacts are written to `output/<profile-name>/`:

```
output/
├── default/                          ← default 6-domain profile
│   ├── us_economy_governance_model.md
│   ├── us_healthcare_governance_model.md
│   ├── us_education_governance_model.md
│   ├── us_immigration_governance_model.md
│   ├── us_climate_governance_model.md
│   ├── us_infrastructure_governance_model.md
│   └── session_summary.json
│
├── my-opioid-profile/                ← any custom profile you create
│   ├── us_opioid-crisis_governance_model.md
│   └── session_summary.json
│
└── social_<domain>.json              ← collected Reddit + News data (just collect)
```

### Final Thesis Documents

Each `output/us_<domain>_governance_model.md` is the **primary research output** for that
domain. It contains:

| Section | Contents |
|---------|---------|
| **Executive Summary** | Decision outcome, confidence, vote tally, LLM call count, token usage |
| **Social Data** | Reddit opinion count, media narrative count, average sentiment scores |
| **Final Conjecture** | The LLM-synthesised thesis statement with confidence score |
| **Contradicting Evidence** | Counter-arguments surfaced during investigation |
| **Top Ranked Solutions** | Scored policy recommendations ranked by tier weight × quality |
| **Democratic Decision** | Full vote breakdown, anti-pattern flags, fairness assessment |
| **Fairness Assessment** | Proportional representation check, disparity metrics |
| **Anti-Pattern Analysis** | Detection results for 15+ historical governance failure patterns |
| **Technical Metadata** | Timestamps, elapsed time, LLM endpoint, config file used |

The **`session_summary.json`** gives a machine-readable overview of the entire run:
elapsed time, total LLM calls and tokens, and per-domain outcomes.

The **`social_<domain>.json`** files contain the raw collected social narratives (from
`just collect`) and are inputs to subsequent analysis runs.

> **Note:** Generated output files are not committed to git. The `output/` directory
> contains a `.gitkeep` placeholder so the directory exists on fresh clones. Run
> `just run` or `just demo-run` to generate the thesis documents locally.

---

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — Python package manager
- [just](https://just.systems/) ≥ 1.39 — command runner
- A running [llama.cpp](https://github.com/ggerganov/llama.cpp) server (optional — system
  degrades gracefully with rule-based fallback when unavailable)

### Install just and uv

```bash
# just (≥1.39 required for require(), path_exists(), [doc], [group])
curl -LsSf https://just.systems/install.sh | sudo bash -s -- --to /usr/local/bin

# uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Installation

```bash
git clone https://github.com/paulpas/democratic_machine_learning.git
cd democratic_machine_learning

# Create venv and install all dependencies from the lockfile
just sync
# or: uv sync --all-groups
```

No additional steps required. `uv sync` reads `pyproject.toml` and `uv.lock` and
installs an exact reproducible environment into `.venv/`.

---

## LLM Setup (llama.cpp)

The system sends `POST /completion` requests to a llama.cpp server. Any GGUF model works.

```bash
# Single slot — sequential (safest baseline)
./llama-server -m model.gguf --port 8080 --ctx-size 8192

# Multiple parallel slots — keeps all GPU compute busy
./llama-server -m model.gguf --port 8080 --ctx-size 4096 \
  --parallel 4 --n-gpu-layers 999
```

Then set `parallel_workers` to match in `config.yaml`:

```yaml
llm:
  endpoint: "http://localhost:8080"
  parallel_workers: 4   # must match --parallel N on the server
```

Or use an environment variable without touching any file:

```bash
DML_LLM__PARALLEL_WORKERS=4 just run economy
```

**Auto-detect** the server's slot count at startup:

```bash
DML_LLM__PARALLEL_WORKERS=0 just run   # queries GET /props
```

If the server is unreachable the system continues with rule-based fallback reasoning.
All six thesis documents are still generated — conjectures use heuristic confidence
values instead of LLM-generated text.

---

## Quick Start — just recipes

```bash
just              # list all recipes with descriptions (grouped)

just sync         # install / update .venv

# ── Interactive profile menu (recommended entry point) ──────────────────────
just menu                   # opens TUI: create/select/edit profiles → run

# ── Production run ──────────────────────────────────────────────────────────
just run                           # default profile — all 6 domains
just run economy                   # single built-in domain (CLI shorthand)
just run economy healthcare        # multiple built-in domains
just run --profile default         # explicit profile name
just run --profile my-opioid-study # any custom profile you created via menu

# ── Demo run (~30 seconds) ──────────────────────────────────────────────────
just demo-run               # economy domain, depth=1, no geo fan-out
just demo-run climate       # demo on a specific domain

# ── Social data collection ──────────────────────────────────────────────────
just collect                # all 6 domains → output/social_*.json
just collect economy        # one domain

# ── Configuration ────────────────────────────────────────────────────────────
just show-config            # print active config.yaml + env overrides
just show-config-demo       # print config/demo.yaml effective values
just show-config-prod       # print config/production.yaml effective values

# ── Development ──────────────────────────────────────────────────────────────
just test                   # pytest with ≥95% coverage
just test-one tests/unit/test_config.py  # single file
just lint                   # ruff check
just fmt                    # ruff format + fix
just typecheck              # mypy
just check                  # lint + typecheck + test

# ── Maintenance ──────────────────────────────────────────────────────────────
just clean                  # remove caches and coverage artifacts
just clean-output           # remove generated output files (asks first)
just upgrade                # uv lock --upgrade + sync
just env-info               # show just/uv/Python versions
```

### Recipe groups

| Group | Recipes |
|-------|---------|
| `setup` | `sync`, `env-info` |
| `run` | `menu`, `run`, `demo-run`, `collect` |
| `config` | `show-config`, `show-config-demo`, `show-config-prod` |
| `dev` | `test`, `test-one`, `lint`, `fmt`, `typecheck`, `check` |
| `maintenance` | `clean`, `clean-output`, `upgrade` |

---

## Configuration

All runtime behaviour is controlled by `config.yaml` at the repo root. Edit it directly
or pass `--config path/to/file.yaml` to use an alternative.

**Priority order** (highest wins):

| Priority | Source | Example |
|----------|--------|---------|
| 1 | Environment variable | `DML_LLM__PARALLEL_WORKERS=4` |
| 2 | YAML config file | `config.yaml` → `llm.parallel_workers: 4` |
| 3 | Hardcoded defaults | same as shipped `config.yaml` |

**Key settings:**

```yaml
llm:
  endpoint: "http://localhost:8080"
  parallel_workers: 2          # concurrent LLM requests (match --parallel N)
  timeout_seconds: 900

voter_pool:
   prod_llm_max_depth: 2        # recursion depth — biggest runtime multiplier
   prod_llm_subtopics_per_level: 3
   prod_geo_fan_out: true       # include all 50 states + representative counties

web_search:
   enabled: true                # Enable web search for real-time information
   primary_engine: "duckduckgo" # 'duckduckgo' or 'google' (no API keys)
   use_javascript: true         # Playwright for dynamic content
   search_on_fanout: true       # Enable searches at state/county levels
```

**Pre-built config files:**

| File | Use |
|------|-----|
| `config.yaml` | Default production config (edit this) |
| `config/production.yaml` | Explicit full-depth reference |
| `config/demo.yaml` | Minimal config for `just demo-run` (~30 s) |

See **[CONFIG.md](CONFIG.md)** for the complete reference — every parameter with its
default value, valid range, runtime effect, and performance impact.

---

## Running Without just

```bash
# Interactive profile menu
uv run src/ui/profile_menu.py

# Full run — built-in domains (CLI shorthand)
uv run run_all_domains.py
uv run run_all_domains.py economy healthcare
uv run run_all_domains.py --config config/demo.yaml economy

# Full run — named profile (writes to output/<profile-name>/)
uv run run_all_domains.py --profile default
uv run run_all_domains.py --profile my-opioid-study

# Show config
uv run run_all_domains.py --show-config

# Social collection
uv run scripts/collect_social.py
uv run scripts/collect_social.py economy climate

# Tests
uv run pytest tests/
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=95 tests/
```

---

## Repository Structure

```
democratic_machine_learning/
│
├── justfile                    # All recipes (run, demo-run, collect, test, …)
├── pyproject.toml              # Project metadata + dependency groups
├── uv.lock                     # Reproducible lockfile (commit this)
├── .python-version             # Pins Python 3.12 for uv
├── config.yaml                 # Default production configuration (edit this)
│
├── config/                     ← ALL CONFIGURATION LIVES HERE
│   ├── demo.yaml               # Minimal config for just demo-run (~30 s)
│   ├── production.yaml         # Explicit full-depth production reference
│   └── profiles/               ← PROFILE DEFINITIONS LIVE HERE
│       ├── default.yaml        # Built-in 6-domain production profile
│       └── README.md           # Profile authoring guide
│
├── scripts/
│   └── collect_social.py       # Standalone social data collector
│
├── run_all_domains.py          # Main production entry point (--profile NAME)
│
├── output/                     ← ALL GENERATED THESIS DOCUMENTS LIVE HERE
│   ├── default/                ← one sub-directory per profile
│   │   ├── us_economy_governance_model.md
│   │   ├── us_healthcare_governance_model.md
│   │   ├── us_education_governance_model.md
│   │   ├── us_immigration_governance_model.md
│   │   ├── us_climate_governance_model.md
│   │   ├── us_infrastructure_governance_model.md
│   │   └── session_summary.json
│   ├── <custom-profile>/       ← custom profile outputs isolated here
│   │   └── us_<topic>_governance_model.md
│   └── social_<domain>.json    ← collected Reddit + News data (from just collect)
│
├── src/
│   ├── config.py               # Config loader (YAML + env vars + defaults)
│   │                           # Includes ProfileConfig dataclass
│   ├── core/
│   │   ├── decision_engine.py  # Central decision orchestrator
│   │   ├── weighting_system.py # Adaptive voter weight calculation
│   │   ├── feedback_loop.py    # Self-balancing feedback mechanism
│   │   └── policy_cell.py
│   ├── llm/
│   │   ├── integration.py      # LLM client — deep recursive investigation
│   │   │                       # parallel via ThreadPoolExecutor + Semaphore
│   │   └── web_search.py       # Web search with DuckDuckGo API + Playwright
│   ├── data/
│   │   └── social_narrative_collector.py  # Reddit + Google News, thread-safe
│   ├── models/
│   │   ├── voter.py            # Voter + VoterType
│   │   ├── policy.py           # Policy + PolicyDomain
│   │   ├── region.py           # Region
│   │   └── decision.py         # Decision
│   ├── security/
│   │   └── trust_system.py     # TrustScorer, EvidenceValidator, bot detection
│   ├── history/
│   │   └── anti_patterns.py    # 15+ historical governance failure patterns
│   ├── policy/
│   │   └── policy_tree.py      # Hierarchical policy tree
│   ├── ui/
│   │   ├── profile_menu.py     # Interactive TUI menu (just menu entry point)
│   │   ├── profile_loader.py   # Load/validate/list profiles from disk
│   │   └── profile_manager.py  # Create/update/delete/import/export profiles
│   └── utils/
│       └── metrics.py          # FairnessMetrics, EfficiencyMetrics
│
├── tests/
│   ├── unit/
│   │   ├── test_config.py      # 40 tests — config loading and overrides
│   │   └── test_llm_integration.py
│   └── integration/
│       └── test_run_all_domains.py
│
├── logs/                       # LLM audit logs (auto-created, not committed)
│   └── llm_calls.log           # Full prompt + response log, rotates at 50 MB
│
├── research/                   # Academic reference documents
│   ├── political_philosophy_foundations.md
│   ├── anti_corruption_mechanisms.md
│   ├── decision_making_frameworks.md
│   ├── fairness_and_inclusion_design.md
│   └── …
│
├── README.md                   # This file
├── CONFIG.md                   # Full configuration reference
├── ARCHITECTURE.md             # System architecture and data flows
├── TUTORIAL.md                 # API usage guide and code examples
└── AGENTS.md                   # Developer/AI agent guidelines
```

---

## Key Concepts

### Voter tiers

| Tier | Count | Weight multiplier | Preference distribution |
|------|-------|------------------|------------------------|
| Domain experts | 8–12 per domain | 1.5× base | Normal μ=0.65 σ=0.10 |
| State delegates | 50 (one per state) | 2.0× base | Normal μ=0.60 σ=0.15 |
| County delegates | 10 (urban/suburban/rural) | 1.0× base | Type-specific normal |
| General public | ~331 (≈1 per 1M residents) | 1.0× base | Uniform [−0.3, 0.9] |

### LLM recursive investigation

```
Level 0  — national domain overview  →  extract N subtopics
Level 1  — per subtopic:
              national tier (investigate → elaborate)
              all 50 state tiers    (parallel, semaphore-gated)
              10 county tiers       (parallel, semaphore-gated)
              → extract sub-subtopics
…
Level N  — same fan-out
Synthesis — form_conjecture from all elaborations  →  ranked solutions
                                     ↓
                         output/us_<domain>_governance_model.md
```

`prod_llm_max_depth` and `prod_geo_fan_out` are the primary levers controlling depth vs.
speed. Full production run: ~700 LLM calls per domain, 2–4 h on CPU. Demo run: ~6 calls,
< 60 s.

### Parallel inference

The system uses `threading.Semaphore(N)` to fire up to `N` concurrent HTTP requests to
llama.cpp. Match `parallel_workers` to the `--parallel N` flag on `llama-server`:

```bash
./llama-server -m model.gguf --parallel 4   # server opens 4 decode slots
just run DML_LLM__PARALLEL_WORKERS=4        # client uses all 4 simultaneously
```

---

## Documentation Index

| File | Contents |
|------|---------|
| [README.md](README.md) | This file — overview, quick start, output location |
| [PROFILES_WALKTHROUGH.md](PROFILES_WALKTHROUGH.md) | **Step-by-step guide: menu, profiles, custom topics** |
| [CONFIG.md](CONFIG.md) | Complete configuration reference — every parameter documented |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, data flows, component diagrams |
| [TUTORIAL.md](TUTORIAL.md) | API usage guide, code examples, advanced patterns |
| [AGENTS.md](AGENTS.md) | Developer/AI agent guidelines, build commands, code style |
| [config/profiles/README.md](config/profiles/README.md) | Profile YAML authoring reference |
| [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) | Non-technical overview |
| [DEEP_RECURSIVE_INVESTIGATION.md](DEEP_RECURSIVE_INVESTIGATION.md) | LLM investigation architecture |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Implementation details for major features |
| [ENHANCED_LOGGING.md](ENHANCED_LOGGING.md) | LLM audit logging reference |
| [research/](research/) | Academic foundations (political science, fairness theory) |
