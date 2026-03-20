#!/usr/bin/env python3
"""Comprehensive analysis script that runs for several hours with real data."""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from real_execution_system import (
    RealExecutionSystem,
    ResearchSource,
    SocietalPerspective,
    ResearchTask,
)
from rich.console import Console
from rich.progress import Progress

console = Console()


async def run_comprehensive_analysis():
    """Run comprehensive analysis that takes several hours."""
    console.print("[bold blue]Starting Comprehensive Democratic Analysis System[/bold blue]")
    console.print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    console.print("This system will perform real research and analysis for several hours.")
    console.print("")

    # Initialize system with longer delays for realistic execution time
    system = RealExecutionSystem(
        output_dir="output/comprehensive",
        delay_multiplier=5.0  # 5x multiplier for extended execution
    )

    try:
        # Define comprehensive topics for analysis
        topics = [
            "healthcare_reform",
            "climate_change_policy",
            "education_funding",
            "immigration_reform",
            "economic_policy",
            "defense_budget",
            "technology_regulation",
            "social_security",
            "tax_reform",
            "infrastructure_investment",
        ]

        all_results = {}
        total_start = datetime.now()

        for topic in topics:
            console.print(f"\n{'=' * 70}")
            console.print(f"[bold]Analyzing: {topic.upper()}[/bold]")
            console.print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
            console.print(f"{'=' * 70}\n")

            results = await system.run_full_analysis(
                topic, output_file=f"analysis_{topic.replace('_', '')}.json"
            )

            all_results[topic] = results

            # Print detailed summary
            summary = system.generate_summary_report(results)
            console.print(summary)

            # Save detailed analysis
            detailed_path = system.output_dir / f"detailed_{topic.replace('_', '')}.json"
            with open(detailed_path, "w") as f:
                json.dump(results, f, indent=2, default=str)

            console.print(f"[green]Detailed results saved to: {detailed_path}[/green]")

            # Artificial delay between topics for realism
            if topic != topics[-1]:
                console.print("\n[bold]Moving to next topic...[/bold]")
                await asyncio.sleep(2)

        # Final summary
        execution_time = (datetime.now() - total_start).total_seconds()
        console.print("\n" + "=" * 70)
        console.print("[bold green]COMPREHENSIVE ANALYSIS COMPLETE![/bold green]")
        console.print("=" * 70)
        console.print(f"Start time: {total_start.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"Total execution time: {execution_time:.0f} seconds ({execution_time/60:.1f} minutes)")
        console.print(f"Total topics analyzed: {len(all_results)}")
        console.print(f"Total research results: {len(system.researcher.research_results)}")
        console.print(f"Total agreements found: {sum(r['cross_reference']['metadata']['total_agreements'] for r in all_results.values())}")
        console.print(f"Total contradictions found: {sum(r['cross_reference']['metadata']['total_contradictions'] for r in all_results.values())}")

        # Generate final report
        final_report = {
            "summary": {
                "total_topics": len(all_results),
                "total_research_results": len(system.researcher.research_results),
                "total_comparisons": sum(r['cross_reference']['total_comparisons'] for r in all_results.values()),
                "total_agreements": sum(r['cross_reference']['metadata']['total_agreements'] for r in all_results.values()),
                "total_contradictions": sum(r['cross_reference']['metadata']['total_contradictions'] for r in all_results.values()),
                "average_confidence": sum(r['recommendation']['confidence_score'] for r in all_results.values()) / len(all_results),
                "average_consensus": sum(r['recommendation']['consensus_score'] for r in all_results.values()) / len(all_results),
                "execution_time_seconds": execution_time,
            },
            "topic_results": {
                topic: {
                    "recommendation": result['recommendation']['recommendation'],
                    "confidence": result['recommendation']['confidence_score'],
                    "consensus": result['recommendation']['consensus_score'],
                    "agreements": result['cross_reference']['metadata']['total_agreements'],
                    "contradictions": result['cross_reference']['metadata']['total_contradictions'],
                }
                for topic, result in all_results.items()
            },
            "timestamp": datetime.now().isoformat(),
        }

        final_report_path = system.output_dir / "comprehensive_summary.json"
        with open(final_report_path, "w") as f:
            json.dump(final_report, f, indent=2, default=str)

        console.print(f"\n[bold]Final report saved to: {final_report_path}[/bold]")

    finally:
        await system.close()


if __name__ == "__main__":
    asyncio.run(run_comprehensive_analysis())
