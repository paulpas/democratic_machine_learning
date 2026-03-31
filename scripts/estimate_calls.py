#!/usr/bin/env python3
"""Print an LLM call estimate for the active (or supplied) config.

Usage:
    uv run scripts/estimate_calls.py
    uv run scripts/estimate_calls.py --config config/demo.yaml
    uv run scripts/estimate_calls.py --domains 3
"""

import argparse
import sys
from pathlib import Path

# Make sure 'src' is importable when run from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import get_config, load_config  # noqa: E402
from src.llm.integration import estimate_calls  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate LLM call count for a config.")
    parser.add_argument("--config", default="", help="Path to a YAML config file")
    parser.add_argument("--domains", type=int, default=6, help="Number of domains (default 6)")
    parser.add_argument(
        "--no-progressive", action="store_true", help="Estimate without progressive synthesis"
    )
    parser.add_argument(
        "--no-combine",
        action="store_true",
        help="Estimate without combined geo calls (old 2-call mode)",
    )
    args = parser.parse_args()

    if args.config:
        load_config(args.config)

    cfg = get_config()
    vp = cfg.voter_pool
    est = estimate_calls(
        max_depth=vp.prod_llm_max_depth,
        subtopics_per_level=vp.prod_llm_subtopics_per_level,
        geo_fan_out=vp.prod_geo_fan_out,
        domains=args.domains,
        progressive_synthesis=False if args.no_progressive else None,
        combine_geo=False if args.no_combine else None,
    )

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
