# Democratic Machine Learning Architecture

## Overview

This system implements a multi-tiered democratic decision-making algorithm that scales with society and adapts to individual and community needs. It combines traditional democratic principles with machine learning to create a self-balancing, fair decision-making system.

## Core Principles

### 1. Multi-Tiered Representation
- **County/City Level**: Direct participation for local issues
- **State Level**: Representation for regional concerns
- **National Level**: Strategic decision-making for broad policies
- **Cross-Tier Coordination**: Policies flow through all levels for comprehensive impact assessment

### 2. Adaptive Weighting
Voter weights are dynamically adjusted based on:
- **Expertise**: Weight increases for voters with demonstrated expertise in policy areas
- **Proximity**: Voters directly affected by a policy have higher weight
- **Participation History**: Consistent参与者 receive slight weight boosts
- **Representative Status**: Elected representatives have weighted votes

### 3. Fairness Metrics
The system ensures fairness through:
- **Proportional Representation**: No group can be consistently outvoted
- **Minority Protection**: Mechanisms to protect against tyranny of the majority
- **Geographic Balance**: Regional representation across tiers
- **Impact Assessment**: Evaluating policy effects on different demographics

### 4. Feedback Loop**
The system continuously learns and adapts:
- **Outcome Analysis**: Evaluating decision outcomes
- **Weight Adjustment**: Updating voter weights based on performance
- **Policy Evolution**: Adapting policies based on real-world results

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TUI Layer (UI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Decision TUI │  │ Display      │  │ Interactive  │      │
│  │ Commands     │  │ Dashboards   │  │ Prompts      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Core Engine Layer                          │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Decision Engine  │  │ Policy Cell      │                │
│  │ - Vote collection│  │ - Policy matrix  │                │
│  │ - Weight calculation│  │ - Group analysis│             │
│  │ - Outcome generation│  └──────────────────┘              │
│  └──────────────────┘                                       │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Weighting System │  │ Feedback Loop    │                │
│  │ - Adaptive weights│  │ - Learning rate  │                │
│  │ - Expertise boost│  │ - Adaptation     │                │
│  │ - Proximity boost│  └──────────────────┘                │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Data Loader      │  │ Preprocessor     │                │
│  │ - JSON/CSV load  │  │ - Normalization  │                │
│  │ - API integration│  │ - Standardization│                │
│  │ - Real-time data │  │ - Feature encoding│               │
│  └──────────────────┘  └──────────────────┘                │
│  ┌──────────────────┐                                      │
│  │ Feature Engineer │                                      │
│  │ - Voter features │                                      │
│  │ - Region features│                                      │
│  │ - Policy features│                                      │
│  └──────────────────┘                                      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Model Layer                                │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Voter Model      │  │ Policy Model     │                │
│  │ - Preferences    │  │ - Impact scores  │                │
│  │ - Expertise      │  │ - Dependencies   │                │
│  │ - Weights        │  │ - Affected regions│               │
│  └──────────────────┘  └──────────────────┘                │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Region Model     │  │ Decision Model   │                │
│  │ - Hierarchy      │  │ - Outcomes       │                │
│  │ - Population     │  │ - Confidence     │                │
│  │ - Metrics        │  │ - Participation  │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Utils Layer                                │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Metrics          │  │ Validation       │                │
│  │ - Fairness       │  │ - Data validation│                │
│  │ - Efficiency     │  │ - Policy checks  │                │
│  │ - Analysis       │  └──────────────────┘                │
│  └──────────────────┘                                      │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### Decision Engine (`src/core/decision_engine.py`)
The core engine that orchestrates the decision-making process:
- Registers voters, policies, and regions
- Collects preferences and calculates weights
- Generates decisions with confidence scores
- Checks fairness constraints

### Policy Cell (`src/core/policy_cell.py`)
Organizes policy decisions in a matrix format:
- Tracks supporters/opposers for each policy-region combination
- Calculates support ratios
- Computes weighted impact scores

### Weighting System (`src/core/weighting_system.py`)
Manages adaptive voter weights:
- Base weight: 1.0
- Representative boost: 2.0x
- Expert boost: 1.5x + expertise level
- Proximity boost: +0.3 for directly affected voters
- Historical participation boost: up to +0.2

### Feedback Loop (`src/core/feedback_loop.py`)
Enables continuous adaptation:
- Evaluates decision fairness and effectiveness
- Adjusts weights based on outcomes
- Tracks trends over time
- Maintains historical record

## Data Models

### Voter
- `voter_id`: Unique identifier
- `region_id`: Geographic region
- `preferences`: Policy preference scores (-1 to 1)
- `expertise`: Policy expertise levels
- `voting_weight`: Current voting power
- `voter_type`: participant, representative, expert, algorithm

### Policy
- `policy_id`: Unique identifier
- `name`: Policy name
- `description`: Policy details
- `domain`: Economic, Social, Education, etc.
- `impact_score`: Predicted impact
- `support_score`: Current support level
- `implementation_cost`: Resource requirements
- `expected_benefit`: Projected benefits

### Region
- `region_id`: Unique identifier
- `name`: Region name
- `region_type`: county, state, city, national
- `population`: Number of residents
- `parent_id`: Parent region (for hierarchy)
- `children_ids`: Sub-regions
- `policies`: Active policies
- `metrics`: Regional metrics

### Decision
- `decision_id`: Unique identifier
- `policy_id`: Policy being decided
- `region_id`: Region applying decision
- `decision_type`: Vote type
- `outcome`: approved, rejected, abstain
- `confidence`: Decision confidence (0-1)
- `voters_participated`: List of voter IDs
- `votes_for/against`: Vote counts

## Fairness Metrics

### Proportional Representation
- Minimum 30% of affected groups must be satisfied
- Maximum 40% disparity between groups

### Fairness Score (0-1)
- Based on variance in voter satisfaction
- Lower variance = higher fairness
- Weighted average across all voters

### Group Fairness
- Calculates fairness per demographic group
- Ensures no group is consistently disadvantaged
- Tracks historical fairness trends

## Execution Examples

### Basic Usage

```python
from src.core.decision_engine import DecisionEngine
from src.models.voter import Voter, VoterType
from src.models.policy import Policy, PolicyDomain
from src.models.region import Region

# Initialize engine
engine = DecisionEngine(fairness_threshold=0.7)

# Create a region
region = Region(
    region_id="CA",
    name="California",
    region_type="state",
    population=39000000
)

# Create policies
policy = Policy(
    policy_id="education_funding",
    name="Increase Education Funding",
    description="Increase K-12 education funding by 10%",
    domain=PolicyDomain.Education
)

# Create voters
voter1 = Voter(
    voter_id="v1",
    region_id="CA",
    preferences={"education_funding": 0.8},
    expertise={"education_funding": 0.9},
    voter_type=VoterType.EXPERT
)

voter2 = Voter(
    voter_id="v2",
    region_id="CA",
    preferences={"education_funding": -0.3}
)

# Register entities
engine.register_region(region)
engine.register_policy(policy)
engine.register_voter(voter1)
engine.register_voter(voter2)

# Make decision
decision = engine.make_decision(
    policy_id="education_funding",
    region_id="CA"
)

print(f"Decision: {decision.outcome}")
print(f"Confidence: {decision.confidence}")
print(f"Fairness: {engine.check_fairness()}")
```

### Command Line Interface

```bash
# Run the decision engine with default data
python -m src.ui.tui --region CA --policy education_funding

# Run with custom data file
python -m src.ui.tui --data data/example.json --region CA

# Run with feedback loop enabled
python -m src.ui.tui --feedback --region CA

# Run with custom fairness threshold
python -m src.ui.tui --fairness 0.8 --region CA
```

### Multi-Tiered Decision Making

```python
from src.core.decision_engine import DecisionEngine

engine = DecisionEngine()

# Register counties
counties = [
    Region("CA-001", "Los Angeles", "county", population=10000000),
    Region("CA-002", "San Francisco", "county", population=800000),
    Region("CA-003", "Rural County", "county", population=50000),
]

# Register state
state = Region("CA", "California", "state", population=39000000)
state.children_ids = ["CA-001", "CA-002", "CA-003"]

# Make decisions at each tier
for county in counties:
    engine.make_decision("education_funding", county.region_id)

# State-level decision (considers county outcomes)
engine.make_decision("education_funding", "CA")
```

### Using the Feedback Loop

```python
from src.core.feedback_loop import FeedbackLoop

feedback = FeedbackLoop(learning_rate=0.1, fairness_target=0.7)

# Evaluate decisions
evaluation = feedback.evaluate_decision(decision)

# Adapt weights based on feedback
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

## Data Formats

### Voter Data (JSON)
```json
{
  "voters": [
    {
      "id": "v1",
      "region": "CA",
      "preferences": {"policy_a": 0.8, "policy_b": -0.3},
      "expertise": {"policy_a": 0.9},
      "weight": 1.0,
      "type": "participant"
    }
  ]
}
```

### Policy Data (JSON)
```json
{
  "policies": [
    {
      "id": "policy_a",
      "name": "Education Reform",
      "description": "Reform K-12 education system",
      "domain": "education",
      "cost": 1000000,
      "benefit": 5000000
    }
  ]
}
```

### Region Data (JSON)
```json
{
  "regions": [
    {
      "id": "CA",
      "name": "California",
      "type": "state",
      "population": 39000000,
      "children": ["CA-001", "CA-002"]
    }
  ]
}
```

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=. --cov-report=term-missing --cov-fail-under=95 tests/

# Run specific test
pytest tests/test_decision_engine.py::test_fairness_calculation
```

## Future Enhancements

1. **ML Integration**: Use ML models to predict policy outcomes
2. **Dynamic Delegation**: Allow voters to delegate votes based on expertise
3. **Real-time Data**: Integrate real-time economic/social indicators
4. **Visualization**: Interactive dashboards for decision analysis
5. **Scalability**: Distributed processing for large populations

## Political Science Framework

This system draws from:
- **Athenian Democracy**: Direct participation principles
- **Roman Republic**: Mixed government with checks and balances
- **Representative Democracy**: Elected representatives
- **Liquid Democracy**: Delegative voting
- **Condorcet Paradox**: Handling voting inconsistencies
- **Arrow's Impossibility Theorem**: Fairness constraints

The system balances:
- **Majority Rule**: Decisions reflect majority preference
- **Minority Protection**: Mechanisms to protect disadvantaged groups
- **Efficiency**: Practical implementation constraints
- **Fairness**: Proportional representation across demographics
