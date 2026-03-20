# Quick Start Guide

## Overview

This system implements a multi-tiered democratic decision-making algorithm that scales with society and adapts to individual and community needs. It combines traditional democratic principles with machine learning to create a self-balancing, fair decision-making system.

## Quick Start

### Basic Example

```python
from src.core.decision_engine import DecisionEngine
from src.models.voter import Voter, VoterType
from src.models.policy import Policy, PolicyDomain
from src.models.region import Region

# Initialize
engine = DecisionEngine()

# Create entities
california = Region("CA", "California", "state", population=39000000)
policy = Policy("ed_funding", "Education Funding", "Increase K-12 funding", PolicyDomain.EDUCATION)

voter1 = Voter("v1", "CA", {"ed_funding": 0.8}, {"ed_funding": 0.9}, voter_type=VoterType.EXPERT)
voter2 = Voter("v2", "CA", {"ed_funding": -0.3})

# Register and make decision
engine.register_region(california)
engine.register_policy(policy)
engine.register_voter(voter1)
engine.register_voter(voter2)

decision = engine.make_decision("ed_funding", "CA")
print(f"Decision: {decision.outcome}")
print(f"Confidence: {decision.confidence:.2f}")
```

### Command Line

```bash
# Run with defaults
python -m src.ui.tui --region CA

# With custom data
python -m src.ui.tui --data data/voters.json --region CA

# With feedback loop
python -m src.ui.tui --feedback --region CA
```

## Key Components

### Decision Engine
- Collects preferences and calculates weights
- Generates decisions with confidence scores
- Checks fairness constraints

### Weighting System
- Base weight: 1.0
- Representative boost: 2.0x
- Expert boost: 1.5x + expertise level
- Proximity boost: +0.3 for directly affected voters

### Feedback Loop
- Evaluates decision fairness and effectiveness
- Adjusts weights based on outcomes
- Tracks trends over time

## Multi-Tiered System

```python
# County level
counties = ["CA-001", "CA-002", "CA-003"]
for county in counties:
    engine.make_decision("policy", county)

# State level
engine.make_decision("policy", "CA")
```

## Data Formats

### JSON
```json
{
  "voters": [{"id": "v1", "region": "CA", "preferences": {"policy": 0.8}}],
  "policies": [{"id": "policy", "name": "Policy", "domain": "education"}],
  "regions": [{"id": "CA", "name": "California", "type": "state"}]
}
```

## Testing

```bash
pytest --cov=. --cov-report=term-missing --cov-fail-under=95 tests/
```

## Documentation

- `ARCHITECTURE.md` - System architecture and design
- `TUTORIAL.md` - Detailed usage examples
- `AGENTS.md` - Development guidelines
