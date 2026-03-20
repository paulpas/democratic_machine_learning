"""Policy cell for organizing policy decisions."""

from typing import Dict, List, Optional
from src.models.policy import Policy, PolicyDomain
from src.models.voter import Voter
from src.models.region import Region


class PolicyCell:
    """Represents a cell in the policy decision matrix."""

    def __init__(self, policy: Policy, region: Region) -> None:
        """Initialize a policy cell.

        Args:
            policy: The policy being considered
            region: The region where the policy applies
        """
        self.policy = policy
        self.region = region
        self.supporters: List[str] = []
        self.opposers: List[str] = []
        self.abstentions: List[str] = []

    def add_supporter(self, voter_id: str) -> None:
        """Record a supporter of this policy in this region."""
        if voter_id not in self.supporters:
            self.supporters.append(voter_id)

    def add_opposer(self, voter_id: str) -> None:
        """Record an opposer of this policy in this region."""
        if voter_id not in self.opposers:
            self.opposers.append(voter_id)

    def add_abstention(self, voter_id: str) -> None:
        """Record an abstention from this policy in this region."""
        if voter_id not in self.abstentions:
            self.abstentions.append(voter_id)

    def get_support_ratio(self) -> float:
        """Calculate the ratio of support to total participation."""
        total = len(self.supporters) + len(self.opposers)
        if total == 0:
            return 0.0
        return len(self.supporters) / total

    def get_impact_score(self, voter_weights: Dict[str, float]) -> float:
        """Calculate weighted impact score.

        Args:
            voter_weights: Mapping of voter IDs to their weights

        Returns:
            Weighted impact score
        """
        support_weight = sum(voter_weights.get(v, 1.0) for v in self.supporters)
        opposition_weight = sum(voter_weights.get(v, 1.0) for v in self.opposers)

        return support_weight - opposition_weight
