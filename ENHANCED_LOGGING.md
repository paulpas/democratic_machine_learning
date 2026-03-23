# Deep Recursive LLM Investigation - Enhanced Logging

## Overview

The Deep Recursive LLM Investigation system now features comprehensive stdout logging that tracks every LLM call, domain investigation, subtopic analysis, and geographic tier examination.

## Logging Features

### 1. Session-Level Logging

```
╔==============================================================================╗
║                                                                              ║
║                   🌐 DEEP RECURSIVE LLM INVESTIGATION SESSION                 ║
║                                                                              ║
╚==============================================================================╝

📋 SESSION INFO:
   Domain: healthcare
   Started: 2026-03-22 13:41:40
```

### 2. Configuration Overview

```
================================================================================
🔄 INITIATING DEEP RECURSIVE LLM INVESTIGATION OF DOMAIN: healthcare
================================================================================
📊 Configuration:
   - Max Depth: 3
   - Subtopics per Level: 3
   - State/County Representation: YES
```

### 3. Level-by-Level Investigation

```
╔==============================================================================╗
║  📊 LEVEL 0: Initial Domain Investigation - healthcare                         ║
║  🌍 Tier: NATIONAL                                                             ║
╚==============================================================================╝
   Investigating domain: healthcare
   Population: 331,000,000

   Research Questions: 5
   Max Tokens: 2048
   Principles: 7
```

### 4. LLM Call Details

```
  📊 LLM CALL: Domain 'healthcare' | Tier 'national' | Depth '0'
  📝 Research Questions: 5
  📝 Prompt length: 1116 characters
  🎯 Max tokens: 2048
  🚀 Sending request to http://localhost:8080/completion
  ✅ LLM RESPONSE: 0 tokens generated
```

### 5. Subtopic Investigation

```
────────────────────────────────────────────────────────────────────────────────
🔍 SUBTOPIC 1/1: Domain
────────────────────────────────────────────────────────────────────────────────
   Domain: healthcare
   Depth: 1/3
   Population Context: 331,000,000
```

### 6. Geographic Tier Analysis

```
   📍 TIER 1/3: NATIONAL
      Investigating: Domain
      Population: 331,000,000
      Questions: 5
      Max Tokens: 1536

      🚀 INITIATING LLM CALL...

  📊 LLM CALL: Domain 'healthcare' | Tier 'national' | Depth '1'
  🔍 Subtopic: Domain
  📝 Research Questions: 5
  📝 Prompt length: 1079 characters
  🎯 Max tokens: 1536
  🚀 Sending request to http://localhost:8080/completion
  ✅ LLM RESPONSE: 0 tokens generated

     📋 ELABORATION: Domain 'healthcare' | Subtopic 'Domain' | Tier 'national'
     📊 Depth: 1/3
     🚀 INITIATING LLM CALL...
      ✅ COMPLETE: Elaboration generated (0 chars)
```

### 7. Conjecture Formation

```
  🧠 CONJECTURE FORMATION: Domain 'healthcare'
  📝 Question: Optimal healthcare governance approach
  📊 Evidence Items: 0
  📝 Prompt length: 385 characters
  🎯 Max tokens: 1536
  🚀 Sending request to http://localhost:8080/completion
```

### 8. Solution Ranking

```
  ⚖️  RANKING SOLUTIONS
  🌍 With Geographic Weighting
   Domain: healthcare
   Total Elaborations: 0
   Geographic Tiers: 0

   🚀 INITIATING SOLUTION RANKING...
```

### 9. Investigation Summary

```
╔==============================================================================╗
║  📋 INVESTIGATION SUMMARY                                                      ║
╚==============================================================================╝
   Domain: healthcare
   Levels Investigated: 4
   Geographic Tiers: 3
   Total Subtopics: 1
   Total Elaborations: 3
   Top Solutions Identified: 0

   🎯 Top Solution: N/A
   📈 Confidence: 0.750

   Completed: 2026-03-22 13:41:45
```

## Logging Hierarchy

```
SESSION
├── Domain
├── Timestamp
└── Configuration
    ├── Max Depth
    ├── Subtopics per Level
    └── Geographic Representation

LEVEL
├── Level Number
├── Geographic Tier
├── Domain
├── Population
├── Research Questions
└── Tokens Configuration

LLM CALL
├── Domain
├── Tier
├── Depth
├── Subtopic
├── Research Questions Count
├── Prompt Length
├── Max Tokens
└── Request Status

ELABORATION
├── Domain
├── Subtopic
├── Tier
├── Depth
├── Status
└── Output Size

SYNTHESIS
├── Total Elaborations
├── Geographic Tiers
├── Evidence Items
└── Conjecture Confidence

SUMMARY
├── Domain
├── Levels Investigated
├── Geographic Tiers
├── Total Subtopics
├── Total Elaborations
├── Top Solutions
├── Final Confidence
└── Timestamp
```

## Implementation Details

### Enhanced Logging Methods

1. **`generate_reasoning_with_recursion()`**
   - Session header with domain and timestamp
   - Configuration summary
   - Level headers with geographic tier info
   - LLM call details per domain/tier/depth
   - Subtopic investigation details
   - Elaboration status
   - Final conjecture and ranking logs

2. **`generate_reasoning()`**
   - Domain, tier, depth context
   - Subtopic being investigated
   - Research questions count
   - Prompt length
   - Max tokens
   - Request status
   - Response preview

3. **`form_conjecture()`**
   - Domain being analyzed
   - Question being answered
   - Evidence items count
   - Prompt length
   - Max tokens
   - Request status

4. **`_elaborate_on_subtopic_with_tier()`**
   - Domain, subtopic, tier context
   - Current depth
   - Request status

### Fallback Handling

When LLM returns empty response:

```
  ⚠️  LLM returned empty response, using fallback subtopics
```

Domain-specific fallback subtopics are used:
- Healthcare: "policy frameworks", "implementation strategies", "stakeholder engagement", "regulatory oversight", "performance metrics"
- Economy: "fiscal policy", "monetary policy", "trade policy", "labor markets", "economic growth"
- Education: "curriculum standards", "funding models", "teacher training", "student outcomes", "accessibility"
- Immigration: "border control", "visa policies", "citizenship", "refugee policy", "integration programs"
- Climate: "emission reduction", "renewable energy", "adaptation strategies", "conservation", "regulatory frameworks"
- Infrastructure: "transportation", "utilities", "digital infrastructure", "resilience planning", "maintenance"

## Usage Example

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
    subtopics_per_level=3,
    include_state_county_rep=True,
)
```

## Output File

The logging output is displayed to stdout. To save to a file:

```bash
python3 demo_deep_recursive_investigation.py > investigation_log.txt 2>&1
```

## Benefits

1. **Transparency**: Every LLM call is logged with full context
2. **Debugging**: Easy to identify which domain/subtopic/tier is having issues
3. **Monitoring**: Track investigation progress in real-time
4. **Auditing**: Complete record of all LLM calls for compliance
5. **Performance**: Identify slow or problematic investigations

## Future Enhancements

1. Add logging to file with rotation
2. Add JSON logging for programmatic parsing
3. Add timing information per LLM call
4. Add error tracking and alerting
5. Add progress bar for long investigations
