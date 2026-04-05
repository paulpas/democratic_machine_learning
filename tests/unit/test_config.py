"""Unit tests for src/config.py — configuration loading and override mechanics."""

import os
import tempfile
import textwrap
from pathlib import Path

import pytest

from src.config import (
    AppConfig,
    dump_config,
    get_config,
    load_config,
    reset_config,
)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _write_yaml(content: str) -> Path:
    """Write content to a temp YAML file and return the path."""
    tf = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8")
    tf.write(textwrap.dedent(content))
    tf.flush()
    tf.close()
    return Path(tf.name)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_config_singleton():
    """Ensure each test starts with a clean global singleton."""
    reset_config()
    yield
    reset_config()


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove any DML_* env vars left over from other tests."""
    for key in list(os.environ):
        if key.startswith("DML_") or key in (
            "LLAMA_CPP_ENDPOINT",
            "LLAMA_MODEL",
            "LLAMA_TIMEOUT",
            "LLM_LOG_DIR",
        ):
            monkeypatch.delenv(key, raising=False)
    yield


# ─────────────────────────────────────────────────────────────────────────────
# Defaults
# ─────────────────────────────────────────────────────────────────────────────


class TestDefaults:
    def test_default_llm_endpoint(self):
        cfg = AppConfig()
        assert cfg.llm.endpoint == "http://localhost:8080"

    def test_default_max_depth(self):
        cfg = AppConfig()
        assert cfg.llm.max_depth == 4

    def test_default_fairness_threshold(self):
        cfg = AppConfig()
        assert cfg.decision.fairness_threshold == 0.7

    def test_default_trust_min_threshold(self):
        cfg = AppConfig()
        assert cfg.trust.min_threshold == 0.7

    def test_default_weighting_base(self):
        cfg = AppConfig()
        assert cfg.weighting.base_weight == 1.0

    def test_default_rng_seed(self):
        cfg = AppConfig()
        assert cfg.voter_pool.rng_seed == 42

    def test_default_social_cache_hours(self):
        cfg = AppConfig()
        assert cfg.social.cache_hours == 6

    def test_default_experts_per_domain_keys(self):
        cfg = AppConfig()
        assert set(cfg.voter_pool.experts_per_domain.keys()) == {
            "economy",
            "healthcare",
            "education",
            "immigration",
            "climate",
            "infrastructure",
        }


# ─────────────────────────────────────────────────────────────────────────────
# YAML loading
# ─────────────────────────────────────────────────────────────────────────────


class TestYamlLoading:
    def test_load_llm_endpoint_from_yaml(self):
        path = _write_yaml(
            """
            llm:
              endpoint: "http://custom:9999"
            """
        )
        cfg = load_config(path)
        assert cfg.llm.endpoint == "http://custom:9999"
        Path(path).unlink()

    def test_load_max_depth_from_yaml(self):
        path = _write_yaml(
            """
            llm:
              max_depth: 2
            """
        )
        cfg = load_config(path)
        assert cfg.llm.max_depth == 2
        Path(path).unlink()

    def test_partial_yaml_leaves_defaults_intact(self):
        path = _write_yaml(
            """
            llm:
              max_depth: 2
            """
        )
        cfg = load_config(path)
        # endpoint was not overridden
        assert cfg.llm.endpoint == "http://localhost:8080"
        Path(path).unlink()

    def test_nested_sections_loaded(self):
        path = _write_yaml(
            """
            decision:
              fairness_threshold: 0.85
            weighting:
              base_weight: 2.0
            trust:
              min_threshold: 0.9
            """
        )
        cfg = load_config(path)
        assert cfg.decision.fairness_threshold == 0.85
        assert cfg.weighting.base_weight == 2.0
        assert cfg.trust.min_threshold == 0.9
        Path(path).unlink()

    def test_voter_pool_experts_override(self):
        path = _write_yaml(
            """
            voter_pool:
              rng_seed: 99
              experts_per_domain:
                economy: 5
                healthcare: 5
                education: 5
                immigration: 5
                climate: 5
                infrastructure: 5
            """
        )
        cfg = load_config(path)
        assert cfg.voter_pool.rng_seed == 99
        assert cfg.voter_pool.experts_per_domain["economy"] == 5
        Path(path).unlink()

    def test_missing_file_raises_when_explicit(self):
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_missing_default_file_uses_hardcoded_defaults(self, tmp_path, monkeypatch):
        """When no config.yaml exists at repo root the defaults should apply."""
        # Point the config module's default path at a nonexistent location
        import src.config as config_module

        original = config_module._DEFAULT_CONFIG_PATH
        try:
            config_module._DEFAULT_CONFIG_PATH = tmp_path / "nonexistent.yaml"
            cfg = load_config()
            assert cfg.llm.max_depth == 4  # hardcoded default
        finally:
            config_module._DEFAULT_CONFIG_PATH = original

    def test_float_values_loaded_correctly(self):
        path = _write_yaml(
            """
            feedback:
              learning_rate: 0.05
              fairness_target: 0.8
            """
        )
        cfg = load_config(path)
        assert cfg.feedback.learning_rate == pytest.approx(0.05)
        assert cfg.feedback.fairness_target == pytest.approx(0.8)
        Path(path).unlink()

    def test_bool_values_loaded_correctly(self):
        path = _write_yaml(
            """
            voter_pool:
              prod_geo_fan_out: false
            logging:
              show_locals_in_tracebacks: true
            """
        )
        cfg = load_config(path)
        assert cfg.voter_pool.prod_geo_fan_out is False
        assert cfg.logging.show_locals_in_tracebacks is True
        Path(path).unlink()


# ─────────────────────────────────────────────────────────────────────────────
# Environment variable overrides
# ─────────────────────────────────────────────────────────────────────────────


class TestEnvOverrides:
    def test_env_overrides_llm_max_depth(self, monkeypatch):
        monkeypatch.setenv("DML_LLM__MAX_DEPTH", "2")
        cfg = load_config()
        assert cfg.llm.max_depth == 2

    def test_env_overrides_llm_endpoint(self, monkeypatch):
        monkeypatch.setenv("DML_LLM__ENDPOINT", "http://envhost:1234")
        cfg = load_config()
        assert cfg.llm.endpoint == "http://envhost:1234"

    def test_env_overrides_fairness_threshold(self, monkeypatch):
        monkeypatch.setenv("DML_DECISION__FAIRNESS_THRESHOLD", "0.9")
        cfg = load_config()
        assert cfg.decision.fairness_threshold == pytest.approx(0.9)

    def test_env_overrides_rng_seed(self, monkeypatch):
        monkeypatch.setenv("DML_VOTER_POOL__RNG_SEED", "123")
        cfg = load_config()
        assert cfg.voter_pool.rng_seed == 123

    def test_env_bool_true_variants(self, monkeypatch):
        for val in ("true", "1", "yes", "on", "True", "TRUE"):
            reset_config()
            monkeypatch.setenv("DML_VOTER_POOL__PROD_GEO_FAN_OUT", val)
            cfg = load_config()
            assert cfg.voter_pool.prod_geo_fan_out is True

    def test_env_bool_false_variants(self, monkeypatch):
        for val in ("false", "0", "no", "off", "False", "FALSE"):
            reset_config()
            monkeypatch.setenv("DML_VOTER_POOL__PROD_GEO_FAN_OUT", val)
            cfg = load_config()
            assert cfg.voter_pool.prod_geo_fan_out is False

    def test_env_takes_priority_over_yaml(self, monkeypatch):
        path = _write_yaml(
            """
            llm:
              max_depth: 3
            """
        )
        monkeypatch.setenv("DML_LLM__MAX_DEPTH", "1")
        cfg = load_config(path)
        assert cfg.llm.max_depth == 1  # env wins
        Path(path).unlink()

    def test_legacy_env_llama_cpp_endpoint(self, monkeypatch):
        monkeypatch.setenv("LLAMA_CPP_ENDPOINT", "http://legacy:8080")
        cfg = load_config()
        assert cfg.llm.endpoint == "http://legacy:8080"

    def test_legacy_env_llama_timeout(self, monkeypatch):
        monkeypatch.setenv("LLAMA_TIMEOUT", "600")
        cfg = load_config()
        assert cfg.llm.timeout_seconds == 600

    def test_env_unknown_section_ignored(self, monkeypatch):
        monkeypatch.setenv("DML_NONEXISTENT__SOME_KEY", "value")
        cfg = load_config()  # should not raise
        assert cfg is not None

    def test_env_unknown_key_ignored(self, monkeypatch):
        monkeypatch.setenv("DML_LLM__NONEXISTENT_KEY", "value")
        cfg = load_config()  # should not raise
        assert cfg is not None


# ─────────────────────────────────────────────────────────────────────────────
# Singleton behaviour
# ─────────────────────────────────────────────────────────────────────────────


class TestSingleton:
    def test_get_config_returns_same_instance(self):
        c1 = get_config()
        c2 = get_config()
        assert c1 is c2

    def test_load_config_updates_singleton(self):
        path = _write_yaml(
            """
            llm:
              max_depth: 1
            """
        )
        load_config(path)
        assert get_config().llm.max_depth == 1
        Path(path).unlink()

    def test_reset_config_clears_singleton(self):
        # Load with a custom value to pollute the singleton
        path = _write_yaml(
            """
            llm:
              max_depth: 99
            """
        )
        load_config(path)
        assert get_config().llm.max_depth == 99
        Path(path).unlink()

        reset_config()
        # After reset get_config() reloads from scratch (config.yaml + env vars)
        cfg = get_config()
        # The custom value (99) must be gone — back to whatever config.yaml says
        assert cfg.llm.max_depth != 99


# ─────────────────────────────────────────────────────────────────────────────
# dump_config
# ─────────────────────────────────────────────────────────────────────────────


class TestDumpConfig:
    def test_dump_contains_endpoint(self):
        cfg = AppConfig()
        output = dump_config(cfg)
        assert "endpoint" in output

    def test_dump_contains_max_depth(self):
        cfg = AppConfig()
        output = dump_config(cfg)
        assert "max_depth" in output

    def test_dump_reflects_override(self):
        path = _write_yaml(
            """
            llm:
              max_depth: 1
            """
        )
        cfg = load_config(path)
        output = dump_config(cfg)
        assert "1" in output
        Path(path).unlink()


# ─────────────────────────────────────────────────────────────────────────────
# Integration: config values flow into downstream classes
# ─────────────────────────────────────────────────────────────────────────────


class TestConfigFlowsIntoClasses:
    def test_fairness_metrics_uses_config(self):
        path = _write_yaml(
            """
            fairness:
              min_proportion: 0.25
              max_disparity: 0.35
            """
        )
        load_config(path)
        from src.utils.metrics import FairnessMetrics

        fm = FairnessMetrics()
        assert fm.min_proportion == pytest.approx(0.25)
        assert fm.max_disparity == pytest.approx(0.35)
        Path(path).unlink()

    def test_weighting_system_uses_config(self):
        path = _write_yaml(
            """
            weighting:
              base_weight: 2.0
              expertise_boost: 1.0
            """
        )
        load_config(path)
        from src.core.weighting_system import WeightingSystem

        ws = WeightingSystem()
        assert ws.base_weight == pytest.approx(2.0)
        assert ws.expertise_boost == pytest.approx(1.0)
        Path(path).unlink()

    def test_feedback_loop_uses_config(self):
        path = _write_yaml(
            """
            feedback:
              learning_rate: 0.05
              fairness_target: 0.8
              stability_threshold: 0.1
            """
        )
        load_config(path)
        from src.core.feedback_loop import FeedbackLoop

        fl = FeedbackLoop()
        assert fl.learning_rate == pytest.approx(0.05)
        assert fl.fairness_target == pytest.approx(0.8)
        assert fl.stability_threshold == pytest.approx(0.1)
        Path(path).unlink()

    def test_trust_scorer_uses_config(self):
        path = _write_yaml(
            """
            trust:
              base_score: 0.5
              expertise_boost: 0.2
            """
        )
        load_config(path)
        from src.security.trust_system import TrustScorer

        ts = TrustScorer()
        assert ts.base_score == pytest.approx(0.5)
        assert ts.expertise_boost == pytest.approx(0.2)
        Path(path).unlink()

    def test_explicit_constructor_args_override_config(self):
        path = _write_yaml(
            """
            weighting:
              base_weight: 99.0
            """
        )
        load_config(path)
        from src.core.weighting_system import WeightingSystem

        # Explicit arg should take priority over config
        ws = WeightingSystem(base_weight=1.5)
        assert ws.base_weight == pytest.approx(1.5)
        Path(path).unlink()

    def test_feedback_loop_trend_window_from_config(self):
        path = _write_yaml(
            """
            feedback:
              trend_window: 5
            """
        )
        load_config(path)
        from src.core.feedback_loop import FeedbackLoop

        fl = FeedbackLoop()
        # Inject some history entries
        for _ in range(10):
            fl.record_history({"fairness": 0.8, "effectiveness": 0.7, "balance": 0.75})
        trends = fl.get_trends()  # no explicit window → uses config value (5)
        assert "avg_fairness" in trends
        Path(path).unlink()
