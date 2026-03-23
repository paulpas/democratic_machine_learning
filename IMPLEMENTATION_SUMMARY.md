# Implementation Summary: Deep Recursive LLM Investigation

## Overview

This implementation adds comprehensive deep recursive LLM investigation to the democratic machine learning system, with full support for state and county geographic representation across all levels of recursion.

## What Was Implemented

### 1. Enhanced `generate_reasoning_with_recursion()` Method

**File**: `src/llm/integration.py:121-425`

**Key Features**:
- **Deep recursion**: Up to 4 levels (configurable)
- **Geographic fan-out**: National, state, and county tiers
- **Extensive elaboration**: Comprehensive analysis at each level
- **Hierarchical synthesis**: Final conjecture formation from all evidence

**Parameters**:
```python
def generate_reasoning_with_recursion(
    domain: str,
    initial_context: Dict[str, Any],
    max_depth: int = 4,              # Default: 4 levels
    subtopics_per_level: int = 5,    # Default: 5 subtopics per level
    principles: Optional[List[str]] = None,
    include_state_county_rep: bool = True,  # NEW: Enable/disable geographic representation
) -> Dict[str, Any]:
```

**Returns**:
```python
{
    "domain": str,
    "max_depth": int,
    "subtopics_per_level": int,
    "include_state_county_rep": bool,
    
    "recursive_analysis": dict,       # Detailed analysis per level
    "subtopics_by_level": dict,       # Subtopics organized by depth
    "final_conjecture": dict,         # Synthesized final thesis
    "all_elaborations": list,         # All elaborations from all levels
    "best_solutions": list,           # Ranked solutions
    "state_county_analysis": dict,    # Analysis by geographic tier
}
```

### 2. Geographic Representation Methods

**File**: `src/llm/integration.py:427-485`

#### `_get_us_geography()`
- Returns comprehensive US geography data
- Includes population, state/county counts
- Provides state-level details (population, county count)

#### `_get_tier_population(tier: str, geography: Dict)`
- Returns population for national, state, or county tier
- Used for context-aware weighting

#### `_build_tiered_questions()`
- Generates tier-specific research questions
- National: Country-wide perspective
- State: State-level variations and adaptations
- County: Local variations and rural/urban differences

### 3. Enhanced Elaboration Methods

**File**: `src/llm/integration.py:487-545`

#### `_elaborate_on_subtopic_with_tier()`
- **NEW**: Elaborates on subtopics at specific geographic tiers
- Includes tier-specific analysis
- Considers multi-tier relationships

#### `_elaborate_on_subtopic()` (Legacy)
- Backward compatible wrapper
- Calls `_elaborate_on_subtopic_with_tier()` with "national" tier

### 4. Geographic Weighted Solution Ranking

**File**: `src/llm/integration.py:547-612`

#### `_rank_solutions_with_geographic_weighting()`
- **NEW**: Ranks solutions with geographic weighting
- Weights tiers differently: National (1.0) > State (0.8) > County (0.6)
- Multi-tier bonus for coverage across multiple geographic scales
- Considers evidence support and confidence

#### `_rank_solutions()` (Legacy)
- Backward compatible wrapper
- Calls `_rank_solutions_with_geographic_weighting()` with empty state_county_elaborations

### 5. Multi-Tiered Voter Representation

**File**: `src/core/decision_engine.py:66-145`

#### `_get_voters_for_region()`
- **NEW**: Supports multi-tiered voter selection
- Supports "US"/"national" for entire country
- Supports state abbreviations (CA, TX, etc.)
- Supports county names
- Falls back to all voters if region not found

#### `make_decision()` (Enhanced)
- Updated to use multi-tiered voter selection
- Supports national, state, and county level decisions
- Maintains backward compatibility

## Investigation Flow

```
LEVEL 0: Initial Domain Investigation (National)
  ├─ Research questions about domain
  ├─ LLM generates analysis
  └─ Extract subtopics

LEVEL 1: Subtopic Investigation
  ├─ Subtopic 1
  │  ├─ National tier analysis
  │  ├─ State tier analysis (50 states)
  │  └─ County tier analysis
  ├─ Subtopic 2
  │  ├─ National tier analysis
  │  ├─ State tier analysis (50 states)
  │  └─ County tier analysis
  └─ ...

LEVEL 2: Deeper Subtopics
  ├─ Sub-subtopic 1.1
  │  ├─ National tier analysis
  │  ├─ State tier analysis
  │  └─ County tier analysis
  └─ ...

LEVEL 3+: Continue Recursion
  └─ Continue fan-out with geographic representation

SYNTHESIS PHASE
  ├─ Aggregate all elaborations
  ├─ Form final conjecture
  ├─ Rank solutions with geographic weighting
  └─ Determine best approaches
```

## Example Investigation (Healthcare Domain)

### Configuration
- Domain: healthcare
- Max depth: 3 (4 levels total)
- Subtopics per level: 5
- Geographic representation: Enabled

###Investigation Breakdown

**Level 0 (National)**:
- 1 investigation
- Research questions: 5
- Elaborations: 1 (national only)
- Subtopics extracted: 5

