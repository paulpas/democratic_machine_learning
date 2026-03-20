# AGENTS.md

## Build/Lint/Test Commands

```bash
# Run all tests with coverage
pytest --cov=. --cov-report=term-missing --cov-report=xml --cov-fail-under=95 tests/

# Run a single test file
pytest tests/test_module.py

# Run a single test
pytest tests/test_module.py::test_function_name

# Lint with ruff
ruff check src/ tests/

# Type check
mypy src/ tests/

# Format code
ruff format src/ tests/

# All checks
make check  # or make test
```

## Code Style Guidelines

### General
- Python 3.11+ with type hints
- Follow PEP 8 with ruff formatting
- 100% test coverage minimum (95% for integration tests)
- TDD: write tests before implementation

### Imports
- Absolute imports only
- Group: stdlib, third-party, local
- Use `from package import Module` not `import package.module`

### Naming
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`
- Types: `PascalCase` with `Type` suffix if needed

### Types
- Always type hint function signatures
- Use `typing` module: `List`, `Dict`, `Optional`, `Union`, `Callable`
- Use `Literal` for fixed options
- Use `Protocol` for duck-typed interfaces

### Error Handling
- Custom exception classes in `src/exceptions.py`
- Use specific exceptions, not generic `Exception`
- Log errors with context
- Never swallow exceptions silently

### Testing
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Mock external dependencies
- Test edge cases and error paths
- Use pytest fixtures for test data

### Documentation
- Docstrings in Google style
- Exported functions need docstrings
- Complex logic needs inline comments
- Update README for new features

### File Structure
```
src/
  __init__.py
  core/
    decision_engine.py
    weighting_system.py
    policy_cell.py
    feedback_loop.py
  data/
    data_loader.py
    preprocessing.py
    feature_engineer.py
  models/
    voter.py
    policy.py
    region.py
    decision.py
  ui/
    tui.py
    display.py
  utils/
    metrics.py
    validation.py
    logging.py
  security/
    trust_system.py
  __init__.py
tests/
  unit/
  integration/
  fixtures/
```

## TUI Output Guidelines
- Use `rich` library for formatted output
- Progress indicators with `rich.progress`
- Tables with `rich.table`
- Color-coded status (green=success, yellow=warning, red=error)
- Interactive prompts with `rich.prompt`

## Political Science Framework
- Reference historical systems: Athenian democracy, Roman Republic, representative democracies
- Incorporate: Condorcet paradox, Arrow's impossibility theorem, approval voting
- Multi-tiered representation with adaptive weighting
- Fairness metrics: proportional representation, minority protection, geographic balance

## Security & Trust Framework
- **Malicious Influence Protection**:
  - Bot detection for automated accounts
  - Manipulation detection for coordinated influence campaigns
  - Source verification for data provenance
  - Evidence cross-referencing across multiple sources
  - Temporal validation to detect sudden anomalies
  
- **Trust Scoring**:
  - Base trust score with expertise boosts
  - Consistency tracking for preference stability
  - Participation history weighting
  - Evidence quality assessment
  
- **Social Influence Analysis**:
  - Bot score calculation based on behavior patterns
  - Manipulation detection for suspicious preferences
  - Influence network mapping
  - Coordinated manipulation detection

## Environmental & Geographic Factors
- **Geographic Weighting**:
  - Direct impact voters get higher weight
  - Regional representation across tiers
  - Geographic diversity in decision-making
  
- **Climate Impact Assessment**:
  - Climate vulnerability scoring per region
  - Environmental policy impact analysis
  - Geographic risk factors in decision models
  
- **Demographic Considerations**:
  - Population density weighting
  - Urban/rural balance
  - Regional economic factors
  - Cultural diversity metrics

## Core Principles
1. **Adaptive Weighting**: Voter weights based on expertise, proximity, participation
2. **Multi-Tiered Representation**: County → State → National feedback loop
3. **Fairness Constraints**: Minimum 30% group satisfaction, max 40% disparity
4. **Feedback Loop**: Continuous learning and weight adjustment
5. **Security First**: Malicious influence detection and mitigation
6. **Environmental Context**: Geography and climate as decision factors

## Data Sources
- Public polling and elections (realistic, existing data)
- Synthetic population simulation (controlled experiment)
- Social media sentiment (with manipulation detection)
- Economic indicators
- Climate and geographic data

## Decision-Making Approaches
- **Hierarchical Representation**: Multi-tiered weighted voting
- **Liquid Democracy**: Delegative voting with dynamic delegation
- **Predictive Consensus**: ML predicts optimal policy with minority protection
- **Hybrid Approach**: Combine multiple mechanisms with adaptive weighting

## Key Metrics
- Fairness Score (0-1): Variance-based voter satisfaction
- Consensus Score (0-1): Support percentage threshold
- Trust Score (0-1): Weighted by expertise, consistency, participation
- Geographic Balance: Regional representation ratio
- Climate Impact Index: Environmental effect per policy
