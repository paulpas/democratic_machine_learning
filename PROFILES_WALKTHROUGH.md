# Profile System — Complete Walkthrough

The **profile system** lets you direct the Democratic Machine Learning System at any
policy topic — from the six built-in domains to completely arbitrary questions like
*"How should the US address the opioid crisis?"* — without modifying a single line of
code. This document walks through every capability with concrete examples and expected
output.

---

## Table of Contents

1. [Concepts in 60 Seconds](#concepts-in-60-seconds)
2. [Launching the Menu](#launching-the-menu)
3. [Menu Reference](#menu-reference)
4. [Walkthrough A — Running the Default Profile](#walkthrough-a--running-the-default-profile)
5. [Walkthrough B — Creating a Custom Topic Profile](#walkthrough-b--creating-a-custom-topic-profile)
6. [Walkthrough C — Editing a Profile](#walkthrough-c--editing-a-profile)
7. [Walkthrough D — Deleting a Custom Profile](#walkthrough-d--deleting-a-custom-profile)
8. [Running Profiles from the CLI (no menu)](#running-profiles-from-the-cli-no-menu)
9. [Profile YAML Reference](#profile-yaml-reference)
10. [Output Structure](#output-structure)
11. [Report Format](#report-format)
12. [Troubleshooting](#troubleshooting)

---

## Concepts in 60 Seconds

| Term | Meaning |
|------|---------|
| **Profile** | A YAML file in `config/profiles/` that names a set of topics and analysis settings |
| **Topic / Domain** | A policy subject to investigate (built-in or free-text) |
| **Geo fan-out** | When enabled, the LLM recursively analyses all 50 US states + 10 representative counties |
| **Depth** | Number of recursive investigation levels (2 = quick, 4 = production, 6 = exhaustive) |
| **Output sub-dir** | Each profile writes to `output/<profile-name>/` — results never overwrite each other |

The six **built-in domains** (economy, healthcare, education, immigration, climate,
infrastructure) are simply the defaults. **Any non-empty topic string is equally valid.**
The LLM does not know or care whether a topic is "official" — it researches whatever you
give it with the same rigour.

---

## Launching the Menu

```bash
just menu
```

Or without `just`:

```bash
uv run src/ui/profile_menu.py
```

The terminal clears and the following banner and menu appear:

```
╔══════════════════════════════════════════════════════════╗
║  Democratic Machine Learning System                      ║
║  Profile-based Topic Selection & Analysis Launcher       ║
╚══════════════════════════════════════════════════════════╝

Profiles available: 1

 Democratic Machine Learning System
 Profile Management Menu

  Arrow keys = navigate  ·  Enter = select  ·  Ctrl-C = exit

  ( ) Select profile and run analysis
  ( ) Create new profile
  ( ) View profile details
  ( ) Edit existing profile
  ( ) Delete custom profile
  ( ) List all profiles (table view)
  ( ) Exit

  [OK]    [Cancel]
```

Navigation is fully keyboard-driven:
- `↑` / `↓` — move between options
- `Space` — select/deselect a radio option
- `Enter` — confirm
- `Escape` or `Ctrl-C` — cancel / exit

---

## Menu Reference

| Option | Description |
|--------|-------------|
| **Select profile and run analysis** | Radiolist of all saved profiles → confirm settings → launches `run_all_domains.py` |
| **Create new profile** | 4-step wizard: name → description → topics → depth |
| **View profile details** | Rich table showing all fields of a chosen profile |
| **Edit existing profile** | Change one field at a time: description, depth, subtopics, geo, or topics |
| **Delete custom profile** | Removes a custom profile file (the `default` profile is protected) |
| **List all profiles** | Prints a summary table of every profile with domain list, depth, and geo setting |
| **Exit** | Closes the menu |

---

## Walkthrough A — Running the Default Profile

**Goal:** Run the full 6-domain production analysis using the `default` profile.

### Step 1 — Open the menu

```bash
just menu
```

### Step 2 — Select "Select profile and run analysis"

Navigate to the first option with `↓` (it is pre-selected) and press `Enter`.

A radiolist appears:

```
 Select Profile to Run

  Arrow keys = navigate  ·  Enter = confirm  ·  Esc = cancel

  (•) default
  ( ) my-opioid-study        ← any custom profiles you've created appear here

  [OK]    [Cancel]
```

`default` is pre-highlighted. Press `Enter`.

### Step 3 — Review the profile summary

A rich table is displayed:

```
         Profile: default
┌──────────────────────┬──────────────────────────────────────────────┐
│ Field                │ Value                                        │
├──────────────────────┼──────────────────────────────────────────────┤
│ Name                 │ default                                      │
│ Description          │ Full production analysis across all 6 policy │
│                      │ domains                                      │
│ Topics / Domains     │   • economy                                  │
│                      │   • healthcare                               │
│                      │   • education                                │
│                      │   • immigration                              │
│                      │   • climate                                  │
│                      │   • infrastructure                           │
│ Recursion Depth      │ 4                                            │
│ Subtopics / Level    │ 5                                            │
│ Geographic Scope     │ All 50 US states + counties                  │
│ Expert Allocation    │   economy: 12                                │
│                      │   healthcare: 10  …                          │
└──────────────────────┴──────────────────────────────────────────────┘
```

### Step 4 — Confirm

A confirmation dialog appears:

```
 Run Analysis: default

  Topics : economy, healthcare, education, immigration, climate, infrastructure
  Depth  : 4
  Geo    : All 50 states

  Launch full analysis pipeline now?

  [Run]    [Cancel]
```

Press `Enter` on **Run**. The menu exits and `run_all_domains.py` starts immediately,
printing real-time progress to the terminal.

### Step 5 — Watch the output

```
[12:00:01] ================================================================================
[12:00:01]   DEMOCRATIC MACHINE LEARNING SYSTEM  |  6 domains  |  started=2026-03-30 12:00:01
[12:00:01] ================================================================================
[12:00:01]   domains: ['economy', 'healthcare', 'education', 'immigration', 'climate', 'infrastructure']
[12:00:01]   output : output/default
[12:00:01]
[12:00:01]   Initialising LLM client ...
[12:00:02] ✅ LLM endpoint connected: http://localhost:8080
[12:00:02] ⚡ Parallel mode: 3 concurrent slots (llama-server --parallel 3)
[12:00:02]   est. total LLM calls : ~4,200 across 6 domain(s)
…
```

### Step 6 — Find the results

When complete, thesis documents are in:

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

---

## Walkthrough B — Creating a Custom Topic Profile

**Goal:** Analyse the US opioid crisis and AI governance policy — topics not in the
built-in six — at production depth across all 50 states.

### Step 1 — Open Create wizard

From the main menu, select **"Create new profile"** and press `Enter`.

### Step 2 — Name the profile (Step 1/4)

```
 Create Profile — Step 1/4: Name

  Enter a profile name (letters, numbers, hyphens only):
  > opioid-ai-study_
```

Type `opioid-ai-study` and press `Enter`. The name is normalised to lowercase; underscores
and hyphens are both permitted.

### Step 3 — Description (Step 2/4)

```
 Create Profile — Step 2/4: Description

  Brief description (press Enter to use default):
  > US opioid crisis and AI governance — comparative analysis
```

### Step 4 — Select topics (Step 3/4, Part 1)

A checkbox list of the six built-in domains appears. They are all pre-checked:

```
 Select Topics / Domains  (Step 1)

  Space = toggle  ·  Enter = confirm  ·  Esc = cancel

  [x] Economy
  [x] Healthcare
  [x] Education
  [x] Immigration
  [ ] Climate
  [ ] Infrastructure
```

Uncheck the domains you don't want (Space to toggle), then press `Enter`. For this
example, deselect all six (we'll use only custom topics).

### Step 5 — Add custom topics (Step 3/4, Part 2)

```
 Add Custom Topics?  (Step 2)

  Would you like to add custom free-text topics?

  Examples:
    opioid crisis, AI governance,
    housing affordability, water scarcity

  [Yes — add topics]    [No — continue]
```

Press `Enter` on **Yes**.

```
 Enter Custom Topics

  Type topic names separated by commas:
  > opioid crisis, AI governance
```

Type `opioid crisis, AI governance` and press `Enter`. These strings become your domains
verbatim.

### Step 6 — Recursion depth (Step 4/4)

```
 Create Profile — Step 4/4: Recursion Depth

  Recursion depth (higher = more thorough, more LLM calls):
    2 = quick exploration
    4 = full production (default)
    6 = exhaustive
  > 4_
```

Accept the default `4` by pressing `Enter`.

### Step 7 — Profile created

```
Profile 'opioid-ai-study' created successfully.

         Profile: opioid-ai-study
┌──────────────────────┬────────────────────────────────────┐
│ Name                 │ opioid-ai-study                    │
│ Topics / Domains     │   • opioid crisis                  │
│                      │   • AI governance                  │
│ Recursion Depth      │ 4                                  │
│ Geographic Scope     │ All 50 US states + counties        │
└──────────────────────┴────────────────────────────────────┘

 Run Now?

  Profile 'opioid-ai-study' is ready.
  Launch analysis now?

  [Run Now]    [Later]
```

Press **Run Now** to start immediately, or **Later** to return to the menu.

### Step 8 — Results

When the run completes:

```
output/opioid-ai-study/
├── us_opioid-crisis_governance_model.md
├── us_ai-governance_governance_model.md
└── session_summary.json
```

Each `.md` file is a full PhD-format report with Abstract, Methodology, 50-state
findings, Principal Thesis, and Policy Recommendations — exactly the same structure
as the built-in domain reports.

---

## Walkthrough C — Editing a Profile

**Goal:** Increase the recursion depth of `opioid-ai-study` from 4 to 6 for an exhaustive
analysis.

### Step 1 — Select "Edit existing profile"

From the main menu.

### Step 2 — Select the profile

```
 Edit Profile — Select

  ( ) default
  (•) opioid-ai-study

  [OK]    [Cancel]
```

### Step 3 — Choose the field

```
 Edit: opioid-ai-study

  Which field do you want to change?

  ( ) Description
  (•) Recursion depth  (current: 4)
  ( ) Subtopics per level  (current: 5)
  ( ) Geo fan-out  (current: enabled)
  ( ) Topics/Domains  (current: opioid crisis, AI governance)
```

Navigate to **Recursion depth** and press `Enter`.

### Step 4 — Enter new value

```
 Edit Depth

  New recursion depth (1–6):
  > 6_
```

Type `6`, press `Enter`. The profile is saved immediately.

```
Profile 'opioid-ai-study' updated.
```

---

## Walkthrough D — Deleting a Custom Profile

> The `default` profile **cannot** be deleted. This guard is intentional — the built-in
> six-domain profile is the system default and must always be available.

### Step 1 — Select "Delete custom profile"

Only non-default profiles are shown in the deletion list.

### Step 2 — Confirm

```
 Confirm Delete

  Permanently delete profile 'opioid-ai-study'?
  This cannot be undone.

  [Delete]    [Cancel]
```

Press **Delete**. The `config/profiles/opioid-ai-study.yaml` file is removed. Existing
output in `output/opioid-ai-study/` is **not** deleted — reports you already generated
are preserved.

---

## Running Profiles from the CLI (no menu)

The menu is not required. You can drive profiles entirely from the command line:

```bash
# Run a specific profile
just run --profile default
just run --profile opioid-ai-study

# Equivalent without just
uv run run_all_domains.py --profile opioid-ai-study

# Combine with other flags
uv run run_all_domains.py --profile default --no-resume
uv run run_all_domains.py --profile default --config configs/demo.yaml

# Show effective config for a profile run (does not start analysis)
uv run run_all_domains.py --profile default --show-config
```

---

## Profile YAML Reference

Every profile is a plain YAML file in `config/profiles/<name>.yaml`.
You can create or edit profiles by hand — the menu is just a convenience layer.

```yaml
# config/profiles/example.yaml

name: "example"                         # REQUIRED — must match the filename stem
description: "What this profile does"   # Optional human-readable summary

# ── Topics ───────────────────────────────────────────────────────────────────
# Any non-empty string is valid. Built-in names (economy, healthcare, …) map to
# pre-written context paragraphs in the report. Custom strings are analysed
# identically — the LLM researches them without restriction.
domains:
  - economy
  - healthcare
  - opioid crisis          # custom free-text topic
  - AI governance          # another custom topic

# ── Analysis depth ────────────────────────────────────────────────────────────
depth: 4                    # 1–6 (2=quick, 4=production default, 6=exhaustive)
subtopics_per_level: 5      # subtopics extracted per recursion level (1–10)

# ── Geographic scope ─────────────────────────────────────────────────────────
geo_fan_out: true           # true  = all 50 states + 10 representative counties
                            # false = national-level only (much faster)

# ── Expert allocation ────────────────────────────────────────────────────────
# Number of domain-expert voters in the deliberative panel per topic.
# Omit or leave empty {} to use config.yaml defaults (8 experts per domain).
expert_allocation:
  economy: 12
  healthcare: 10
  opioid crisis: 8          # custom topics use 8 if not specified

# ── LLM token budgets ────────────────────────────────────────────────────────
# Override per-call token limits for this profile.
# Omit or leave empty {} to use config.yaml defaults.
llm_budgets:
  max_tokens_default: 16384
  max_tokens_subtopic: 16384

# ── Social data collection ───────────────────────────────────────────────────
# Override social collection limits for this profile.
# Omit or leave empty {} to use config.yaml defaults.
social_collection:
  max_opinions: 15
  max_narratives: 12

# ── Metadata (informational only) ────────────────────────────────────────────
metadata:
  author: "Your Name"
  created: "2026-03-30"
  type: "custom"
  version: "1.0.0"
```

### Valid field summary

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | string | yes | — | Must match filename stem; letters, numbers, `-`, `_` |
| `description` | string | no | `""` | Human-readable label |
| `domains` | list[str] | yes | — | Any non-empty strings; ≥1 required |
| `depth` | int | no | `2` | Recursion levels; production = 4 |
| `subtopics_per_level` | int | no | `3` | Subtopics per level; production = 5 |
| `geo_fan_out` | bool | no | `true` | `true` = all 50 states |
| `expert_allocation` | dict | no | `{}` | `{domain: count}` |
| `llm_budgets` | dict | no | `{}` | Overrides `llm.*` config keys |
| `social_collection` | dict | no | `{}` | Overrides `social.*` config keys |
| `metadata` | dict | no | `{}` | Freeform; stored in report |

---

## Output Structure

Every profile writes to its own isolated sub-directory:

```
output/
├── default/
│   ├── us_economy_governance_model.md
│   ├── us_healthcare_governance_model.md
│   ├── us_education_governance_model.md
│   ├── us_immigration_governance_model.md
│   ├── us_climate_governance_model.md
│   ├── us_infrastructure_governance_model.md
│   └── session_summary.json
│
└── opioid-ai-study/
    ├── us_opioid-crisis_governance_model.md
    ├── us_ai-governance_governance_model.md
    └── session_summary.json
```

The `session_summary.json` records:
```json
{
  "started_at": "2026-03-30T14:00:00",
  "elapsed_seconds": 7342,
  "domains_processed": ["opioid crisis", "AI governance"],
  "domains_failed": [],
  "total_llm_calls": 840,
  "total_tokens": 1240000,
  "results": [
    {
      "domain": "opioid crisis",
      "outcome": "approved",
      "confidence": 0.847,
      "llm_calls": 420,
      "tokens": 620000,
      "elapsed": 3671
    }
  ]
}
```

---

## Report Format

Every `us_<topic>_governance_model.md` follows a rigorous academic structure:

| Section | Contents |
|---------|---------|
| **Title / Metadata table** | Domain, date, duration, LLM calls, tokens, voter count, outcome |
| **Abstract** | 2-paragraph summary of methodology, key finding, and confidence |
| **1. Introduction** | Policy context and research questions |
| **2. Methodology** | DML framework, data collection, decision mechanism, limitations |
| **3. Evidence Base** | Social data summary — Reddit opinions, media narratives, sentiment |
| **4. National-Level Findings** | LLM investigation at each recursive depth (national tier) |
| **5. State-Level Analysis** | Per-state findings for every subtopic at every depth (all 50 states) |
| **6. County-Level Analysis** | Urban / suburban / rural differentiation (10 counties) |
| **7. Progressive Synthesis** | Depth-by-depth conjecture chain (how evidence was rolled up) |
| **8. Principal Thesis** | The final LLM-synthesised policy thesis — full text |
| **9. Policy Recommendations** | Top-ranked solutions scored by tier weight × quality |
| **10. Democratic Deliberation** | Vote breakdown, trust scores, anti-pattern detection results |
| **11. Conclusions & Limitations** | Summary, future research directions, methodological caveats |
| **Technical Appendix** | Voter pool parameters, fairness metrics, LLM configuration |

This structure is identical whether the topic is a built-in domain like *economy* or a
custom topic like *opioid crisis*.

---

## Troubleshooting

### "Profile not found" error

```
ERROR: Profile not found: my-profile (expected at: config/profiles/my-profile.yaml)
```

The profile YAML file does not exist. Check:
1. The file is in `config/profiles/`, not `configs/` (note: no `s` on `config`)
2. The filename matches the `--profile` argument exactly (case-sensitive on Linux)
3. The YAML is valid — run `python3 -c "import yaml; yaml.safe_load(open('config/profiles/my-profile.yaml'))"` to check

### "Profile failed validation" error

The profile has structural problems. Common causes:
- `domains` key is missing or empty
- A domain entry is an empty string (`""`)
- `depth` is 0 or negative

### Analysis never calls the LLM

If you see `⏩ DOMAIN X fully complete — synthesis checkpoint found`, an existing
checkpoint is being reused. Force a fresh run:

```bash
just run --profile my-profile --no-resume
# or
just clean-checkpoints
```

### Custom topics produce thin reports

Custom topics do not have the pre-written introduction paragraphs that built-in domains
have. The Abstract and Introduction will use a generic template. All LLM-generated
content (state findings, thesis, recommendations) is just as deep as for built-in domains.
To improve the introduction, edit the generated `.md` file directly, or add a custom
`description` field to the profile.

### "Geo fan-out is slow"

`geo_fan_out: true` (all 50 states) is the production default and is intentional —
geographic breadth is a core feature. For quick iteration, set it to `false`:

```yaml
geo_fan_out: false   # national analysis only; ~50× fewer LLM calls
depth: 2             # combine with reduced depth for a very fast prototype run
```

Or use the demo config:

```bash
just demo-run        # 30 s — depth=1, 1 subtopic, no geo fan-out
```
