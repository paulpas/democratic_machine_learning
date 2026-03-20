"""Data models for regions in the democratic decision-making system."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Region:
    """Represents a geographic region in the system."""

    region_id: str
    name: str
    region_type: str
    population: int = 0
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    policies: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate region data after initialization."""
        if not self.region_id:
            raise ValueError("Region must have an ID")
        if not self.name:
            raise ValueError("Region must have a name")
        if not self.region_type:
            raise ValueError("Region must have a type")

    def add_child(self, child_id: str) -> None:
        """Add a child region."""
        if child_id not in self.children_ids:
            self.children_ids.append(child_id)

    def add_policy(self, policy_id: str) -> None:
        """Add a policy to this region."""
        if policy_id not in self.policies:
            self.policies.append(policy_id)

    def add_metric(self, metric_name: str, value: float) -> None:
        """Add or update a metric."""
        self.metrics[metric_name] = value

    def get_metric(self, metric_name: str) -> float:
        """Get a metric value."""
        return self.metrics.get(metric_name, 0.0)

    def is_leaf(self) -> bool:
        """Check if this region has no children."""
        return len(self.children_ids) == 0
