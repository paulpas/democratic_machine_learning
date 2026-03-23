#!/usr/bin/env python3
"""Deep Recursive LLM Investigation Demo with State/County Representation.

This script demonstrates the enhanced recursive LLM investigation system that:
1. Investigates a domain comprehensively at the national level
2. Fans out to subtopics at multiple levels of depth
3. Investigates each subtopic at national, state, and county levels
4. Elaborates extensively on each aspect
5. Synthesizes a final conjecture based on all evidence
6. Ranks solutions with geographic weighting
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.llm.integration import LLMClient
from src.data.social_narrative_collector import SocialNarrativeCollector


def demonstrate_deep_recursive_investigation():
    """Demonstrate deep recursive LLM investigation with state/county representation."""

    print("=" * 80)
    print("DEEP RECURSIVE LLM INVESTIGATION DEMO")
    print("=" * 80)
    print()

    # Initialize LLM client
    llm_client = LLMClient()

    # Initialize social narrative collector
    social_collector = SocialNarrativeCollector()

    # Domain to investigate
    domain = "healthcare"

    # Initial context
    initial_context = {
        "population": 331000000,
        "diversity_index": 0.73,
        "urban_ratio": 0.83,
        "domain": domain,
        "region_type": "national",
    }

    print(f"INITIATING DEEP RECURSIVE INVESTIGATION OF: {domain.upper()}")
    print(f"Population: {initial_context['population']:,}")
    print(f"Diversity Index: {initial_context['diversity_index']}")
    print(f"Urban Ratio: {initial_context['urban_ratio']}")
    print()

    # Run deep recursive investigation with state/county representation (FULL EXECUTION)
    results = llm_client.generate_reasoning_with_recursion(
        domain=domain,
        initial_context=initial_context,
        max_depth=4,  # Full 5 levels: national + 4 levels of recursion
        subtopics_per_level=5,  # Full 5 subtopics per level
        principles=[
            "Inclusivity",
            "Transparency",
            "Accountability",
            "Adaptability",
            "Equity",
            "Evidence-Based",
            "Context-Aware",
        ],
        include_state_county_rep=True,  # Enable state/county representation
    )


def demonstrate_social_data_integration():
    """Demonstrate social data collection integration."""

    print("=" * 80)
    print("SOCIAL DATA COLLECTION INTEGRATION DEMO")
    print("=" * 80)
    print()

    social_collector = SocialNarrativeCollector()

    # Collect social data for a domain
    domain = "healthcare"

    social_data = social_collector.get_comprehensive_social_data(
        topic="healthcare policy",
        domain=domain,
    )

    print(f"Collected social data for domain: {domain}")
    print(f"Total Opinions: {social_data.get('summary', {}).get('total_opinions', 0)}")
    print(
        f"Total Media Narratives: {social_data.get('summary', {}).get('total_narratives', 0)}"
    )
    print(
        f"Average Opinion Sentiment: {social_data.get('summary', {}).get('average_opinion_sentiment', 0):.3f}"
    )
    print(
        f"Average Narrative Sentiment: {social_data.get('summary', {}).get('average_narrative_sentiment', 0):.3f}"
    )
    print()

    # Show sample opinions
    print("SAMPLE OPINIONS:")
    for i, opinion in enumerate(social_data.get("opinions", [])[:3], 1):
        print(
            f"  {i}. [{opinion.get('perspective', 'unknown')}] {opinion.get('text', '')[:100]}..."
        )
    print()

    # Show sample media narratives
    print("SAMPLE MEDIA NARRATIVES:")
    for i, narrative in enumerate(social_data.get("media_narratives", [])[:3], 1):
        print(
            f"  {i}. [{narrative.get('outlet', 'unknown')}] {narrative.get('title', '')}"
        )
    print()


def main():
    """Main entry point."""

    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print(
        "║"
        + "  DEEP RECURSIVE LLM INVESTIGATION WITH STATE/COUNTY REPRESENTATION".center(
            78
        )
        + "║"
    )
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Run demonstrations
    results = demonstrate_deep_recursive_investigation()

    print()
    print()

    # Social data integration demo
    demonstrate_social_data_integration()

    print()
    print("=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ Deep recursive LLM investigation (4 levels)")
    print("  ✓ State/county geographic representation")
    print("  ✓ Extensive elaboration at each level")
    print("  ✓ Fan-out to subtopics with hierarchical depth")
    print("  ✓ Final conjecture synthesis with evidence ranking")
    print("  ✓ Geographic weighting in solution ranking")
    print("  ✓ Social data integration from Reddit and Google News")
    print()

    return results


if __name__ == "__main__":
    main()
