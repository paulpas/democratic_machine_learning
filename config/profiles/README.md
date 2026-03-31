# Policy Domain Profiles

This directory contains YAML configuration files that define which policy
domains to analyze and how to configure each analysis.

## Overview

A **profile** is a reusable configuration that specifies:
- Which policy domains to analyze (e.g., economy, healthcare)
- Recursion depth for LLM investigation
- Number of subtopics per level
- Geographic fan-out settings
- LLM token budgets
- Expert allocation per domain
- Social data collection limits

## Default Profile

The `default.yaml` profile provides full production analysis across all 6
policy domains:

- **economy**
- **healthcare**
- **education**
- **immigration**
- **climate**
- **infrastructure**

It uses:
- Depth 4 recursion
- 5 subtopics per level
- Full geographic fan-out (all 50 states + counties)
- Production LLM budgets (16K tokens per call)

## Profile Structure

Each profile YAML file has the following structure:

```yaml
name: "profile-name"
description: "Brief description of this profile"

# Policy domains to analyze
domains:
  - economy
  - healthcare
  # ... more domains

# Analysis depth (number of recursive levels)
depth: 4

# Number of subtopics to extract at each level
subtopics_per_level: 5

# Geographic fan-out
geo_fan_out: true

# Expert allocation per domain
expert_allocation:
  economy: 12
  healthcare: 10
  # ... more domains

# LLM token budgets
llm_budgets:
  max_tokens_default: 16384
  max_tokens_subtopic: 16384

# Social data collection limits
social_collection:
  max_opinions: 15
  max_narratives: 12

# Metadata
metadata:
  author: "Your Name"
  created: "2026-03-30"
  type: "custom"
```

## Valid Domains

The following policy domains are supported:

| Domain | Description |
|--------|-------------|
| economy | Economic policy, fiscal management, labor markets |
| healthcare | Healthcare systems, insurance, public health |
| education | K-12, higher education, curriculum policy |
| immigration | Border policy, visas, integration |
| climate | Environmental policy, climate change mitigation |
| infrastructure | Transportation, utilities, broadband |

## Usage

### Run with Default Profile

```bash
just run
```

This runs the default profile, analyzing all 6 domains.

### Run with Specific Profile

```bash
just run --profile custom-analysis
```

This uses the profile defined in `config/profiles/custom-analysis.yaml`.

### List Available Profiles

```bash
python3 -m src.ui.profile_menu
```

This opens an interactive menu to view, create, edit, and delete profiles.

### Create a New Profile

Use the interactive menu:

```bash
just menu
```

Or create manually by copying `default.yaml` and modifying it.

## Output Structure

When running with profile `<name>`, output files are written to:

```
output/<name>/
  ├── us_<domain>_governance_model.md   # Per-domain analysis
  └── session_summary.json              # Run metadata
```

Example for default profile:

```
output/default/
  ├── us_economy_governance_model.md
  ├── us_healthcare_governance_model.md
  ├── us_education_governance_model.md
  ├── us_immigration_governance_model.md
  ├── us_climate_governance_model.md
  ├── us_infrastructure_governance_model.md
  └── session_summary.json
```

## Profile Management

### Using the Interactive Menu

```bash
python3 -m src.ui.profile_menu
```

Commands:
- **Select existing profile** — Choose a profile to run
- **Create new profile** — Define custom domain set and settings
- **Edit profile** — Modify existing profile configuration
- **Delete profile** — Remove custom profiles (cannot delete default)
- **Run analysis with profile** — Execute analysis with selected profile
- **Exit** — Close the menu

### Programmatic API

```python
from src.ui.profile_loader import load_profile, list_available_profiles
from src.ui.profile_manager import create_profile, update_profile, delete_profile

# List all profiles
profiles = list_available_profiles()

# Load a profile
profile = load_profile("default")

# Create a new profile
profile = create_profile(
    name="custom",
    domains=["economy", "healthcare"],
    config_overrides={"depth": 3}
)

# Update a profile
profile = update_profile("custom", {"depth": 4})

# Delete a profile
deleted = delete_profile("custom")
```

## Best Practices

1. **Start Simple**: Begin with shallow depth (2) and few subtopics (2-3) for
   testing, then increase for full analysis

2. **Geographic Scope**: Set `geo_fan_out: false` for national-only analysis
   to save LLM tokens and time

3. **Expert Allocation**: Adjust experts_per_domain based on available
   computational resources (more experts = more LLM calls)

4. **Social Data**: Reduce `max_opinions` and `max_narratives` for faster
   iteration during development

5. **Version Control**: Keep profiles in the `config/profiles/` directory
   under version control for reproducibility

## Example Custom Profiles

### Quick Demo Profile (config/profiles/demo.yaml)

```yaml
name: "demo"
description: "Quick smoke-test with minimal domains and depth"
domains:
  - economy
depth: 1
subtopics_per_level: 1
geo_fan_out: false
expert_allocation:
  economy: 4
llm_budgets:
  max_tokens_default: 1024
social_collection:
  max_opinions: 3
  max_narratives: 2
metadata:
  type: "demo"
```

### State-Focused Profile (config/profiles/healthcare_ca.yaml)

```yaml
name: "healthcare_ca"
description: "Healthcare policy analysis for California only"
domains:
  - healthcare
depth: 3
subtopics_per_level: 3
geo_fan_out: true
expert_allocation:
  healthcare: 10
llm_budgets:
  max_tokens_default: 16384
social_collection:
  max_opinions: 20
  max_narratives: 15
metadata:
  region: "California"
  type: "state-specific"
```

## Troubleshooting

### Profile Not Found

Ensure the profile file exists in `config/profiles/<name>.yaml` and has
valid YAML syntax.

### Validation Errors

Check that:
- All domains are valid (see valid domains table)
- Depth and subtopics_per_level are positive integers
- Names contain only alphanumeric characters and hyphens

### Too Many LLM Calls

Reduce:
- `depth` (fewer recursive levels)
- `subtopics_per_level` (fewer subtopics per level)
- `geo_fan_out` (set to false for national-only)
- `expert_allocation` values (fewer domain experts)

## License

Part of the Democratic Machine Learning System.
See the main repository for license information.
