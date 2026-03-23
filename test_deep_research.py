"""Integration test for deep research engine."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.research.deep_research_engine import DeepResearchEngine, ResearchDepth
from src.verbose_logging.verbose_logger import get_logger, reset_logger


async def test_deep_research():
    """Test the deep research engine with healthcare topic."""
    print("=" * 70)
    print("DEEP RESEARCH ENGINE TEST")
    print("=" * 70)

    # Initialize logger
    logger = get_logger(output_dir="output/logs", log_prefix="deep_research_test")
    print(f"\nLogger initialized: {logger.log_file}")

    # Initialize engine
    engine = DeepResearchEngine(verbose_logger=logger)

    # Test with healthcare topic
    topic = "healthcare_reform"
    print(f"\nResearching: {topic}")
    print("-" * 70)

    # Decompose topic
    questions = engine.decompose_topic(topic)
    print(f"\nDecomposed into {len(questions)} research questions:")
    for q in questions[:10]:  # Show first 10
        print(f"  [{q.question_id}] ({q.category}) {q.question}")
    if len(questions) > 10:
        print(f"  ... and {len(questions) - 10} more")

    # Build knowledge graph
    graph = engine.build_knowledge_graph(questions)
    print(f"\nKnowledge graph built with {len(graph)} categories:")
    for cat, connections in graph.items():
        print(f"  {cat} -> {connections}")

    # Investigate a sample of questions
    print(f"\nInvestigating questions...")
    sample_size = min(5, len(questions))
    print(f"Sample size: {sample_size} questions")

    investigated = []
    for q in questions[:sample_size]:
        print(f"\n  Investigating: {q.question}")
        result = await engine.investigate_question(q, topic)
        investigated.append(result)
        print(f"    Evidence found: {len(result.evidence)} sources")
        print(f"    Confidence: {result.confidence:.1%}")

    # Synthesize findings
    print(f"\nSynthesizing findings...")
    synthesis = await engine.synthesize_findings(investigated)

    print(f"\n" + "=" * 70)
    print("RESEARCH SUMMARY")
    print("=" * 70)
    print(f"Topic: {topic}")
    print(f"Questions decomposed: {len(questions)}")
    print(f"Questions investigated: {len(investigated)}")
    print(f"Overall confidence: {synthesis['overall_confidence']:.1%}")
    print(f"\nCategory synthesis:")
    for cat, data in synthesis["category_synthesis"].items():
        print(f"  {cat}:")
        print(f"    Questions: {data['questions_answered']}")
        print(f"    Confidence: {data['average_confidence']:.1%}")
        print(f"    Key findings: {len(data['key_findings'])} items")

    print(f"\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"Log file: {logger.log_file}")
    print(f"Summary file: {logger.summary_file}")

    return synthesis


if __name__ == "__main__":
    result = asyncio.run(test_deep_research())
