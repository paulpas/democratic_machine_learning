#!/usr/bin/env python3
"""Standalone social-narrative collector.

Fetches Reddit opinions and Google News narratives for every policy domain
(or a subset) and writes results to ``output/social_<domain>.json``.

Usage (via just):
    just collect                   # all six domains
    just collect economy           # one domain
    just collect economy climate   # multiple domains

Usage (direct):
    uv run scripts/collect_social.py [domain ...]
    python3 scripts/collect_social.py economy healthcare
"""

from __future__ import annotations

import json
import sys
import datetime
from pathlib import Path

# ── path setup ────────────────────────────────────────────────────────────────
# Allow running from any directory — insert repo root so `src` is importable.
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from src.config import load_config  # noqa: E402  (after sys.path fixup)

# ── domain → canonical search topic mapping ───────────────────────────────────
DOMAIN_TOPICS: dict[str, str] = {
    "economy": "US economic policy federal budget",
    "healthcare": "US healthcare policy insurance coverage",
    "education": "US education policy public schools funding",
    "immigration": "US immigration policy border enforcement",
    "climate": "US climate policy carbon emissions energy",
    "infrastructure": "US infrastructure policy roads bridges broadband",
}

ALL_DOMAINS = list(DOMAIN_TOPICS.keys())


def _banner(msg: str) -> None:
    width = 72
    print(f"\n{'=' * width}")
    print(f"  {msg}")
    print(f"{'=' * width}")


def collect_domain(domain: str, collector: object) -> dict:  # type: ignore[type-arg]
    """Collect social data for one domain and return the result dict."""
    topic = DOMAIN_TOPICS[domain]
    print(f"\n  [{domain.upper()}]  topic='{topic}'")
    data = collector.get_comprehensive_social_data(topic=topic, domain=domain)  # type: ignore[attr-defined]
    summary = data.get("summary", {})
    print(
        f"    opinions={summary.get('total_opinions', 0)}"
        f"  narratives={summary.get('total_narratives', 0)}"
        f"  avg_sentiment={summary.get('average_opinion_sentiment', 0.0):.3f}"
        f"  avg_credibility={summary.get('average_media_credibility', 0.0):.3f}"
    )
    return data


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]

    # Filter to known domains; unknown args are ignored with a warning.
    domains: list[str] = []
    for arg in args:
        d = arg.lower().strip()
        if d in DOMAIN_TOPICS:
            domains.append(d)
        else:
            print(f"  WARNING: unknown domain '{arg}' — skipped", file=sys.stderr)

    if not domains:
        domains = ALL_DOMAINS

    _banner(
        f"SOCIAL NARRATIVE COLLECTOR  |  "
        f"{len(domains)} domain(s)  |  "
        f"started {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print(f"  domains : {domains}")

    # Load config (honours config.yaml + DML_* env vars)
    cfg = load_config()
    print(f"  cache_hours    : {cfg.social.cache_hours}")
    print(f"  max_opinions   : {cfg.social.max_opinions}")
    print(f"  max_narratives : {cfg.social.max_narratives}")

    from src.data.social_narrative_collector import SocialNarrativeCollector  # noqa: E402

    collector = SocialNarrativeCollector()

    output_dir = _REPO_ROOT / "output"
    output_dir.mkdir(exist_ok=True)

    results: dict[str, dict] = {}  # type: ignore[type-arg]
    failed: list[str] = []

    for domain in domains:
        try:
            data = collect_domain(domain, collector)
            results[domain] = data

            out_path = output_dir / f"social_{domain}.json"
            out_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
            print(f"    saved → {out_path.relative_to(_REPO_ROOT)}")

        except Exception as exc:
            print(f"  ERROR collecting {domain}: {exc}", file=sys.stderr)
            failed.append(domain)

    # ── summary ───────────────────────────────────────────────────────────────
    _banner("COLLECTION COMPLETE")
    print(f"  succeeded : {len(results)}")
    print(f"  failed    : {len(failed)}")
    if failed:
        print(f"  FAILED    : {failed}")
    print(f"\n  Output files:")
    for domain in results:
        p = output_dir / f"social_{domain}.json"
        kb = p.stat().st_size / 1024
        print(f"    {p.relative_to(_REPO_ROOT)}  ({kb:.1f} KB)")
    print()

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
