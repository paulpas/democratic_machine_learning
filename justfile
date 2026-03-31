# =============================================================================
# Democratic Machine Learning — Justfile
# =============================================================================
#
# Prerequisites:
#   uv   — https://docs.astral.sh/uv/
#          install: curl -LsSf https://astral.sh/uv/install.sh | sh
#   just — https://just.systems/  (≥1.39 required for require(), path_exists())
#          install: curl -LsSf https://just.systems/install.sh | sudo bash -s -- --to /usr/local/bin
#
# Quick reference:
#   just              — list all recipes with descriptions
#   just run          — full production run (all 6 domains)
#   just demo-run     — quick smoke-test (~30 s, economy domain only)
#   just collect      — fetch Reddit + Google News data for all domains
#   just test         — run the full test suite
#   just show-config  — print the active configuration and exit
# =============================================================================

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

# Load .env if present — never required, safe to omit
set dotenv-load

# Strict bash: unbound variable → immediate error
set shell := ["bash", "-uc"]

# ---------------------------------------------------------------------------
# Variables — built-in functions only, no shell backticks
# ---------------------------------------------------------------------------

root    := justfile_directory()
src     := root / "src"
tests   := root / "tests"
scripts := root / "scripts"
config  := root / "config"
output  := root / "output"

# require() aborts with a clear message if the binary is not in PATH
uv     := require("uv")
python := require("python3")

# Config file paths — / operator, no shell needed
cfg_demo    := config / "demo.yaml"
cfg_prod    := config / "production.yaml"

# Informational: detect whether a local .env override file exists
has_dotenv  := if path_exists(root / ".env") == "true" { "yes (loaded)" } else { "no" }

# ---------------------------------------------------------------------------
# Default recipe — shown on bare `just`
# ---------------------------------------------------------------------------

[doc("List all available recipes")]
default:
    @just --list

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------

[doc("Sync virtual environment from pyproject.toml via uv")]
[group("setup")]
sync:
    {{ uv }} sync --all-groups

[doc("Show just, uv, and Python versions plus venv location")]
[group("setup")]
env-info: sync
    @echo "── Environment ──────────────────────────────────────"
    @echo "just   : $(just --version)"
    @echo "uv     : $({{ uv }} --version)"
    @{{ uv }} run python --version
    @echo "python : {{ python }}"
    @echo "root   : {{ root }}"
    @echo "venv   : {{ root }}/.venv"
    @echo "dotenv : {{ has_dotenv }}"
    @echo "─────────────────────────────────────────────────────"

# ---------------------------------------------------------------------------
# Core recipes
# ---------------------------------------------------------------------------

# Interactive profile selection and analysis launcher.
# Opens a TUI menu to create/select/edit profiles and kick off a run.
[doc("Launch interactive profile menu — create/select/edit profiles, then run")]
[group("run")]
menu: sync
    {{ uv }} run {{ src / "ui" / "profile_menu.py" }}

# Full production run — all 6 domains, full depth, geo fan-out enabled.
# Pass domain names to limit scope: `just run economy healthcare`
# Pass --profile <name> to use a named profile: `just run --profile default`
[doc("Full production run — all domains, full depth, geo fan-out enabled")]
[group("run")]
run *domains="": sync
    {{ uv }} run run_all_domains.py {{ domains }}

# Quick demo run that exercises every code path in ~30 seconds.
# Uses config/demo.yaml: depth=1, 1 subtopic, no geo fan-out, 256-token budgets.
# Default domain is economy; override with: `just demo-run healthcare`
[doc("Demo run — shallow depth, no geo fan-out, ~30 s per domain (default: economy)")]
[group("run")]
demo-run *domains="economy": sync
    {{ uv }} run run_all_domains.py --config {{ cfg_demo }} {{ domains }}

# Collect Reddit opinions + Google News narratives for all domains (or a subset).
# Results are written to output/social_<domain>.json.
# Examples:
#   just collect                   → all 6 domains
#   just collect economy climate   → only those two
[doc("Fetch Reddit + Google News social data → output/social_<domain>.json")]
[group("run")]
collect *domains="": sync
    {{ uv }} run {{ scripts / "collect_social.py" }} {{ domains }}

