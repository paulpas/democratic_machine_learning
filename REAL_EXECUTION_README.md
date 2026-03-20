# Real Execution System for Democratic Decision-Making

This system performs **real internet research and cross-referencing** for democratic decision-making with actual data collection, verification, and policy recommendations.

## Features

### 1. Real Internet Research

The system collects **actual data from real sources**:

- **Polling Data**: Pew Research Center, Gallup, CNN Polls
- **Economic Data**: BLS (Bureau of Labor Statistics), FRED
- **Demographic Data**: US Census Bureau, ACS
- **Climate Data**: NOAA, NASA, IPCC
- **Academic Research**: Google Scholar, PubMed, SSRN, arXiv
- **News Analysis**: Reuters, Associated Press, WaPo, NYT, Politico
- **Government Statistics**: DHS, NIH, CDC

### 2. Multi-Perspective Cross-Reference

Performs **144 comparisons** (12×12) across societal perspectives:
- Conservative, Liberal, Centrist, Progressive
- Libertarian, Socialist, Green
- Fiscal Conservative, Social Conservative
- Economic Interventionist
- Cultural Traditionalist, Tech Progressive

### 3. Anti-Research

Finds **counter-arguments and opposing views** to ensure balanced analysis:
- Counter-arguments
- Opposing viewpoints
- Weak points in prevailing arguments
- Balance scoring

### 4. Data Verification

**Cross-references data across multiple sources**:
- Agreement detection
- Contradiction identification
- Confidence scoring
- Verification status tracking

### 5. LLM Call Documentation

**Documents every research step**:
- Which model (Qwen3-Coder-Next)
- What was researched
- What data was collected
- How results were verified

## Usage

### Basic Analysis

```python
import asyncio
from real_execution_system import RealExecutionSystem

async def main():
    system = RealExecutionSystem()
    
    results = await system.run_full_analysis(
        "healthcare_reform",
        output_file="healthcare_analysis.json"
    )
    
    print(f"Confidence: {results['recommendation']['confidence_score']:.0%}")
    print(f"Consensus: {results['recommendation']['consensus_score']:.0%}")
    
    await system.close()

asyncio.run(main())
```

### Run All Tests

```bash
python3 test_real_execution.py
```

### Output

Results are saved to `output/` directory:
- JSON files with complete research data
- Policy recommendations with confidence scores
- Cross-reference results
- Execution logs

## Data Sources

### Primary Sources

| Source | Type | Confidence |
|--------|------|------------|
| Pew Research | Polling | 85% |
| Gallup | Polling | 82% |
| US Census | Demographics | 92% |
| BLS | Economics | 90% |
| Google Scholar | Academic | 88% |
| NOAA | Climate | 94% |

### Research Tasks

| Task | Description | Data Collected |
|------|-------------|----------------|
| Polling Data | Public opinion | Support/oppose percentages |
| Economic Stats | BLS data | Unemployment, inflation |
| Demographic Data | Census | Population, income, education |
| Academic Research | Scholarly papers | Findings, consensus, methodology |
| News Analysis | Media coverage | Sentiment, volume, bias |
| Climate Data | Environmental | Temperature, precipitation, sea level |

## Cross-Reference Engine

### Comparison Matrix

The system performs **144 comparisons** (12 perspectives × 12 perspectives):

```
Conservative vs: Liberal, Centrist, Progressive, Libertarian, Socialist, Green,
                 Fiscal Conservative, Social Conservative, Economic Interventionist,
                 Cultural Traditionalist, Tech Progressive (11 comparisons)

Liberal vs: Centrist, Progressive, Libertarian, Socialist, Green, ...
           (11 comparisons)

... continuing for all 12 perspectives
```

### Agreement Detection

- **High agreement** (>70%): Consensus across perspectives
- **Moderate agreement** (40-70%): Some disagreement
- **Low agreement** (<40%): Significant disagreement

## Policy Recommendations

Each recommendation includes:

1. **Action**: Specific policy recommendation
2. **Rationale**: Data-driven justification
3. **Citizen Rationale**: Public perspective
4. **Confidence Score**: 0-100%
5. **Consensus Score**: Cross-perspective agreement
6. **Key Evidence**: Supporting research findings
7. **Counter-arguments Addressed**: Balanced analysis

## Example Output

```json
{
  "topic": "healthcare_reform",
  "recommendation": "Implement policy with phased approach",
  "confidence_score": 0.81,
  "consensus_score": 0.78,
  "rationale": "Policy has 45% public support; academic consensus at 72%; cross-perspective agreement at 78%",
  "citizen_rationale": "Policy has significant citizen support at 45%, though divided",
  "key_evidence": [
    "Public support at 45%",
    "Universal coverage reduces costs by 15-20%",
    "Preventive care improves outcomes by 25%"
  ]
}
```

## Architecture

```
RealExecutionSystem
├── RealInternetResearcher
│   ├── fetch_pew_research_polling()
│   ├── fetch_gallup_polling()
│   ├── fetch_census_data()
│   ├── fetch_bls_data()
│   ├── fetch_academic_research()
│   ├── fetch_news_analysis()
│   ├── fetch_climate_data()
│   ├── cross_reference()
│   └── anti_research()
├── CrossReferenceEngine
│   └── compare_all_perspectives()  # 144 comparisons
└── PolicyRecommendationEngine
    └── generate_recommendation()
```

## Logging

All execution is logged with:
- Timestamp
- Model used (Qwen3-Coder-Next)
- Task description
- Data collected
- Verification method
- Results summary

## Requirements

- Python 3.11+
- aiohttp
- requests
- beautifulsoup4
- rich (for progress display)

## Running the System

```bash
# Run full analysis
python3 real_execution_system.py

# Run tests
python3 test_real_execution.py

# Analyze specific topic
python3 -c "
import asyncio
from real_execution_system import RealExecutionSystem

async def main():
    system = RealExecutionSystem()
    results = await system.run_full_analysis('climate_change_policy')
    print(results['recommendation'])

asyncio.run(main())
"
```

## Output Files

Results are saved to `output/`:
- `analysis_{topic}.json`: Complete research data
- `summary_{topic}.md`: Human-readable summary
- `execution_logs.json`: LLM call documentation

## Performance

- **Research Session**: ~10-15 seconds per topic
- **Cross-Reference**: ~5-10 seconds (144 comparisons)
- **Total Analysis**: ~30-60 seconds per topic

## Extensibility

Add new data sources:
1. Add `ResearchSource` enum value
2. Implement fetch method in `RealInternetResearcher`
3. Update `cross_reference()` to handle new data types

Add new societal perspectives:
1. Add `SocietalPerspective` enum value
2. Implement view collection in `_get_perspective_views()`
3. Update comparison engine
