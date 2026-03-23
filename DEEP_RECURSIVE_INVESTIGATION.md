# Deep Recursive LLM Investigation System

## Overview

The Deep Recursive LLM Investigation System is a sophisticated architecture that performs comprehensive domain analysis through multiple levels of recursive investigation with geographic representation.

## Architecture

### Core Components

1. **LLMClient** (`src/llm/integration.py`)
   - Main interface for LLM-based reasoning
   - Implements deep recursive investigation with fan-out
   - Supports state/county geographic representation

2. **DecisionEngine** (`src/core/decision_engine.py`)
   - Orchestrates the decision-making process
   - Integrates LLM investigation with democratic voting
   - Manages multi-tiered voter representation

3. **SocialNarrativeCollector** (`src/data/social_narrative_collector.py`)
   - Collects real-world social data from Reddit and Google News
   - Provides context for LLM analysis

## Deep Recursive Investigation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    LEVEL 0: INITIAL INVESTIGATION            │
│                    (National Perspective)                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Research questions about the domain               │   │
│  │ 2. LLM generates comprehensive analysis              │   │
│  │ 3. Extract subtopics from reasoning                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              LEVEL 1: SUBTOPIC FAN-OUT                       │
│  ┌──────────────────────┬──────────────────────┐           │
│  │ Subtopic 1           │ Subtopic 2           │           │
│  │ - National tier      │ - National tier      │           │
│  │ - State tier (50)    │ - State tier (50)    │           │
│  │ - County tier        │ - County tier        │           │
│  └──────────────────────┴──────────────────────┘           │
│  ┌──────────────────────┬──────────────────────┐           │
│  │ ... (more subtopics) │                      │           │
│  └──────────────────────┴──────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              LEVEL 2: DEEPER SUBTOPICS                       │
│  For each subtopic from Level 1, fan out to:               │
│  - New sub-subtopics                                         │
│  - National/state/county tiers again                       │
│  - Extensive elaboration                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              LEVEL 3+: CONTINUED RECURSION                   │
│  - Continue fan-out to deeper subtopics                     │
│  - Maintain geographic representation at each level         │
│  - Generate comprehensive elaborations                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              SYNTHESIS PHASE                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Aggregate all elaborations from all levels        │   │
│  │ 2. Form final conjecture from comprehensive evidence │   │
│  │ 3. Rank solutions with geographic weighting          │   │
│  │ 4. Determine which aspects to capture in final thesis│   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Multi-Level Recursion

- **Level 0**: Initial domain investigation (national)
- **Level 1**: Subtopic investigation with geographic fan-out
- **Level 2+**: Deeper subtopic investigation
- **Configurable depth**: Default 4 levels (0-3)

### 2. Geographic Representation

At each level, subtopics are investigated at three geographic tiers:

1. **National**: Country-wide perspective
2. **State**: All 50 US states
3. **County**: Selected counties for local variation

This ensures policies account for regional differences.

### 3. Extensive Elaboration

Each subtopic at each tier receives comprehensive analysis including:

1. Detailed analysis of components
2. Interactions with other domain aspects
3. Supporting/challenging evidence
4. Unintended consequences
5. Implementation considerations
6. Success metrics
7. Historical precedents
8. Expert perspectives

### 4. Solution Ranking with Geographic Weighting

Solutions are ranked using:

- **Confidence score**: LLM's confidence in the analysis
- **Geographic weight**: National > State > County
- **Evidence support**: Mentions in final conjecture
- **Multi-tier bonus**: Bonus for coverage across multiple tiers

### 5. Final Conjecture Formation

The final conjecture is formed by:

1. Aggregating all elaborations from all levels and tiers
2. Using LLM to synthesize a coherent thesis
3. Ranking evidence by support and confidence
4. Determining which aspects should be captured

## Usage

### Basic Usage

```python
from src.llm.integration import LLMClient

# Initialize LLM client
llm_client = LLMClient()

# Initial context
initial_context = {
    "population": 331000000,
    "diversity_index": 0.73,
    "urban_ratio": 0.83,
    "domain": "healthcare",
    "region_type": "national",
}

# Run deep recursive investigation
results = llm_client.generate_reasoning_with_recursion(
    domain="healthcare",
    initial_context=initial_context,
    max_depth=3,  # 4 levels total
    subtopics_per_level=5,
    principles=[
        "Inclusivity",
        "Transparency",
        "Accountability",
        "Adaptability",
        "Equity",
        "Evidence-Based",
        "Context-Aware",
    ],
    include_state_county_rep=True,  # Enable geographic representation
)

# Access results
print(f"Subtopics: {results['subtopics_by_level']}")
print(f"Elaborations: {len(results['all_elaborations'])}")
print(f"Best solutions: {results['best_solutions']}")
print(f"Final conjecture: {results['final_conjecture']}")
```

### With Social Data Integration

