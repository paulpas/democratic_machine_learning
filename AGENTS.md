# AGENTS.md

## Build/Lint/Test Commands

```bash
# ── Preferred: use just (manages uv + venv automatically) ────────────────────
just sync          # install / update .venv
just test          # full test suite with ≥95% coverage
just test-one tests/unit/test_config.py  # single file
just lint          # ruff check
just fmt           # ruff format + fix
just typecheck     # mypy
just check         # lint + typecheck + test

# ── Direct uv commands (if just is not available) ────────────────────────────
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=95 tests/
uv run pytest tests/unit/test_config.py
uv run pytest tests/unit/test_config.py::TestDefaults::test_default_max_depth
uv run ruff check src/ tests/
uv run mypy src/
uv run ruff format src/ tests/
```

## Output Location

All generated thesis documents and analysis artifacts are written to **`output/`**:

```
output/us_<domain>_governance_model.md   ← final thesis per domain
output/session_summary.json              ← run metadata (tokens, calls, outcomes)
output/social_<domain>.json              ← collected Reddit + News data
output/logs/                             ← LLM call audit logs
cache/web_search/                        ← cached web search results
```

These files are **not committed** (generated artifacts). Reproduce them with:

```bash
just run          # full production run
just demo-run     # quick ~30 s smoke-test
just collect      # social data only
```

## Code Style Guidelines

### General
- Python 3.11+ with type hints
- Follow PEP 8 with ruff formatting
- 100% test coverage minimum (95% for integration tests)
- TDD: write tests before implementation

### Imports
- Absolute imports only
- Group: stdlib, third-party, local
- Use `from package import Module` not `import package.module`

### Naming
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`
- Types: `PascalCase` with `Type` suffix if needed

### Types
- Always type hint function signatures
- Use `typing` module: `List`, `Dict`, `Optional`, `Union`, `Callable`
- Use `Literal` for fixed options
- Use `Protocol` for duck-typed interfaces

### Error Handling
- Custom exception classes in `src/exceptions.py`
- Use specific exceptions, not generic `Exception`
- Log errors with context
- Never swallow exceptions silently

### Testing
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Mock external dependencies
- Test edge cases and error paths
- Use pytest fixtures for test data

### Documentation
- Docstrings in Google style
- Exported functions need docstrings
- Complex logic needs inline comments
- Update README for new features

### File Structure
```
src/
  __init__.py
  core/
    decision_engine.py
    weighting_system.py
    policy_cell.py
    feedback_loop.py
  data/
    data_loader.py
    preprocessing.py
    feature_engineer.py
  models/
    voter.py
    policy.py
    region.py
    decision.py
  ui/
    tui.py
    display.py
  utils/
    metrics.py
    validation.py
    logging.py
  security/
    trust_system.py
  __init__.py
tests/
  unit/
  integration/
  fixtures/
