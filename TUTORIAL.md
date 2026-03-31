# Tutorial: Using the Democratic Machine Learning System

## Quick Start — Interactive Profile Menu (Recommended)

The **profile menu** is the primary entry point. It lets you choose what to analyse,
create new custom topics, and launch a full run — all from a keyboard-driven TUI.

```bash
just menu
```

From there you can:
- Run the default 6-domain analysis immediately
- Create a profile for any custom topic ("opioid crisis", "AI governance", "water policy")
- Edit depth, geographic scope, or topic list for any saved profile

See **[PROFILES_WALKTHROUGH.md](PROFILES_WALKTHROUGH.md)** for a complete step-by-step
guide with example terminal output for every action.

---

## Quick Start — just Recipes

```bash
# Install dependencies once
just sync

# Interactive profile menu (recommended)
just menu

# Full production run — default 6 domains
just run

# Run a specific named profile
just run --profile default
just run --profile my-opioid-study

# Quick demo (~30 s per domain, exercises every code path)
just demo-run

# Collect social data only (Reddit + Google News)
just collect

# Inspect what configuration will be used
just show-config
just show-config-demo
```

### Where output goes

All results are written to **`output/<profile-name>/`**:

```
output/default/                          ← default 6-domain profile
├── us_economy_governance_model.md       ← PhD/thesis-format report
├── us_healthcare_governance_model.md
├── us_education_governance_model.md
├── us_immigration_governance_model.md
├── us_climate_governance_model.md
├── us_infrastructure_governance_model.md
└── session_summary.json                 ← machine-readable run summary

output/my-opioid-study/                  ← custom profile
├── us_opioid-crisis_governance_model.md
└── session_summary.json

output/social_<domain>.json              ← collected social narratives (just collect)
```

Each thesis document is a structured scientific report containing:
- **Abstract** with key finding and confidence score
- **Methodology** section (DML framework, data sources, decision mechanism)
- **National / State / County findings** (all 50 states when geo fan-out enabled)
- **Principal Thesis** — the LLM-synthesised policy conjecture
- **Policy Recommendations** ranked by evidence quality
- **Democratic Deliberation** record (trust-weighted vote breakdown, anti-pattern detection)

---

## Quick Start — Python API

### Basic Decision Making

```python
from src.core.decision_engine import DecisionEngine
from src.models.voter import Voter, VoterType
from src.models.policy import Policy, PolicyDomain
from src.models.region import Region

# 1. Initialize the engine
engine = DecisionEngine()

# 2. Create a region (e.g., California)
california = Region(
    region_id="CA",
    name="California",
    region_type="state",
    population=39000000
)

# 3. Create a policy
education_policy = Policy(
    policy_id="ed_funding",
    name="Education Funding Increase",
    description="Increase K-12 funding by 10%",
    domain=PolicyDomain.EDUCATION
)

# 4. Create voters with preferences
voters = [
    Voter("v1", "CA", {"ed_funding": 0.8}, {"ed_funding": 0.9}, voter_type=VoterType.EXPERT),
    Voter("v2", "CA", {"ed_funding": 0.7}),
    Voter("v3", "CA", {"ed_funding": -0.3}),
]

# 5. Register everything with the engine
engine.register_region(california)
engine.register_policy(education_policy)
for voter in voters:
    engine.register_voter(voter)

# 6. Make a decision
decision = engine.make_decision("ed_funding", "CA")
print(f"Decision: {decision.outcome}")  # approved/rejected
print(f"Confidence: {decision.confidence:.2f}")
print(f"Support: {decision.votes_for}")
print(f"Opposition: {decision.votes_against}")
```

### Multi-Tiered System

```python
from src.core.decision_engine import DecisionEngine

engine = DecisionEngine()

# Create counties
counties = {
    "LA": Region("LA", "Los Angeles County", "county", population=10000000),
    "SF": Region("SF", "San Francisco County", "county", population=800000),
    "RURAL": Region("RURAL", "Rural County", "county", population=50000),
}

# Create state
state = Region("CA", "California", "state", population=39000000)
state.children_ids = list(counties.keys())

# Register counties and state
for county in counties.values():
    engine.register_region(county)
engine.register_region(state)

# Make county-level decisions
for county_id in counties:
    engine.make_decision("ed_funding", county_id)

# State-level decision (considers county outcomes)
state_decision = engine.make_decision("ed_funding", "CA")
```

