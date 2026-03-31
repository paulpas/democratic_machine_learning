"""Profile manager module for the Democratic Machine Learning System.

Provides functions to create, edit, delete, and manage profile configurations.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Ensure repo root is on sys.path when this module is imported directly.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ui.profile_loader import (
    ProfileConfig,
    get_profile_path,
)

logger = logging.getLogger(__name__)

# __file__ = src/ui/profile_manager.py  →  parents[2] = repo root
_DEFAULT_PROFILES_DIR = Path(__file__).resolve().parents[2] / "config" / "profiles"


def create_profile(
    name: str,
    domains: List[str],
    config_overrides: Dict[str, Any] | None = None,
) -> ProfileConfig:
    """Create a new profile and save it to file.

    Args:
        name: Profile name (must be unique, alphanumeric + hyphens)
        domains: List of policy domains to include
        config_overrides: Optional configuration overrides for depth, etc.

    Returns:
        Created ProfileConfig instance

    Raises:
        ValueError: If profile name is invalid or already exists
    """
    if not name or not isinstance(name, str):
        raise ValueError("Profile name must be a non-empty string")

    name = name.strip().lower().replace(" ", "-")

    if not all(c.isalnum() or c in "-_" for c in name):
        raise ValueError(
            "Profile name must contain only letters, numbers, hyphens, and underscores"
        )

    if get_profile_path(name).exists():
        raise ValueError(f"Profile '{name}' already exists")

    # Allow any non-empty string as a domain/topic — custom free-text topics
    # such as "opioid crisis" or "AI governance" are fully supported.
    invalid = [d for d in domains if not isinstance(d, str) or not d.strip()]
    if invalid:
        raise ValueError(f"Invalid domains: {invalid!r}. Each domain must be a non-empty string.")

    base_config = {
        "name": name,
        "description": f"Custom profile for {', '.join(domains)}",
        "domains": domains,
        "depth": 2,
        "subtopics_per_level": 3,
        "geo_fan_out": True,
        "expert_allocation": {},
        "llm_budgets": {},
        "social_collection": {},
        "metadata": {
            "author": "Profile Manager",
            "created": __import__("datetime").date.today().isoformat(),
            "type": "custom",
        },
    }

    if config_overrides:
        base_config.update(config_overrides)

    profile = ProfileConfig.from_dict(base_config)

    if not profile.validate():
        raise ValueError("Created profile failed validation")

    save_profile(profile)

    logger.info(f"Created profile: {name}")
    return profile


def update_profile(name: str, updates: Dict[str, Any]) -> ProfileConfig:
    """Update an existing profile with new values.

    Args:
        name: Name of the profile to update
        updates: Dictionary of fields to update

    Returns:
        Updated ProfileConfig instance

    Raises:
        FileNotFoundError: If profile doesn't exist
        ValueError: If updates are invalid
    """
    profile_path = get_profile_path(name)

    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {name}")

    with open(profile_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    for key, value in updates.items():
        if key in data:
            data[key] = value
        else:
            logger.warning(f"Unknown profile field '{key}' - ignored")

    profile = ProfileConfig.from_dict(data)

    if not profile.validate():
        raise ValueError("Updated profile failed validation")

    save_profile(profile)

    logger.info(f"Updated profile: {name}")
    return profile


def delete_profile(name: str) -> bool:
    """Delete a profile by name.

    Args:
        name: Name of the profile to delete

    Returns:
        True if deleted, False if not found

    Raises:
        ValueError: If trying to delete a system profile
    """
    if name in ("default",):
        raise ValueError(f"Cannot delete system profile: {name}")

    profile_path = get_profile_path(name)

    if not profile_path.exists():
        logger.warning(f"Profile not found: {name}")
        return False

    profile_path.unlink()

    logger.info(f"Deleted profile: {name}")
    return True


def save_profile(profile: ProfileConfig) -> None:
    """Save a profile to file.

    Args:
        profile: ProfileConfig to save

    Raises:
        OSError: If file cannot be written
    """
    _DEFAULT_PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    profile_path = get_profile_path(profile.name)

    with open(profile_path, "w", encoding="utf-8") as f:
        yaml.dump(
            profile.to_dict(),
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    logger.info(f"Saved profile to {profile_path}")


def export_profile(profile_name: str, export_path: Path) -> Path:
    """Export a profile to a file.

    Args:
        profile_name: Name of the profile to export
        export_path: Destination path for exported file

    Returns:
        Path to the exported file

    Raises:
        FileNotFoundError: If profile doesn't exist
    """
    profile_path = get_profile_path(profile_name)

    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_name}")

    export_path.parent.mkdir(parents=True, exist_ok=True)

    with open(profile_path, "r", encoding="utf-8") as src:
        content = src.read()

    with open(export_path, "w", encoding="utf-8") as dst:
        dst.write(content)

    logger.info(f"Exported profile '{profile_name}' to {export_path}")
    return export_path


def import_profile(import_path: Path) -> ProfileConfig:
    """Import a profile from a file.

    Args:
        import_path: Path to the profile file to import

    Returns:
        Imported ProfileConfig instance

    Raises:
        FileNotFoundError: If import file doesn't exist
        ValueError: If profile is invalid or name conflicts
    """
    if not import_path.exists():
        raise FileNotFoundError(f"Import file not found: {import_path}")

    with open(import_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Import file is not a valid YAML mapping")

    if "name" not in data:
        raise ValueError("Import file missing 'name' field")

    name = data["name"]

    if get_profile_path(name).exists():
        raise ValueError(f"Profile '{name}' already exists (import would overwrite)")

    profile = ProfileConfig.from_dict(data)

    if not profile.validate():
        raise ValueError("Imported profile failed validation")

    save_profile(profile)

    logger.info(f"Imported profile: {name}")
    return profile