**Level 1**:
- 5 subtopics × 3 tiers = 15 elaborations
- National, State (50), County

**Level 2**:
- 2-3 subtopics × 3 tiers = 6-9 elaborations
- Deeper sub-subtopics

**Level 3**:
- 1-2 subtopics × 3 tiers = 3-6 elaborations
- Deepest level

**Total**: ~30-40 elaborations across 4 levels and 3 geographic tiers

### Token Usage Estimate
- Level 0: 2,048 tokens
- Level 1: 15 × 1,536 = 23,040 tokens
- Level 2: 7 × 1,536 = 10,752 tokens
- Level 3: 4 × 1,536 = 6,144 tokens
- Synthesis: 1,536 tokens
- **Total: ~43,520 tokens**

## Usage Examples

### Basic Recursive Investigation

```python
from src.llm.integration import LLMClient

llm = LLMClient()

results = llm.generate_reasoning_with_recursion(
    domain="healthcare",
    initial_context={
        "population": 331000000,
        "diversity_index": 0.73,
        "urban_ratio": 0.83,
    },
    max_depth=3,
    subtopics_per_level=5,
    include_state_county_rep=True,
)

print(f"Subtopics: {results['subtopics_by_level']}")
print(f"Best solutions: {results['best_solutions'][:3]}")
print(f"Final conjecture: {results['final_conjecture']['statement']}")
```

### With Social Data Integration

```python
from src.llm.integration import LLMClient
from src.data.social_narrative_collector import SocialNarrativeCollector

llm = LLMClient()
social = SocialNarrativeCollector()

social_data = social.get_comprehensive_social_data(
    topic="healthcare policy",
    domain="healthcare",
)

results = llm.generate_reasoning_with_recursion(
    domain="healthcare",
    initial_context={
        "population": 331000000,
        "social_data": social_data,
    },
    include_state_county_rep=True,
)
```

### Integration with Decision Engine

```python
from src.core.decision_engine import DecisionEngine

engine = DecisionEngine()

# National decision
decision = engine.make_decision(
    policy_id="healthcare_policy",
    region_id="US",  # Entire country
)

# State-level decision
decision = engine.make_decision(
    policy_id="healthcare_policy",
    region_id="CA",  # California
)

# County-level decision
decision = engine.make_decision(
    policy_id="healthcare_policy",
    region_id="Los Angeles County",  # Specific county
)
```

## Configuration Guide

### For Comprehensive Analysis
```python
results = llm.generate_reasoning_with_recursion(
    domain="healthcare",
    initial_context=context,
    max_depth=4,              # 5 levels
    subtopics_per_level=5,    # 5 subtopics per level
    include_state_county_rep=True,
)
```

### For Faster Results
```python
results = llm.generate_reasoning_with_recursion(
    domain="healthcare",
    initial_context=context,
    max_depth=2,              # 3 levels
    subtopics_per_level=3,    # 3 subtopics per level
    include_state_county_rep=False,  # National only
)
```

### For State-Level Policy
```python
results = llm.generate_reasoning_with_recursion(
    domain="healthcare",
    initial_context={
        **context,
        "region_type": "state",
        "state_abbreviation": "CA",
    },
    max_depth=3,
    subtopics_per_level=4,
    include_state_county_rep=True,
)
```

## Testing

### Run Demo
```bash
python3 demo_deep_recursive_investigation.py
```

### Run Tests
```bash
pytest tests/ -v
```

### Run Linting
```bash
ruff check src/ tests/
```

### Type Check
```bash
mypy src/ tests/
```

## Documentation Files

1. **DEEP_RECURSIVE_INVESTIGATION.md** - Comprehensive documentation
2. **IMPLEMENTATION_SUMMARY.md** - This file
3. **demo_deep_recursive_investigation.py** - Working demo script

## Files Modified

1. `src/llm/integration.py`
   - Enhanced `generate_reasoning_with_recursion()` method
   - Added geographic representation methods
   - Added weighted ranking methods
   - Fixed circular import issues

2. `src/core/decision_engine.py`
   - Enhanced `make_decision()` method
   - Added `_get_voters_for_region()` method

3. `src/utils/__init__.py`
   - Fixed imports to avoid circular dependency

4. `src/logging/` → `src/verbose_logging/`
   - Renamed to avoid conflict with Python's logging module

## Benefits

1. **Comprehensive Analysis**: Investigates domain from multiple angles
2. **Geographic Awareness**: Accounts for state and county variations
3. **Hierarchical Depth**: Multiple levels of recursion for thorough coverage
4. **Evidence-Based**: Synthesizes findings from extensive elaborations
5. **Geographic Weighting**: Prioritizes solutions based on geographic relevance
6. **Flexible Configuration**: Adjust depth and scope as needed
7. **Backward Compatible**: Existing code continues to work

## Future Enhancements

1. Parallel investigation of subtopics
2. Adaptive depth based on domain complexity
3. Dynamic geographic weighting
4. Multi-language support
5. Real-time updates and continuous investigation
6. Advanced clustering of similar subtopics
7. Confidence-based pruning of low-value paths
