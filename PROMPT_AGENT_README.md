# Prompt Agent - Automated Prompt Engineering

## Overview

The **Prompt Agent** is a meta-learning component that analyzes datasets to discover patterns and automatically generate optimized prompts for the Estimator Agent.

### Problem It Solves

Manually crafting prompts by analyzing data and identifying patterns is time-consuming:
- FRESCO (12 classes): Took multiple iterations to discover patterns
- ACORN (22 classes): Would take even longer manually
- New datasets: Start from scratch each time

**Solution:** Let an AI agent discover the patterns and generate prompts automatically!

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     PROMPT AGENT WORKFLOW                    │
└──────────────────────────────────────────────────────────────┘

INPUT: Quantitative Data (CSVs) + Qualitative Data (Text)
   │
   ▼
┌─────────────────────────────────────────┐
│ STEP 1: Aggregate Quantitative Data    │
│ - Load all class CSVs                  │
│ - Find high-variance questions         │
│ - Calculate statistics by category     │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│ STEP 2: Aggregate Qualitative Data     │
│ - Load all pen portraits               │
│ - Extract key themes                   │
│ - Identify demographic descriptions    │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│ STEP 3: Discover Demographic Patterns  │  ← LLM Analysis (GPT-5)
│ - Income patterns (wealthy vs poor)    │
│ - Age patterns (young vs elderly)      │
│ - Lifestyle patterns (urban vs rural)  │
│ - Key differentiators                  │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│ STEP 4: Discover Concept Patterns      │  ← LLM Analysis (GPT-5)
│ - Attitude vs behavior patterns        │
│ - Low-friction vs high-friction        │
│ - Identity statement patterns          │
│ - Category-specific patterns           │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│ STEP 5: Generate Baseline Prompt       │  ← LLM Synthesis (GPT-5)
│ - Decision workflow (8 steps)          │
│ - Concept type classification          │
│ - Demographic calibrations             │
│ - Proximal guardrails                  │
│ - Evidence hierarchy                   │
│ - Output format                        │
└─────────────────────────────────────────┘
   │
   ▼
OUTPUT:
- Generated baseline prompt (general for all classes)
- 22 class-specific prompts (demographic calibrations)
- Analysis results (JSON)
```

## Components

### 1. PromptAgent Class

**Location:** `agent_estimator/prompt_agent/analyzer.py`

**Key Methods:**

```python
class PromptAgent:
    def analyze_dataset(quant_dir, qual_dir) -> Dict:
        """Full dataset analysis -> patterns + prompt"""

    def _aggregate_quantitative(quant_dir) -> Dict:
        """Analyze all quantitative CSVs"""

    def _aggregate_qualitative(qual_dir) -> Dict:
        """Analyze all pen portraits"""

    def _discover_demographic_patterns(...) -> Dict:
        """LLM discovers demographic patterns"""

    def _discover_concept_patterns(...) -> Dict:
        """LLM discovers concept-type patterns"""

    def _generate_prompt(...) -> str:
        """LLM generates final prompt"""

    def generate_demographic_specific_prompt(class_name, ...) -> str:
        """Generate prompt for single class"""
```

### 2. Runner Script

**Location:** `run_prompt_discovery_ACORN.py`

Convenience script that:
- Runs full analysis on ACORN dataset
- Generates baseline + 22 class prompts
- Saves results to `ACORN_prompt_analysis/`

## Usage

### Quick Start

```bash
cd "c:\Users\d.zhang\Desktop\Experiments"

# Ensure GPT-5 API key is set
# In .env: OPENAI_API_KEY=...

# Run discovery
./venv/Scripts/python.exe run_prompt_discovery_ACORN.py
```

**Estimated time:** 5-10 minutes (depends on API speed)

### Programmatic Usage

```python
from pathlib import Path
from agent_estimator.prompt_agent.analyzer import PromptAgent

# Initialize
agent = PromptAgent(model="gpt-5")

# Analyze dataset
results = agent.analyze_dataset(
    quant_dir=Path("demographic_runs_ACORN/exclusive_addresses/Flattened Data Inputs"),
    qual_dir=Path("demographic_runs_ACORN/exclusive_addresses/Textual Data Inputs"),
    output_file=Path("prompt_analysis/results.json")
)

