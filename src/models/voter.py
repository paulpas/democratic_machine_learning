"""Data models for voters in the democratic decision-making system."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class VoterType(Enum):
    """Types of voters in the system."""

    PARTICIPANT = "participant"
    REPRESENTATIVE = "representative"
    EXPERT = "expert"
    ALGORITHM = "algorithm"


@dataclass
class Voter:
    """Represents a voter in the democratic decision-making system."""

    voter_id: str
    region_id: str
    preferences: Dict[str, float] = field(default_factory=dict)
    expertise: Dict[str, float] = field(default_factory=dict)
    voting_weight: float = 1.0
    voter_type: VoterType = VoterType.PARTICIPANT
    delegation_to: Optional[str] = None

    def add_preference(self, policy_id: str, score: float) -> None:
        """Add or update preference for a policy."""
        self.preferences[policy_id] = max(-1.0, min(1.0, score))

    def get_preference(self, policy_id: str) -> float:
        """Get preference for a policy."""
        return self.preferences.get(policy_id, 0.0)

    def get_weighted_preference(self, policy_id: str) -> float:
        """Get preference multiplied by voting weight."""
        return self.get_preference(policy_id) * self.voting_weight
