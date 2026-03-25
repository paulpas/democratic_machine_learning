#!/usr/bin/env python3
"""Print an LLM call estimate for the active (or supplied) config.

Usage:
    uv run scripts/estimate_calls.py
    uv run scripts/estimate_calls.py --config configs/demo.yaml
    uv run scripts/estimate_calls.py --domains 3
"""

import argparse
import sys
from pathlib import Path

# Make sure 'src' is importable when run from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import load_config, get_config  # noqa: E402
from src.llm.integration import estimate_calls  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate LLM call count for a config.")
    parser.add_argument("--config", default="", help="Path to a YAML config file")
    parser.add_argument("--domains", type=int, default=6, help="Number of domains (default 6)")
    args = parser.parse_args()

    if args.config:
        load_config(args.config)

    cfg = get_config()
    est = estimate_calls(domains=args.domains)

    print()
    print("  LLM Call Estimate")
    print("  " + "═" * 44)
    print(est["breakdown"])
    print()
    print(f"  config file : {args.config or 'config.yaml (default)'}")
    print(f"  llm endpoint: {cfg.llm.endpoint}")
    print()


if __name__ == "__main__":
    main()