```

## TUI Output Guidelines
- Use `rich` library for formatted output
- Progress indicators with `rich.progress`
- Tables with `rich.table`
- Color-coded status (green=success, yellow=warning, red=error)
- Interactive prompts with `rich.prompt`

## Political Science Framework
- Reference historical systems: Athenian democracy, Roman Republic, representative democracies
- Incorporate: Condorcet paradox, Arrow's impossibility theorem, approval voting
- Multi-tiered representation with adaptive weighting
- Fairness metrics: proportional representation, minority protection, geographic balance

## Security & Trust Framework
- **Malicious Influence Protection**:
  - Bot detection for automated accounts
  - Manipulation detection for coordinated influence campaigns
  - Source verification for data provenance
  - Evidence cross-referencing across multiple sources
  - Temporal validation to detect sudden anomalies
  
- **Trust Scoring**:
  - Base trust score with expertise boosts
  - Consistency tracking for preference stability
  - Participation history weighting
  - Evidence quality assessment
  
- **Social Influence Analysis**:
  - Bot score calculation based on behavior patterns
  - Manipulation detection for suspicious preferences
  - Influence network mapping
  - Coordinated manipulation detection

## Environmental & Geographic Factors
- **Geographic Weighting**:
  - Direct impact voters get higher weight
  - Regional representation across tiers
  - Geographic diversity in decision-making
  
- **Climate Impact Assessment**:
  - Climate vulnerability scoring per region
  - Environmental policy impact analysis
  - Geographic risk factors in decision models
  
- **Demographic Considerations**:
  - Population density weighting
  - Urban/rural balance
  - Regional economic factors
  - Cultural diversity metrics

## Core Principles
1. **Adaptive Weighting**: Voter weights based on expertise, proximity, participation
2. **Multi-Tiered Representation**: County → State → National feedback loop
3. **Fairness Constraints**: Minimum 30% group satisfaction, max 40% disparity
4. **Feedback Loop**: Continuous learning and weight adjustment
5. **Security First**: Malicious influence detection and mitigation
6. **Environmental Context**: Geography and climate as decision factors

## Data Sources
- Public polling and elections (realistic, existing data)
- Synthetic population simulation (controlled experiment)
- Social media sentiment (with manipulation detection)
- Economic indicators
- Climate and geographic data

## Decision-Making Approaches
- **Hierarchical Representation**: Multi-tiered weighted voting
- **Liquid Democracy**: Delegative voting with dynamic delegation
- **Predictive Consensus**: ML predicts optimal policy with minority protection
- **Hybrid Approach**: Combine multiple mechanisms with adaptive weighting

## Key Metrics
- Fairness Score (0-1): Variance-based voter satisfaction
- Consensus Score (0-1): Support percentage threshold
- Trust Score (0-1): Weighted by expertise, consistency, participation
- Geographic Balance: Regional representation ratio
- Climate Impact Index: Environmental effect per policy

## 🚀 ENHANCEMENT SUMMARY: LLM Integration & Social Data Collection

### 📋 **Overview**
Enhanced the Democratic Machine Learning System with LLM integration using llama.cpp endpoint at http://localhost:8080 and real social narrative collection from free internet sources (no API keys required).

### 🔧 **Key Improvements Made:**

#### 1. **LLM Integration with Logging**
- **Files Modified**: `src/llm/integration.py`
- **Enhancements**:
  - Added comprehensive stdout logging for all LLM calls
  - Logs prompt length, max tokens, token usage, and response previews
  - Tracks LLM availability and fallback usage
  - Shows detailed request/response information for debugging
  - Preserves all existing functionality while adding visibility

#### 2. **Real Social Narrative Collection (FREE, No API Keys)**
- **Files Created**: `src/data/social_narrative_collector.py`
- **Data Sources**:
  - **Reddit JSON API**: Real public opinions and social narratives (bopinions)
  - **Google News RSS**: Real media narratives and news perspectives
- **Integration**: Automatically collects social data during each policy analysis
- **Output**: Provides realistic public sentiment to enhance LLM analysis

#### 3. **Enhanced Decision Engine**
- **Files Modified**: `src/core/decision_engine.py`
- **Enhancements**:
  - Integrated social narrative collector for real-time data
  - Enhanced `_analyze_policy_context()` method to use real social data
  - Maintains all core democratic algorithms (trust-weighted voting, anti-pattern detection, fairness constraints)
  - Preserves backward compatibility

#### 4. **Automated Domain Processing**
- **Files Created**: `run_all_domains_simple.sh`
- **Functionality**:
  - Processes all 6 policy domains: economy, healthcare, education, immigration, climate, infrastructure
  - Generates well-formatted markdown reports (not JSON dumps)
  - Saved to intuitive filenames: `output/us_<domain>_governance_model.md`
  - Each report includes LLM-enhanced analysis, social data integration, and democratic decision details

### 📊 **Verification Results:**
- ✅ **Social Data Collection**: 15 Reddit opinions + 12 Google News narratives per domain
- ✅ **LLM Connectivity**: Verified connection to http://localhost:8080
- ✅ **Report Generation**: All 6 domain reports successfully created
- ✅ **Core Algorithms**: Trust-weighted voting, anti-pattern detection, fairness constraints preserved
- ✅ **Output Format**: Substantive markdown reports (5KB+ detailed analysis per file)
- ✅ **LLM Enhancement**: Visible logging confirms LLM calls are made with meaningful token generation

### 📁 **Generated Output Files:**
- `output/us_economy_governance_model.md`
- `output/us_healthcare_governance_model.md`
- `output/us_education_governance_model.md`
- `output/us_immigration_governance_model.md`
- `output/us_climate_governance_model.md`
- `output/us_infrastructure_governance_model.md`

### Usage

```bash
just run           # full production run — generates output/us_<domain>_governance_model.md
just demo-run      # quick smoke-test (~30 s, economy domain, no geo fan-out)
just collect       # collect Reddit + News data → output/social_<domain>.json
```

Each thesis document (`output/us_<domain>_governance_model.md`) contains:
- Executive summary with key decision metrics
- Social data summary (Reddit opinions + media narratives)
- **Final Conjecture** — the LLM-synthesised policy thesis with confidence score
- Contradicting evidence surfaced during recursive investigation
- Top-ranked policy solutions (scored by tier weight × quality)
- Democratic decision details (trust-weighted voting)
- Fairness constraint assessments
- Anti-pattern detection results
- Technical metadata (LLM calls, tokens, config file, timestamps)

## Current System State (for new sessions)

The system is fully operational. Key facts:

| Component | Status |
|-----------|--------|
| Config system | `src/config.py` — YAML + env vars + defaults, 9 sections, ~90 params |
| LLM client | `src/llm/integration.py` — parallel via ThreadPoolExecutor + Semaphore |
| Social collector | `src/data/social_narrative_collector.py` — Reddit + Google News, thread-safe cache |
| Decision engine | `src/core/decision_engine.py` — trust-weighted voting, anti-pattern detection |
| Test suite | 129 tests passing, ≥95% coverage |
| just recipes | `justfile` — run, demo-run, collect, test, lint, fmt, typecheck, check |
| uv project | `pyproject.toml` + `uv.lock` — reproducible 39-package environment |
| Output | `output/us_<domain>_governance_model.md` per domain (not committed) |

**Default parallel_workers: 2** — set `llm.parallel_workers` to match `--parallel N` on llama-server.

**To resume work in a new session:**
1. Read `ARCHITECTURE.md` for system overview and output location
2. Read `CONFIG.md` for all configurable parameters
3. Run `just env-info` to verify the environment
4. Run `just demo-run` to smoke-test the full pipeline
5. Run `just run` for full production analysis
