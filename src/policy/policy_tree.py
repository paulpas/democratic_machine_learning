"""Policy tree for hierarchical policy definitions.

This module implements a tree structure that drills down from national policies
to localized laws and ordinances, identifying anti-patterns at each level.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import os

from src.history.anti_patterns import AntiPatternDatabase, AntiPatternCategory


class PolicyHierarchyLevel(Enum):
    """Hierarchy levels for policy definitions."""

    NATIONAL = "national"
    REGIONAL = "regional"
    STATE = "state"
    COUNTY = "county"
    MUNICIPAL = "municipal"
    LOCAL = "local"


@dataclass
class PolicyNode:
    """Represents a node in the policy tree."""

    policy_id: str
    name: str
    description: str
    level: PolicyHierarchyLevel
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    legislation_references: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)
    impact_regions: List[str] = field(default_factory=list)

    def add_child(self, child_id: str) -> None:
        """Add a child policy node."""
        if child_id not in self.children_ids:
            self.children_ids.append(child_id)

    def add_legislation(self, reference: str) -> None:
        """Add legislation reference."""
        if reference not in self.legislation_references:
            self.legislation_references.append(reference)

    def add_anti_pattern(self, pattern_id: str) -> None:
        """Add identified anti-pattern."""
        if pattern_id not in self.anti_patterns:
            self.anti_patterns.append(pattern_id)

    def get_ancestors(self, policy_tree: "PolicyTree") -> List[str]:
        """Get all ancestor policy IDs."""
        ancestors = []
        current_id = self.parent_id
        while current_id:
            ancestors.append(current_id)
            current_id = policy_tree.nodes.get(
                current_id, PolicyNode("", "", "", PolicyHierarchyLevel.NATIONAL)
            ).parent_id
        return ancestors

    def get_path_to_root(self, policy_tree: "PolicyTree") -> List[str]:
        """Get path from this node to root."""
        path = [self.policy_id]
        current_id = self.parent_id
        while current_id:
            path.append(current_id)
            current_id = policy_tree.nodes.get(
                current_id, PolicyNode("", "", "", PolicyHierarchyLevel.NATIONAL)
            ).parent_id
        return path


class PolicyTree:
    """Hierarchical policy tree structure."""

    def __init__(self, anti_pattern_db: Optional[AntiPatternDatabase] = None) -> None:
        """Initialize the policy tree.

        Args:
            anti_pattern_db: Optional database of anti-patterns
        """
        self.nodes: Dict[str, PolicyNode] = {}
        self.anti_pattern_db = anti_pattern_db or AntiPatternDatabase()

    def add_policy(
        self,
        policy_id: str,
        name: str,
        description: str,
        level: PolicyHierarchyLevel,
        parent_id: Optional[str] = None,
    ) -> PolicyNode:
        """Add a policy node to the tree.

        Args:
            policy_id: Unique policy identifier
            name: Policy name
            description: Policy description
            level: Hierarchy level
            parent_id: Optional parent policy ID

        Returns:
            Created PolicyNode
        """
        node = PolicyNode(
            policy_id=policy_id,
            name=name,
            description=description,
            level=level,
            parent_id=parent_id,
        )

        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].add_child(policy_id)

        self.nodes[policy_id] = node
        return node

    def scan_for_anti_patterns(self, legislation_data: Dict) -> Dict[str, List[str]]:
        """Scan legislation data for anti-patterns.

        Args:
            legislation_data: Dictionary of legislation to scan

        Returns:
            Dictionary mapping policy IDs to identified anti-patterns
        """
        identified = {}

        for policy_id, policy_data in legislation_data.items():
            if policy_id not in self.nodes:
                continue

            # Check against anti-pattern database
            patterns = self.anti_pattern_db.detect_patterns(policy_data)
            self.nodes[policy_id].anti_patterns = [p.pattern_id for p in patterns]

            if patterns:
                identified[policy_id] = [p.pattern_id for p in patterns]

        return identified

    def get_affected_regions(self, policy_id: str) -> List[str]:
        """Get all regions affected by a policy and its children."""
        if policy_id not in self.nodes:
            return []

        affected = set()
        node = self.nodes[policy_id]
        affected.update(node.impact_regions)

        for child_id in node.children_ids:
            affected.update(self.get_affected_regions(child_id))

        return list(affected)

    def get_policy_depth(self, policy_id: str) -> int:
        """Get the depth of a policy in the tree."""
        if policy_id not in self.nodes:
            return 0

        depth = 0
        current_id = policy_id
        while current_id:
            node = self.nodes.get(current_id)
            if not node or not node.parent_id:
                break
            depth += 1
            current_id = node.parent_id

        return depth

    def get_policy_path(self, policy_id: str) -> List[PolicyNode]:
        """Get the path from root to a policy node."""
        if policy_id not in self.nodes:
            return []

        path = []
        current_id = policy_id
        while current_id:
            node = self.nodes.get(current_id)
            if not node:
                break
            path.append(node)
            current_id = node.parent_id

        return list(reversed(path))

    def analyze_tree_for_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Analyze entire tree for anti-patterns.

        Returns:
            Dictionary with tree-wide pattern analysis
        """
        analysis = {
            "total_policies": len(self.nodes),
            "patterns_by_category": {},
            "policies_with_patterns": [],
            "deep_tree_patterns": [],
        }

        for node in self.nodes.values():
            if node.anti_patterns:
                analysis["policies_with_patterns"].append(node.policy_id)

                for pattern_id in node.anti_patterns:
                    category = self.anti_pattern_db.get_pattern_by_id(pattern_id)
                    if category:
                        cat_key = category.category.value
                        if cat_key not in analysis["patterns_by_category"]:
                            analysis["patterns_by_category"][cat_key] = []
                        analysis["patterns_by_category"][cat_key].append(pattern_id)

            # Check for deep tree patterns (too many levels)
            depth = self.get_policy_depth(node.policy_id)
            if depth > 5:
                analysis["deep_tree_patterns"].append(
                    {
                        "policy_id": node.policy_id,
                        "depth": depth,
                        "path": [
                            n.policy_id for n in self.get_policy_path(node.policy_id)
                        ],
                    }
                )

        return analysis


