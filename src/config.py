"""Centralized configuration for the Democratic Machine Learning System.

Configuration is loaded in this priority order (highest → lowest):
  1. Environment variables  (e.g. DML_LLM__MAX_DEPTH=3)
  2. YAML config file       (default: config.yaml in repo root, or --config path)
  3. Hardcoded defaults     (defined in the dataclasses below)

Environment variable naming convention:
  DML_<SECTION>__<KEY>  (double underscore as section separator)

  Examples:
    DML_LLM__ENDPOINT=http://myserver:8080
    DML_LLM__MAX_DEPTH=3
    DML_LLM__MAX_TOKENS_DEFAULT=4096
    DML_WEIGHTING__BASE_WEIGHT=1.0
    DML_TRUST__MIN_THRESHOLD=0.7
    DML_FEEDBACK__LEARNING_RATE=0.1

Usage:
    from src.config import get_config, load_config

    # Use the global singleton (auto-loads config.yaml if it exists)
    cfg = get_config()

    # Or load a specific config file and make it the new global
    cfg = load_config("path/to/my_config.yaml")

    # Access nested settings
    depth   = cfg.llm.max_depth
    timeout = cfg.llm.timeout_seconds
    fair    = cfg.decision.fairness_threshold
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── repo root ─────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_CONFIG_PATH = _REPO_ROOT / "config.yaml"


# ─────────────────────────────────────────────────────────────────────────────
# Nested config sections
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class LLMConfig:
    """LLM endpoint and token/sampling settings."""

    # Connection
    endpoint: str = "http://localhost:8080"
    model: str = "llama.cpp-model"
    timeout_seconds: int = 900  # 15-minute hard timeout per request
    connect_test_timeout: int = 30  # timeout for the initial ping

    # Token budgets per call type
    max_tokens_default: int = 8192
    max_tokens_domain_initial: int = 4096
    max_tokens_subtopic: int = 4096
    max_tokens_elaboration: int = 4096
    max_tokens_conjecture: int = 4096
    max_tokens_policy_analysis: int = 4096
    max_tokens_synthesis: int = 700
    max_tokens_legacy: int = 4096

    # Sampling temperatures
    temperature_default: float = 0.7
    temperature_conjecture: float = 0.6

    # Recursion structure
    max_depth: int = 4
    subtopics_per_level: int = 5

    # Context window slicing (chars / items)
    preview_chars: int = 120  # stdout preview of each response
    context_snippet_chars: int = 300  # parent-context chars fed to subtopic prompt
    prior_snippet_chars: int = 400  # prior-reasoning chars fed to elaboration
    conjecture_evidence_limit: int = 15  # max evidence items for conjecture
    analysis_context_limit: int = 5  # max context items in policy analysis prompt
    synthesis_evidence_limit: int = 20  # max evidence items for final synthesis

    # Ranking / scoring
    tier_weight_national: float = 1.0
    tier_weight_state: float = 0.8
    tier_weight_county: float = 0.6
    ranking_length_norm: int = 800  # chars used to normalise solution length score
    solution_capture_threshold: float = 0.5  # min score to include a solution

    # Fallback confidence values (when LLM is unavailable)
    default_confidence: float = 0.75
    fallback_confidence_with_evidence: float = 0.6
    fallback_confidence_empty: float = 0.4

    # Parallel request concurrency
    # How many LLM requests to fire simultaneously.
    # Set to match the --parallel / -np N value you passed to llama-server.
    # 0 = auto-probe the server for its slot count (reads /props endpoint).
    # 1 = fully sequential (original behaviour).
    parallel_workers: int = 1
    # When a 503 / slot-full error is returned, wait this many seconds then retry
    # (exponential backoff up to parallel_retry_max_wait).
    parallel_retry_base_wait: float = 1.0
    parallel_retry_max_wait: float = 30.0
    # Number of automatic retries on transient server errors (503, 429, timeout).
    parallel_max_retries: int = 3

    # Logging
    log_dir: str = ""  # empty → <repo_root>/logs
    log_max_bytes: int = 52_428_800  # 50 MB per rotating file
    log_backup_count: int = 5


@dataclass
class DecisionConfig:
    """Democratic decision engine settings."""

    fairness_threshold: float = 0.7
    policy_analysis_max_depth: int = 3
    policy_analysis_subtopics: int = 5
    fairness_check_window: int = 10  # recent decisions evaluated in fairness check

    # How many social items are fed to the LLM context
    llm_context_max_opinions: int = 5
    llm_context_max_narratives: int = 3


@dataclass
class WeightingConfig:
    """Voter weighting system settings."""

    base_weight: float = 1.0
    expertise_boost: float = 0.5
    proximity_boost: float = 0.3
    historical_weight: float = 0.2

    # Type-based multipliers
    mult_representative: float = 2.0
    mult_expert: float = 1.5

    # Participation normalization
    participation_norm: float = 10.0  # divide raw participation count by this


@dataclass
class FeedbackConfig:
    """Adaptive feedback-loop settings."""

    learning_rate: float = 0.1
    fairness_target: float = 0.7
    stability_threshold: float = 0.2
    trend_window: int = 10


@dataclass
class TrustConfig:
    """Trust-scoring and bot/manipulation detection thresholds."""

    base_score: float = 1.0
    expertise_boost: float = 0.3
    consistency_weight: float = 0.4
    participation_weight: float = 0.3
    evidence_weight: float = 0.3
    participation_norm: float = 10.0  # same semantics as WeightingConfig

    anomaly_std_threshold: float = 2.0
    inconsistency_threshold: float = 0.5
    min_threshold: float = 0.7  # minimum trust to be considered a "trusted" voter
    source_reputation_min: float = 0.7
    temporal_anomaly_threshold: float = 0.5

    bot_detection_threshold: float = 0.7
    manipulation_detection_threshold: float = 0.6

    # Bot score component weights
    bot_score_uniform_pref: float = 0.3
    bot_score_no_expertise: float = 0.2
    bot_score_unusual_weight: float = 0.1

    # Manipulation score component weights
    manip_score_extreme_pref: float = 0.2


@dataclass
class FairnessConfig:
    """Fairness constraint thresholds."""

    min_proportion: float = 0.3  # minimum 30 % group satisfaction
    max_disparity: float = 0.4  # maximum 40 % inter-group disparity
    consensus_high_threshold: float = 0.8


@dataclass
class SocialConfig:
    """Social narrative collector settings."""

    cache_hours: int = 6
    reddit_user_agent: str = (
        "python:democratic_machine_learning:v1.0 (by /u/democratic_ml_bot)"
    )
    reddit_timeout: int = 15
    reddit_rate_limit_sleep: float = 1.0
    reddit_retry_sleep: float = 5.0
    reddit_fetch_multiplier: int = 2

    # Sentiment classification thresholds
    reddit_supportive_score: int = 10
    reddit_supportive_ratio: float = 0.7
    reddit_critical_score: int = -5
    reddit_critical_ratio: float = 0.3

    # Normalisation
    reddit_score_norm: int = 50
    reddit_sentiment_score_weight: float = 0.4
    reddit_sentiment_ratio_weight: float = 0.6
    relevance_text_norm: int = 200

    news_timeout: int = 10
    news_text_max_chars: int = 800

    max_opinions: int = 15
    max_narratives: int = 12


@dataclass
class VoterPoolConfig:
    """Synthetic voter-pool generation parameters (run_all_domains.py)."""

    rng_seed: int = 42
    public_voters_per_million: int = 1
    public_voters_min_per_state: int = 1

    experts_per_domain: Dict[str, int] = field(
        default_factory=lambda: {
            "economy": 12,
            "healthcare": 10,
            "education": 8,
            "immigration": 7,
            "climate": 9,
            "infrastructure": 11,
        }
    )

    # Expert preference distribution
    expert_pref_mu: float = 0.65
    expert_pref_sigma: float = 0.10
    expert_expertise_min: float = 0.85
    expert_expertise_max: float = 0.95

    # State delegate preference distribution
    state_delegate_pref_mu: float = 0.60
    state_delegate_pref_sigma: float = 0.15
    state_delegate_expertise: float = 0.65

    # County type preference distributions  (mu, sigma)
    county_pref_urban_mu: float = 0.68
    county_pref_urban_sigma: float = 0.08
    county_pref_suburban_mu: float = 0.60
    county_pref_suburban_sigma: float = 0.10
    county_pref_rural_mu: float = 0.48
    county_pref_rural_sigma: float = 0.12

    # Public opinion range (uniform)
    public_pref_min: float = -0.3
    public_pref_max: float = 0.9

    # Context metadata injected into LLM prompt
    us_diversity_index: float = 0.73
    us_urban_ratio: float = 0.83

    # Production LLM call parameters
    prod_llm_max_depth: int = 4
    prod_llm_subtopics_per_level: int = 5
    prod_geo_fan_out: bool = True


@dataclass
class LoggingConfig:
    """Verbose / structured logging settings."""

    verbose_log_dir: str = "output/logs"
    verbose_log_prefix: str = "chain_of_reasoning"
    show_locals_in_tracebacks: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Root config
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class AppConfig:
    """Root application configuration container."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    decision: DecisionConfig = field(default_factory=DecisionConfig)
    weighting: WeightingConfig = field(default_factory=WeightingConfig)
    feedback: FeedbackConfig = field(default_factory=FeedbackConfig)
    trust: TrustConfig = field(default_factory=TrustConfig)
    fairness: FairnessConfig = field(default_factory=FairnessConfig)
    social: SocialConfig = field(default_factory=SocialConfig)
    voter_pool: VoterPoolConfig = field(default_factory=VoterPoolConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


# ─────────────────────────────────────────────────────────────────────────────
# YAML loader (optional dependency — falls back gracefully if PyYAML missing)
# ─────────────────────────────────────────────────────────────────────────────


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML file and return as a plain dict.  Returns {} on failure."""
    try:
        import yaml  # type: ignore
    except ImportError:
        logger.warning(
            "PyYAML is not installed; cannot load %s.  "
            "Install it with: pip install pyyaml",
            path,
        )
        return {}

    try:
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if not isinstance(data, dict):
            logger.warning(
                "Config file %s did not contain a YAML mapping; ignored.", path
            )
            return {}
        return data
    except Exception as exc:
        logger.warning("Failed to read config file %s: %s", path, exc)
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# Deep merge helper
# ─────────────────────────────────────────────────────────────────────────────


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge *override* into *base* (non-destructive to *base*)."""
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Environment variable overlay
# ─────────────────────────────────────────────────────────────────────────────

_ENV_PREFIX = "DML_"
_SECTION_SEP = "__"


def _env_overrides() -> Dict[str, Any]:
    """Scan environment for DML_<SECTION>__<KEY> variables and return nested dict."""
    result: Dict[str, Any] = {}
    for env_key, env_val in os.environ.items():
        if not env_key.startswith(_ENV_PREFIX):
            continue
        rest = env_key[len(_ENV_PREFIX) :]
        if _SECTION_SEP not in rest:
            continue
        section, _, key = rest.partition(_SECTION_SEP)
        section = section.lower()
        key = key.lower()
        if section not in result:
            result[section] = {}
        result[section][key] = env_val
    return result


def _coerce(value: Any, target_type: type) -> Any:
    """Coerce a string (from env) to the target type."""
    if target_type is bool:
        return str(value).lower() in ("1", "true", "yes", "on")
    if target_type is int:
        return int(value)
    if target_type is float:
        return float(value)
    return value  # str or unknown → return as-is


def _apply_section_dict(section_obj: Any, raw: Dict[str, Any]) -> None:
    """Apply a flat dict of {key: value} onto a dataclass instance, coercing types."""
    for key, val in raw.items():
        if not hasattr(section_obj, key):
            logger.debug(
                "Config: unknown key '%s' in section %s — skipped.",
                key,
                type(section_obj).__name__,
            )
            continue
        current = getattr(section_obj, key)
        if isinstance(current, dict) and isinstance(val, dict):
            # Merge dict fields (like experts_per_domain)
            current.update(val)
        elif isinstance(val, str):
            setattr(section_obj, key, _coerce(val, type(current)))
        else:
            setattr(section_obj, key, val)


def _apply_raw_dict(cfg: AppConfig, raw: Dict[str, Any]) -> None:
    """Apply a nested raw dict onto an AppConfig instance."""
    section_map = {
        "llm": cfg.llm,
        "decision": cfg.decision,
        "weighting": cfg.weighting,
        "feedback": cfg.feedback,
        "trust": cfg.trust,
        "fairness": cfg.fairness,
        "social": cfg.social,
        "voter_pool": cfg.voter_pool,
        "logging": cfg.logging,
    }
    for section_name, section_data in raw.items():
        section_name = section_name.lower()
        if section_name not in section_map:
            logger.debug("Config: unknown section '%s' — skipped.", section_name)
            continue
        if not isinstance(section_data, dict):
            logger.debug(
                "Config: section '%s' is not a mapping — skipped.", section_name
            )
            continue
        _apply_section_dict(section_map[section_name], section_data)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

# Module-level singleton
_global_config: Optional[AppConfig] = None


def load_config(config_path: Optional[str | Path] = None) -> AppConfig:
    """Load configuration and set the global singleton.

    Args:
        config_path: Path to a YAML config file.  If *None* the default
                     ``config.yaml`` in the repo root is used when it exists.

    Returns:
        The populated :class:`AppConfig` instance (also stored as the global).
    """
    global _global_config

    cfg = AppConfig()  # start from defaults

    # ── 1. YAML file ──────────────────────────────────────────────────────────
    if config_path is not None:
        yaml_path = Path(config_path)
    else:
        yaml_path = _DEFAULT_CONFIG_PATH

    if yaml_path.exists():
        raw = _load_yaml(yaml_path)
        if raw:
            _apply_raw_dict(cfg, raw)
            logger.info("Config loaded from %s", yaml_path)
    else:
        if config_path is not None:
            # User explicitly requested a file that does not exist
            raise FileNotFoundError(f"Config file not found: {yaml_path}")
        # No default file — silently use defaults + env vars

    # ── 2. Environment variable overrides ────────────────────────────────────
    env_raw = _env_overrides()
    if env_raw:
        _apply_raw_dict(cfg, env_raw)
        logger.debug(
            "Applied %d env-var config override(s).",
            sum(len(v) for v in env_raw.values()),
        )

    # ── 3. Legacy env vars (pre-config era) — map to LLM section ─────────────
    _apply_legacy_env(cfg)

    _global_config = cfg
    return cfg


def _apply_legacy_env(cfg: AppConfig) -> None:
    """Honour the original env vars so existing scripts keep working."""
    legacy_map = {
        "LLAMA_CPP_ENDPOINT": ("llm", "endpoint"),
        "LLAMA_MODEL": ("llm", "model"),
        "LLAMA_TIMEOUT": ("llm", "timeout_seconds"),
        "LLM_LOG_DIR": ("llm", "log_dir"),
    }
    for env_var, (section, key) in legacy_map.items():
        val = os.environ.get(env_var)
        if val is not None:
            section_obj = getattr(cfg, section)
            current = getattr(section_obj, key)
            setattr(section_obj, key, _coerce(val, type(current)))


def get_config() -> AppConfig:
    """Return the global :class:`AppConfig` singleton.

    Calls :func:`load_config` with no arguments on first access (auto-loads
    ``config.yaml`` if present, then applies env var overrides).
    """
    global _global_config
    if _global_config is None:
        load_config()
    return _global_config  # type: ignore[return-value]


def reset_config() -> None:
    """Reset the global singleton (mainly useful in tests)."""
    global _global_config
    _global_config = None


def dump_config(cfg: Optional[AppConfig] = None) -> str:
    """Return the current configuration as a YAML-formatted string.

    Useful for ``--show-config`` flags or debugging.
    """
    if cfg is None:
        cfg = get_config()
    try:
        import yaml  # type: ignore

        return yaml.dump(asdict(cfg), default_flow_style=False, sort_keys=True)
    except ImportError:
        import json

        return json.dumps(asdict(cfg), indent=2)
