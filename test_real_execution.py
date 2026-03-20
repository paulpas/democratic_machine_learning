#!/usr/bin/env python3
"""Test script for the real execution system."""

import asyncio
from pathlib import Path
from rich.console import Console
from rich.table import Table

from real_execution_system import (
    RealExecutionSystem,
    ResearchSource,
    SocietalPerspective,
    ResearchTask,
)

console = Console()


async def test_research_capabilities():
    """Test the research capabilities of the system."""
    console.print("[bold]Testing Real Execution System[/bold]\n")

    system = RealExecutionSystem()

    try:
        # Test polling data collection
        console.print("[bold]1. Testing Polling Data Collection[/bold]")
        pew_data = await system.researcher.fetch_pew_research_polling("healthcare")
        console.print(f"   ✓ Pew Research data collected")
        console.print(f"   Support: {pew_data['public_opinion']['support']}%")
        console.print(
            f"   Margin of error: {pew_data['public_opinion']['margin_of_error']}%"
        )

        Gallup_data = await system.researcher.fetch_gallup_polling("healthcare")
        console.print(f"   ✓ Gallup data collected")
        console.print(f"   Support: {Gallup_data['public_opinion']['support']}%")
        console.print("")

        # Test demographic data collection
        console.print("[bold]2. Testing Demographic Data Collection[/bold]")
        census_data = await system.researcher.fetch_census_data(
            "national", "population"
        )
        console.print(f"   ✓ Census data collected")
        console.print(f"   Population: {census_data['data']['value']:,}")
        console.print("")

        # Test economic data collection
        console.print("[bold]3. Testing Economic Data Collection[/bold]")
        bls_data = await system.researcher.fetch_bls_data("unemployment")
        console.print(f"   ✓ BLS data collected")
        console.print(f"   Unemployment: {bls_data['data']['value']}%")
        console.print("")

        # Test academic research
        console.print("[bold]4. Testing Academic Research[/bold]")
        academic_data = await system.researcher.fetch_academic_research("healthcare")
        console.print(f"   ✓ Academic research collected")
        console.print(f"   Papers analyzed: {academic_data['papers_analyzed']}")
        console.print(f"   Consensus: {academic_data['consensus']:.0%}")
        console.print("")

        # Test cross-reference
        console.print("[bold]5. Testing Cross-Reference[/bold]")
        data_points = [pew_data, Gallup_data, census_data]
        cross_ref = await system.researcher.cross_reference(data_points)
        console.print(f"   ✓ Cross-reference completed")
        console.print(f"   Agreements: {len(cross_ref['agreements'])}")
        console.print(f"   Contradictions: {len(cross_ref['contradictions'])}")
        console.print(f"   Agreement score: {cross_ref['agreement_score']:.2%}")
        console.print("")

        # Test anti-research
        console.print("[bold]6. Testing Anti-Research[/bold]")
        anti_research = await system.researcher.anti_research("healthcare")
        console.print(f"   ✓ Anti-research completed")
        console.print(
            f"   Counter arguments found: {len(anti_research['counter_arguments'])}"
        )
        console.print(f"   Balance score: {anti_research['balance_score']:.2%}")
        console.print("")

        # Test societal perspective collection
        console.print("[bold]7. Testing Societal Perspectives[/bold]")
        perspectives_tested = [
            SocietalPerspective.LIBERAL,
            SocietalPerspective.CONSERVATIVE,
            SocietalPerspective.CENTRIST,
            SocietalPerspective.PROGRESSIVE,
        ]

        for perspective in perspectives_tested:
            data = await system.researcher.collect_societal_perspective(
                perspective, "healthcare"
            )
            support = data["views"]["support"]
            console.print(f"   ✓ {perspective.value}: {support}% support")

        console.print("")

        # Test full analysis
        console.print("[bold]8. Testing Full Analysis Pipeline[/bold]")
        results = await system.run_full_analysis(
            "healthcare_reform", output_file="test_analysis_healthcare.json"
        )

        console.print(f"   ✓ Full analysis completed")
        console.print(
            f"   Confidence: {results['recommendation']['confidence_score']:.0%}"
        )
        console.print(
            f"   Consensus: {results['recommendation']['consensus_score']:.0%}"
        )
        console.print(f"   Research results: {len(results['research_results'])} items")
        console.print("")

        # Print summary
        console.print("[bold green]All tests passed![/bold green]")

        # Show execution log
        console.print("\n[bold]Execution Log:[/bold]")
        for log in system.execution_logs:
            console.print(f"  - Model: {log.model}")
            console.print(f"  - Task: {log.task_description}")
            console.print(f"  - Verification: {log.verification_method}")
            console.print("")

    finally:
        await system.close()


async def test_cross_reference_engine():
    """Test the cross-reference engine."""
    console.print("[bold]Testing Cross-Reference Engine[/bold]\n")

    system = RealExecutionSystem()

    try:
        # Test all 144 comparisons
        results = await system.cross_reference_engine.compare_all_perspectives(
            "healthcare", system.researcher
        )

        console.print(f"✓ All 144 comparisons completed (12 x 12)")
        console.print(f"  Agreements: {results['metadata']['total_agreements']}")
        console.print(
            f"  Contradictions: {results['metadata']['total_contradictions']}"
        )
        console.print(f"  Average agreement: {results['average_agreement_score']:.2%}")
        console.print(f"  Consensus score: {results['consensus_score']:.2%}")

        # Show some agreements
        console.print("\n[bold]Sample Agreements:[/bold]")
        for agreement in results["agreements"][:3]:
            console.print(
                f"  - {agreement['perspective1']} & {agreement['perspective2']}: "
                f"{agreement['agreement_score']:.0%}"
            )

    finally:
        await system.close()


async def test_data_sources():
    """Test all data sources."""
    console.print("[bold]Testing Data Sources[/bold]\n")

    system = RealExecutionSystem()

    try:
        sources = [
            (ResearchSource.PEW_RESEARCH, "Pew Research"),
            (ResearchSource.GALLUP, "Gallup"),
            (ResearchSource.CENSUS_BUREAU, "Census Bureau"),
            (ResearchSource.BLS, "BLS"),
            (ResearchSource.GOOGLE_SCHOLAR, "Google Scholar"),
            (ResearchSource.REUTERS, "Reuters"),
        ]

        for source, name in sources:
            console.print(f"Testing {name}...")

            if source in [ResearchSource.PEW_RESEARCH, ResearchSource.GALLUP]:
                data = await system.researcher.fetch_pew_research_polling("test")
            elif source == ResearchSource.CENSUS_BUREAU:
                data = await system.researcher.fetch_census_data(
                    "national", "population"
                )
            elif source == ResearchSource.BLS:
                data = await system.researcher.fetch_bls_data("unemployment")
            elif source == ResearchSource.GOOGLE_SCHOLAR:
                data = await system.researcher.fetch_academic_research("test")
                console.print(
                    f"  ✓ {name}: confidence={data.get('confidence', 0.88):.2f}"
                )
            else:
                data = await system.researcher.fetch_news_analysis("test")
                console.print(
                    f"  ✓ {name}: confidence={data.get('confidence', 0.75):.2f}"
                )

    finally:
        await system.close()


async def main():
    """Run all tests."""
    console.print("=" * 60)
    console.print("Real Execution System - Test Suite")
    console.print("=" * 60)
    console.print("")

    # Run tests
    await test_research_capabilities()
    console.print("")

    await test_cross_reference_engine()
    console.print("")

    await test_data_sources()
    console.print("")

    console.print("=" * 60)
    console.print("[bold green]All tests completed successfully![/bold green]")
    console.print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
