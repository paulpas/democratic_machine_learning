"""Data models for decisions in the democratic decision-making system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Decision:
    """Represents a decision made by the system."""

    decision_id: str
    policy_id: str
    region_id: str
    decision_type: str
    outcome: str
    confidence: float
    voters_participated: List[str] = field(default_factory=list)
    votes_for: int = 0
    votes_against: int = 0
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate decision data after initialization."""
        if not self.decision_id:
            raise ValueError("Decision must have an ID")
        if not self.policy_id:
            raise ValueError("Decision must have a policy ID")
        if not self.region_id:
            raise ValueError("Decision must have a region ID")
        if not self.decision_type:
            raise ValueError("Decision must have a type")
        if not self.outcome:
            raise ValueError("Decision must have an outcome")

    def add_voter(self, voter_id: str) -> None:
        """Record that a voter participated in this decision."""
        if voter_id not in self.voters_participated:
            self.voters_participated.append(voter_id)

    def get_margin(self) -> float:
        """Calculate the vote margin."""
        total = self.votes_for + self.votes_against
        if total == 0:
            return 0.0
        return (self.votes_for - self.votes_against) / total

    def get_support_percentage(self) -> float:
        """Calculate percentage of votes in support."""
        total = self.votes_for + self.votes_against
        if total == 0:
            return 0.0
        return (self.votes_for / total) * 100