# Access discovered patterns
demographic_patterns = results["demographic_patterns"]
concept_patterns = results["concept_patterns"]
generated_prompt = results["generated_prompt"]

# Generate class-specific prompt
class_prompt = agent.generate_demographic_specific_prompt(
    class_name="exclusive_addresses",
    quant_csv=Path("...csv"),
    qual_txt=Path("...txt")
)
```

## Output Files

### 1. analysis_results.json

Complete analysis results:

```json
{
  "demographic_patterns": {
    "income_patterns": {
      "high_income": "Wealthy demographics show +20pp for premium concepts",
      "low_income": "Budget demographics show +25pp for price sensitivity"
    },
    "age_patterns": {
      "young": "Digital behaviors LIFT +15-20pp",
      "elderly": "Digital behaviors REDUCE -25-30pp"
    },
    "lifestyle_patterns": {...},
    "key_differentiators": ["income", "age", "location"]
  },
  "concept_patterns": {
    "attitude_pattern": {
      "description": "...",
      "distribution_template": "SA 10-18%, A 22-30%, ...",
      "calibration_rules": [...]
    },
    "behavior_low_friction": {...},
    "behavior_high_friction": {...},
    "identity_pattern": {...}
  },
  "generated_prompt": "SYSTEM PROMPT: You are predicting...",
  "quantitative_summary": {...},
  "qualitative_summary": {...}
}
```

### 2. generated_baseline_prompt.txt

The baseline prompt to use in `agent_estimator/estimator_agent/prompts.py`:

```
SYSTEM PROMPT: You are predicting survey responses...

DECISION WORKFLOW:
Step 1: ...
Step 2: ...
...

CONCEPT TYPE CLASSIFICATION:
- Attitude: keywords "I think", "I believe"...
- Behavior: keywords "I use", "I do"...
...

DEMOGRAPHIC CALIBRATIONS:
- High income demographics: +20pp for premium concepts
- Young demographics: +15pp for digital behaviors
...

PROXIMAL GUARDRAILS:
If proximal data ≥80%: predict 75-95%
...
```

### 3. class_specific_prompts.json

22 demographic-specific prompts:

```json
{
  "exclusive_addresses": "[Profile]\nUltra-wealthy...\n[Calibrations]\n...",
  "flourishing_capital": "...",
  ...
}
```

## Integration with Estimator

### Step 1: Review Generated Prompt

```bash
cat ACORN_prompt_analysis/generated_baseline_prompt.txt
```

Review for:
- ✅ Logical structure
- ✅ Specific calibrations (not vague)
- ✅ Actionable rules

### Step 2: Integrate Baseline Prompt

Edit `agent_estimator/estimator_agent/prompts.py`:

```python
# Replace or update GENERAL_SYSTEM_PROMPT
GENERAL_SYSTEM_PROMPT = """
[Paste generated baseline prompt here]
"""
```

### Step 3: Add Class-Specific Prompts

```python
# Load class prompts
import json
with open('ACORN_prompt_analysis/class_specific_prompts.json') as f:
    acorn_prompts = json.load(f)

# Add to DEMOGRAPHIC_PROMPTS
DEMOGRAPHIC_PROMPTS.update(acorn_prompts)

# Or selectively add:
DEMOGRAPHIC_PROMPTS["exclusive_addresses"] = acorn_prompts["exclusive_addresses"]
DEMOGRAPHIC_PROMPTS["flourishing_capital"] = acorn_prompts["flourishing_capital"]
# ... etc
```

### Step 4: Test Predictions

```bash
python run_ACORN_single_class.py exclusive_addresses
```

### Step 5: Evaluate and Iterate

```python
# Compare predictions vs ground truth
# If errors high:
#   - Refine prompts manually
#   - Or re-run Prompt Agent with feedback
```

## Why This Works

### 1. Meta-Learning

The Prompt Agent learns "how to learn" by:
- Analyzing patterns across ALL classes at once
- Identifying what distinguishes demographics
- Discovering concept-response patterns

### 2. Leverage GPT-5's Power

GPT-5 (or other powerful models):
- Can analyze large amounts of data
- Understands nuanced patterns
- Generates coherent, structured prompts

### 3. Automated RL "Iteration 0"

Instead of:
1. Run baseline → 2. Manual error analysis → 3. Manual prompt updates

We get:
1. **Automated pattern discovery** → Generated prompts → Run predictions

This gives us a strong starting point, reducing manual RL iterations from 5-7 to 2-3.

## Advanced Usage

### Custom Pattern Discovery

Provide custom analysis prompts:

```python
agent = PromptAgent(model="gpt-5")

