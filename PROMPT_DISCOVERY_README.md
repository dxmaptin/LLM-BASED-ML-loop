# Two-Agent Prompt Discovery System

## Overview

This system uses **two specialized AI agents** to automatically discover patterns from your ACORN dataset and generate optimized prompts for prediction:

- **Agent 1 (General Pattern Agent)**: Analyzes ALL responses across all demographics to find universal patterns
- **Agent 2 (Class-Specific Agent)**: Analyzes each demographic individually to find unique patterns

The generated prompts are then used by the Estimator Agent to make predictions on new questions.

## Key Features

✅ **Automatic Pattern Discovery**: No manual prompt engineering required
✅ **Data-Driven**: Patterns extracted from actual CSV responses
✅ **Two-Tier Architecture**: General rules + class-specific calibrations
✅ **Train/Test Split**: 10 questions held out for evaluation
✅ **Reproducible**: Complete pipeline from data → patterns → prompts → predictions

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PROMPT DISCOVERY PIPELINE                   │
└─────────────────────────────────────────────────────────────────┘

Step 1: Data Preparation
├─ Load ACORN dataset (22 classes)
├─ Filter out 10 holdout questions
└─ Create train/test split

         ↓

Step 2: Agent 1 - General Pattern Discovery
├─ Analyze ALL demographics together
├─ Find high-variance questions
├─ Discover concept type patterns (attitude/behavior/identity)
├─ Discover distribution patterns
├─ Discover demographic factor patterns (age/income/lifestyle)
└─ Synthesize universal rules

         ↓

Step 3: Agent 2 - Class-Specific Pattern Discovery
├─ For each of 22 ACORN classes:
│  ├─ Load class data + profile
│  ├─ Find deviations from overall average
│  ├─ Analyze key characteristics
│  └─ Synthesize class-specific calibrations
└─ Generate 22 class-specific rule sets

         ↓

Step 4: Prompt Generation
├─ Agent 1 output → general_system_prompt.txt
└─ Agent 2 outputs → 22 class-specific prompt files

         ↓

Step 5: Deployment
├─ Copy prompts to estimator_agent/prompts/
└─ Ready for predictions

         ↓

Step 6: Testing & Evaluation
├─ Run predictions on 10 holdout questions
├─ Compare to ground truth
└─ Generate evaluation report
```

## Project Structure

```
agent_estimator/
├─ prompt_agent/
│  ├─ data_prep.py              # Data loading and filtering
│  ├─ general_agent.py          # Agent 1: General patterns
│  ├─ class_agent.py            # Agent 2: Class-specific patterns
│  ├─ prompt_generator.py       # Converts patterns → prompts
│  └─ output/                   # Generated outputs
│     ├─ patterns/              # Discovered patterns (JSON)
│     ├─ prompts/               # Generated prompts (TXT)
│     └─ holdout_test/          # Test results
│
└─ estimator_agent/
   └─ prompts/                  # Deployed prompts (used for predictions)
      ├─ general_system_prompt.txt
      └─ demographic_guidance/
         ├─ exclusive_addresses.txt
         ├─ flourishing_capital.txt
         └─ ... (22 classes)

