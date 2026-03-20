"""Test script for verbose logging system."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.logging.verbose_logger import VerboseLogger, get_logger


def test_verbose_logging():
    """Test the verbose logging system."""
    logger = get_logger()

    print("=" * 70)
    print("VERBOSE LOGGING SYSTEM TEST")
    print("=" * 70)

    # 1. Research question
    logger.record_research_question(
        "What voting methods prevent minority tyranny?",
        "Based on Arrow's Impossibility Theorem and need for fair representation",
    )

    # 2. Source discovery
    source1 = logger.discover_source(
        url="https://www.wiley.com/en-us/Social+Choice+and+Individual+Values-p-9780300013205",
        title="Arrow, K. J. (1951). Social Choice and Individual Values",
        relevance=98,
        usefulness=95,
        discovery_method="Academic search",
    )

    # 3. Information extraction
    logger.record_information_extraction(
        source1,
        "Arrow's Impossibility Theorem: No rank-order system can satisfy all fairness criteria",
    )

    # 4. Initial conjecture
    logger.record_conjecture(
        "Approval voting prevents minority tyranny because it allows expressing support for multiple candidates",
        "Based on Arrow's theorem showing all systems have trade-offs",
    )

    # 5. Evidence evaluation
    logger.add_evidence(
        logger.current_conjecture_id,
        "Approval voting allows voters to support multiple candidates, preventing vote-splitting",
        "supporting",
    )

    # 6. Conjecture update
    logger.update_conjecture(
        logger.current_conjecture_id,
        "Approval voting may not fully prevent gerrymandering",
        "Approval voting solves some issues but not all",
        "Review of Lijphart's democratic peace research",
    )

    # 7. Prompt execution
    logger.record_prompt(
        "Analyze voting systems for minority protection",
        context="Based on Arrow and Lijphart research",
        position=1,
    )

    logger.record_prompt(
        "Evaluate approval voting vs ranked choice",
        context="Comparing systems for minority representation",
        position=2,
    )

    # 8. Final conclusion
    logger.record_final_conclusion(
        "Approval voting is the best system for preventing minority tyranny",
        confidence=85,
    )

    # 9. Save summary
    logger.save_summary()
    logger.print_summary()

    print("\nTest completed successfully!")
    print(f"Log file: {logger.log_file}")
    print(f"Summary file: {logger.summary_file}")


if __name__ == "__main__":
    test_verbose_logging()
