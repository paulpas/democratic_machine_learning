"""Fairness and efficiency metrics for democratic decision-making."""

from typing import Dict, List, Optional
import numpy as np
from src.models.decision import Decision
from src.models.voter import Voter, VoterType
from src.models.region import Region
from src.config import get_config


class FairnessMetrics:
    """Calculates fairness metrics for democratic decisions."""

    def __init__(
        self,
        min_proportion: Optional[float] = None,
        max_disparity: Optional[float] = None,
    ) -> None:
        """Initialize fairness metrics.

        Args:
            min_proportion: Minimum proportion of affected groups that must be satisfied.
            max_disparity: Maximum allowed disparity in outcomes.
            Both parameters default to ``config.yaml`` ``fairness.*`` values.
        """
        _cfg = get_config().fairness
        self.min_proportion = (
            min_proportion if min_proportion is not None else _cfg.min_proportion
        )
        self.max_disparity = (
            max_disparity if max_disparity is not None else _cfg.max_disparity
        )

    def calculate_fairness(
        self, decision: Decision, voters: Dict[str, Voter], regions: Dict[str, Region]
    ) -> float:
        """Calculate fairness score for a decision.

        Args:
            decision: The decision to evaluate
            voters: Dictionary of voters
            regions: Dictionary of regions

        Returns:
            Fairness score (0-1)
        """
        if not voters:
            return 1.0

        voter_scores = []
        for voter in voters.values():
            preference = voter.get_preference(decision.policy_id)
            weight = voter.voting_weight

            if decision.outcome == "approved" and preference > 0:
                score = weight
            elif decision.outcome == "rejected" and preference < 0:
                score = weight
            elif decision.outcome == "abstain":
                score = 0.5 * weight
            else:
                score = 0.0

            voter_scores.append(score)

        if not voter_scores:
            return 1.0

        total_score = sum(voter_scores)
        avg_score = total_score / len(voter_scores)

        variance = np.var(voter_scores)
        std_dev = np.sqrt(variance)

        fairness = 1.0 - min(std_dev / (avg_score + 0.1), 1.0)

        return max(0.0, min(1.0, fairness))

    def calculate_group_fairness(
        self, decision: Decision, voters: Dict[str, Voter], group_key: str = "region_id"
    ) -> Dict[str, float]:
        """Calculate fairness scores for different groups.

        Args:
            decision: The decision to evaluate
            voters: Dictionary of voters
            group_key: Key to group voters by

        Returns:
            Dictionary mapping group IDs to fairness scores
        """
        groups: Dict[str, List[Voter]] = {}

        for voter in voters.values():
            group_id = getattr(voter, group_key, "unknown")
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(voter)

        group_scores = {}
        for group_id, group_voters in groups.items():
            group_voters_dict = {v.voter_id: v for v in group_voters}
            group_scores[group_id] = self.calculate_fairness(
                decision, group_voters_dict, {}
            )

        return group_scores

    def check_proportional_representation(
        self,
        voters: Dict[str, Voter],
        decision_outcomes: List[Decision],
        target_proportion: float = 0.5,
    ) -> bool:
        """Check if decisions satisfy proportional representation.

        Args:
            voters: Dictionary of voters
            decision_outcomes: List of decisions
            target_proportion: Target proportion of satisfied voters

        Returns:
            True if proportional representation is satisfied
        """
        group_outcomes: Dict[str, int] = {}
        group_totals: Dict[str, int] = {}

        for decision in decision_outcomes:
            for voter_id in decision.voters_participated:
                voter = voters.get(voter_id)
                if not voter:
                    continue

                group_id = voter.region_id
                group_totals[group_id] = group_totals.get(group_id, 0) + 1

                if (
                    decision.outcome == "approved"
                    and voter.get_preference(decision.policy_id) > 0
                ):
                    group_outcomes[group_id] = group_outcomes.get(group_id, 0) + 1
                elif (
                    decision.outcome == "rejected"
                    and voter.get_preference(decision.policy_id) < 0
                ):
                    group_outcomes[group_id] = group_outcomes.get(group_id, 0) + 1

        for group_id, total in group_totals.items():
            satisfied = group_outcomes.get(group_id, 0)
            proportion = satisfied / total if total > 0 else 0

            if proportion < target_proportion:
                return False

        return True


class EfficiencyMetrics:
    """Calculates efficiency metrics for the system."""

    def __init__(self) -> None:
        """Initialize efficiency metrics."""
        self.decision_times: List[float] = []
        self.voter_participation_rates: List[float] = []

    def calculate_consensus_score(self, decision: Decision) -> float:
        """Calculate consensus score for a decision.

        Args:
            decision: The decision to evaluate

        Returns:
            Consensus score (0-1)
        """
        total_votes = decision.votes_for + decision.votes_against

        if total_votes == 0:
            return 0.0

        support_pct = decision.votes_for / total_votes

        if support_pct > 0.8:
            return 1.0
        elif support_pct > 0.5:
            return (support_pct - 0.5) * 2.5
        else:
            return 0.0

    def calculate_participation_rate(
        self, voters_in_region: int, voters_participated: int
    ) -> float:
        """Calculate participation rate.

        Args:
            voters_in_region: Total voters in region
            voters_participated: Voters who participated

        Returns:
            Participation rate (0-1)
        """
        if voters_in_region == 0:
            return 0.0

        return voters_participated / voters_in_region

    def calculate_system_efficiency(
        self, decisions: List[Decision], total_voters: int
    ) -> float:
        """Calculate overall system efficiency.

        Args:
            decisions: List of decisions
            total_voters: Total number of voters

        Returns:
            System efficiency score (0-1)
        """
        if not decisions:
            return 1.0

        total_participation = sum(len(d.voters_participated) for d in decisions)
        avg_participation = total_participation / len(decisions)

        participation_rate = min(avg_participation / total_voters, 1.0)

        avg_consensus = sum(self.calculate_consensus_score(d) for d in decisions) / len(
            decisions
        )

        return (participation_rate + avg_consensus) / 2.0
