"""Feature engineering utilities."""

from typing import Dict, List

import numpy as np

from src.models.policy import Policy
from src.models.region import Region
from src.models.voter import Voter


class FeatureEngineer:
    """Engineers features for ML models."""

    def __init__(self) -> None:
        """Initialize the feature engineer."""
        self.feature_names: List[str] = []

    def create_voter_features(
        self, voter: Voter, policy: Policy, region: Region
    ) -> Dict[str, float]:
        """Create features for a voter-policy-region combination.

        Args:
            voter: The voter
            policy: The policy
            region: The region

        Returns:
            Dictionary of feature names to values
        """
        features = {
            "voter_weight": voter.voting_weight,
            "preference": voter.get_preference(policy.policy_id),
            "is_representative": 1.0 if voter.voter_type.value == "representative" else 0.0,
            "is_expert": 1.0 if voter.voter_type.value == "expert" else 0.0,
            "expertise_level": voter.expertise.get(policy.policy_id, 0.0),
            "proximity_to_region": 1.0 if voter.region_id == region.region_id else 0.0,
            "policy_cost": policy.implementation_cost,
            "policy_benefit": policy.expected_benefit,
            "policy_net_benefit": policy.get_net_benefit(),
            "region_population": region.population,
        }

        self.feature_names = list(features.keys())
        return features

    def create_region_features(
        self, region: Region, voters: List[Voter], policies: List[Policy]
    ) -> Dict[str, float]:
        """Create aggregate features for a region.

        Args:
            region: The region
            voters: List of voters in the region
            policies: List of policies

        Returns:
            Dictionary of feature names to values
        """
        if not voters:
            return {}

        preferences = [v.get_preference(p.policy_id) for v in voters for p in policies]

        features = {
            "region_population": region.population,
            "region_voter_count": len(voters),
            "avg_preference": np.mean(preferences) if preferences else 0.0,
            "preference_std": np.std(preferences) if preferences else 0.0,
            "max_preference": max(preferences) if preferences else 0.0,
            "min_preference": min(preferences) if preferences else 0.0,
            "consensus_score": 1.0 - (np.std(preferences) / 2.0) if preferences else 0.0,
        }

        return features
