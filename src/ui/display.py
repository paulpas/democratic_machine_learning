"""Display utilities for the democratic decision-making system."""

from typing import Dict, Optional

from src.models.decision import Decision
from src.utils.metrics import FairnessMetrics


class DecisionDisplay:
    """Displays decision results in various formats."""

    def __init__(self) -> None:
        """Initialize the display."""
        self.metrics = FairnessMetrics()

    def display_decision(self, decision: Decision, fairness: Optional[float] = None) -> str:
        """Display a decision with formatting.

        Args:
            decision: The decision to display
            fairness: Optional fairness score

        Returns:
            Formatted string
        """
        lines = [
            f"Policy: {decision.policy_id}",
            f"Region: {decision.region_id}",
            f"Decision: {decision.outcome.upper()}",
            f"Confidence: {decision.confidence:.2%}",
            f"Votes For: {decision.votes_for}",
            f"Votes Against: {decision.votes_against}",
            f"Margin: {decision.get_margin():.2%}",
        ]

        if fairness is not None:
            lines.append(f"Fairness: {fairness:.2%}")

        return "\n".join(lines)

    def display_batch(self, decisions: list, fairness_scores: Optional[Dict] = None) -> str:
        """Display multiple decisions.

        Args:
            decisions: List of decisions
            fairness_scores: Optional fairness scores by region

        Returns:
            Formatted string
        """
        lines = ["\n" + "=" * 50, "DECISION BATCH RESULTS", "=" * 50]

        for i, decision in enumerate(decisions, 1):
            fairness = fairness_scores.get(decision.region_id) if fairness_scores else None
            lines.append(f"\n--- Decision {i} ---")
            lines.append(self.display_decision(decision, fairness))

        return "\n".join(lines)


class PolicyDashboard:
    """Displays policy analysis dashboard."""

    def __init__(self) -> None:
        """Initialize the dashboard."""
        self.metrics = FairnessMetrics()

    def display_policy_analysis(
        self, policy_id: str, decisions: list, voters: dict, regions: dict
    ) -> str:
        """Display policy analysis dashboard.

        Args:
            policy_id: Policy ID to analyze
            decisions: List of decisions for this policy
            voters: Dictionary of voters
            regions: Dictionary of regions

        Returns:
            Formatted dashboard string
        """
        lines = [
            "\n" + "╔" + "═" * 58 + "╗",
            f"║{policy_id.center(58)}║",
            "╚" + "═" * 58 + "╝",
            "",
            "DECISION SUMMARY",
            "-" * 40,
        ]

        if not decisions:
            lines.append("No decisions made yet")
            return "\n".join(lines)

        approved = sum(1 for d in decisions if d.outcome == "approved")
        rejected = sum(1 for d in decisions if d.outcome == "rejected")
        avg_confidence = sum(d.confidence for d in decisions) / len(decisions)

        lines.extend(
            [
                f"Total Decisions: {len(decisions)}",
                f"Approved: {approved}",
                f"Rejected: {rejected}",
                f"Avg. Confidence: {avg_confidence:.2%}",
            ]
        )

        if voters:
            fairness = self.metrics.calculate_fairness(decisions[0], voters, regions)
            lines.extend(
                [
                    "",
                    "FAIRNESS METRICS",
                    "-" * 40,
                    f"Fairness Score: {fairness:.2%}",
                ]
            )

        return "\n".join(lines)