### Using the Feedback Loop

```python
from src.core.feedback_loop import FeedbackLoop

feedback = FeedbackLoop(learning_rate=0.1, fairness_target=0.7)

# Evaluate decisions
for decision in engine.decisions:
    evaluation = feedback.evaluate_decision(decision)
    print(f"Fairness: {evaluation['fairness']:.3f}")
    print(f"Effectiveness: {evaluation['effectiveness']:.3f}")

# Adapt weights if fairness is low
if evaluation["fairness"] < 0.7:
    feedback.adapt_weighting(
        region_id=decision.region_id,
        fairness_score=evaluation["fairness"],
        effectiveness_score=evaluation["effectiveness"]
    )

# Get trends
trends = feedback.get_trends(window=10)
print(f"Average fairness: {trends['avg_fairness']:.3f}")
```

## Command Line Interface

### Basic Usage

```bash
# Run with defaults
python -m src.ui.tui

# Specify region
python -m src.ui.tui --region CA

# Use custom data
python -m src.ui.tui --data data/voters.json --region CA

# Enable feedback loop
python -m src.ui.tui --feedback --region CA

# Custom fairness threshold
python -m src.ui.tui --fairness 0.8 --region CA
```

### Arguments

```
--data          Path to data file (JSON)
--region        Region ID to run decision for
--policy        Policy ID to decide on (default: "default_policy")
--type          Decision type: direct_vote, representative, expert
--feedback      Enable feedback loop for adaptation
--fairness      Fairness threshold (0.0-1.0, default: 0.7)
--output        Output format: text, json, rich
--help          Show help message
```

### Example CLI Output

```bash
$ python -m src.ui.tui --region CA --policy ed_funding

╔════════════════════════════════════════════════════════════╗
║     DEMOCRATIC DECISION ENGINE - DECISION REPORT           ║
╚════════════════════════════════════════════════════════════╝

Region: California (CA)
Policy: Education Funding Increase

┌────────────────────────────────────────────────────────────┐
│ VOTER ANALYSIS                                             │
├────────────────────────────────────────────────────────────┤
│ Total Voters:         1,000                                │
│ Participated:         950                                  │
│ Avg. Weight:          1.05                                 │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ VOTING RESULTS                                             │
├────────────────────────────────────────────────────────────┤
│ For:      58% (551 votes)                                  │
│ Against:  42% (401 votes)                                  │
│ Margin:   +16%                                             │
│ Confidence: 0.82                                           │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ FAIRNESS METRICS                                           │
├────────────────────────────────────────────────────────────┤
│ Overall Fairness:     0.78 ✓                               │
│ Group Fairness:       0.72 ✓                               │
│ Consensus Score:      0.65                                 │
│ Participation Rate:   95%                                  │
└────────────────────────────────────────────────────────────┘

Decision: APPROVED ✓
Confidence: 82%
```

## Data Loading

### JSON Format

```json
{
  "voters": [
    {
      "id": "v1",
      "region": "CA",
      "preferences": {"policy_a": 0.8, "policy_b": -0.3},
      "expertise": {"policy_a": 0.9},
      "weight": 1.0,
      "type": "expert"
    }
  ],
  "policies": [
    {
      "id": "policy_a",
      "name": "Policy Name",
      "description": "Description",
      "domain": "education"
    }
  ],
  "regions": [
    {
      "id": "CA",
      "name": "California",
      "type": "state",
      "population": 39000000,
      "children": ["CA-001"]
    }
  ]
}
```

### CSV Format

```csv
id,region,preferences,expertise,weight,type
v1,CA,"policy_a:0.8,policy_b:-0.3","policy_a:0.9",1.0,expert
```

## Advanced Features

### Custom Weighting

```python
from src.core.weighting_system import WeightingSystem

weights = WeightingSystem(
    base_weight=1.0,
    expertise_boost=0.5,
    proximity_boost=0.3,
    historical_weight=0.2
)

# Calculate weight for specific voter-policy-region
weight = weights.calculate_weight(voter, policy, region)

# Normalize weights across all voters
normalized = weights.normalize_weights(voters)
```

