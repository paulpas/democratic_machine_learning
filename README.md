# Democratic Machine Learning System

A production-grade AI-augmented democratic governance framework for the United States. It
simulates multi-tiered decision-making (county → state → national), applies adaptive
trust-weighted voting, collects live social data from Reddit and Google News, runs deep
recursive policy analysis through a local LLM (llama.cpp), and generates detailed governance
reports across six major policy domains.

---

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [LLM Setup (llama.cpp)](#llm-setup-llamacpp)
5. [Quick Start](#quick-start)
6. [Configuration](#configuration)
7. [Running the System](#running-the-system)
8. [Repository Structure](#repository-structure)
9. [Key Concepts](#key-concepts)
10. [Documentation Index](#documentation-index)

---

## Features

- **Deep recursive LLM investigation** — up to N levels of subtopic fan-out across national,
  all-50-state, and county tiers, culminating in a synthesized conjecture with confidence score
- **Trust-weighted democratic voting** — adaptive weights based on expertise, proximity,
  participation history, and trust scores
- **Real social data** — live Reddit opinions and Google News narratives via free APIs (no
  keys required)
- **Anti-pattern detection** — 15+ historical governance failure patterns (elite capture,
  populist decay, regulatory capture, etc.)
- **Fairness constraints** — minimum 30% group satisfaction, maximum 40% inter-group disparity
- **Bot and manipulation detection** — coordinated influence detection in the voter pool
- **Fully configurable** — every threshold, depth, timeout, and token budget is adjustable via
  `config.yaml` or environment variables without touching source code

---

## Requirements

- Python 3.11+
- A running [llama.cpp](https://github.com/ggerganov/llama.cpp) server (optional — system
  falls back gracefully when unavailable)

Python packages:

```
pyyaml>=6.0
requests>=2.32
beautifulsoup4>=4.12
lxml>=5.0
rich>=13.0
numpy>=1.26
aiohttp>=3.9
pytest>=7.4          # development only
pytest-cov>=4.1      # development only
ruff>=0.1            # development only
```

Install all dependencies:

```bash
pip install pyyaml requests beautifulsoup4 lxml rich numpy aiohttp
# development extras
pip install pytest pytest-cov pytest-asyncio ruff
```

---

## Installation

```bash
git clone https://github.com/your-org/democratic_machine_learning.git
cd democratic_machine_learning
pip install -r requirements.txt   # or the pip command above
```

No package install step is required — the `src/` directory is added to `sys.path` by the
entry-point scripts automatically.

---

## LLM Setup (llama.cpp)

The system calls `POST /completion` on a llama.cpp server. Any model supported by llama.cpp
works. The default endpoint is `http://localhost:8080`.

```bash
# Download a model (example: Mistral-7B-Instruct GGUF)
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# Start the server — single slot (sequential, default)
./llama-server -m mistral-7b-instruct-v0.2.Q4_K_M.gguf --port 8080 --ctx-size 8192
```

If the server is not running the system detects the failure at startup and continues with
rule-based fallback reasoning. All six domains can still produce reports — they just use
heuristic conjectures instead of LLM-generated text.

Override the endpoint without changing any file:

```bash
export LLAMA_CPP_ENDPOINT=http://192.168.1.10:8080
python3 run_all_domains.py
```

### Parallel inference (multiple GPU cards or slots)

If your model is loaded on multiple GPUs, or if llama.cpp is configured with multiple
decode slots, you can fire concurrent requests to keep all compute busy:

```bash
# Start llama-server with N parallel decode slots
./llama-server -m model.gguf --port 8080 --ctx-size 8192 --parallel 4

# Tell the client to use 4 concurrent requests
# Option A: in config.yaml
#   llm:
#     parallel_workers: 4

# Option B: environment variable (no file change)
DML_LLM__PARALLEL_WORKERS=4 python3 run_all_domains.py

# Option C: auto-detect from server (queries GET /props)
DML_LLM__PARALLEL_WORKERS=0 python3 run_all_domains.py
```

The system uses a `threading.Semaphore(N)` to cap in-flight requests at exactly N,
so the server is never flooded beyond its capacity. All thread-safety is handled
internally — you just set the number.

**GPU split example** — model sharded across 4 cards, each handling one decode slot:

```bash
# llama.cpp splits the model layers across all visible GPUs automatically.
# --parallel 4 opens 4 decode slots so all 4 GPUs stay busy simultaneously.
./llama-server -m model.gguf --port 8080 \
  --ctx-size 4096 --parallel 4 \
  --n-gpu-layers 999   # put all layers on GPU
```

```yaml
# config.yaml
llm:
  parallel_workers: 4
  timeout_seconds: 300   # reduce if GPUs are fast
```

With 4 parallel slots the 50-state geo fan-out (100 sequential calls → 25 batches of 4)
runs approximately 3–4× faster than sequential.

---

## Quick Start

### 1. Run all six policy domains (production mode)

```bash
python3 run_all_domains.py
```

Generates `output/us_<domain>_governance_model.md` for economy, healthcare, education,
immigration, climate, and infrastructure.

### 2. Run a single domain

```bash
python3 run_all_domains.py healthcare
python3 run_all_domains.py economy climate
```

### 3. Inspect the active configuration before running

```bash
python3 run_all_domains.py --show-config
```

### 4. Use a custom config file

```bash
python3 run_all_domains.py --config fast_test.yaml economy
```

### 5. Override a setting on the fly with an environment variable

```bash
# Run with depth 2 instead of 4 (much faster)
DML_LLM__MAX_DEPTH=2 DML_LLM__MAX_TOKENS_DEFAULT=1024 python3 run_all_domains.py economy
```

### 6. Interactive TUI

```bash
python3 -m src.ui.tui
```

---

## Configuration

The system ships with `config.yaml` at the repository root containing every tuneable
parameter with explanatory comments. Edit it directly or point to an alternative file with
`--config`.

**Priority order** (highest wins):

| Priority | Source | Example |
|----------|--------|---------|
| 1 | Environment variable | `DML_LLM__MAX_DEPTH=2` |
| 2 | YAML config file | `config.yaml` → `llm.max_depth: 2` |
| 3 | Hardcoded defaults | same value as `config.yaml` ships with |

**Environment variable format:** `DML_<SECTION>__<KEY>=value`
(double underscore separates section from key, all uppercase)

```bash
# Examples
DML_LLM__ENDPOINT=http://myserver:8080
DML_LLM__MAX_DEPTH=2
DML_LLM__TIMEOUT_SECONDS=300
DML_VOTER_POOL__RNG_SEED=99
DML_TRUST__MIN_THRESHOLD=0.65
DML_SOCIAL__CACHE_HOURS=1
```

Legacy env vars (`LLAMA_CPP_ENDPOINT`, `LLAMA_MODEL`, `LLAMA_TIMEOUT`, `LLM_LOG_DIR`) are
still honoured for backwards compatibility.

See **[CONFIG.md](CONFIG.md)** for the full reference with every parameter documented,
including its default value, valid range, runtime effect, and performance impact.

---

## Running the System

### `run_all_domains.py` — primary entry point

```
python3 run_all_domains.py [OPTIONS] [domain ...]

Options:
  --config PATH      Path to a YAML config file
  --show-config      Print the effective configuration and exit

Domains (default: all six):
  economy  healthcare  education  immigration  climate  infrastructure
```

### `run_all_domains.sh` — shell wrapper

Sets `LLAMA_CPP_ENDPOINT` from the environment and delegates to `run_all_domains.py`.

```bash
LLAMA_CPP_ENDPOINT=http://localhost:8080 ./run_all_domains.sh
```

### Other entry points

| Script | Purpose |
|--------|---------|
| `governance_reasoning_engine.py` | Standalone reasoning engine (older, no LLM) |
| `real_execution_system.py` | Internet-researched policy analysis |
| `deep_research_execution.py` | Async deep-research runner |
| `run_election_analysis.py` | Election policy analysis |
| `run_immigration_eval.py` | Immigration policy evaluator |
| `run_state_multi_perspective_analysis.py` | Multi-perspective state analysis |

### Running tests

```bash
# All tests with coverage
pytest --cov=. --cov-report=term-missing --cov-fail-under=95 tests/

# Config system tests only
pytest tests/unit/test_config.py -v

# LLM integration tests only
pytest tests/unit/test_llm_integration.py -v

# Lint
ruff check src/ tests/

# Type check
mypy src/ tests/
```

---

## Repository Structure

```
democratic_machine_learning/
├── config.yaml                   # Primary configuration file (edit this)
├── run_all_domains.py            # Main production entry point
├── run_all_domains.sh            # Shell wrapper
│
├── src/                          # Core Python package
│   ├── config.py                 # Config loader (YAML + env vars + defaults)
│   ├── core/
│   │   ├── decision_engine.py    # Central decision orchestrator
│   │   ├── weighting_system.py   # Adaptive voter weight calculation
│   │   ├── feedback_loop.py      # Self-balancing feedback mechanism
│   │   └── policy_cell.py        # Policy decision matrix cell
│   ├── llm/
│   │   └── integration.py        # LLM client — deep recursive investigation
│   ├── data/
│   │   ├── social_narrative_collector.py  # Reddit + Google News scraper
│   │   ├── data_loader.py
│   │   ├── preprocessing.py
│   │   └── feature_engineer.py
│   ├── models/
│   │   ├── voter.py              # Voter dataclass + VoterType enum
│   │   ├── policy.py             # Policy dataclass + PolicyDomain enum
│   │   ├── region.py             # Region dataclass
│   │   └── decision.py           # Decision dataclass
│   ├── security/
│   │   └── trust_system.py       # TrustScorer, EvidenceValidator, SocialInfluenceAnalyzer
│   ├── history/
│   │   └── anti_patterns.py      # 15+ historical anti-pattern database
│   ├── policy/
│   │   ├── policy_tree.py        # Hierarchical policy tree
│   │   ├── immigration_evaluator.py
│   │   ├── election_analysis.py
│   │   └── multi_perspective_analysis.py
│   ├── research/
│   │   └── deep_research_engine.py
│   ├── verbose_logging/
│   │   └── verbose_logger.py     # Rich-based structured logging
│   └── utils/
│       ├── metrics.py            # FairnessMetrics, EfficiencyMetrics
│       ├── validation.py
│       └── logging.py
│
├── tests/
│   ├── unit/
│   │   ├── test_config.py        # Config system tests (40 tests)
│   │   └── test_llm_integration.py
│   └── integration/
│       └── test_run_all_domains.py
│
├── output/                       # Generated governance reports
├── logs/                         # LLM audit logs (auto-created)
├── research/                     # Academic reference documents
│
├── README.md                     # This file
├── CONFIG.md                     # Full configuration reference
├── ARCHITECTURE.md               # System architecture
├── TUTORIAL.md                   # Usage guide and API examples
├── AGENTS.md                     # Developer/AI agent guidelines
└── policy_domains.json           # Policy domain tree data
```

---

## Key Concepts

### Voter tiers

The national voter pool used by `run_all_domains.py` contains four tiers:

| Tier | Count | Weight basis | Preference distribution |
|------|-------|-------------|------------------------|
| Domain experts | 8–12 per domain | Expertise score (0.85–0.95) | Normal μ=0.65 σ=0.10 |
| State delegates | 50 (one per state) | Population share | Normal μ=0.60 σ=0.15 |
| County delegates | 10 (urban/suburban/rural sample) | Population share | Type-specific normal |
| General public | ~331 (≈1 per 1M residents) | Equal (1.0) | Uniform [−0.3, 0.9] |

All counts, weights, and distributions are configurable via `voter_pool.*` settings.

### LLM recursive investigation

For each policy domain the LLM client performs a depth-first investigation:

```
Level 0  — domain overview  →  extract N subtopics
Level 1  — per subtopic:
              national investigation
              all 50 state investigations  (if prod_geo_fan_out=true)
              representative county investigations
              elaboration on each finding
              → extract sub-subtopics for next level
...
Level N  — same as Level 1
Synthesis — form_conjecture from all elaborations  →  ranked solutions
```

`max_depth` and `subtopics_per_level` are the primary knobs controlling depth vs. speed.
Halving both roughly quarters total LLM call count.

### Trust scoring

Each voter receives a trust score (0–1) composed of:

```
trust = base_score
      + expertise_boost  (if expert voter type)
      + consistency  × consistency_weight
      + participation_factor × participation_weight
      + evidence_quality × evidence_weight
```

Voters below `trust.min_threshold` (default 0.7) are excluded from trusted-voter analysis.

### Fairness constraints

Decisions are constrained by:

- `fairness.min_proportion` (0.3) — at least 30% of any affected group must be satisfied
- `fairness.max_disparity` (0.4) — outcome disparity between groups cannot exceed 40%

Both thresholds are configurable and tested against every decision via `FairnessMetrics`.

---

## Documentation Index

| File | Contents |
|------|---------|
| [README.md](README.md) | This file — overview, installation, quick start |
| [CONFIG.md](CONFIG.md) | Complete configuration reference |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, data flows, component diagrams |
| [TUTORIAL.md](TUTORIAL.md) | API usage guide, code examples, advanced patterns |
| [AGENTS.md](AGENTS.md) | Developer/AI agent instructions, code style, build commands |
| [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) | Non-technical overview |
| [DEEP_RECURSIVE_INVESTIGATION.md](DEEP_RECURSIVE_INVESTIGATION.md) | LLM investigation architecture |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Implementation details for recent features |
| [ENHANCED_LOGGING.md](ENHANCED_LOGGING.md) | Logging system reference |
| [research/](research/) | Academic foundations (political science, fairness theory) |
