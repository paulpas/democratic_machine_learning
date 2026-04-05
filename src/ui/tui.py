"""TUI interface for the democratic decision-making system."""

import argparse
import json
from typing import Dict

from src.core.decision_engine import DecisionEngine
from src.core.feedback_loop import FeedbackLoop
from src.models.policy import Policy, PolicyDomain
from src.models.region import Region
from src.models.voter import Voter, VoterType


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Democratric Decision Engine - Make fair, adaptive decisions"
    )

    parser.add_argument("--data", "-d", type=str, help="Path to data file (JSON)")
    parser.add_argument("--region", "-r", type=str, required=True, help="Region ID")
    parser.add_argument("--policy", "-p", type=str, default="default_policy", help="Policy ID")
    parser.add_argument(
        "--type",
        "-t",
        type=str,
        default="direct_vote",
        choices=["direct_vote", "representative", "expert"],
        help="Decision type",
    )
    parser.add_argument("--feedback", action="store_true", help="Enable feedback loop")
    parser.add_argument("--fairness", type=float, default=0.7, help="Fairness threshold (0.0-1.0)")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="rich",
        choices=["text", "json", "rich"],
        help="Output format",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    return parser.parse_args()


def load_data(data_path: str) -> Dict:
    """Load data from JSON file."""
    with open(data_path, "r") as f:
        return json.load(f)


def create_entities(data: Dict) -> tuple:
    """Create engine entities from data."""
    engine = DecisionEngine()

    # Create regions
    for region_data in data.get("regions", []):
        region = Region(
            region_id=region_data["id"],
            name=region_data["name"],
            region_type=region_data.get("type", "county"),
            population=region_data.get("population", 0),
        )
        engine.register_region(region)

    # Create policies
    for policy_data in data.get("policies", []):
        policy = Policy(
            policy_id=policy_data["id"],
            name=policy_data["name"],
            description=policy_data.get("description", ""),
            domain=PolicyDomain(policy_data.get("domain", "economic")),
        )
        engine.register_policy(policy)

    # Create voters
    for voter_data in data.get("voters", []):
        voter = Voter(
            voter_id=voter_data["id"],
            region_id=voter_data.get("region", "default"),
            preferences=voter_data.get("preferences", {}),
            expertise=voter_data.get("expertise", {}),
            voting_weight=voter_data.get("weight", 1.0),
            voter_type=VoterType(voter_data.get("type", "participant")),
        )
        engine.register_voter(voter)

    return engine


def run_decision(
    engine: DecisionEngine,
    region_id: str,
    policy_id: str,
    decision_type: str,
    feedback: bool = False,
) -> tuple:
    """Run decision and optionally feedback loop."""
    decision = engine.make_decision(policy_id, region_id, decision_type)

    feedback_loop = None
    if feedback:
        feedback_loop = FeedbackLoop()
        evaluation = feedback_loop.evaluate_decision(decision)
        return decision, feedback_loop, evaluation

    return decision, None, None


def display_results(decision, feedback_loop, evaluation, output_format: str) -> None:
    """Display results in specified format."""
    if output_format == "json":
        display_json(decision, evaluation)
    elif output_format == "rich":
        display_rich(decision, evaluation)
    else:
        display_text(decision, evaluation)


def display_text(decision, evaluation) -> None:
    """Display results as plain text."""
    print("\n" + "=" * 60)
    print("DECISION ENGINE - DECISION REPORT")
    print("=" * 60)
    print(f"\nPolicy: {decision.policy_id}")
    print(f"Region: {decision.region_id}")
    print("\nVoting Results:")
    print(f"  For:      {decision.votes_for}")
    print(f"  Against:  {decision.votes_against}")
    print(f"  Margin:   {decision.get_margin():.2%}")
    print(f"\nDecision: {decision.outcome.upper()}")
    print(f"Confidence: {decision.confidence:.2%}")

    if evaluation:
        print(f"\nFairness: {evaluation['fairness']:.2%}")
        print(f"Effectiveness: {evaluation['effectiveness']:.2%}")
        print(f"Balance: {evaluation['balance']:.2%}")


def display_rich(decision, evaluation) -> None:
    """Display results with rich formatting."""
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + "     DEMOCRATIC DECISION ENGINE - DECISION REPORT".center(58) + "║")
    print("╚" + "═" * 58 + "╝")

    print(f"\n[bold]Policy:[/bold] {decision.policy_id}")
    print(f"[bold]Region:[/bold] {decision.region_id}")

    print("\n[bold]Voting Results:[/bold]")
    print(f"  [green]For:[/green]      {decision.votes_for}")
    print(f"  [red]Against:[/red]  {decision.votes_against}")
    print(f"  [cyan]Margin:[/cyan]    {decision.get_margin():.2%}")

    status = "[green]APPROVED[/green]" if decision.outcome == "approved" else "[red]REJECTED[/red]"
    print(f"\nDecision: {status}")
    print(f"Confidence: {decision.confidence:.2%}")

    if evaluation:
        print("\n[bold]Fairness Metrics:[/bold]")
        print(f"  Fairness: {evaluation['fairness']:.2%}")
        print(f"  Effectiveness: {evaluation['effectiveness']:.2%}")
        print(f"  Balance: {evaluation['balance']:.2%}")


def display_json(decision, evaluation) -> None:
    """Display results as JSON."""
    result = {
        "policy": decision.policy_id,
        "region": decision.region_id,
        "decision": {
            "outcome": decision.outcome,
            "confidence": decision.confidence,
            "votes_for": decision.votes_for,
            "votes_against": decision.votes_against,
            "margin": decision.get_margin(),
        },
    }

    if evaluation:
        result["fairness"] = evaluation

    print(json.dumps(result, indent=2))


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Load data if provided
    if args.data:
        data = load_data(args.data)
        engine = create_entities(data)
    else:
        engine = DecisionEngine(fairness_threshold=args.fairness)

    # Run decision
    decision, feedback_loop, evaluation = run_decision(
        engine=engine,
        region_id=args.region,
        policy_id=args.policy,
        decision_type=args.type,
        feedback=args.feedback,
    )

    # Display results
    display_results(decision, feedback_loop, evaluation, args.output)

    # Print feedback trends if available
    if feedback_loop and args.verbose:
        trends = feedback_loop.get_trends()
        if trends:
            print("\n[bold]Trends:[/bold]")
            print(f"  Avg Fairness: {trends['avg_fairness']:.2%}")
            print(f"  Avg Effectiveness: {trends['avg_effectiveness']:.2%}")


if __name__ == "__main__":
    main()