### Fairness Analysis

```python
from src.utils.metrics import FairnessMetrics

metrics = FairnessMetrics()

# Calculate fairness for a decision
fairness = metrics.calculate_fairness(decision, voters, regions)

# Check group fairness
group_fairness = metrics.calculate_group_fairness(decision, voters)

# Check proportional representation
proportional = metrics.check_proportional_representation(voters, decisions)
```

### Policy Impact Analysis

```python
from src.models.policy import Policy

policy = Policy(
    policy_id="ed_funding",
    name="Education Funding",
    description="Increase funding",
    domain=PolicyDomain.EDUCATION
)

# Set impact metrics
policy.implementation_cost = 1000000
policy.expected_benefit = 5000000
policy.support_score = 600
policy.opposition_score = 400

# Get metrics
print(f"Net benefit: {policy.get_net_benefit()}")
print(f"Balance score: {policy.get_balance_score():.3f}")
```

## Integration with Existing Systems

### Loading Real Data

```python
from src.data.data_loader import DataLoader

loader = DataLoader()

# Load from various sources
voters = loader.load_voters("data/voters.json", format="json")
policies = loader.load_policies("data/policies.json", format="json")
regions = loader.load_regions("data/regions.json", format="json")

# Process and use
for voter in voters:
    engine.register_voter(voter)
```

### Real-time Data Integration

```python
import requests

# Fetch polling data
response = requests.get("https://api.example.com/polling")
polling_data = response.json()

# Process into voters
for region, preferences in polling_data.items():
    voter = Voter(
        voter_id=f"poll_{region}",
        region_id=region,
        preferences=preferences
    )
    engine.register_voter(voter)
```

## Performance Optimization

```python
# Use batching for large numbers of decisions
engine.make_decision_batch(
    policy_id="ed_funding",
    region_ids=["CA", "NY", "TX"],
    decision_type="representative"
)

# Parallel processing
from concurrent.futures import ThreadPoolExecutor

def process_decision(region_id):
    return engine.make_decision("ed_funding", region_id)

with ThreadPoolExecutor() as executor:
    decisions = list(executor.map(process_decision, region_ids))
```

## Debugging and Testing

```python
# Enable debug mode
engine = DecisionEngine(debug=True)

# Check system state
print(f"Voters: {len(engine.voters)}")
print(f"Policies: {len(engine.policies)}")
print(f"Decisions: {len(engine.decisions)}")

# Verify fairness
print(f"Fairness check: {engine.check_fairness()}")
```

## Common Patterns

### Pattern 1: Tiered Decision Making

```python
# 1. County level
for county in counties:
    engine.make_decision("policy", county.id)

# 2. State level
engine.make_decision("policy", state.id)

# 3. National level (if applicable)
engine.make_decision("policy", "US")
```

### Pattern 2: Feedback-Driven Adaptation

```python
for iteration in range(10):
    # Make decisions
    decision = engine.make_decision("policy", region.id)
    
    # Evaluate and adapt
    evaluation = feedback.evaluate_decision(decision)
    if evaluation["fairness"] < 0.7:
        feedback.adapt_weighting(region.id, evaluation["fairness"], ...)
    
    # Record history
    feedback.record_history(evaluation)
```

### Pattern 3: Policy Comparison

```python
policies = [
    Policy("policy_a", "Option A", "", PolicyDomain.ECONOMIC),
    Policy("policy_b", "Option B", "", PolicyDomain.ECONOMIC),
]

results = {}
for policy in policies:
    decision = engine.make_decision(policy.policy_id, region.id)
    results[policy.policy_id] = {
        "outcome": decision.outcome,
        "confidence": decision.confidence,
        "fairness": fairness.calculate_fairness(decision, ...)
    }
```

## Configuration

The system ships with `config.yaml` at the repo root. Every threshold, depth, timeout,
and token budget is adjustable there or via environment variables — no source code changes
needed.

### Quick start

```python
from src.config import load_config, get_config

# Auto-loads config.yaml + env var overrides (call once at startup)
cfg = load_config()                        # from config.yaml
cfg = load_config("experiments/fast.yaml") # from a specific file

# After load_config(), get_config() returns the same singleton anywhere
from src.config import get_config
cfg = get_config()
print(cfg.llm.max_depth)           # 4
print(cfg.decision.fairness_threshold)  # 0.7
print(cfg.voter_pool.rng_seed)     # 42
```