class LegislationScanner:
    """Scans legislation for policy tree construction and anti-pattern detection."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize the legislation scanner.

        Args:
            api_key: Optional API key for external legislation sources
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.policies_by_level: Dict[PolicyHierarchyLevel, List[Dict]] = {}

    def scan_national_legislation(self) -> List[Dict]:
        """Scan national legislation.

        Returns:
            List of national policy definitions
        """
        # In real implementation, would call legislation API
        # For now, return placeholder data
        return [
            {
                "id": "US-FED-001",
                "name": "Federal Budget Act",
                "description": "Framework for federal budget process",
                "level": PolicyHierarchyLevel.NATIONAL,
                "references": ["U.S. Code Title 31"],
            }
        ]

    def scan_state_legislation(self, state_id: str) -> List[Dict]:
        """Scan state legislation.

        Args:
            state_id: State identifier

        Returns:
            List of state policy definitions
        """
        return [
            {
                "id": f"US-{state_id}-001",
                "name": f"{state_id} Education Funding Law",
                "description": "State education funding framework",
                "level": PolicyHierarchyLevel.STATE,
                "references": [f"{state_id} Code § 123-456"],
            }
        ]

    def scan_local_legislation(self, region_id: str) -> List[Dict]:
        """Scan local legislation (county/municipal).

        Args:
            region_id: Region identifier

        Returns:
            List of local policy definitions
        """
        return [
            {
                "id": f"US-{region_id}-001",
                "name": f"{region_id} Zoning Ordinance",
                "description": "Local zoning regulations",
                "level": PolicyHierarchyLevel.LOCAL,
                "references": [f"{region_id} Municipal Code § 789-012"],
            }
        ]

    def build_policy_tree(self) -> PolicyTree:
        """Build complete policy tree from legislation.

        Returns:
            Complete policy tree with all levels
        """
        tree = PolicyTree()

        # Scan all levels
        national_policies = self.scan_national_legislation()
        for policy in national_policies:
            tree.add_policy(
                policy_id=policy["id"],
                name=policy["name"],
                description=policy["description"],
                level=policy["level"],
            )

        # Scan state and local policies (would scan all states/counties)
        states = ["CA", "NY", "TX", "FL"]
        for state in states:
            state_policies = self.scan_state_legislation(state)
            for policy in state_policies:
                tree.add_policy(
                    policy_id=policy["id"],
                    name=policy["name"],
                    description=policy["description"],
                    level=policy["level"],
                    parent_id=f"US-FED-{policy['id'].split('-')[-1]}",
                )

        return tree
