"""Data loading and preprocessing utilities."""

from typing import Dict, List, Optional
import json
import csv
from pathlib import Path
from src.models.voter import Voter, VoterType
from src.models.policy import Policy, PolicyDomain
from src.models.region import Region


class DataLoader:
    """Loads data for the democratic decision-making system."""

    def __init__(self, data_dir: Optional[str] = None) -> None:
        """Initialize the data loader.

        Args:
            data_dir: Directory containing data files
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.voters: List[Voter] = []
        self.policies: List[Policy] = []
        self.regions: List[Region] = []

    def load_voters(self, filepath: str, format: str = "json") -> List[Voter]:
        """Load voters from file.

        Args:
            filepath: Path to the voters file
            format: File format (json or csv)

        Returns:
            List of Voter objects
        """
        path = Path(filepath)

        if format == "json":
            return self._load_voters_json(path)
        elif format == "csv":
            return self._load_voters_csv(path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _load_voters_json(self, filepath: Path) -> List[Voter]:
        """Load voters from JSON file."""
        if not filepath.exists():
            return []

        with open(filepath, "r") as f:
            data = json.load(f)

        voters = []
        for voter_data in data.get("voters", []):
            voter = Voter(
                voter_id=voter_data["id"],
                region_id=voter_data.get("region", "default"),
                preferences=voter_data.get("preferences", {}),
                expertise=voter_data.get("expertise", {}),
                voting_weight=voter_data.get("weight", 1.0),
                voter_type=VoterType(voter_data.get("type", "participant")),
            )
            voters.append(voter)

        self.voters.extend(voters)
        return voters

    def _load_voters_csv(self, filepath: Path) -> List[Voter]:
        """Load voters from CSV file."""
        if not filepath.exists():
            return []

        voters = []
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                voter = Voter(
                    voter_id=row["id"],
                    region_id=row.get("region", "default"),
                    preferences={},
                    expertise={},
                    voting_weight=float(row.get("weight", 1.0)),
                    voter_type=VoterType(row.get("type", "participant")),
                )
                voters.append(voter)

        self.voters.extend(voters)
        return voters

    def load_policies(self, filepath: str, format: str = "json") -> List[Policy]:
        """Load policies from file."""
        path = Path(filepath)

        if format == "json":
            return self._load_policies_json(path)
        elif format == "csv":
            return self._load_policies_csv(path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _load_policies_json(self, filepath: Path) -> List[Policy]:
        """Load policies from JSON file."""
        if not filepath.exists():
            return []

        with open(filepath, "r") as f:
            data = json.load(f)

        policies = []
        for policy_data in data.get("policies", []):
            policy = Policy(
                policy_id=policy_data["id"],
                name=policy_data["name"],
                description=policy_data.get("description", ""),
                domain=PolicyDomain(policy_data.get("domain", "economic")),
            )
            policies.append(policy)

        self.policies.extend(policies)
        return policies

    def load_regions(self, filepath: str, format: str = "json") -> List[Region]:
        """Load regions from file."""
        path = Path(filepath)

        if format == "json":
            return self._load_regions_json(path)
        elif format == "csv":
            return self._load_regions_csv(path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _load_regions_json(self, filepath: Path) -> List[Region]:
        """Load regions from JSON file."""
        if not filepath.exists():
            return []

        with open(filepath, "r") as f:
            data = json.load(f)

        regions = []
        for region_data in data.get("regions", []):
            region = Region(
                region_id=region_data["id"],
                name=region_data["name"],
                region_type=region_data.get("type", "county"),
                population=region_data.get("population", 0),
            )
            regions.append(region)

        self.regions.extend(regions)
        return regions

    def _load_policies_csv(self, filepath: Path) -> List[Policy]:
        """Load policies from CSV file."""
        if not filepath.exists():
            return []

        policies = []
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                policy = Policy(
                    policy_id=row["id"],
                    name=row.get("name", ""),
                    description=row.get("description", ""),
                    domain=PolicyDomain(row.get("domain", "economic")),
                )
                policies.append(policy)

        self.policies.extend(policies)
        return policies

    def _load_regions_csv(self, filepath: Path) -> List[Region]:
        """Load regions from CSV file."""
        if not filepath.exists():
            return []

        regions = []
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                region = Region(
                    region_id=row["id"],
                    name=row.get("name", ""),
                    region_type=row.get("type", "county"),
                    population=int(row.get("population", 0)),
                )
                regions.append(region)

        self.regions.extend(regions)
        return regions