```python
from src.llm.integration import LLMClient
from src.data.social_narrative_collector import SocialNarrativeCollector

llm_client = LLMClient()
social_collector = SocialNarrativeCollector()

# Collect social data
social_data = social_collector.get_comprehensive_social_data(
    topic="healthcare policy",
    domain="healthcare",
)

# Use in recursive investigation
results = llm_client.generate_reasoning_with_recursion(
    domain="healthcare",
    initial_context={**initial_context, "social_data": social_data},
    include_state_county_rep=True,
)
```

### Integration with Decision Engine

```python
from src.core.decision_engine import DecisionEngine

engine = DecisionEngine()

# Make decision with LLM investigation
decision = engine.make_decision(
    policy_id="healthcare_policy_2026",
    region_id="US",  # National level
    decision_type="llm_enhanced",
)

# Or for a specific state
decision = engine.make_decision(
    policy_id="healthcare_policy_2026",
    region_id="CA",  # California
    decision_type="llm_enhanced",
)
```

## Configuration Options

### max_depth (default: 3)
- Number of recursion levels
- Higher = more comprehensive but more expensive
- Recommended: 3-4 for most domains

### subtopics_per_level (default: 5)
- Number of subtopics to fan out to at each level
- Level 1: full number
- Level 2+: reduced by half each level
- Recommended: 3-5 for balance

### include_state_county_rep (default: True)
- Whether to include state and county geographic tiers
- True: Investigate at national, state, county levels
- False: National level only

### principles
- Core principles to apply during investigation
- Default: Inclusivity, Transparency, Accountability, Adaptability, Equity, Evidence-Based, Context-Aware

## Results Structure

```python
{
    "domain": str,                    # Investigated domain
    "max_depth": int,                 # Maximum recursion depth
    "subtopics_per_level": int,       # Subtopics per level
    "include_state_county_rep": bool, # Geographic representation enabled
    
    "recursive_analysis": dict,       # Detailed analysis at each level
    "subtopics_by_level": dict,       # Subtopics organized by level
    "final_conjecture": dict,         # Final synthesized conjecture
    "all_elaborations": list,         # All elaborations from all levels
    "best_solutions": list,           # Ranked solutions
    "state_county_analysis": dict,    # Analysis by geographic tier
}
```

## Performance Considerations

### Token Usage
- Level 0: ~2048 tokens
- Each subtopic at each tier: ~1536 tokens
- Elaboration per subtopic: ~1024 tokens
- Final synthesis: ~1536 tokens

### Example Calculation
For healthcare domain with max_depth=3, subtopics_per_level=5:
- Level 0: 1 investigation × 2048 tokens = 2048 tokens
- Level 1: 5 subtopics × 3 tiers × 1536 tokens = 23040 tokens
- Level 2: 2 subtopics × 3 tiers × 1536 tokens = 9216 tokens
- Level 3: 1 subtopic × 3 tiers × 1536 tokens = 4608 tokens
- Synthesis: 1536 tokens
- **Total: ~40,448 tokens**

### Optimization Tips
1. Reduce `max_depth` for faster results
2. Reduce `subtopics_per_level` for less comprehensive but faster analysis
3. Disable `include_state_county_rep` for national-only analysis
4. Use caching for repeated investigations

## Advanced Features

### Custom Principles
```python
principles = [
    "Inclusivity",
    "Transparency",
    "Accountability",
    "Adaptability",
    "Equity",
    "Evidence-Based",
    "Context-Aware",
    "Sustainability",
    "Innovation",
]
```

### Geographic Weighting
Adjust weights for different geographic tiers:

```python
tier_weights = {
    "national": 1.0,    # Full weight for national policies
    "state": 0.8,       # 80% weight for state policies
    "county": 0.6,      # 60% weight for county policies
}
```

### Confidence Thresholds
Adjust confidence thresholds for solution capture:

```python
confidence_threshold = 0.7  # Minimum confidence for inclusion
solution_score_threshold = 0.5  # Minimum score for capture
```

## Troubleshooting

### LLM Returns Empty Responses
- Check if llama.cpp endpoint is running
- Verify max_tokens is sufficient
- Check network connectivity

### No Subtopics Extracted
- Increase max_tokens for initial investigation
- Adjust subtopic extraction heuristics
- Provide more detailed initial context

### Slow Performance
- Reduce max_depth
- Reduce subtopics_per_level
- Disable geographic representation
- Use faster LLM model

## Future Enhancements

1. **Parallel Investigation**: Investigate multiple subtopics in parallel
2. **Adaptive Depth**: Automatically adjust depth based on complexity
3. **Hierarchical Clustering**: Group similar subtopics
4. **Dynamic Weighting**: Adjust geographic weights dynamically
5. **Multi-language Support**: Support for non-English domains
6. **Real-time Updates**: Continuous investigation with updates