# ---------------------------------------------------------------------------
# Configuration inspection
# ---------------------------------------------------------------------------

[doc("Estimate total LLM calls for the active config — use --config to override")]
[group("config")]
estimate-calls *args="": sync
    {{ uv }} run {{ scripts / "estimate_calls.py" }} {{ args }}

[doc("Print the effective configuration (config.yaml + env overrides) and exit")]
[group("config")]
show-config:
    {{ uv }} run run_all_domains.py --show-config

[doc("Print the demo configuration and exit")]
[group("config")]
show-config-demo:
    {{ uv }} run run_all_domains.py --config {{ cfg_demo }} --show-config

[doc("Print the production configuration and exit")]
[group("config")]
show-config-prod:
    {{ uv }} run run_all_domains.py --config {{ cfg_prod }} --show-config

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

[doc("Run pytest with coverage report (≥95% required)")]
[group("dev")]
test *flags="": sync
    {{ uv }} run pytest --cov={{ src }} --cov-report=term-missing --cov-fail-under=95 {{ tests }} {{ flags }}

# Run a single test file or function:
#   just test-one tests/unit/test_config.py
#   just test-one tests/unit/test_config.py::TestDefaults::test_default_max_depth
[doc("Run a single test file or function: `just test-one tests/unit/test_config.py`")]
[group("dev")]
test-one target: sync
    {{ uv }} run pytest -v {{ target }}

[doc("Run ruff linter over src/ and tests/")]
[group("dev")]
lint: sync
    {{ uv }} run ruff check {{ src }} {{ tests }}

[doc("Auto-format and auto-fix lint issues in src/ and tests/")]
[group("dev")]
fmt: sync
    {{ uv }} run ruff format {{ src }} {{ tests }}
    {{ uv }} run ruff check --fix {{ src }} {{ tests }}

[doc("Run mypy type checker over src/")]
[group("dev")]
typecheck: sync
    {{ uv }} run mypy {{ src }}

[doc("Run all CI checks: lint → typecheck → test")]
[group("dev")]
check: lint typecheck test

# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

[doc("Remove __pycache__, .pytest_cache, .ruff_cache, and coverage artifacts")]
[group("maintenance")]
clean:
    -find {{ root }} -type d -name "__pycache__" -not -path "*/.venv/*" -exec rm -rf {} +
    -rm -rf {{ root / ".pytest_cache" }}
    -rm -rf {{ root / ".ruff_cache" }}
    -rm -rf {{ root / ".coverage" }}
    -rm -rf {{ root / "coverage.xml" }}
    -rm -rf {{ root / "htmlcov" }}

[doc("Remove generated output reports and social data files (keeps .gitkeep and checkpoints/)")]
[confirm("Delete all generated output files in output/?")]
[group("maintenance")]
clean-output:
    -find {{ output }} -maxdepth 1 -name "*.md" -not -name ".gitkeep" -delete
    -find {{ output }} -maxdepth 1 -name "*.json" -not -name ".gitkeep" -delete

[doc("Delete domain checkpoints to force fresh LLM run: `just clean-checkpoints` (all) or `just clean-checkpoints economy healthcare`")]
[group("maintenance")]
clean-checkpoints *domains="":
    #!/usr/bin/env bash
    set -euo pipefail
    ckpt_dir="{{ output }}/checkpoints"
    if [ ! -d "$ckpt_dir" ]; then
        echo "No checkpoints directory found at $ckpt_dir"
        exit 0
    fi
    if [ -z "{{ domains }}" ]; then
        rm -rf "$ckpt_dir"
        echo "All checkpoints deleted ($ckpt_dir)"
    else
        for d in {{ domains }}; do
            if [ -d "$ckpt_dir/$d" ]; then
                rm -rf "$ckpt_dir/$d"
                echo "Checkpoints deleted for domain: $d"
            else
                echo "No checkpoints found for domain: $d"
            fi
        done
    fi

[doc("Upgrade all dependencies and regenerate uv.lock")]
[group("maintenance")]
upgrade:
    {{ uv }} lock --upgrade
    {{ uv }} sync --all-groups