### Using a custom config in Python scripts

```python
from src.config import load_config

# Load before creating any engine objects — config is a singleton
load_config("my_config.yaml")

from src.core.decision_engine import DecisionEngine
from src.core.weighting_system import WeightingSystem

# These now automatically pick up values from my_config.yaml
engine = DecisionEngine()      # uses decision.fairness_threshold from YAML
ws = WeightingSystem()         # uses weighting.* from YAML
```

### Environment variable overrides

Environment variables always take priority over the YAML file and are useful for
one-off experiments without creating a new file:

```bash
# Run with shallower LLM investigation (much faster)
DML_LLM__MAX_DEPTH=2 python3 run_all_domains.py economy

# Stricter fairness constraints
DML_DECISION__FAIRNESS_THRESHOLD=0.85 \
DML_FAIRNESS__MIN_PROPORTION=0.4 \
python3 run_all_domains.py healthcare

# Different random seed for voter preferences
DML_VOTER_POOL__RNG_SEED=99 python3 run_all_domains.py

# Disable geographic fan-out for a quick national-only run
DML_VOTER_POOL__PROD_GEO_FAN_OUT=false \
DML_VOTER_POOL__PROD_LLM_MAX_DEPTH=2 \
python3 run_all_domains.py climate
```

### Inspecting the active config

```bash
# Print every effective setting (YAML format)
python3 run_all_domains.py --show-config

# Verify your overrides took effect
DML_LLM__MAX_DEPTH=2 python3 run_all_domains.py --show-config | grep max_depth
```

### Common config recipes

**Fastest possible run (smoke test):**

```yaml
# fast_test.yaml
llm:
  max_depth: 1
  subtopics_per_level: 2
  max_tokens_default: 256
  max_tokens_subtopic: 256
  max_tokens_elaboration: 256
  max_tokens_synthesis: 128
voter_pool:
  prod_llm_max_depth: 1
  prod_llm_subtopics_per_level: 2
  prod_geo_fan_out: false
social:
  cache_hours: 168   # one week — skip re-fetching
```

**Stricter democratic constraints:**

```yaml
decision:
  fairness_threshold: 0.85
fairness:
  min_proportion: 0.4   # 40% minimum group satisfaction
  max_disparity: 0.25   # 25% maximum disparity
trust:
  min_threshold: 0.8    # higher bar for "trusted" voters
  bot_detection_threshold: 0.5  # stricter bot detection
```

**Different LLM server:**

```yaml
llm:
  endpoint: "http://192.168.1.10:11434"
  model: "llama3-8b"
  timeout_seconds: 120
  temperature_default: 0.5
```

**Adjusting voter pool distributions:**

```yaml
voter_pool:
  rng_seed: 7                       # different preference sample
  expert_pref_mu: 0.55              # experts slightly less supportive
  public_pref_min: -0.5             # more divided public
  public_pref_max: 0.8
  county_pref_rural_mu: 0.35        # more rural scepticism
  county_pref_rural_sigma: 0.18     # more rural variance
```

See **[CONFIG.md](CONFIG.md)** for the complete reference with every parameter's
default value, valid range, and detailed description of its runtime and performance impact.

---

## LLM Integration

The system uses a local llama.cpp server for deep recursive policy investigation.

### Checking LLM availability

```python
from src.llm.integration import LLMClient

client = LLMClient()
print(f"LLM available: {client.available}")
print(f"Endpoint: {client.endpoint}")
```

If the server is unreachable `client.available` is `False` and all LLM calls return
empty strings, triggering the rule-based fallback path. Reports are still generated
with heuristic conjectures.

### Running a domain investigation manually

```python
from src.llm.integration import LLMClient
from src.config import load_config

load_config()  # load config.yaml
client = LLMClient()

results = client.generate_reasoning_with_recursion(
    domain="healthcare",
    initial_context={
        "population": 331_000_000,
        "diversity_index": 0.73,
        "urban_ratio": 0.83,
    },
    max_depth=2,           # override config for this call
    subtopics_per_level=3,
    include_state_county_rep=False,  # national only
)

print(f"LLM calls: {results['llm_calls']}")
print(f"Total tokens: {results['total_tokens']}")
print(f"Confidence: {results['final_conjecture']['confidence']:.2f}")
print(f"Statement: {results['final_conjecture']['statement'][:200]}")
```

