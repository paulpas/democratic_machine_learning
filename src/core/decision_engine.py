"""Core decision engine for democratic decision-making."""

from typing import Dict, List, Optional
from src.models.voter import Voter, VoterType
from src.models.policy import Policy
from src.models.region import Region
from src.models.decision import Decision
from src.utils.metrics import FairnessMetrics


class DecisionEngine:
    """Main engine for making democratic decisions."""

    def __init__(self, fairness_threshold: float = 0.7) -> None:
        """Initialize the decision engine.

        Args:
            fairness_threshold: Minimum fairness score required for decisions
        """
        self.fairness_threshold = fairness_threshold
        self.voters: Dict[str, Voter] = {}
        self.policies: Dict[str, Policy] = {}
        self.regions: Dict[str, Region] = {}
        self.decisions: List[Decision] = []
        self.fairness_metrics = FairnessMetrics()

    def register_voter(self, voter: Voter) -> None:
        """Register a voter in the system."""
        self.voters[voter.voter_id] = voter

    def register_policy(self, policy: Policy) -> None:
        """Register a policy in the system."""
        self.policies[policy.policy_id] = policy

    def register_region(self, region: Region) -> None:
        """Register a region in the system."""
        self.regions[region.region_id] = region

    def make_decision(
        self, policy_id: str, region_id: str, decision_type: str = "direct_vote"
    ) -> Decision:
        """Make a decision on a policy for a specific region.

        Args:
            policy_id: ID of the policy to decide on
            region_id: ID of the region to apply the decision to
            decision_type: Type of decision-making method

        Returns:
            Decision object with the outcome
        """
        policy = self.policies.get(policy_id)
        region = self.regions.get(region_id)

        if not policy:
            raise ValueError(f"Policy {policy_id} not found")
        if not region:
            raise ValueError(f"Region {region_id} not found")

        voters_in_region = [
            v
            for v in self.voters.values()
            if v.region_id == region_id or region_id in v.region_id
        ]

        votes_for = 0
        votes_against = 0

        for voter in voters_in_region:
            preference = voter.get_preference(policy_id)
            if preference > 0:
                votes_for += voter.voting_weight
            elif preference < 0:
                votes_against += voter.voting_weight

        total_weight = votes_for + votes_against
        if total_weight == 0:
            outcome = "abstain"
            confidence = 0.0
        else:
            support_percentage = votes_for / total_weight
            if support_percentage > 0.5:
                outcome = "approved"
            else:
                outcome = "rejected"
            confidence = abs(support_percentage - 0.5) * 2

        decision = Decision(
            decision_id=f"{policy_id}_{region_id}_{len(self.decisions)}",
            policy_id=policy_id,
            region_id=region_id,
            decision_type=decision_type,
            outcome=outcome,
            confidence=confidence,
            voters_participated=[v.voter_id for v in voters_in_region],
            votes_for=int(votes_for),
            votes_against=int(votes_against),
        )

        self.decisions.append(decision)
        return decision

    def check_fairness(self) -> bool:
        """Check if all recent decisions meet fairness threshold.

        Returns:
            True if all decisions are fair, False otherwise
        """
        recent_decisions = (
            self.decisions[-10:] if len(self.decisions) > 10 else self.decisions
        )

        for decision in recent_decisions:
            fairness_score = self.fairness_metrics.calculate_fairness(
                decision, self.voters, self.regions
            )
            if fairness_score < self.fairness_threshold:
                return False

        return True
