"""Data models for policies in the democratic decision-making system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class PolicyDomain(Enum):
    """Domains of policy categories."""

    ECONOMIC = "economic"
    SOCIAL = "social"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    ENVIRONMENT = "environment"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    TECHNOLOGY = "technology"


@dataclass
class Policy:
    """Represents a policy in the democratic decision-making system."""

    policy_id: str
    name: str
    description: str
    domain: PolicyDomain
    impact_score: float = 0.0
    support_score: float = 0.0
    opposition_score: float = 0.0
    implementation_cost: float = 0.0
    expected_benefit: float = 0.0
    affected_regions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate policy data after initialization."""
        if not self.policy_id:
            raise ValueError("Policy must have an ID")
        if not self.name:
            raise ValueError("Policy must have a name")

    def add_affected_region(self, region_id: str) -> None:
        """Add a region affected by this policy."""
        if region_id not in self.affected_regions:
            self.affected_regions.append(region_id)

    def add_dependency(self, dependency_id: str) -> None:
        """Add a policy dependency."""
        if dependency_id not in self.dependencies:
            self.dependencies.append(dependency_id)

    def get_net_benefit(self) -> float:
        """Calculate net benefit (benefit - cost)."""
        return self.expected_benefit - self.implementation_cost

    def get_balance_score(self) -> float:
        """Calculate a balance score considering support vs opposition."""
        total = self.support_score + self.opposition_score
        if total == 0:
            return 0.0
        return (self.support_score - self.opposition_score) / total
