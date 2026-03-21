#!/usr/bin/env python3
"""Deep research execution system for democratic decision-making.

This system performs comprehensive research by breaking down each policy topic
into fundamental research questions and investigating each one thoroughly.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.research.deep_research_engine import DeepResearchEngine
from src.logging.verbose_logger import get_logger, reset_logger


async def run_deep_research_on_topic(topic: str) -> dict:
    """Run deep research on a single topic.

    Args:
        topic: Policy topic to research

    Returns:
        Research results
    """
    logger = get_logger(
        output_dir="output/logs",
        log_prefix=f"deep_research_{topic.replace('_', '')}",
    )

    engine = DeepResearchEngine(verbose_logger=logger)

    results = await engine.research_topic(topic)

    return {
        "topic": topic,
        "results": results,
        "logger": logger.log_file,
    }


async def main():
    """Run deep research on all topics."""
    print("=" * 70)
    print("DEEP RESEARCH EXECUTION SYSTEM")
    print("=" * 70)

    topics = [
        "healthcare_reform",
        "climate_change_policy",
        "education_funding",
        "immigration_reform",
        "economic_policy",
    ]

    all_results = []

    for topic in topics:
        print(f"\n{'=' * 70}")
        print(f"RESEARCHING: {topic}")
        print("=" * 70)

        result = await run_deep_research_on_topic(topic)
        result["logger"] = str(result["logger"])
        all_results.append(result)

        print(f"\nResults summary:")
        print(f"  Questions decomposed: {result['results']['questions_decomposed']}")
        print(
            f"  Questions investigated: {result['results']['questions_investigated']}"
        )
        print(
            f"  Overall confidence: {result['results']['synthesis']['overall_confidence']:.1%}"
        )
        print(
            f"  Categories: {len(result['results']['synthesis']['category_synthesis'])}"
        )
        print(f"  Log file: {result['logger']}")

    # Save combined results
    output_file = "output/deep_research_all_topics.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'=' * 70}")
    print("COMPLETE")
    print("=" * 70)
    print(f"Topics analyzed: {len(all_results)}")
    print(f"Results saved to: {output_file}")

    return all_results


if __name__ == "__main__":
    asyncio.run(main())