# Override discovery method
custom_prompt = """
Analyze this data focusing on:
1. Environmental attitudes by income
2. Digital adoption by age
3. Brand loyalty patterns
...
"""

patterns = agent._discover_demographic_patterns(
    quant_summary,
    qual_summary,
    custom_analysis_prompt=custom_prompt  # (Requires code modification)
)
```

### Iterative Refinement

Use Prompt Agent in RL loop:

```python
# Initial discovery
agent = PromptAgent()
results_v1 = agent.analyze_dataset(...)

# Run predictions
predictions = run_pipeline(...)

# Calculate errors
errors = calculate_errors(predictions, ground_truth)

# Re-run Prompt Agent with error feedback
results_v2 = agent.analyze_dataset(
    ...,
    previous_errors=errors,  # Guide next iteration
    focus_areas=["under-predicting digital", "over-predicting financial"]
)
```

### Multi-Dataset Learning

Discover patterns across FRESCO + ACORN:

```python
# Analyze both datasets
fresco_results = agent.analyze_dataset(fresco_dir, ...)
acorn_results = agent.analyze_dataset(acorn_dir, ...)

# Compare patterns
common_patterns = compare_patterns(fresco_results, acorn_results)

# Generate universal prompt
universal_prompt = agent._generate_prompt(common_patterns, ...)
```

## Limitations

### 1. Quality Depends on LLM

- GPT-5 gives better results than GPT-4o
- May need manual review/editing
- Sometimes generates overly generic rules

**Mitigation:** Always review generated prompts, test on sample data first

### 2. May Miss Subtle Patterns

- Focuses on high-level patterns
- May not catch demographic-specific nuances
- Statistical patterns may differ from LLM interpretation

**Mitigation:** Use as starting point, refine with traditional RL loop

### 3. Computational Cost

- Analyzing 22 classes requires multiple LLM calls
- GPT-5 is expensive (~$0.50-1.00 per full run)

**Mitigation:** Run once, cache results, iterate manually

## Comparison: Manual vs Automated

| Aspect | Manual Prompt Engineering | Automated (Prompt Agent) |
|--------|--------------------------|--------------------------|
| **Time** | 2-3 days per dataset | 5-10 minutes |
| **Effort** | High (read data, analyze, write) | Low (review output) |
| **Consistency** | Variable | Consistent |
| **Coverage** | May miss patterns | Systematic analysis |
| **Quality** | Depends on human expertise | Depends on LLM |
| **Iteration** | Slow | Fast |
| **Cost** | Free (time) | ~$1 per run (API) |

**Recommendation:** Use Prompt Agent for initial discovery, then refine manually.

## Troubleshooting

### Issue: Generated prompt too vague

**Solution:**
- Use more powerful model (GPT-5 vs GPT-4o)
- Provide more specific analysis instructions
- Manually add specificity after generation

### Issue: Patterns don't match data

**Solution:**
- Check data quality/format
- Review quantitative summary for errors
- Run on subset first to validate

### Issue: API errors/timeouts

**Solution:**
- Check API key is valid
- Reduce data sent to LLM (sample fewer classes)
- Add retry logic

### Issue: JSON parsing errors

**Solution:**
- Prompt Agent catches JSON errors and returns raw response
- Review raw response in `analysis_results.json`
- Extract patterns manually if needed

## Next Steps

After running Prompt Agent:

1. **Review outputs** (generated_baseline_prompt.txt)
2. **Test on 1-2 classes** (run predictions)
3. **Evaluate accuracy** (compare vs ground truth)
4. **Refine prompts** (manual edits based on errors)
5. **Run full pipeline** (all 22 classes)
6. **Enter RL loop** (iterate on errors)

---

**Status:** Beta - Tested on ACORN dataset
**Model:** GPT-5 recommended (GPT-4o acceptable)
**Integration:** Drop-in replacement for manual prompt engineering
