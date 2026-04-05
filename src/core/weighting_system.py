"""Weighting system for adaptive voter representation."""

from typing import Dict, List, Optional

from src.config import get_config
from src.models.policy import Policy, PolicyDomain
from src.models.region import Region
from src.models.voter import Voter


class WeightingSystem:
    """Manages adaptive voter weights based on various factors."""

    def __init__(
        self,
        base_weight: Optional[float] = None,
        expertise_boost: Optional[float] = None,
        proximity_boost: Optional[float] = None,
        historical_weight: Optional[float] = None,
    ) -> None:
        """Initialize the weighting system.

        Args:
            base_weight: Base weight for all voters.
            expertise_boost: Boost for voters with expertise in policy area.
            proximity_boost: Boost for voters directly affected by policy.
            historical_weight: Weight based on historical participation.
            All parameters default to ``config.yaml`` ``weighting.*`` values.
        """
        _cfg = get_config().weighting
        self.base_weight = base_weight if base_weight is not None else _cfg.base_weight
        self.expertise_boost = (
            expertise_boost if expertise_boost is not None else _cfg.expertise_boost
        )
        self.proximity_boost = (
            proximity_boost if proximity_boost is not None else _cfg.proximity_boost
        )
        self.historical_weight = (
            historical_weight if historical_weight is not None else _cfg.historical_weight
        )

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
        _cfg = get_config().weighting
        weight = self.base_weight

        if voter.voter_type.value == "representative":
            weight *= _cfg.mult_representative
        elif voter.voter_type.value == "expert":
            weight *= _cfg.mult_expert

        if policy.policy_id in voter.expertise:
            weight += self.expertise_boost * voter.expertise[policy.policy_id]

        if voter.region_id == region.region_id:
            weight += self.proximity_boost

        participation = self.voter_participation.get(voter.voter_id, 0)
        weight += self.historical_weight * min(participation / _cfg.participation_norm, 1.0)

        return weight

    def update_participation(self, voter_id: str) -> None:
        """Update participation count for a voter."""
        self.voter_participation[voter_id] = self.voter_participation.get(voter_id, 0) + 1

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