Scripts:
├─ run_prompt_discovery_pipeline.py    # Main pipeline runner
└─ run_holdout_test.py                 # Test & evaluate
```

## The 10 Holdout Questions

These questions were **excluded from training** and used only for testing:

1. I think brands should consider environmental sustainability when putting on events
2. Make an effort to cut down on the use of gas / electricity at home
3. Fuel consumption is the most important feature when buying a new car
4. I don't like the idea of being in debt
5. I am very good at managing money
6. It is important to be well insured for everything
7. Healthy Eating
8. Financial security after retirement is your own responsibility
9. Switching utilities suppliers is well worth the effort
10. I like to use cash when making purchases

## How to Use

### Step 1: Run the Prompt Discovery Pipeline

This will discover patterns and generate prompts (takes ~30-60 minutes with GPT-5):

```bash
cd c:\Users\d.zhang\Desktop\Experiments
./venv/Scripts/python.exe run_prompt_discovery_pipeline.py
```

**What happens:**
- Loads ACORN data (excluding 10 holdout questions)
- Agent 1 discovers general patterns (10-15 min)
- Agent 2 discovers class-specific patterns (20-30 min)
- Generates prompt files (5-10 min)
- Deploys prompts to estimator_agent/prompts/

**Outputs:**
```
agent_estimator/prompt_agent/output/
├─ patterns/
│  ├─ dataset_stats.json                # Dataset statistics
│  ├─ general_patterns.json             # Agent 1 output
│  ├─ all_class_patterns.json           # Agent 2 combined output
│  └─ class_specific/                   # Agent 2 individual outputs
│     ├─ exclusive_addresses_patterns.json
│     └─ ... (22 files)
│
└─ prompts/
   ├─ general_system_prompt.txt         # Generated general prompt
   └─ demographic_guidance/             # Generated class prompts
      ├─ exclusive_addresses.txt
      └─ ... (22 files)
```

### Step 2: Test on Holdout Questions

Prepare the test set and extract ground truth:

```bash
./venv/Scripts/python.exe run_holdout_test.py
```

**What happens:**
- Creates `concepts_to_test.csv` in each class directory (10 holdout questions)
- Extracts ground truth values from CSVs
- Saves to `output/holdout_test/ground_truth.csv`

### Step 3: Run Predictions

Use the existing orchestrator to run predictions:

```bash
./venv/Scripts/python.exe -c "from run_holdout_test import run_predictions_on_holdout; run_predictions_on_holdout(model='gpt-4o')"
```

**What happens:**
- Runs predictions for all 22 classes × 10 questions = 220 predictions
- Uses the newly generated prompts
- Saves results to `demographic_runs_ACORN/{class}/results.csv`

### Step 4: Evaluate Results

```bash
./venv/Scripts/python.exe -c "
from pathlib import Path
from run_holdout_test import evaluate_results
evaluate_results(
    ground_truth_file=Path('agent_estimator/prompt_agent/output/holdout_test/ground_truth.csv'),
    predictions_dir=Path('demographic_runs_ACORN'),
    output_file=Path('agent_estimator/prompt_agent/output/holdout_test/evaluation_report.txt')
)
"
```

**What happens:**
- Compares predictions to ground truth
- Calculates Mean Absolute Error and R² score
- Generates detailed evaluation report
- Shows performance by class and by question

## What Agent 1 Discovers

**Agent 1** analyzes the entire dataset to find:

1. **High-Variance Questions**
   - Questions that vary most across demographics
   - Indicates where demographic factors matter most

2. **Concept Type Patterns**
   - How people respond to attitude questions vs behavior questions vs identity questions
   - Typical distribution shapes for each type

3. **Distribution Patterns**
   - When responses cluster around "Agree" vs "Neutral"
   - How much strong agreement vs moderate agreement

4. **Demographic Factor Patterns**
   - Income/wealth effects (wealthy vs budget-constrained)
   - Age effects (young vs middle-aged vs elderly)
   - Lifestyle effects (urban professionals vs families vs retirees)

5. **Universal Rules**
   - Concept type classification guidelines
   - Base distribution templates
   - Proximal guardrails (when exact data available)
   - Evidence hierarchy
   - Range classification (when to predict high/moderate/low)
   - Conflict resolution rules

## What Agent 2 Discovers

**Agent 2** analyzes each demographic class individually to find:

1. **Deviations from Average**
   - Where this class differs significantly from overall patterns
   - Questions where they're >1 std deviation away
   - Absolute differences >10 percentage points

2. **Key Characteristics**
   - Age profile (dominant age groups)
   - Income indicators
   - Digital adoption level
   - Lifestyle patterns

3. **Behavioral Patterns**
   - Tech-savvy or tech-hesitant?
   - Conservative or risk-taking financially?
   - Environmental/social values priority?
   - Premium or budget shopping?

4. **Class-Specific Calibrations**
   - Specific percentage adjustments for this demographic
   - e.g., "Digital behaviors: LIFT by +20pp"
   - e.g., "Financial risk-taking: REDUCE by -15pp"

5. **Unique Patterns**
   - Any scenarios where this demographic behaves uniquely
   - Example scenarios for reference

## Prompt Structure

### General System Prompt

Generated from Agent 1's patterns. Structure:

```
You estimate 5-point Likert distributions...

