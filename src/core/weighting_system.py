"""Weighting system for adaptive voter representation."""

from typing import Dict, List, Optional
from src.models.voter import Voter
from src.models.region import Region
from src.models.policy import Policy, PolicyDomain


class WeightingSystem:
    """Manages adaptive voter weights based on various factors."""

    def __init__(
        self,
        base_weight: float = 1.0,
        expertise_boost: float = 0.5,
        proximity_boost: float = 0.3,
        historical_weight: float = 0.2,
    ) -> None:
        """Initialize the weighting system.

        Args:
            base_weight: Base weight for all voters
            expertise_boost: Boost for voters with expertise in policy area
            proximity_boost: Boost for voters directly affected by policy
            historical_weight: Weight based on historical participation
        """
        self.base_weight = base_weight
        self.expertise_boost = expertise_boost
        self.proximity_boost = proximity_boost
        self.historical_weight = historical_weight

        self.voter_weights: Dict[str, float] = {}
        self.voter_participation: Dict[str, int] = {}

    def calculate_weight(self, voter: Voter, policy: Policy, region: Region) -> float:
        """Calculate weighted voting power for a voter on a specific policy.

        Args:
            voter: The voter
            policy: The policy being voted on
            region: The region where the vote occurs

        Returns:
            Calculated voting weight
        """
        weight = self.base_weight

        if voter.voter_type.value == "representative":
            weight *= 2.0
        elif voter.voter_type.value == "expert":
            weight *= 1.5

        if policy.policy_id in voter.expertise:
            weight += self.expertise_boost * voter.expertise[policy.policy_id]

        if voter.region_id == region.region_id:
            weight += self.proximity_boost

        participation = self.voter_participation.get(voter.voter_id, 0)
        weight += self.historical_weight * min(participation / 10, 1.0)

        return weight

    def update_participation(self, voter_id: str) -> None:
        """Update participation count for a voter."""
        self.voter_participation[voter_id] = (
            self.voter_participation.get(voter_id, 0) + 1
        )

    def normalize_weights(self, voters: List[Voter]) -> Dict[str, float]:
        """Normalize weights so average is 1.0.

        Args:
            voters: List of voters to normalize

        Returns:
            Dictionary of voter_id to normalized weight
        """
        weights = {}
        for voter in voters:
            weights[voter.voter_id] = self.calculate_weight(
                voter,
                Policy("dummy", "Dummy", "", PolicyDomain.ECONOMIC),
                Region("dummy", "Dummy", "test"),
            )

        if not weights:
            return weights

        avg_weight = sum(weights.values()) / len(weights)
        return {k: v / avg_weight for k, v in weights.items()}
