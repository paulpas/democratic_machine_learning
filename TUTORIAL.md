# Tutorial: Using the Democratic Machine Learning System

## Quick Start

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

## Troubleshooting

### Common Issues

1. **Low fairness scores**: Increase weight diversity or adjust fairness threshold
2. **High confidence but wrong outcome**: Review preference data quality
3. **Slow performance**: Use batching or parallel processing
4. **Data loading errors**: Check JSON format and data types

### Debug Mode

```python
engine = DecisionEngine(debug=True)
engine.make_decision("policy", "region")
# Prints detailed processing info
```