### Viewing LLM audit logs

Every prompt and response is written to `logs/llm_calls.log`:

```bash
tail -f logs/llm_calls.log
```

To also mirror audit logs to stdout, set `PYTHONLOGGING=DEBUG`:

```bash
PYTHONLOGGING=DEBUG python3 run_all_domains.py economy 2>&1 | tee run.log
```

---

## Social Narrative Collection

The `SocialNarrativeCollector` gathers real-world public opinion from Reddit (via the
free JSON API) and media narratives from Google News RSS — no API keys required.

### Basic usage

```python
from src.data.social_narrative_collector import SocialNarrativeCollector
from src.config import load_config

load_config()
collector = SocialNarrativeCollector()

# Fetch comprehensive social data for a topic
data = collector.get_comprehensive_social_data(
    topic="universal healthcare",
    domain="healthcare",
)

print(f"Opinions fetched: {len(data['opinions'])}")
print(f"Narratives fetched: {len(data['media_narratives'])}")
print(f"Avg opinion sentiment: {data['summary']['average_opinion_sentiment']:.2f}")

# Browse opinions
for op in data["opinions"][:3]:
    print(f"  [{op['perspective']}] {op['text'][:100]}")
```

### Controlling fetch size and caching

The collector caches results in memory for `social.cache_hours` (default 6 hours).
To force a fresh fetch, use `cache_hours=0` or restart the process.

```python
from src.config import load_config

# Reduce fetches for offline development
load_config()
import src.config as cfg_module
cfg_module.get_config().social.cache_hours = 168   # 1 week
cfg_module.get_config().social.max_opinions = 5    # smaller fetch

# Or set in config.yaml
```

```yaml
# config.yaml
social:
  cache_hours: 168
  max_opinions: 5
  max_narratives: 5
```

### Sentiment classification

Reddit posts are classified based on configurable score and ratio thresholds:

| Classification | Condition |
|---------------|-----------|
| `supportive` | `score > 10 AND upvote_ratio > 0.7` (defaults) |
| `critical` | `score < -5 OR upvote_ratio < 0.3` (defaults) |
| `neutral` | `abs(score) <= 5 AND 0.4 <= ratio <= 0.6` |
| `engaged` | all other cases |

Change thresholds in `config.yaml`:

```yaml
social:
  reddit_supportive_score: 20    # require higher score for "supportive"
  reddit_supportive_ratio: 0.75
  reddit_critical_score: -10
```

---

## Troubleshooting

### Common Issues

1. **Low fairness scores**: Increase weight diversity, lower `decision.fairness_threshold`,
   or adjust `fairness.min_proportion`
2. **High confidence but wrong outcome**: Review preference data quality; check if voter
   preferences are realistic for the policy domain
3. **Slow performance**: Reduce `voter_pool.prod_llm_max_depth` and set
   `voter_pool.prod_geo_fan_out=false`; use token budgets of 512–1024
4. **LLM timeout errors**: Increase `llm.timeout_seconds`; reduce `llm.max_tokens_default`
5. **Reddit 403/429 errors**: These are logged at DEBUG level and silently retried via
   the old.reddit.com fallback; increase `social.reddit_rate_limit_sleep` if persistent
6. **Data loading errors**: Check JSON format and data types

### Checking the config singleton

If a class is not picking up the values you set in `config.yaml`, make sure `load_config()`
was called **before** any class was instantiated:

```python
# CORRECT: load first, then import and instantiate
from src.config import load_config
load_config("my.yaml")

from src.core.decision_engine import DecisionEngine
engine = DecisionEngine()   # picks up my.yaml values

# INCORRECT: class instantiated before config is loaded
from src.core.decision_engine import DecisionEngine
engine = DecisionEngine()   # uses hardcoded defaults!
from src.config import load_config
load_config("my.yaml")      # too late — engine already constructed
```

### Debug Mode

```python
engine = DecisionEngine(debug=True)
engine.make_decision("policy", "region")
# Prints detailed processing info
```
