"""Unit tests for the profile-based topic selection system."""

from pathlib import Path
from typing import Dict
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.ui.profile_loader import (
    ProfileConfig,
    get_default_domains,
    get_profile_path,
    list_available_profiles,
    load_profile,
    profile_exists,
    validate_profile,
)
from src.ui.profile_manager import (
    create_profile,
    delete_profile,
    export_profile,
    import_profile,
    save_profile,
    update_profile,
)

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def temp_profiles_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Temp profiles directory for testing."""
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()

    # Override the module-level constant
    with patch("src.ui.profile_loader._DEFAULT_PROFILES_DIR", profiles_dir):
        with patch("src.ui.profile_manager._DEFAULT_PROFILES_DIR", profiles_dir):
            yield profiles_dir


@pytest.fixture
def default_profile_data() -> Dict:
    """Default profile YAML content."""
    return {
        "name": "default",
        "description": "Full production analysis across all 6 policy domains",
        "domains": [
            "economy",
            "healthcare",
            "education",
            "immigration",
            "climate",
            "infrastructure",
        ],
        "depth": 4,
        "subtopics_per_level": 5,
        "geo_fan_out": True,
        "expert_allocation": {
            "economy": 12,
            "healthcare": 10,
            "education": 8,
            "immigration": 7,
            "climate": 9,
            "infrastructure": 11,
        },
        "llm_budgets": {
            "max_tokens_default": 16384,
            "max_tokens_subtopic": 16384,
        },
        "social_collection": {
            "max_opinions": 15,
            "max_narratives": 12,
        },
        "metadata": {
            "author": "DML System",
            "created": "2026-03-30",
            "type": "production",
        },
    }


@pytest.fixture
def mock_profile_yaml(default_profile_data: Dict) -> str:
    """Mock YAML content for a profile."""
    import yaml

    return yaml.dump(default_profile_data, default_flow_style=False)


# ─────────────────────────────────────────────────────────────────────────────
# ProfileConfig Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestProfileConfig:
    """Tests for ProfileConfig dataclass."""

    def test_from_dict_minimum_fields(self):
        """Create ProfileConfig with minimum required fields."""
        data = {
            "name": "test",
            "description": "Test profile",
            "domains": ["economy"],
        }

        profile = ProfileConfig.from_dict(data)

        assert profile.name == "test"
        assert profile.description == "Test profile"
        assert profile.domains == ["economy"]
        assert profile.depth == 2  # default
        assert profile.subtopics_per_level == 3  # default
        assert profile.geo_fan_out is True  # default

    def test_from_dict_all_fields(self):
        """Create ProfileConfig with all fields."""
        data = {
            "name": "custom",
            "description": "Custom profile",
            "domains": ["economy", "healthcare"],
            "depth": 3,
            "subtopics_per_level": 4,
            "geo_fan_out": False,
            "expert_allocation": {"economy": 10},
            "llm_budgets": {"max_tokens": 8192},
            "social_collection": {"max_opinions": 20},
            "metadata": {"author": "test"},
        }

        profile = ProfileConfig.from_dict(data)

        assert profile.name == "custom"
        assert profile.depth == 3
        assert profile.geo_fan_out is False
        assert profile.expert_allocation == {"economy": 10}

    def test_from_dict_missing_required_field(self):
        """Raise ValueError when required field is missing."""
        data = {
            "name": "test",
            "description": "Test",
            # Missing domains
        }

        with pytest.raises(ValueError, match="Missing required fields"):
            ProfileConfig.from_dict(data)

    def test_to_dict(self, default_profile_data: Dict):
        """Convert ProfileConfig to dict."""
        profile = ProfileConfig.from_dict(default_profile_data)
        result = profile.to_dict()

        assert result["name"] == "default"
        assert result["domains"] == default_profile_data["domains"]
        assert result["depth"] == 4

    def test_validate_valid_profile(self, default_profile_data: Dict):
        """Validate a correct profile."""
        profile = ProfileConfig.from_dict(default_profile_data)

        assert profile.validate() is True

    def test_validate_invalid_domain(self):
        """Validate fails when a domain entry is an empty string (not a valid topic)."""
        # Any non-empty string is a valid domain/topic — custom free-text topics
        # such as "opioid crisis" are fully supported.  Only structurally invalid
        # entries (empty string, whitespace-only) should fail validation.
        data = {
            "name": "test",
            "description": "Test",
            "domains": [""],  # empty string is not a valid topic
        }
        profile = ProfileConfig.from_dict(data)

        assert profile.validate() is False

    def test_validate_zero_depth(self):
        """Validate fails with depth < 1."""
        data = {
            "name": "test",
            "description": "Test",
            "domains": ["economy"],
            "depth": 0,
        }
        profile = ProfileConfig.from_dict(data)

        assert profile.validate() is False

    def test_validate_empty_domains(self):
        """Validate fails with empty domains list."""
        data = {
            "name": "test",
            "description": "Test",
            "domains": [],
        }
        profile = ProfileConfig.from_dict(data)

        assert profile.validate() is False

    def test_default_domains_function(self):
        """Get default list of domains."""
        domains = get_default_domains()

        assert len(domains) == 6
        assert "economy" in domains
        assert "healthcare" in domains


# ─────────────────────────────────────────────────────────────────────────────
# Profile Loader Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestProfileLoader:
    """Tests for profile_loader module."""

    def test_get_profile_path(self):
        """Get profile file path."""
        path = get_profile_path("test")

        assert path.name == "test.yaml"
        assert "config" in str(path)
        assert "profiles" in str(path)

    def test_list_available_profiles_empty(self, temp_profiles_dir: Path):
        """List profiles when none exist."""
        profiles = list_available_profiles()

        assert profiles == []

    def test_list_available_profiles_with_files(self, temp_profiles_dir: Path):
        """List profiles when files exist."""
        (temp_profiles_dir / "default.yaml").write_text("name: default\ndomains: [economy]\n")
        (temp_profiles_dir / "custom.yaml").write_text("name: custom\ndomains: [healthcare]\n")

        profiles = list_available_profiles()

        assert "custom" in profiles
        assert "default" in profiles

    def test_profile_exists_true(self, temp_profiles_dir: Path, mock_profile_yaml: str):
        """Check profile exists."""
        path = temp_profiles_dir / "default.yaml"
        path.write_text(mock_profile_yaml)

        assert profile_exists("default") is True

    def test_profile_exists_false(self):
        """Check non-existent profile."""
        assert profile_exists("nonexistent") is False

    @patch("pathlib.Path.exists")
    def test_load_profile_success(
        self, mock_exists: MagicMock, temp_profiles_dir: Path, mock_profile_yaml: str
    ):
        """Load a valid profile."""
        mock_exists.return_value = True

        with patch("pathlib.Path.open", mock_open(read_data=mock_profile_yaml)):
            profile = load_profile("default")

            assert profile.name == "default"
            assert "economy" in profile.domains

    @patch("pathlib.Path.exists")
    def test_load_profile_not_found(self, mock_exists: MagicMock):
        """Load non-existent profile raises FileNotFoundError."""
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError, match="Profile not found"):
            load_profile("nonexistent")

    def test_load_profile_invalid_yaml(self, temp_profiles_dir: Path):
        """Load invalid YAML raises error."""
        path = temp_profiles_dir / "invalid.yaml"
        path.write_text("invalid: yaml: content:")

        with pytest.raises(Exception):  # yaml.YAMLError or ValueError
            load_profile("invalid")

    def test_load_profile_invalid_profile(self, temp_profiles_dir: Path):
        """Load profile with empty-string domain raises validation error."""
        # Any non-empty topic string is valid; an empty string is not.
        data = {
            "name": "test",
            "description": "Test",
            "domains": [""],  # empty string is not a valid topic
        }
        import yaml

        path = temp_profiles_dir / "bad.yaml"
        path.write_text(yaml.dump(data))

        with pytest.raises(ValueError, match="failed validation"):
            load_profile("bad")


# ─────────────────────────────────────────────────────────────────────────────
# Profile Manager Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestProfileManager:
    """Tests for profile_manager module."""

    def test_create_profile_success(self, temp_profiles_dir: Path):
        """Create a new profile."""
        profile = create_profile(
            name="custom",
            domains=["economy", "healthcare"],
            config_overrides={"depth": 3},
        )

        assert profile.name == "custom"
        assert profile.depth == 3
        assert "economy" in profile.domains

        # Verify file was created
        assert (temp_profiles_dir / "custom.yaml").exists()

    def test_create_profile_duplicate(self, temp_profiles_dir: Path, mock_profile_yaml: str):
        """Creating duplicate profile raises error."""
        path = temp_profiles_dir / "duplicate.yaml"
        path.write_text(mock_profile_yaml)

        with pytest.raises(ValueError, match="already exists"):
            create_profile(
                name="duplicate",
                domains=["economy"],
            )

    def test_create_profile_invalid_domain(self):
        """Creating profile with empty-string domain raises error."""
        # Any non-empty string is a valid topic; only empty/whitespace entries fail.
        with pytest.raises(ValueError, match="Invalid domains"):
            create_profile(
                name="test",
                domains=[""],
            )

    def test_create_profile_invalid_name(self):
        """Creating profile with invalid name raises error."""
        with pytest.raises(ValueError, match="must contain only"):
            create_profile(
                name="test profile!",  # Contains invalid character (space + !)
                domains=["economy"],
            )

    def test_update_profile_success(self, temp_profiles_dir: Path, mock_profile_yaml: str):
        """Update an existing profile."""
        path = temp_profiles_dir / "update_test.yaml"
        path.write_text(mock_profile_yaml)

        profile = update_profile("update_test", {"depth": 5, "geo_fan_out": False})

        assert profile.depth == 5
        assert profile.geo_fan_out is False

    def test_update_profile_not_found(self):
        """Update non-existent profile raises error."""
        with pytest.raises(FileNotFoundError, match="Profile not found"):
            update_profile("nonexistent", {"depth": 3})

    def test_delete_profile_success(self, temp_profiles_dir: Path, mock_profile_yaml: str):
        """Delete an existing profile."""
        path = temp_profiles_dir / "delete_test.yaml"
        path.write_text(mock_profile_yaml)

        result = delete_profile("delete_test")

        assert result is True
        assert not (temp_profiles_dir / "delete_test.yaml").exists()

    def test_delete_profile_not_found(self):
        """Delete non-existent profile returns False."""
        result = delete_profile("nonexistent")

        assert result is False

    def test_delete_system_profile(self):
        """Deleting system profile raises error."""
        with pytest.raises(ValueError, match="Cannot delete system profile"):
            delete_profile("default")

    def test_save_profile(self, temp_profiles_dir: Path):
        """Save a profile to file."""
        profile = ProfileConfig(
            name="save_test",
            description="Test save",
            domains=["economy"],
        )

        save_profile(profile)

        assert (temp_profiles_dir / "save_test.yaml").exists()

    def test_export_profile(self, temp_profiles_dir: Path, mock_profile_yaml: str):
        """Export a profile to file."""
        path = temp_profiles_dir / "export_source.yaml"
        path.write_text(mock_profile_yaml)

        export_path = temp_profiles_dir / "exported" / "export_dest.yaml"
        result_path = export_profile("export_source", export_path)

        assert result_path == export_path
        assert export_path.exists()

    def test_import_profile(self, temp_profiles_dir: Path):
        """Import a profile from file."""
        import yaml

        profile_data = {
            "name": "imported",
            "description": "Imported profile",
            "domains": ["climate", "infrastructure"],
            "depth": 2,
            "subtopics_per_level": 3,
        }

        import_file = temp_profiles_dir / "import_source.yaml"
        import_file.write_text(yaml.dump(profile_data))

        profile = import_profile(import_file)

        assert profile.name == "imported"
        assert "climate" in profile.domains

    def test_import_profile_conflict(self, temp_profiles_dir: Path, mock_profile_yaml: str):
        """Import with conflicting name raises error.

        mock_profile_yaml has name='default'.  We pre-create default.yaml so
        the subsequent import attempt sees a conflict.
        """
        # Pre-create the target profile file so the name is taken
        existing_path = temp_profiles_dir / "default.yaml"
        existing_path.write_text(mock_profile_yaml)

        # Import file also carries name='default' → conflict expected
        import_file = temp_profiles_dir / "import_conflict.yaml"
        import_file.write_text(mock_profile_yaml)

        with pytest.raises(ValueError, match="already exists"):
            import_profile(import_file)

    def test_create_profile_default_expert_allocation(self, temp_profiles_dir: Path):
        """Create profile uses defaults for expert_allocation."""
        profile = create_profile(
            name="no_experts",
            domains=["economy"],
        )

        # Should have empty expert_allocation (not the full default)
        assert profile.expert_allocation == {}


# ─────────────────────────────────────────────────────────────────────────────
# Integration Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestProfileSystemIntegration:
    """Integration tests for the profile system."""

    def test_create_and_load_profile(self, temp_profiles_dir: Path, mock_profile_yaml: str):
        """Create a profile and load it back."""
        # Create
        profile1 = create_profile(
            name="integ_test",
            domains=["education", "immigration"],
            config_overrides={"depth": 3},
        )

        assert profile1.depth == 3
        assert "education" in profile1.domains

        # Load
        profile2 = load_profile("integ_test")

        assert profile2.depth == 3
        assert "education" in profile2.domains
        assert profile2.name == profile1.name

    def test_update_and_validate(self, temp_profiles_dir: Path, mock_profile_yaml: str):
        """Update profile and validate."""
        path = temp_profiles_dir / "validate_test.yaml"
        path.write_text(mock_profile_yaml)

        # Update with valid data
        profile = update_profile("validate_test", {"depth": 5})

        assert profile.depth == 5

        # Validate should pass
        assert validate_profile(profile) is True

    def test_export_import_roundtrip(self, temp_profiles_dir: Path):
        """Export and import maintains profile data."""
        import yaml

        # Create and save original
        _profile1 = create_profile(
            name="round_trip",
            domains=["climate"],
            config_overrides={"depth": 4, "geo_fan_out": False},
        )

        # Export to a separate file
        export_path = temp_profiles_dir / "exported.yaml"
        export_profile("round_trip", export_path)

        # Verify export file exists and has correct data
        assert export_path.exists()
        with open(export_path, "r") as f:
            data = yaml.safe_load(f)
        assert data["depth"] == 4
        assert data["geo_fan_out"] is False

        # Delete original so we can import the exported copy without conflict
        delete_profile("round_trip")

        # Now import succeeds (name "round_trip" is no longer taken)
        imported = import_profile(export_path)
        assert imported.depth == 4
        assert imported.geo_fan_out is False

    def test_full_workflow(self, temp_profiles_dir: Path):
        """Test complete workflow: create, list, load, update, delete."""
        # Create
        p1 = create_profile("workflow", ["economy"])
        assert p1.name == "workflow"

        # List
        profiles = list_available_profiles()
        assert "workflow" in profiles

        # Load
        p2 = load_profile("workflow")
        assert p2.name == "workflow"

        # Update
        p3 = update_profile("workflow", {"depth": 5})
        assert p3.depth == 5

        # Delete
        result = delete_profile("workflow")
        assert result is True

        # Verify deleted
        profiles = list_available_profiles()
        assert "workflow" not in profiles


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
