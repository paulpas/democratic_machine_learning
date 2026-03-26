# Configuration Reference

This document describes every configurable parameter in the Democratic Machine Learning
System, including its default value, valid range, runtime effect, and performance impact.

---

## Where Output Lives

Configuration affects **where** and **how much** content the system generates. All
output artifacts are written to the **`output/`** directory:

```
output/us_<domain>_governance_model.md   ← final thesis document per domain
output/session_summary.json              ← run metadata (tokens, calls, timing)
output/social_<domain>.json              ← collected Reddit + News social data
```

The thesis documents are the primary research output. The configuration parameters
in this file control their depth, quality, and the computational resources consumed
to produce them. The most impactful settings are:

| Setting | Location | Effect on output |
|---------|----------|-----------------|
| `voter_pool.prod_llm_max_depth` | `config.yaml` | Recursion depth — higher = richer thesis |
| `voter_pool.prod_geo_fan_out` | `config.yaml` | Include all 50 states in analysis |
| `llm.max_tokens_*` | `config.yaml` | Response length — higher = more detailed sections |
| `llm.parallel_workers` | `config.yaml` | Concurrent requests — higher = faster runtime |

---

## Table of Contents

1. [How Configuration Works](#how-configuration-works)
2. [Quick Override Recipes](#quick-override-recipes)
3. [Section: `llm` — LLM Endpoint and Token Budgets](#section-llm)
4. [Section: `decision` — Decision Engine](#section-decision)
5. [Section: `weighting` — Voter Weight Formula](#section-weighting)
6. [Section: `feedback` — Adaptive Feedback Loop](#section-feedback)
7. [Section: `trust` — Trust Scoring and Security](#section-trust)
8. [Section: `fairness` — Fairness Constraints](#section-fairness)
9. [Section: `social` — Social Narrative Collector](#section-social)
10. [Section: `voter_pool` — Synthetic Voter Pool](#section-voter_pool)
11. [Section: `logging` — Logging and Tracing](#section-logging)
12. [Full Default config.yaml](#full-default-configyaml)

---

## How Configuration Works

Configuration is loaded once at startup and stored as a process-wide singleton. The loading
pipeline applies three sources in priority order:

```
Environment variables  (DML_<SECTION>__<KEY>)   ← highest priority
         ↓
  config.yaml  (or --config path)
         ↓
  Hardcoded defaults  (identical to shipped config.yaml)  ← lowest priority
```

### Loading in Python

```python
from src.config import load_config, get_config, dump_config

# Auto-loads config.yaml if it exists, then applies env vars
cfg = get_config()

# Load a specific file (also sets the global singleton)
cfg = load_config("experiments/fast_test.yaml")

# Print the full effective configuration as YAML
print(dump_config())
```

### Loading at the CLI

```bash
# Use default config.yaml
python3 run_all_domains.py

# Use an alternative config file
python3 run_all_domains.py --config experiments/fast_test.yaml

# Print the effective config and exit (useful to verify overrides)
python3 run_all_domains.py --show-config
python3 run_all_domains.py --config my.yaml --show-config
```

### Environment variable format

```
DML_<SECTION>__<KEY>=<value>
```

- Section and key names are case-insensitive (`DML_LLM__MAX_DEPTH` = `dml_llm__max_depth`)
- Use double underscore (`__`) as the section separator
- Values are automatically coerced to the target type (int, float, bool, str)
- Boolean values: `true/1/yes/on` → `True`, `false/0/no/off` → `False`

### Legacy environment variables

These pre-config variables are still honoured and map directly to `llm.*` settings:

| Legacy variable | Maps to | Notes |
|----------------|---------|-------|
| `LLAMA_CPP_ENDPOINT` | `llm.endpoint` | Highest priority (overrides config file) |
| `LLAMA_MODEL` | `llm.model` | Log label only, not sent to server |
| `LLAMA_TIMEOUT` | `llm.timeout_seconds` | Integer seconds |
| `LLM_LOG_DIR` | `llm.log_dir` | Absolute or relative path |

---

## Quick Override Recipes

### Faster development runs

```yaml
# fast_dev.yaml
llm:
  max_depth: 1
  subtopics_per_level: 2
  max_tokens_default: 512
  max_tokens_subtopic: 512
  max_tokens_elaboration: 512
  max_tokens_synthesis: 256
voter_pool:
  prod_llm_max_depth: 1
  prod_llm_subtopics_per_level: 2
  prod_geo_fan_out: false
```

```bash
python3 run_all_domains.py --config fast_dev.yaml economy
```

Reduces a full economy run from ~700 LLM calls to ~10, cutting runtime from 2+ hours
to under 5 minutes.

### One-shot environment variable overrides

```bash
# Depth 2, no geographic fan-out, smaller token budgets
DML_LLM__MAX_DEPTH=2 \
DML_LLM__MAX_TOKENS_DEFAULT=1024 \
DML_VOTER_POOL__PROD_GEO_FAN_OUT=false \
python3 run_all_domains.py healthcare
```

### Stricter fairness

```yaml
fairness:
  min_proportion: 0.4     # was 0.3
  max_disparity: 0.3      # was 0.4
decision:
  fairness_threshold: 0.8  # was 0.7
```

### Different LLM server

```yaml
llm:
  endpoint: "http://192.168.1.50:11434"
  model: "llama3-8b"
  timeout_seconds: 300
```

### Reproducible vs. random voter preferences

```yaml
voter_pool:
  rng_seed: 42    # fixed → same preferences every run
  # rng_seed: 0  # use 0 for a different but still deterministic seed
```

---

## Section: `llm`

Controls the LLM server connection and all token/sampling parameters.

Source: `src/config.py::LLMConfig` — consumed by `src/llm/integration.py::LLMClient`

---

### Connection

#### `llm.endpoint`

| | |
|---|---|
| **Default** | `http://localhost:8080` |
| **Type** | string (URL) |
| **Env var** | `DML_LLM__ENDPOINT` or legacy `LLAMA_CPP_ENDPOINT` |
| **Effect** | Base URL of the llama.cpp server. All requests go to `{endpoint}/completion`. |
| **Notes** | Set to any HTTP(S) URL. If the server is unreachable at startup the system falls back to rule-based reasoning for all LLM calls. Change this to point at a remote server or a different port. |

#### `llm.model`

| | |
|---|---|
| **Default** | `llama.cpp-model` |
| **Type** | string |
| **Env var** | `DML_LLM__MODEL` or legacy `LLAMA_MODEL` |
| **Effect** | Logging label only — printed in stdout and audit logs. Not sent to the server. |
| **Notes** | Set to the actual model name for clarity in logs (e.g. `mistral-7b-instruct`). |

#### `llm.timeout_seconds`

| | |
|---|---|
| **Default** | `900` (15 minutes) |
| **Type** | int (seconds) |
| **Env var** | `DML_LLM__TIMEOUT_SECONDS` or legacy `LLAMA_TIMEOUT` |
| **Effect** | Hard per-request HTTP timeout. A request that takes longer than this is aborted and the call returns an empty string, triggering the fallback path. |
| **Notes** | Large models on CPU can take several minutes per call. Decrease to 60–120 for fast GPU servers; keep at 900+ for 7B+ models running on CPU or slow hardware. If you see many timeout errors in the logs, increase this value. |

#### `llm.connect_test_timeout`

| | |
|---|---|
| **Default** | `30` (seconds) |
| **Type** | int (seconds) |
| **Env var** | `DML_LLM__CONNECT_TEST_TIMEOUT` |
| **Effect** | Timeout for the startup ping (`POST /completion` with `max_tokens=5`). If this probe fails the system marks the LLM as unavailable and uses fallback reasoning for the entire run. |
| **Notes** | Keep short (10–30 s). A long timeout here delays startup when the server is down. |

---

### Token Budgets

Token budgets control **how much text the LLM is allowed to generate** per call. Larger
budgets produce richer, more detailed responses but cost more time and GPU memory.

The call-type hierarchy (from cheapest to most expensive by default):

| Setting | Default | Call type | Typical use |
|---------|---------|-----------|-------------|
| `max_tokens_synthesis` | `700` | Final synthesis conjecture | Keep small — summary only |
| `max_tokens_domain_initial` | `4096` | Level-0 domain overview | Subtopic extraction |
| `max_tokens_subtopic` | `4096` | Per-subtopic investigation | Core analysis |
| `max_tokens_elaboration` | `4096` | Elaboration on findings | Deep dive |
| `max_tokens_conjecture` | `4096` | Intermediate conjecture | Evidence synthesis |
| `max_tokens_policy_analysis` | `4096` | Policy analysis | Decision context |
| `max_tokens_legacy` | `4096` | Legacy `generate_reasoning()` shim | Compatibility |
| `max_tokens_default` | `8192` | Fallback for any unspecified call | Safety net |

**Performance impact:** Token budget is the single largest driver of per-call latency. On a
mid-range GPU a 4096-token response takes 60–90 seconds; a 512-token response takes 8–15 s.
Total run time scales roughly linearly with the sum of all token budgets × call count.

**Recommended tuning strategy:**

```
Production (quality):  use defaults (4096 per call)
Fast development:      set all max_tokens_* to 512
Moderate quality:      set all max_tokens_* to 1024–2048
```

#### `llm.max_tokens_default`

| | |
|---|---|
| **Default** | `8192` |
| **Effect** | Fallback budget used when a call does not match a specific type. Also the budget for `_call_llm()` direct calls. Rarely reached in normal operation. |

#### `llm.max_tokens_domain_initial`

| | |
|---|---|
| **Default** | `4096` |
| **Effect** | Budget for the Level-0 prompt that asks the LLM to describe the domain and enumerate the top N subtopics. Reducing this limits subtopic variety — the LLM may truncate its numbered list, resulting in fewer or lower-quality subtopics extracted. |

#### `llm.max_tokens_subtopic`

| | |
|---|---|
| **Default** | `4096` |
| **Effect** | Budget for each per-subtopic investigation prompt at every tier (national, state, county). This is called `subtopics_per_level × (1 + states + counties)` times per depth level. The largest single contributor to total token count. Reducing to 1024 dramatically cuts runtime. |

#### `llm.max_tokens_elaboration`

| | |
|---|---|
| **Default** | `4096` |
| **Effect** | Budget for the elaboration call that follows each subtopic investigation. Elaborations provide evidence, equity implications, and measurable metrics. Reducing degrades the quality of the final ranked solutions. |

#### `llm.max_tokens_conjecture`

| | |
|---|---|
| **Default** | `4096` |
| **Effect** | Budget for intermediate conjecture formation calls. These synthesize evidence at each depth level. |

#### `llm.max_tokens_policy_analysis`

| | |
|---|---|
| **Default** | `4096` |
| **Effect** | Budget for the `analyze_policy()` method, used by `DecisionEngine._analyze_policy_context()`. |

#### `llm.max_tokens_synthesis`

| | |
|---|---|
| **Default** | `700` |
| **Effect** | Budget for the **final synthesis conjecture** — the single most-important LLM output. Intentionally small because it asks for a concise summary statement. Increasing to 1500–2000 produces more verbose final conjectures. |

#### `llm.max_tokens_legacy`

| | |
|---|---|
| **Default** | `4096` |
| **Effect** | Budget for the `generate_reasoning()` legacy shim, used by older subsystems that call the LLM directly. |

---

### Sampling Parameters

#### `llm.temperature_default`

| | |
|---|---|
| **Default** | `0.7` |
| **Type** | float [0.0, 2.0] |
| **Env var** | `DML_LLM__TEMPERATURE_DEFAULT` |
| **Effect** | Controls randomness of LLM token selection for all calls that don't specify a temperature. `0.0` = deterministic greedy decoding (same output every run). `1.0` = full model temperature. Values above `1.0` increase creativity but may produce incoherent text. |
| **Notes** | `0.7` balances factual accuracy with variety. Use `0.3–0.5` for more consistent, reproducible policy text. Use `0.8–1.0` for more creative or diverse subtopic suggestions. |

#### `llm.temperature_conjecture`

| | |
|---|---|
| **Default** | `0.6` |
| **Type** | float [0.0, 2.0] |
| **Env var** | `DML_LLM__TEMPERATURE_CONJECTURE` |
| **Effect** | Temperature applied specifically to `form_conjecture()` calls. Intentionally slightly lower than `temperature_default` to produce more stable, evidence-grounded final statements. |

---

### Recursion Structure

#### `llm.max_depth`

| | |
|---|---|
| **Default** | `4` |
| **Type** | int [1, 10] |
| **Env var** | `DML_LLM__MAX_DEPTH` |
| **Effect** | Number of recursive investigation levels. At each level every current subtopic is investigated nationally (and state/county-wide if `prod_geo_fan_out=true`), then elaborated. Level 0 is the initial domain overview; levels 1–N are recursive fan-outs. |
| **Performance impact** | Total LLM call count grows roughly as `subtopics_per_level^max_depth × (1 + states + counties)`. `max_depth=4` with `subtopics_per_level=5` and geo fan-out produces ~700–900 calls per domain. `max_depth=2` with `subtopics_per_level=3` produces ~20–40 calls. |
| **Recommendations** | `4` for production quality. `2` for development. `1` for quick smoke-tests. |

#### `llm.subtopics_per_level`

| | |
|---|---|
| **Default** | `5` |
| **Type** | int [1, 20] |
| **Env var** | `DML_LLM__SUBTOPICS_PER_LEVEL` |
| **Effect** | Number of subtopics extracted from each LLM response and carried forward to the next depth level. This is the branching factor of the investigation tree. |
| **Performance impact** | Multiplies with `max_depth`. Doubling `subtopics_per_level` roughly doubles total call count. |
| **Notes** | If the LLM response does not contain enough numbered items the extractor falls back to a domain-specific seed list. |

---

### Context Slicing

These settings control how much text from previous LLM responses is included in subsequent
prompts. They trade prompt cost (token count) for context richness.

#### `llm.context_snippet_chars`

| | |
|---|---|
| **Default** | `300` |
| **Type** | int (characters) |
| **Effect** | Maximum characters of parent-level reasoning text included in each subtopic investigation prompt as "Context:". |
| **Notes** | Longer snippets give the LLM more context for coherent drilling-down but use more prompt tokens. 300 chars is roughly 75–100 words. |

#### `llm.prior_snippet_chars`

| | |
|---|---|
| **Default** | `400` |
| **Type** | int (characters) |
| **Effect** | Maximum characters of the prior subtopic investigation included in the elaboration prompt as "Prior analysis:". |

#### `llm.conjecture_evidence_limit`

| | |
|---|---|
| **Default** | `15` |
| **Type** | int (items) |
| **Effect** | Maximum number of elaboration items fed to `form_conjecture()` as evidence bullet points. Each item adds ~30–60 prompt tokens. |

#### `llm.analysis_context_limit`

| | |
|---|---|
| **Default** | `5` |
| **Type** | int (items) |
| **Effect** | Maximum number of `research_data` key-value pairs included in `analyze_policy()` prompts. |

#### `llm.synthesis_evidence_limit`

| | |
|---|---|
| **Default** | `20` |
| **Type** | int (items) |
| **Effect** | Maximum elaboration items fed to the **final synthesis conjecture** call. More items → richer final output but larger prompt. |

#### `llm.preview_chars`

| | |
|---|---|
| **Default** | `120` |
| **Type** | int (characters) |
| **Effect** | Length of the response preview printed to stdout after each LLM call (the "preview: …" line in logs). Pure cosmetic — no effect on outputs or performance. |

---

### Progressive Synthesis

#### `llm.progressive_synthesis`

| | |
|---|---|
| **Default** | `true` |
| **Type** | boolean |
| **Effect** | When `true`, a per-subtopic intermediate conjecture is formed after each geographic fan-out (synthesising national + all 50 states + 10 counties findings into one compact result). A per-level conjecture then unifies all subtopics at that depth. The final `form_conjecture()` receives only the level conjectures — not raw elaborations — so every state and county finding influences the final result. |
| **Notes** | Only meaningful when `voter_pool.prod_geo_fan_out=true`. With `false`, falls back to the original flat synthesis using `synthesis_evidence_limit` elaborations. |

#### `llm.max_tokens_intermediate_subtopic`

| | |
|---|---|
| **Default** | `4096` |
| **Type** | int |
| **Effect** | Token budget for per-subtopic intermediate conjecture calls (one per subtopic per depth level). These prompts include all 50 state and 10 county findings. |

#### `llm.max_tokens_intermediate_level`

| | |
|---|---|
| **Default** | `2048` |
| **Type** | int |
| **Effect** | Token budget for per-level intermediate conjecture calls (one per depth level). These unify all subtopic conjectures at that depth. |

#### `llm.intermediate_state_chars`

| | |
|---|---|
| **Default** | `200` |
| **Type** | int (characters) |
| **Effect** | Characters per state finding included in the per-subtopic intermediate conjecture prompt. Increase for richer state context; reduce to shrink prompt size. |

#### `llm.intermediate_county_chars`

| | |
|---|---|
| **Default** | `200` |
| **Type** | int (characters) |
| **Effect** | Characters per county finding included in the per-subtopic intermediate conjecture prompt. |

#### `llm.temperature_intermediate`

| | |
|---|---|
| **Default** | `0.5` |
| **Type** | float [0.0, 2.0] |
| **Effect** | Sampling temperature for intermediate synthesis calls. Slightly more deterministic than `temperature_default` to produce stable, structured summaries. |

---

### Combined Geo Investigate+Elaborate

#### `llm.combine_geo_investigate_elaborate`

| | |
|---|---|
| **Default** | `true` |
| **Type** | boolean |
| **Effect** | When `true`, state and county geographic tiers use a single LLM call that covers both investigation and elaboration (structured as `## Part 1` and `## Part 2`). Reduces geo fan-out calls by ~49% (60 calls/subtopic instead of 120) while retaining all content. |
| **Notes** | Set `false` to revert to the original two-call behaviour (investigate then elaborate separately). |

#### `llm.max_tokens_geo_combined`

| | |
|---|---|
| **Default** | `16384` |
| **Type** | int |
| **Effect** | Token budget for combined state/county investigate+elaborate calls. Needs to be roughly `max_tokens_subtopic + max_tokens_elaboration` to accommodate both parts in one response. Safe up to the server's context window (~272k tokens). |

---

### Solution Ranking

#### `llm.tier_weight_national`

| | |
|---|---|
| **Default** | `1.0` |
| **Type** | float [0.0, 10.0] |
| **Effect** | Multiplier applied to the quality score of solutions generated at the national tier during `_rank_solutions_with_geographic_weighting()`. |
| **Notes** | Keep national ≥ state ≥ county to preserve the intended geographic hierarchy. |

#### `llm.tier_weight_state`

| | |
|---|---|
| **Default** | `0.8` |
| **Type** | float [0.0, 10.0] |
| **Effect** | Multiplier for state-tier solutions. Lower than national to reflect that state-specific findings need to be generalised before appearing in the top solutions list. |

#### `llm.tier_weight_county`

| | |
|---|---|
| **Default** | `0.6` |
| **Type** | float [0.0, 10.0] |
| **Effect** | Multiplier for county-tier solutions. Lowest weight because county-level findings are most localised. |

#### `llm.ranking_length_norm`

| | |
|---|---|
| **Default** | `800` |
| **Type** | int (characters) |
| **Effect** | Denominator in the length-score component: `length_score = min(1.0, len(text) / ranking_length_norm)`. Solutions with text shorter than this receive a partial score. Set lower to reward concise solutions; set higher to require longer, more detailed responses for a high score. |

#### `llm.solution_capture_threshold`

| | |
|---|---|
| **Default** | `0.5` |
| **Type** | float [0.0, 1.0] |
| **Effect** | Minimum combined score (quality × tier weight) for a solution to be marked `should_capture=True` in the ranked output. Does not filter the list — it is metadata for downstream consumers. |

---

### Fallback Confidence

These values are returned when the LLM is unavailable and the system must produce a result
from rule-based heuristics.

#### `llm.default_confidence`

| | |
|---|---|
| **Default** | `0.75` |
| **Type** | float [0.0, 1.0] |
| **Effect** | Confidence score used in parsed LLM responses when no explicit confidence value can be extracted, and in fallback analysis/parse returns. |

#### `llm.fallback_confidence_with_evidence`

| | |
|---|---|
| **Default** | `0.6` |
| **Type** | float [0.0, 1.0] |
| **Effect** | Confidence returned by `_form_fallback_conjecture()` when there is at least some evidence from prior levels. |

#### `llm.fallback_confidence_empty`

| | |
|---|---|
| **Default** | `0.4` |
| **Type** | float [0.0, 1.0] |
| **Effect** | Confidence returned by `_form_fallback_conjecture()` when there is no evidence at all. |

---

### Logging

#### `llm.log_dir`

| | |
|---|---|
| **Default** | `""` (empty → `<repo_root>/logs`) |
| **Type** | string (path) |
| **Env var** | `DML_LLM__LOG_DIR` or legacy `LLM_LOG_DIR` |
| **Effect** | Directory where the rotating LLM audit log (`llm_calls.log`) is written. Full prompts and responses are logged here regardless of stdout verbosity. |
| **Notes** | Set to an absolute path to write logs outside the repo (e.g. `/var/log/dml/`). |

#### `llm.log_max_bytes`

| | |
|---|---|
| **Default** | `52428800` (50 MB) |
| **Type** | int (bytes) |
| **Effect** | Maximum size of each rotating log file before rollover. |

#### `llm.log_backup_count`

| | |
|---|---|
| **Default** | `5` |
| **Type** | int |
| **Effect** | Number of backup log files retained (`llm_calls.log.1` … `.5`). |

---

### Parallel Concurrency

These settings control how many LLM requests fire simultaneously. They require a
`llama-server` started with `--parallel N` (or `-np N`).

#### `llm.parallel_workers`

| | |
|---|---|
| **Default** | `1` |
| **Type** | int |
| **Env var** | `DML_LLM__PARALLEL_WORKERS` |
| **Effect** | Maximum number of in-flight HTTP requests to the LLM server at any time. A `threading.Semaphore(N)` enforces this limit — threads that would exceed it block until a slot is free. |
| **Special values** | `0` = auto-detect by querying `GET /props` on the server for its `total_slots` / `n_parallel` field. `1` = fully sequential (original behaviour). |
| **How to choose** | Set to match the `--parallel N` value passed to `llama-server`. With 4 GPUs each loaded with the model you might use `--parallel 4` and set `parallel_workers: 4`. |
| **Performance impact** | With `N` slots you can saturate all GPU decoding lanes simultaneously. Ideal speedup is `N×` but real speedup depends on context length and batch efficiency. Expect 2–3× for N=4 on independent, similar-length prompts. |
| **Thread safety** | All internal counters (`_call_count`, `_total_tokens`) are protected by a `threading.Lock`. The geo fan-out and subtopic loops use `ThreadPoolExecutor` internally so threads never exceed `parallel_workers` concurrent HTTP calls. |

#### `llm.parallel_retry_base_wait`

| | |
|---|---|
| **Default** | `1.0` (seconds) |
| **Type** | float |
| **Env var** | `DML_LLM__PARALLEL_RETRY_BASE_WAIT` |
| **Effect** | Initial wait before retrying a failed request. Subsequent retries use exponential backoff: `wait = min(max_wait, base_wait × 2^attempt)`. |
| **When triggered** | HTTP 503 (all server slots busy), HTTP 429 (rate-limited), or request timeout. |

#### `llm.parallel_retry_max_wait`

| | |
|---|---|
| **Default** | `30.0` (seconds) |
| **Type** | float |
| **Env var** | `DML_LLM__PARALLEL_RETRY_MAX_WAIT` |
| **Effect** | Cap on retry backoff wait. No retry waits longer than this regardless of attempt count. |

#### `llm.parallel_max_retries`

| | |
|---|---|
| **Default** | `3` |
| **Type** | int |
| **Env var** | `DML_LLM__PARALLEL_MAX_RETRIES` |
| **Effect** | Number of retry attempts before giving up and returning an empty string. The original attempt counts as attempt 0, so 3 retries = 4 total attempts. |

---

## Section: `decision`

Controls the core `DecisionEngine` behaviour.

Source: `src/config.py::DecisionConfig` — consumed by `src/core/decision_engine.py`

---

#### `decision.fairness_threshold`

| | |
|---|---|
| **Default** | `0.7` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_DECISION__FAIRNESS_THRESHOLD` |
| **Effect** | Minimum fairness score required for a decision to pass the fairness gate in `check_fairness()`. Decisions with a rolling-average fairness below this threshold trigger a warning. |
| **Notes** | Increasing to 0.8–0.9 enforces stricter fairness but may cause more decisions to be flagged. Decreasing below 0.5 makes the gate nearly permissive. |

#### `decision.policy_analysis_max_depth`

| | |
|---|---|
| **Default** | `3` |
| **Type** | int [1, 10] |
| **Env var** | `DML_DECISION__POLICY_ANALYSIS_MAX_DEPTH` |
| **Effect** | `max_depth` passed to `generate_reasoning_with_recursion()` inside `DecisionEngine._analyze_policy_context()`. This is separate from `voter_pool.prod_llm_max_depth` which governs the production run script. |
| **Notes** | The decision engine calls LLM analysis once per `make_decision()` call. Reducing this speeds up individual policy decisions at the cost of analytical depth. |

#### `decision.policy_analysis_subtopics`

| | |
|---|---|
| **Default** | `5` |
| **Type** | int [1, 20] |
| **Env var** | `DML_DECISION__POLICY_ANALYSIS_SUBTOPICS` |
| **Effect** | `subtopics_per_level` passed to the LLM inside `_analyze_policy_context()`. |

#### `decision.fairness_check_window`

| | |
|---|---|
| **Default** | `10` |
| **Type** | int [1, 1000] |
| **Env var** | `DML_DECISION__FAIRNESS_CHECK_WINDOW` |
| **Effect** | Number of most-recent decisions evaluated by `check_fairness()`. A rolling window avoids early-run outliers dominating long sessions. |

#### `decision.llm_context_max_opinions`

| | |
|---|---|
| **Default** | `5` |
| **Type** | int [0, 50] |
| **Env var** | `DML_DECISION__LLM_CONTEXT_MAX_OPINIONS` |
| **Effect** | Maximum Reddit opinion items included in the LLM context dict passed to `_analyze_policy_context()`. Each item adds ~200 prompt characters. |

#### `decision.llm_context_max_narratives`

| | |
|---|---|
| **Default** | `3` |
| **Type** | int [0, 50] |
| **Env var** | `DML_DECISION__LLM_CONTEXT_MAX_NARRATIVES` |
| **Effect** | Maximum news narrative items included in the LLM context. Fewer narratives reduce prompt size; more improve LLM grounding in real-world media framing. |

---

## Section: `weighting`

Controls how individual voter weights are computed.

Source: `src/config.py::WeightingConfig` — consumed by `src/core/weighting_system.py::WeightingSystem`

The weight formula for voter `v` on policy `p` in region `r`:

```
weight = base_weight
       × mult_representative  (if voter type == representative)
       × mult_expert          (if voter type == expert)
       + expertise_boost × voter.expertise[policy_id]  (if applicable)
       + proximity_boost                                (if voter.region == policy region)
       + historical_weight × min(participation / participation_norm, 1.0)
```

#### `weighting.base_weight`

| | |
|---|---|
| **Default** | `1.0` |
| **Type** | float > 0 |
| **Env var** | `DML_WEIGHTING__BASE_WEIGHT` |
| **Effect** | Starting weight for every voter before any adjustments. All other weight components are additive on top of this. |

#### `weighting.expertise_boost`

| | |
|---|---|
| **Default** | `0.5` |
| **Type** | float [0.0, 5.0] |
| **Env var** | `DML_WEIGHTING__EXPERTISE_BOOST` |
| **Effect** | Multiplied by `voter.expertise[policy_id]` (0–1) and added to the weight. A voter with expertise score 0.9 on a policy gains `0.5 × 0.9 = 0.45` extra weight. |
| **Notes** | Increase to give domain experts more influence. Set to `0.0` to disable expertise-based weighting. |

#### `weighting.proximity_boost`

| | |
|---|---|
| **Default** | `0.3` |
| **Type** | float [0.0, 5.0] |
| **Env var** | `DML_WEIGHTING__PROXIMITY_BOOST` |
| **Effect** | Flat bonus added when `voter.region_id == region.region_id`. Rewards locally-affected voters. |
| **Notes** | Set to `0.0` to make the system purely expertise-and-type-based without geographic proximity advantage. |

#### `weighting.historical_weight`

| | |
|---|---|
| **Default** | `0.2` |
| **Type** | float [0.0, 2.0] |
| **Env var** | `DML_WEIGHTING__HISTORICAL_WEIGHT` |
| **Effect** | Multiplied by `min(participation_count / participation_norm, 1.0)`. A voter who has participated in 10+ decisions gains the full `0.2` bonus. |

#### `weighting.mult_representative`

| | |
|---|---|
| **Default** | `2.0` |
| **Type** | float > 0 |
| **Env var** | `DML_WEIGHTING__MULT_REPRESENTATIVE` |
| **Effect** | `base_weight` is multiplied by this for voters of type `REPRESENTATIVE` (elected delegates). Setting to `1.0` treats representatives identically to regular voters. |

#### `weighting.mult_expert`

| | |
|---|---|
| **Default** | `1.5` |
| **Type** | float > 0 |
| **Env var** | `DML_WEIGHTING__MULT_EXPERT` |
| **Effect** | `base_weight` multiplier for `EXPERT` voter type. Combined with `expertise_boost`, experts can accumulate substantially higher weight than the public. |

#### `weighting.participation_norm`

| | |
|---|---|
| **Default** | `10.0` |
| **Type** | float > 0 |
| **Env var** | `DML_WEIGHTING__PARTICIPATION_NORM` |
| **Effect** | Denominator in `min(participation / participation_norm, 1.0)`. A voter needs `participation_norm` past decisions to earn the full `historical_weight` bonus. Decrease for systems with fewer total decisions. |

---

## Section: `feedback`

Controls the adaptive feedback loop that adjusts regional weights based on fairness outcomes.

Source: `src/config.py::FeedbackConfig` — consumed by `src/core/feedback_loop.py::FeedbackLoop`

#### `feedback.learning_rate`

| | |
|---|---|
| **Default** | `0.1` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_FEEDBACK__LEARNING_RATE` |
| **Effect** | Speed at which `adapt_weighting()` adjusts regional adaptation factors. Formula: `new_factor = current_factor × (1 + (fairness_target - actual_fairness) × learning_rate)`. |
| **Notes** | `0.1` = 10% correction per decision cycle. Values above `0.5` can cause oscillation. Set to `0.0` to disable adaptive weighting entirely. |

#### `feedback.fairness_target`

| | |
|---|---|
| **Default** | `0.7` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_FEEDBACK__FAIRNESS_TARGET` |
| **Effect** | The fairness score the system drives toward. If actual fairness < target, the adaptation factor increases (boosting minority-group representation). If actual > target, it decreases. |
| **Notes** | Should be equal to or consistent with `decision.fairness_threshold`. |

#### `feedback.stability_threshold`

| | |
|---|---|
| **Default** | `0.2` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_FEEDBACK__STABILITY_THRESHOLD` |
| **Effect** | Maximum allowed variance in the fairness scores across recent decisions. Used by callers to detect unstable decision dynamics. |

#### `feedback.trend_window`

| | |
|---|---|
| **Default** | `10` |
| **Type** | int [1, 1000] |
| **Env var** | `DML_FEEDBACK__TREND_WINDOW` |
| **Effect** | Number of recent history entries used by `get_trends()` when no explicit `window` argument is passed. |

---

## Section: `trust`

Controls trust scoring, anomaly detection, and bot/manipulation identification.

Source: `src/config.py::TrustConfig` — consumed by `src/security/trust_system.py`

### Trust score formula

```
trust = base_score
      + expertise_boost            (if voter type == EXPERT)
      + consistency × consistency_weight
      + min(participation / participation_norm, 1.0) × participation_weight
      + evidence_quality × evidence_weight
trust = min(1.0, trust)
```

#### `trust.base_score`

| | |
|---|---|
| **Default** | `1.0` |
| **Type** | float [0.0, 5.0] |
| **Env var** | `DML_TRUST__BASE_SCORE` |
| **Effect** | Starting trust score before any boosts. With all default boosts a fully-qualified expert voter can reach `1.0 + 0.3 + 0.7×0.4 + 1.0×0.3 + 1.0×0.3 = 2.18`, clamped to `1.0`. |

#### `trust.expertise_boost`

| | |
|---|---|
| **Default** | `0.3` |
| **Type** | float [0.0, 2.0] |
| **Env var** | `DML_TRUST__EXPERTISE_BOOST` |
| **Effect** | Added to the trust score for `EXPERT`-type voters. |

#### `trust.consistency_weight`

| | |
|---|---|
| **Default** | `0.4` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_TRUST__CONSISTENCY_WEIGHT` |
| **Effect** | Weight applied to the voter's consistency score (0–1, representing preference stability over time). High weight rewards voters whose preferences remain coherent. |

#### `trust.participation_weight`

| | |
|---|---|
| **Default** | `0.3` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_TRUST__PARTICIPATION_WEIGHT` |
| **Effect** | Weight applied to the normalised participation factor. |

#### `trust.evidence_weight`

| | |
|---|---|
| **Default** | `0.3` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_TRUST__EVIDENCE_WEIGHT` |
| **Effect** | Weight applied to the voter's evidence quality score (0–1, representing the quality of evidence they provide). |

#### `trust.participation_norm`

| | |
|---|---|
| **Default** | `10.0` |
| **Type** | float > 0 |
| **Env var** | `DML_TRUST__PARTICIPATION_NORM` |
| **Effect** | Number of past participations needed to max out the participation factor. Mirrors `weighting.participation_norm`. |

---

### Anomaly and Inconsistency Detection

#### `trust.anomaly_std_threshold`

| | |
|---|---|
| **Default** | `2.0` |
| **Type** | float > 0 |
| **Env var** | `DML_TRUST__ANOMALY_STD_THRESHOLD` |
| **Effect** | Number of standard deviations from the mean above which a single preference value triggers `detect_anomaly()`. Lower values flag more preferences as anomalous (stricter). |

#### `trust.inconsistency_threshold`

| | |
|---|---|
| **Default** | `0.5` |
| **Type** | float [0.0, 2.0] |
| **Env var** | `DML_TRUST__INCONSISTENCY_THRESHOLD` |
| **Effect** | Maximum allowed absolute difference between any two preferences before `detect_inconsistency()` returns `True`. A voter who supports one policy at `+0.8` and opposes another at `-0.3` has a difference of `1.1 > 0.5` and would be flagged. |

#### `trust.min_threshold`

| | |
|---|---|
| **Default** | `0.7` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_TRUST__MIN_THRESHOLD` |
| **Effect** | Minimum trust score for a voter to be included in `get_trusted_voters()`. Voters below this threshold are excluded from trusted-voter analysis in `ObjectiveGovernanceEngine`. |

#### `trust.source_reputation_min`

| | |
|---|---|
| **Default** | `0.7` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_TRUST__SOURCE_REPUTATION_MIN` |
| **Effect** | Minimum reputation score for an external data source to pass `EvidenceValidator.verify_source()`. Sources from `SocialInfluenceAnalyzer` are checked against this. |

#### `trust.temporal_anomaly_threshold`

| | |
|---|---|
| **Default** | `0.5` |
| **Type** | float [0.0, 2.0] |
| **Env var** | `DML_TRUST__TEMPORAL_ANOMALY_THRESHOLD` |
| **Effect** | Maximum allowed jump between consecutive preference values in `validate_temporal()`. Sudden large swings suggest inauthentic behaviour. |

---

### Bot Detection

Bot score components sum to a final bot score. If `bot_score >= bot_detection_threshold`
the voter is flagged.

#### `trust.bot_detection_threshold`

| | |
|---|---|
| **Default** | `0.7` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_TRUST__BOT_DETECTION_THRESHOLD` |
| **Effect** | Minimum accumulated bot score to flag a voter as likely automated. |

#### `trust.bot_score_uniform_pref`

| | |
|---|---|
| **Default** | `0.3` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_TRUST__BOT_SCORE_UNIFORM_PREF` |
| **Effect** | Amount added to a voter's bot score when their preference standard deviation is < 0.1 (all preferences nearly identical — a bot signal). |

#### `trust.bot_score_no_expertise`

| | |
|---|---|
| **Default** | `0.2` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_TRUST__BOT_SCORE_NO_EXPERTISE` |
| **Effect** | Amount added when the voter has no expertise entries (unusual for a real participant). |

#### `trust.bot_score_unusual_weight`

| | |
|---|---|
| **Default** | `0.1` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_TRUST__BOT_SCORE_UNUSUAL_WEIGHT` |
| **Effect** | Amount added when the voter's voting weight is not `1.0` (bots are sometimes inserted with non-standard weights). |

---

### Manipulation Detection

#### `trust.manipulation_detection_threshold`

| | |
|---|---|
| **Default** | `0.6` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_TRUST__MANIPULATION_DETECTION_THRESHOLD` |
| **Effect** | Minimum accumulated manipulation score to flag a voter as likely manipulated. |

#### `trust.manip_score_extreme_pref`

| | |
|---|---|
| **Default** | `0.2` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_TRUST__MANIP_SCORE_EXTREME_PREF` |
| **Effect** | Amount added per preference value where `abs(pref) > 0.95`. Extreme polarisation on every issue is a manipulation signal. |

---

## Section: `fairness`

Defines the constraints enforced by `FairnessMetrics` on every decision.

Source: `src/config.py::FairnessConfig` — consumed by `src/utils/metrics.py::FairnessMetrics`

#### `fairness.min_proportion`

| | |
|---|---|
| **Default** | `0.3` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_FAIRNESS__MIN_PROPORTION` |
| **Effect** | Minimum proportion of any affected demographic group that must be satisfied by a decision. Implemented via `check_proportional_representation()`. If any group falls below this threshold the decision is flagged as potentially unfair. |
| **Notes** | `0.3` = 30% minimum. Increasing to `0.4`–`0.5` provides stronger minority protection but may make consensus harder to achieve. |

#### `fairness.max_disparity`

| | |
|---|---|
| **Default** | `0.4` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_FAIRNESS__MAX_DISPARITY` |
| **Effect** | Maximum allowed satisfaction disparity between the best-off and worst-off groups. If `(best_group_score - worst_group_score) > max_disparity` the decision is flagged. |

#### `fairness.consensus_high_threshold`

| | |
|---|---|
| **Default** | `0.8` |
| **Type** | float [0.0, 1.0] |
| **Env var** | `DML_FAIRNESS__CONSENSUS_HIGH_THRESHOLD` |
| **Effect** | Support percentage above which `calculate_consensus_score()` returns `1.0` (full consensus). Below this it scales proportionally. |

---

## Section: `social`

Controls the `SocialNarrativeCollector` — Reddit and Google News data gathering.

Source: `src/config.py::SocialConfig` — consumed by `src/data/social_narrative_collector.py`

### Caching

#### `social.cache_hours`

| | |
|---|---|
| **Default** | `6` |
| **Type** | int [0, 168] |
| **Env var** | `DML_SOCIAL__CACHE_HOURS` |
| **Effect** | How long (hours) collected social data is cached in memory before re-fetching. Set to `0` to disable caching (always fetch fresh). Set to `168` (one week) for offline/development mode. |
| **Performance impact** | The Reddit and Google News fetches add 3–15 seconds per domain. Caching eliminates re-fetch on repeated runs within the TTL. |

---

### Reddit

#### `social.reddit_user_agent`

| | |
|---|---|
| **Default** | `"python:democratic_machine_learning:v1.0 (by /u/democratic_ml_bot)"` |
| **Type** | string |
| **Env var** | `DML_SOCIAL__REDDIT_USER_AGENT` |
| **Effect** | `User-Agent` header sent with all Reddit API requests. Reddit requires a descriptive user agent in the format `<platform>:<app>:<version> (by /u/<user>)`. Browser-spoofed UAs are blocked with HTTP 403. |
| **Notes** | If you fork this project change this to your own app identity to avoid rate-limit sharing. |

#### `social.reddit_timeout`

| | |
|---|---|
| **Default** | `15` (seconds) |
| **Type** | int |
| **Env var** | `DML_SOCIAL__REDDIT_TIMEOUT` |
| **Effect** | Per-request HTTP timeout for Reddit JSON API calls. |

#### `social.reddit_rate_limit_sleep`

| | |
|---|---|
| **Default** | `1.0` (seconds) |
| **Type** | float |
| **Env var** | `DML_SOCIAL__REDDIT_RATE_LIMIT_SLEEP` |
| **Effect** | `time.sleep()` inserted before every Reddit request to respect the 60 req/min unauthenticated limit. Decrease cautiously — going below `0.5` risks 429 responses. |

#### `social.reddit_retry_sleep`

| | |
|---|---|
| **Default** | `5.0` (seconds) |
| **Type** | float |
| **Env var** | `DML_SOCIAL__REDDIT_RETRY_SLEEP` |
| **Effect** | How long to sleep after receiving an HTTP 429 (rate-limited) before retrying once. |

#### `social.reddit_fetch_multiplier`

| | |
|---|---|
| **Default** | `2` |
| **Type** | int |
| **Env var** | `DML_SOCIAL__REDDIT_FETCH_MULTIPLIER` |
| **Effect** | `limit` parameter sent to Reddit = `max_results × reddit_fetch_multiplier`. Over-fetches so that after filtering (text quality, relevance) the target `max_results` count is still achievable. |

---

### Reddit Sentiment Classification

Posts are classified into `supportive / critical / neutral / engaged` based on these thresholds.

#### `social.reddit_supportive_score`

| | |
|---|---|
| **Default** | `10` |
| **Type** | int |
| **Effect** | A post with `score > reddit_supportive_score AND upvote_ratio > reddit_supportive_ratio` is classified `"supportive"`. |

#### `social.reddit_supportive_ratio`

| | |
|---|---|
| **Default** | `0.7` |
| **Type** | float [0.0, 1.0] |

#### `social.reddit_critical_score`

| | |
|---|---|
| **Default** | `-5` |
| **Type** | int |
| **Effect** | A post with `score < reddit_critical_score OR upvote_ratio < reddit_critical_ratio` is classified `"critical"`. |

#### `social.reddit_critical_ratio`

| | |
|---|---|
| **Default** | `0.3` |
| **Type** | float [0.0, 1.0] |

---

### Reddit Sentiment Score Calculation

```
normalized_score = max(-1, min(1, reddit_score / reddit_score_norm))
ratio_sentiment  = (upvote_ratio - 0.5) × 2
sentiment = normalized_score × reddit_sentiment_score_weight
          + ratio_sentiment  × reddit_sentiment_ratio_weight
```

#### `social.reddit_score_norm`

| | |
|---|---|
| **Default** | `50` |
| **Type** | int |
| **Effect** | Divides the raw Reddit score to normalise it to [-1, 1]. A post with score 50 maps to sentiment component `1.0`. Increase to de-emphasise viral posts. |

#### `social.reddit_sentiment_score_weight`

| | |
|---|---|
| **Default** | `0.4` |
| **Type** | float [0.0, 1.0] |
| **Effect** | Weight of the score-based component in the final sentiment blend. |

#### `social.reddit_sentiment_ratio_weight`

| | |
|---|---|
| **Default** | `0.6` |
| **Type** | float [0.0, 1.0] |
| **Effect** | Weight of the upvote-ratio component. The two weights should sum to `1.0`. |

#### `social.relevance_text_norm`

| | |
|---|---|
| **Default** | `200` |
| **Type** | int (characters) |
| **Effect** | Text length at which `relevance_score` reaches `1.0`: `min(1.0, len(text) / relevance_text_norm)`. Posts shorter than this receive partial relevance. |

---

### Google News

#### `social.news_timeout`

| | |
|---|---|
| **Default** | `10` (seconds) |
| **Type** | int |
| **Env var** | `DML_SOCIAL__NEWS_TIMEOUT` |
| **Effect** | Per-request HTTP timeout for Google News RSS fetches. |

#### `social.news_text_max_chars`

| | |
|---|---|
| **Default** | `800` |
| **Type** | int (characters) |
| **Env var** | `DML_SOCIAL__NEWS_TEXT_MAX_CHARS` |
| **Effect** | Maximum characters extracted from each news item's description field. Limits memory use and downstream prompt sizes. |

---

### Fetch Counts

#### `social.max_opinions`

| | |
|---|---|
| **Default** | `15` |
| **Type** | int |
| **Env var** | `DML_SOCIAL__MAX_OPINIONS` |
| **Effect** | Maximum Reddit opinions requested by `get_comprehensive_social_data()`. |

#### `social.max_narratives`

| | |
|---|---|
| **Default** | `12` |
| **Type** | int |
| **Env var** | `DML_SOCIAL__MAX_NARRATIVES` |
| **Effect** | Maximum Google News narratives requested by `get_comprehensive_social_data()`. |

---

## Section: `web_search`

Controls the `WebSearcher` — real-time web search with DuckDuckGo API and optional Playwright
JavaScript rendering.

Source: `src/config.py::WebSearchConfig` — consumed by `src/llm/web_search.py`

### Basic Settings

#### `web_search.enabled`

| | |
|---|---|
| **Default** | `true` |
| **Type** | boolean |
| **Env var** | `DML_WEB_SEARCH__ENABLED` |
| **Effect** | Enable/disable web search for real-time factual information during LLM calls. When `true`, the system searches the web for up-to-date information and prepends results to prompts. |
| **Performance impact** | Web search adds 2–8 seconds per query. Disable to use only cached social data and heuristic reasoning. |

#### `web_search.primary_engine`

| | |
|---|---|
| **Default** | `"duckduckgo"` |
| **Type** | string (`"duckduckgo"` or `"google"`) |
| **Env var** | `DML_WEB_SEARCH__PRIMARY_ENGINE` |
| **Effect** | Primary search engine to use. DuckDuckGo provides JSON API without API keys. Google requires JavaScript rendering for results. |
| **Notes** | DuckDuckGo API is faster and more reliable. Google requires Playwright for scraping. |

#### `web_search.max_results_in_prompt`

| | |
|---|---|
| **Default** | `5` |
| **Type** | int [1, 20] |
| **Env var** | `DML_WEB_SEARCH__MAX_RESULTS_IN_PROMPT` |
| **Effect** | Maximum number of search results to include in LLM prompts. More results provide more context but increase token usage. |
| **Performance impact** | Each result adds 100–300 tokens to prompts. |

#### `web_search.max_snippet_length`

| | |
|---|---|
| **Default** | `300` |
| **Type** | int |
| **Env var** | `DML_WEB_SEARCH__MAX_SNIPPET_LENGTH` |
| **Effect** | Maximum characters per snippet included in prompts. Longer snippets provide more context but increase token usage. |
| **Performance impact** | Each character adds ~4 tokens. |

#### `web_search.max_results_per_search`

| | |
|---|---|
| **Default** | `10` |
| **Type** | int |
| **Env var** | `DML_WEB_SEARCH__MAX_RESULTS_PER_SEARCH` |
| **Effect** | Maximum results to fetch from a single search. Used by fallback mechanisms. |

---

### JavaScript Rendering

#### `web_search.use_javascript`

| | |
|---|---|
| **Default** | `false` |
| **Type** | boolean |
| **Env var** | `DML_WEB_SEARCH__USE_JAVASCRIPT` |
| **Effect** | Enable Playwright for JavaScript rendering when DuckDuckGo API returns no results. |
| **Notes** | Requires `playwright` package and `playwright install chromium`. Adds 5–15 seconds per search. |

#### `web_search.browser_type`

| | |
|---|---|
| **Default** | `"chromium"` |
| **Type** | string (`"chromium"`, `"firefox"`, or `"webkit"`) |
| **Env var** | `DML_WEB_SEARCH__BROWSER_TYPE` |
| **Effect** | Browser type for Playwright rendering. Chromium is fastest and most compatible. |
| **Notes** | Firefox and WebKit are alternatives if Chromium fails. |

#### `web_search.viewport_width` / `web_search.viewport_height`

| | |
|---|---|
| **Default** | `1920` / `1080` |
| **Type** | int |
| **Env var** | `DML_WEB_SEARCH__VIEWPORT_WIDTH` / `DML_WEB_SEARCH__VIEWPORT_HEIGHT` |
| **Effect** | Browser viewport dimensions for JavaScript rendering. |
| **Notes** | Some sites serve different content at different resolutions. |

---

### Network and Loading

#### `web_search.wait_for_network_idle`

| | |
|---|---|
| **Default** | `2.0` |
| **Type** | float |
| **Env var** | `DML_WEB_SEARCH__WAIT_FOR_NETWORK_IDLE` |
| **Effect** | Seconds to wait for network to become idle before extracting content. |
| **Notes** | Increase for slow-loading sites. Set to `0` to skip. |

#### `web_search.max_scroll_attempts`

| | |
|---|---|
| **Default** | `3` |
| **Type** | int |
| **Env var** | `DML_WEB_SEARCH__MAX_SCROLL_ATTEMPTS` |
| **Effect** | Maximum infinite scroll attempts for dynamic content. |
| **Notes** | Set to `0` to disable infinite scroll. |

#### `web_search.scroll_delay`

| | |
|---|---|
| **Default** | `1.0` |
| **Type** | float |
| **Env var** | `DML_WEB_SEARCH__SCROLL_DELAY` |
| **Effect** | Seconds between scroll attempts for dynamic content loading. |

---

### Caching

#### `web_search.cache_hours`

| | |
|---|---|
| **Default** | `24` |
| **Type** | int [0, 168] |
| **Env var** | `DML_WEB_SEARCH__CACHE_HOURS` |
| **Effect** | Cache search results for this many hours. Set to `0` to disable caching (always search fresh). Set to `168` (one week) for offline/development mode. |
| **Performance impact** | Cache hits eliminate search delay entirely. |

---

### Geographic Fan-out

#### `web_search.search_on_fanout`

| | |
|---|---|
| **Default** | `true` |
| **Type** | boolean |
| **Env var** | `DML_WEB_SEARCH__SEARCH_ON_FANOUT` |
| **Effect** | Enable web search during state/county geographic fan-out. When `true`, each geographic tier investigates with real-time web search in addition to national LLM calls. |
| **Performance impact** | Adds `50 × depth` state searches and `10 × depth × 50` county searches. Consider disabling for demo runs. |

---

### Query Augmentation

#### `web_search.add_current_date`

| | |
|---|---|
| **Default** | `true` |
| **Type** | boolean |
| **Env var** | `DML_WEB_SEARCH__ADD_CURRENT_DATE` |
| **Effect** | Append current date to search queries for time-sensitive results. |
| **Notes** | Helps get current information for queries like "economy" → "economy March 24, 2026". |

#### `web_search.add_location_context`

| | |
|---|---|
| **Default** | `true` |
| **Type** | boolean |
| **Env var** | `DML_WEB_SEARCH__ADD_LOCATION_CONTEXT` |
| **Effect** | Append location bias (from `location_bias`) to search queries for geographic relevance. |
| **Notes** | Set `web_search.location_bias` to your region (e.g., `"United States"`). |

#### `web_search.location_bias`

| | |
|---|---|
| **Default** | `"United States"` |
| **Type** | string |
| **Env var** | `DML_WEB_SEARCH__LOCATION_BIAS` |
| **Effect** | Geographic context appended to queries when `add_location_context` is `true`. |
| **Notes** | Adjust for other regions (e.g., `"European Union"`, `"Worldwide"`). |

---

## Section: `voter_pool`

Controls the synthetic voter pool constructed by `run_all_domains.py`.

Source: `src/config.py::VoterPoolConfig` — consumed by `run_all_domains.py::_build_national_voter_pool()`

---

### Reproducibility

#### `voter_pool.rng_seed`

| | |
|---|---|
| **Default** | `42` |
| **Type** | int |
| **Env var** | `DML_VOTER_POOL__RNG_SEED` |
| **Effect** | Seed for `random.Random` used to sample voter preferences. Changing this produces a different but still deterministic preference distribution. Set to a different integer to explore preference sensitivity without modifying any formulas. |
| **Notes** | Because preferences are sampled from statistical distributions (not individually tuned), any seed produces a realistic national distribution. The seed mainly matters for reproducibility across runs. |

---

### Public Voter Counts

#### `voter_pool.public_voters_per_million`

| | |
|---|---|
| **Default** | `1` |
| **Type** | int |
| **Env var** | `DML_VOTER_POOL__PUBLIC_VOTERS_PER_MILLION` |
| **Effect** | Number of synthetic public voter delegates allocated per 1,000,000 state residents. California (39M) gets ~39 delegates; Wyoming (578K) gets 1. Total public pool ≈ 331 for the US. |
| **Notes** | Increase to `5` or `10` for a denser public sample at the cost of more `Voter` objects registered. Does not affect LLM call count. |

#### `voter_pool.public_voters_min_per_state`

| | |
|---|---|
| **Default** | `1` |
| **Type** | int |
| **Env var** | `DML_VOTER_POOL__PUBLIC_VOTERS_MIN_PER_STATE` |
| **Effect** | Floor applied to `_state_public_voter_count()`. Every state gets at least this many public delegates regardless of population. |

---

### Expert Voter Configuration

#### `voter_pool.experts_per_domain`

| | |
|---|---|
| **Default** | `{economy:12, healthcare:10, education:8, immigration:7, climate:9, infrastructure:11}` |
| **Type** | dict[str, int] |
| **Env var** | Not directly overridable via env var; use a YAML file to change individual domain counts |
| **Effect** | Number of domain-expert voters registered per policy domain. Each expert represents a major federal agency relevant to the domain. |
| **Notes** | Higher counts give experts more collective influence in trust-weighted voting. |

#### `voter_pool.expert_expertise_min` / `voter_pool.expert_expertise_max`

| | |
|---|---|
| **Default** | `0.85` / `0.95` |
| **Type** | float [0.0, 1.0] |
| **Effect** | Range for expert expertise scores, linearly spaced from expert 0 to expert N. Also used as the individual expert's `voting_weight`. |

#### `voter_pool.expert_pref_mu` / `voter_pool.expert_pref_sigma`

| | |
|---|---|
| **Default** | `0.65` / `0.10` |
| **Type** | float |
| **Effect** | Mean and standard deviation of the normal distribution from which expert policy preferences are sampled. `μ=0.65` reflects that domain experts broadly support evidence-based policy. `σ=0.10` gives moderate variance. |

---

### State Delegate Configuration

#### `voter_pool.state_delegate_pref_mu` / `voter_pool.state_delegate_pref_sigma`

| | |
|---|---|
| **Default** | `0.60` / `0.15` |
| **Type** | float |
| **Effect** | Normal distribution parameters for the 50 state-delegate preferences. Higher `σ` produces more ideologically diverse states. |

#### `voter_pool.state_delegate_expertise`

| | |
|---|---|
| **Default** | `0.65` |
| **Type** | float [0.0, 1.0] |
| **Effect** | Fixed expertise score assigned to all state delegates. |

---

### County Delegate Configuration

County types have separate preference distributions reflecting different community priorities.

#### `voter_pool.county_pref_urban_mu` / `voter_pool.county_pref_urban_sigma`

| | |
|---|---|
| **Default** | `0.68` / `0.08` |
| **Effect** | Urban counties (e.g. Los Angeles, Harris) lean more supportive on average, with tight clustering. |

#### `voter_pool.county_pref_suburban_mu` / `voter_pool.county_pref_suburban_sigma`

| | |
|---|---|
| **Default** | `0.60` / `0.10` |
| **Effect** | Suburban counties have moderate preferences with medium spread. |

#### `voter_pool.county_pref_rural_mu` / `voter_pool.county_pref_rural_sigma`

| | |
|---|---|
| **Default** | `0.48` / `0.12` |
| **Effect** | Rural counties lean slightly less supportive with higher variance, reflecting greater ideological diversity. |

---

### Public Voter Preferences

#### `voter_pool.public_pref_min` / `voter_pool.public_pref_max`

| | |
|---|---|
| **Default** | `-0.3` / `0.9` |
| **Type** | float [-1.0, 1.0] |
| **Effect** | Bounds for the uniform distribution from which public voter preferences are drawn. The asymmetric range (`-0.3` to `+0.9`) produces a moderately positive general public. To simulate a more divided public, widen to `[-0.8, 0.9]`. |

---

### LLM Context Metadata

These values are injected into the `initial_context` dict passed to the LLM at the start of each domain run. They are for informational context in the prompt — the LLM reads them to understand the geographic/demographic context of the analysis.

#### `voter_pool.us_diversity_index`

| | |
|---|---|
| **Default** | `0.73` |
| **Type** | float [0.0, 1.0] |
| **Effect** | Included in the LLM prompt as `diversity_index`. Represents the US demographic diversity index. |

#### `voter_pool.us_urban_ratio`

| | |
|---|---|
| **Default** | `0.83` |
| **Type** | float [0.0, 1.0] |
| **Effect** | Included in the LLM prompt as `urban_ratio`. Represents the share of the US population living in urban areas. |

---

### Production LLM Settings

These settings govern the LLM recursion in the production `run_all_domains.py` script,
independently of `llm.max_depth` / `llm.subtopics_per_level` which govern internal
`DecisionEngine` calls.

#### `voter_pool.prod_llm_max_depth`

| | |
|---|---|
| **Default** | `4` |
| **Type** | int [1, 10] |
| **Env var** | `DML_VOTER_POOL__PROD_LLM_MAX_DEPTH` |
| **Effect** | `max_depth` passed to `generate_reasoning_with_recursion()` in `run_all_domains.py`. The primary knob for controlling investigation depth in production. |
| **Performance impact** | See `llm.max_depth` for the call-count formula. With full geo fan-out and depth 4: ~700–900 LLM calls, 2–4 hours on CPU. Depth 2: ~40–80 calls, 10–20 minutes on CPU. |

#### `voter_pool.prod_llm_subtopics_per_level`

| | |
|---|---|
| **Default** | `5` |
| **Type** | int [1, 20] |
| **Env var** | `DML_VOTER_POOL__PROD_LLM_SUBTOPICS_PER_LEVEL` |
| **Effect** | `subtopics_per_level` in the production run. |

#### `voter_pool.prod_geo_fan_out`

| | |
|---|---|
| **Default** | `true` |
| **Type** | bool |
| **Env var** | `DML_VOTER_POOL__PROD_GEO_FAN_OUT` |
| **Effect** | When `true`, every subtopic investigation fans out to all 50 states and 10 representative counties in addition to the national tier. This is the biggest single multiplier on LLM call count (~63× more calls than national-only). Set to `false` for fast runs that only investigate at the national tier. |

---

## Section: `logging`

Controls the `VerboseLogger` used for structured chain-of-reasoning output.

Source: `src/config.py::LoggingConfig` — consumed by `src/verbose_logging/verbose_logger.py`

#### `logging.verbose_log_dir`

| | |
|---|---|
| **Default** | `output/logs` |
| **Type** | string (path, relative to repo root) |
| **Env var** | `DML_LOGGING__VERBOSE_LOG_DIR` |
| **Effect** | Directory for structured verbose log files (chain-of-reasoning JSON/text logs). Distinct from `llm.log_dir` which stores raw LLM audit logs. |

#### `logging.verbose_log_prefix`

| | |
|---|---|
| **Default** | `chain_of_reasoning` |
| **Type** | string |
| **Env var** | `DML_LOGGING__VERBOSE_LOG_PREFIX` |
| **Effect** | Prefix for verbose log file names. Files are named `<prefix>_<timestamp>.json` (or similar). |

#### `logging.show_locals_in_tracebacks`

| | |
|---|---|
| **Default** | `false` |
| **Type** | bool |
| **Env var** | `DML_LOGGING__SHOW_LOCALS_IN_TRACEBACKS` |
| **Effect** | When `true`, local variable values are included in Rich-formatted exception tracebacks. Useful for debugging but can expose sensitive data in logs. |

---

## Full Default config.yaml

The shipped `config.yaml` contains every parameter with inline comments. View it with:

```bash
cat config.yaml
```

Or print the currently-active effective configuration (which may differ if you have
environment variables set):

```bash
python3 run_all_domains.py --show-config
```

To create a minimal override file containing only the settings you want to change:

```yaml
# my_fast_run.yaml — override only what you need
llm:
  endpoint: "http://gpu-server:8080"
  timeout_seconds: 120
  max_tokens_default: 1024
  max_tokens_subtopic: 512
  max_tokens_elaboration: 512

voter_pool:
  prod_llm_max_depth: 2
  prod_llm_subtopics_per_level: 3
  prod_geo_fan_out: false
  rng_seed: 7

social:
  cache_hours: 24
```

All unspecified parameters inherit from `config.yaml` (or the hardcoded defaults if
`config.yaml` is also absent).
