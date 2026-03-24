# =============================================================================
# Democratic Machine Learning — Justfile
# =============================================================================
#
# Prerequisites:
#   uv   — https://docs.astral.sh/uv/
#          install: curl -LsSf https://astral.sh/uv/install.sh | sh
#   just — https://just.systems/
#          install: sudo apt install just  OR  cargo install just
#
# Quick reference:
#   just              — list all recipes
#   just run          — full production run (all 6 domains)
#   just demo-run     — quick smoke-test run (~30 s, economy domain only)
#   just collect      — fetch Reddit + Google News data for all domains
#   just test         — run test suite
#   just show-config  — print active configuration and exit
# =============================================================================

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

# Load .env if present — never required, safe to omit
set dotenv-load

# Strict bash: unbound variable → immediate error
set shell := ["bash", "-uc"]

# ---------------------------------------------------------------------------
# Variables — built-ins and / operator; backtick only for external tools
# ---------------------------------------------------------------------------

root    := justfile_directory()
src     := root / "src"
tests   := root / "tests"
scripts := root / "scripts"
configs := root / "configs"
output  := root / "output"

# Locate uv via backtick — gives a clear path in error messages
uv := `which uv`

# Config file paths resolved with the / operator (no shell needed)
cfg_demo := configs / "demo.yaml"
cfg_prod := configs / "production.yaml"

# ---------------------------------------------------------------------------
# Default recipe — shown on bare `just`
# ---------------------------------------------------------------------------

# List all available recipes with their comments
default:
    @just --list

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------

# Install / sync all dependencies (runtime + dev) into .venv
sync:
    {{ uv }} sync --all-groups

# Print environment info
env-info: sync
    @echo "── Environment ──────────────────────────────────────"
    @echo "just : $(just --version)"
    @echo "uv   : $({{ uv }} --version)"
    @{{ uv }} run python --version
    @echo "root : {{ root }}"
    @echo "venv : {{ root }}/.venv"
    @echo "─────────────────────────────────────────────────────"

# ---------------------------------------------------------------------------
# Core recipes
# ---------------------------------------------------------------------------

# Full production run — all 6 domains, full depth, geo fan-out enabled.
# Pass domain names to limit scope: `just run economy healthcare`
run *domains="": sync
    {{ uv }} run run_all_domains.py {{ domains }}

# Quick demo run — exercises every code path in ~30 seconds.
# Uses configs/demo.yaml: depth=1, 1 subtopic, no geo fan-out, 256-token budgets.
# Default domain is economy. Override: `just demo-run healthcare`
demo-run *domains="economy": sync
    {{ uv }} run run_all_domains.py --config {{ cfg_demo }} {{ domains }}

# Fetch Reddit opinions + Google News narratives and save to output/social_<domain>.json.
# Runs all 6 domains by default. Pass names to limit: `just collect economy climate`
collect *domains="": sync
    {{ uv }} run {{ scripts / "collect_social.py" }} {{ domains }}

# ---------------------------------------------------------------------------
# Configuration inspection
# ---------------------------------------------------------------------------

# Print the effective configuration (config.yaml + env overrides) and exit
show-config:
    {{ uv }} run run_all_domains.py --show-config

# Print the demo configuration and exit
show-config-demo:
    {{ uv }} run run_all_domains.py --config {{ cfg_demo }} --show-config

# Print the production configuration and exit
show-config-prod:
    {{ uv }} run run_all_domains.py --config {{ cfg_prod }} --show-config

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

# Run the full test suite with coverage (≥95% required)
test *flags="": sync
    {{ uv }} run pytest --cov={{ src }} --cov-report=term-missing --cov-fail-under=95 {{ tests }} {{ flags }}

# Run a single test file or test function:
#   just test-one tests/unit/test_config.py
#   just test-one tests/unit/test_config.py::TestDefaults::test_default_max_depth
test-one target: sync
    {{ uv }} run pytest -v {{ target }}

# Run ruff linter
lint: sync
    {{ uv }} run ruff check {{ src }} {{ tests }}

# Auto-format and auto-fix lint issues
fmt: sync
    {{ uv }} run ruff format {{ src }} {{ tests }}
    {{ uv }} run ruff check --fix {{ src }} {{ tests }}

# Run mypy type checker
typecheck: sync
    {{ uv }} run mypy {{ src }}

# Run all CI checks: lint → typecheck → test
check: lint typecheck test

# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

# Remove __pycache__, .pytest_cache, .ruff_cache, coverage artifacts
clean:
    -find {{ root }} -type d -name "__pycache__" -not -path "*/.venv/*" -exec rm -rf {} +
    -rm -rf {{ root / ".pytest_cache" }}
    -rm -rf {{ root / ".ruff_cache" }}
    -rm -rf {{ root / ".coverage" }}
    -rm -rf {{ root / "coverage.xml" }}
    -rm -rf {{ root / "htmlcov" }}

# Remove generated output reports and social data files (keeps .gitkeep)
[confirm]
clean-output:
    -find {{ output }} -name "*.md" -not -name ".gitkeep" -delete
    -find {{ output }} -name "*.json" -not -name ".gitkeep" -delete

# Upgrade all dependencies and regenerate uv.lock
upgrade:
    {{ uv }} lock --upgrade
    {{ uv }} sync --all-groups
