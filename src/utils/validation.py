"""Validation utilities for the democratic decision-making system."""

from typing import List

from src.models.policy import Policy
from src.models.region import Region
from src.models.voter import Voter


class Validator:
    """Validates data and decisions."""

    def __init__(self) -> None:
        """Initialize the validator."""
        self.errors: List[str] = []

    def validate_voter(self, voter: Voter) -> bool:
        """Validate a voter.

        Args:
            voter: The voter to validate

        Returns:
            True if valid
        """
        self.errors = []

        if not voter.voter_id:
            self.errors.append("Voter must have an ID")
        if not voter.region_id:
            self.errors.append("Voter must have a region ID")
        if voter.voting_weight < 0:
            self.errors.append("Voting weight must be non-negative")

        return len(self.errors) == 0

    def validate_policy(self, policy: Policy) -> bool:
        """Validate a policy.

        Args:
            policy: The policy to validate

        Returns:
            True if valid
        """
        self.errors = []

        if not policy.policy_id:
            self.errors.append("Policy must have an ID")
        if not policy.name:
            self.errors.append("Policy must have a name")
        if policy.implementation_cost < 0:
            self.errors.append("Implementation cost must be non-negative")

        return len(self.errors) == 0

    def validate_region(self, region: Region) -> bool:
        """Validate a region.

        Args:
            region: The region to validate

        Returns:
            True if valid
        """
        self.errors = []

        if not region.region_id:
            self.errors.append("Region must have an ID")
        if not region.name:
            self.errors.append("Region must have a name")
        if not region.region_type:
            self.errors.append("Region must have a type")
        if region.population < 0:
            self.errors.append("Population must be non-negative")

        return len(self.errors) == 0

    def validate_decision(self, decision_id: str, policy_id: str, region_id: str) -> bool:
        """Validate decision parameters.

        Args:
            decision_id: Decision ID
            policy_id: Policy ID
            region_id: Region ID

        Returns:
            True if valid
        """
        self.errors = []

        if not decision_id:
            self.errors.append("Decision must have an ID")
        if not policy_id:
            self.errors.append("Decision must have a policy ID")
        if not region_id:
            self.errors.append("Decision must have a region ID")

        return len(self.errors) == 0

    def validate_weight(self, weight: float) -> bool:
        """Validate a weight value.

        Args:
            weight: The weight to validate

        Returns:
            True if valid
        """
        self.errors = []

        if weight < 0:
            self.errors.append("Weight must be non-negative")
        if weight > 10:
            self.errors.append("Weight must be <= 10")

        return len(self.errors) == 0

    def get_errors(self) -> List[str]:
        """Get validation errors.

        Returns:
            List of error messages
        """
        return self.errors
