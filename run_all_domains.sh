#!/usr/bin/env bash
# run_all_domains.sh — Shell entry point for the Democratic Machine Learning System
#
# Usage:
#   ./run_all_domains.sh                          # all 6 domains
#   ./run_all_domains.sh healthcare economy        # specific domains
#
# All output (including LLM call logs, geographic fan-out, voter registration,
# conjecture formation, and report writing) streams to stdout in real-time.
#
# Requirements:
#   - Python 3.11+
#   - llama.cpp server running on http://localhost:8080 (or set LLAMA_CPP_ENDPOINT)
#   - pip install -r requirements.txt

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

echo "=============================================================="
echo "  DEMOCRATIC MACHINE LEARNING SYSTEM"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================================="
echo ""
echo "  Python   : $($PYTHON --version 2>&1)"
echo "  Script   : $SCRIPT_DIR/run_all_domains.py"
echo "  Endpoint : ${LLAMA_CPP_ENDPOINT:-http://localhost:8080}"
echo "  Output   : $SCRIPT_DIR/output/"
echo ""

exec "$PYTHON" "$SCRIPT_DIR/run_all_domains.py" "$@"