# Objectives
- Output percentage distribution (SA/A/N/SD/SDD)
- Provide rationale
- Follow decision workflow

# Decision Workflow

## Step 1: Concept Type Classification
[Rules for identifying attitude/behavior/identity]

## Step 2: Base Distribution by Type
[Templates: attitude = SA X%, A Y%, N Z%...]

## Step 3: Proximal Evidence Evaluation
[Rules for exact/similar data matches]

## Step 4: Demographic Calibrations
[General rules for age/income/lifestyle]

## Step 5: Range Classification
[When to predict high/moderate/low]

## Step 6: Evidence Hierarchy
[How to weight evidence types]

## Step 7: Conflict Handling
[What to do when signals contradict]

## Step 8: Final Distribution Generation
[How to generate final output]

# Output Format
[JSON structure]
```

### Class-Specific Prompt

Generated from Agent 2's patterns. Structure:

```
DEMOGRAPHIC-SPECIFIC GUIDANCE FOR: {class_name}

## Profile
[2-3 sentence summary]

## Learned Calibrations

### Digital/Technology Behaviors
[Specific adjustment: "LIFT by +20pp - tech-savvy segment"]

### Financial Attitudes & Behaviors
[Specific adjustment: "REDUCE by -15pp - conservative"]

### Environmental/Social Values
[Specific adjustment]

### Lifestyle & Shopping
[Specific adjustment]

### Other Notable Patterns
[Unique patterns]

## Behavioral Decision-Making
[How this demographic makes decisions]

