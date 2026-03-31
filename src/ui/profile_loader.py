"""Profile loader module for the Democratic Machine Learning System.

This module provides functions to load profile configurations from YAML files.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import yaml

from src.config import ProfileConfig

logger = logging.getLogger(__name__)

_DEFAULT_PROFILES_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "profiles"


def load_profile(profile_name: str, profiles_dir: Optional[Path] = None) -> ProfileConfig:
    """Load a profile by name from the profiles directory.

    Args:
        profile_name: Name of the profile to load
        profiles_dir: Optional custom directory to search for profiles

    Returns:
        ProfileConfig instance

    Raises:
        FileNotFoundError: If profile doesn't exist
        ValueError: If profile is invalid
    """
    if not profile_name or not isinstance(profile_name, str):
        raise ValueError("Profile name must be a non-empty string")

    profile_path = get_profile_path(profile_name, profiles_dir)

    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_name}")

    with profile_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Profile file {profile_path} is not a valid YAML mapping")

    profile = ProfileConfig.from_dict(data)

    if not profile.validate():
        raise ValueError(f"Profile {profile_name} failed validation")

    logger.info(f"Loaded profile: {profile_name}")
    return profile


def get_profile_path(profile_name: str, profiles_dir: Optional[Path] = None) -> Path:
    """Get the file path for a profile.

    Args:
        profile_name: Name of the profile
        profiles_dir: Optional custom directory

    Returns:
        Path to the profile YAML file
    """
    if profiles_dir is None:
        profiles_dir = _DEFAULT_PROFILES_DIR

    if not profile_name.endswith(".yaml"):
        profile_name = f"{profile_name}.yaml"

    return profiles_dir / profile_name


def profile_exists(profile_name: str, profiles_dir: Optional[Path] = None) -> bool:
    """Check if a profile exists.

    Args:
        profile_name: Name of the profile
        profiles_dir: Optional custom directory

    Returns:
        True if profile exists, False otherwise
    """
    profile_path = get_profile_path(profile_name, profiles_dir)
    return profile_path.exists()


def list_available_profiles(profiles_dir: Optional[Path] = None) -> List[str]:
    """List all available profiles.

    Args:
        profiles_dir: Optional custom directory

    Returns:
        List of profile names (without .yaml extension)
    """
    if profiles_dir is None:
        profiles_dir = _DEFAULT_PROFILES_DIR

    if not profiles_dir.exists():
        return []

    profiles = []
    for path in profiles_dir.glob("*.yaml"):
        if path.is_file():
            profiles.append(path.stem)

    return sorted(profiles)


def get_default_profile() -> ProfileConfig:
    """Get the default profile.

    Returns:
        Default ProfileConfig instance

    Raises:
        FileNotFoundError: If default profile doesn't exist
    """
    return load_profile("default")


def get_default_domains() -> List[str]:
    """Get the default list of policy domains.

    Returns:
        List of default domain names
    """
    return [
        "economy",
        "healthcare",
        "education",
        "immigration",
        "climate",
        "infrastructure",
    ]


def validate_profile(profile: ProfileConfig) -> bool:
    """Validate a profile configuration.

    Args:
        profile: ProfileConfig to validate

    Returns:
        True if valid, False otherwise
    """
    return profile.validate()