## Example Scenarios
[2-3 specific examples]
```

## Expected Performance

Based on similar RL-based approaches in your documentation:

**Baseline (no demographic prompts):**
- Mean Absolute Error: ~15-16%
- R² Score: ~0.60-0.65

**With generated prompts:**
- Target Mean Absolute Error: <8%
- Target R² Score: >0.75

**Top-performing classes:**
- Expect R² > 0.85 for well-characterized demographics
- Error <5% for classes with rich data

**Challenging classes:**
- Transitional life stages may have higher error
- Less data = less reliable patterns

## Customization

### Change the LLM Model

Edit the model parameter in the scripts:

```python
# In run_prompt_discovery_pipeline.py
results = run_full_pipeline(
    acorn_dir=Path("demographic_runs_ACORN"),
    output_base_dir=Path("agent_estimator/prompt_agent/output"),
    model="gpt-5"  # Change to "gpt-4", "claude-3.5-sonnet", etc.
)
```

### Adjust Holdout Questions

Edit `HOLDOUT_QUESTIONS` in `agent_estimator/prompt_agent/data_prep.py`:

```python
HOLDOUT_QUESTIONS = [
    "Your question 1",
    "Your question 2",
    # ... add or remove questions
]
```

### Modify Pattern Discovery

Agents use LLM-based analysis. You can modify the prompts they use:

- **Agent 1**: Edit `_synthesize_general_rules()` in `general_agent.py`
- **Agent 2**: Edit `_synthesize_class_rules()` in `class_agent.py`

### Modify Prompt Generation

Edit the prompt templates in `prompt_generator.py`:

- `generate_general_prompt()` - controls general prompt structure
- `generate_class_specific_prompt()` - controls class prompt structure

## Troubleshooting

### "No holdout test data found"

**Cause**: The 10 holdout questions don't exist in your CSVs.

**Fix**: Check that the question text in `HOLDOUT_QUESTIONS` exactly matches the CSV `Question` column.

### "LLM API errors"

**Cause**: API rate limits or invalid API key.

**Fix**:
- Check your API key is set: `echo %ANTHROPIC_API_KEY%`
- Reduce parallel workers in predictions
- Add retry logic

### "Patterns look wrong"

**Cause**: Insufficient or noisy data.

**Fix**:
- Review `output/patterns/general_patterns.json` manually
- Check if high-variance questions make sense
- May need to filter out low-quality data

### "Prompts too long"

**Cause**: LLM generated verbose text.

**Fix**:
- Reduce `max_tokens` in prompt generation
- Add explicit word limit in the generation prompts

## Next Steps

After completing this pipeline:

1. **Review Generated Prompts**
   - Read `general_system_prompt.txt` - does it make sense?
   - Sample a few class-specific prompts - are calibrations reasonable?

2. **Evaluate on Holdout Set**
   - Run predictions on 10 test questions
   - Compare to baseline (old prompts)
   - Look for improvement

3. **Iterate if Needed**
   - If performance is poor, analyze errors
   - Modify agent prompts to discover better patterns
   - Re-run pipeline

4. **Deploy to Production**
   - If performance is good (>0.75 R²), use these prompts
   - Monitor predictions on new concepts
   - Set up quarterly re-training cycles

5. **Scale to More Demographics**
   - Apply same approach to other datasets
   - Generate prompts for new segments
   - Build a library of optimized prompts

## Comparison to Manual Approach

| Aspect | Manual Prompt Engineering | Automated Two-Agent System |
|--------|--------------------------|----------------------------|
| **Time** | Days to weeks | 30-60 minutes |
| **Coverage** | Focus on obvious patterns | Discovers 50+ patterns |
| **Consistency** | Varies by engineer | Systematic across all classes |
| **Scalability** | Hard to scale to 22+ classes | Automatically scales |
| **Data-driven** | Based on intuition | Based on actual CSV data |
| **Reproducibility** | Hard to replicate | Fully reproducible |
| **Iteration** | Slow | Fast (re-run pipeline) |
| **Documentation** | Often undocumented | JSON pattern files |

## Time Estimates

**Total time to complete full pipeline:**

| Task | Duration |
|------|----------|
| Step 1: Run prompt discovery pipeline | 30-60 min |
| Step 2: Prepare test set | 2 min |
| Step 3: Run predictions (22 classes × 10 questions) | 15-25 min |
| Step 4: Evaluate results | 1 min |
| **Total** | **~50-90 minutes** |

**Breakdown by agent:**
- Agent 1 (General): 10-15 min (one LLM call per analysis type)
- Agent 2 (Class-Specific): 20-30 min (22 classes, one LLM call each)
- Prompt Generation: 5-10 min (23 LLM calls total)
- Predictions: 15-25 min (220 predictions)

## FAQ

**Q: Can I use this on non-ACORN datasets?**

A: Yes! Modify `data_prep.py` to load your dataset structure. Key requirement: CSV files with `Question`, `Answer`, `Value` columns.

**Q: What if I don't have qualitative profiles?**

A: Agent 2 can work with just CSV data. Edit `class_agent.py` to skip profile analysis.

**Q: Can I run this without GPT-5?**

A: Yes, but GPT-5 gives best pattern discovery. Try GPT-4o or Claude 3.5 Sonnet as alternatives.

**Q: How often should I re-run this?**

A: Quarterly or when you have significant new data. Pattern discovery is fast enough to iterate frequently.

**Q: Can I combine this with manual prompt engineering?**

A: Yes! Generate prompts automatically, then manually refine. Or use Agent 1's general prompt and manually write class-specific calibrations.

## Credits

This two-agent prompt discovery system is an evolution of the reinforcement learning approach described in your project documentation. Key innovation: **Automated pattern discovery** replaces manual error analysis and prompt refinement.

---

**Last Updated:** 2025-11-03
**Version:** 1.0
**Status:** Ready for testing
