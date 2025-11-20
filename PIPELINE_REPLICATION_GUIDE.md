# Complete Pipeline Replication Guide

## How to Replicate the ACORN Experiment with Your Own Dataset

This guide provides step-by-step instructions to replicate our 5-agent reinforcement learning pipeline that achieves **84% R²** and **4.97% MAE** on demographic predictions
---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding the Pipeline Architecture](#understanding-the-pipeline-architecture)
3. [Data Preparation](#data-preparation)
4. [Running the Complete Pipeline](#running-the-complete-pipeline)
5. [Replacing ACORN with Your Own Dataset](#replacing-acorn-with-your-own-dataset)
6. [Training vs Testing Splits](#training-vs-testing-splits)
7. [General vs Specific Prompts](#general-vs-specific-prompts)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

1. **Python Environment:**
   ```bash
   python 3.9+
   pip install openai anthropic google-generativeai pandas numpy scikit-learn langchain langgraph
   ```

2. **API Keys:**
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...  # Optional
   GEMINI_API_KEY=...             # Optional

   # Configuration
   AGENT_ESTIMATOR_MODEL=gpt-4o
   AGENT_RUNS=5
   AGENT_MAX_ITERATIONS=3
   ```

3. **Verify Installation:**
   ```bash
   cd /path/to/LLM-BASED-ML-loop
   python -c "from agent_estimator.common.config import LIKERT_ORDER; print('Setup OK')"
   ```

### Run the ACORN Pipeline (5 minutes)

```bash
# Step 1: Run predictions on 10 holdout questions for one demographic
python run_ALL_handpicked_WITH_TARGET.py --demographic young_dependents

# Step 2: View results
cat demographic_runs_ACORN/young_dependents/predictions.csv
```

**Expected Output:**
```
Concept,Strongly agree,Slightly agree,Neither,...,Critic confidence
"I hate to borrow",35.2,21.4,18.8,...,0.91
"I like to use cash",8.0,17.0,30.0,...,0.87
...
```

---

## Understanding the Pipeline Architecture

### The 5-Agent System

Our pipeline consists of **5 specialized AI agents** that work together:

```
┌─────────────────────────────────────────────────────────────┐
│ Agent 1: PATTERN EXTRACTOR                                  │
│ Discovers universal rules and class-specific patterns       │
│ Output: General + demographic-specific prompts              │
└─────────────────────────────────────────────────────────────┘
                          ↓ Prompts
┌─────────────────────────────────────────────────────────────┐
│ Agent 2: IR AGENT (Information Retrieval)                   │
│ Finds relevant evidence from CSV + text files               │
│ Output: Top 5 evidence sources with relevance scores        │
└─────────────────────────────────────────────────────────────┘
                          ↓ Evidence Bundle
┌─────────────────────────────────────────────────────────────┐
│ Agent 3: ESTIMATOR                                          │
│ Makes predictions using prompts + evidence                  │
│ Output: Likert distribution (5 runs, averaged)              │
└─────────────────────────────────────────────────────────────┘
                          ↓ Prediction
┌─────────────────────────────────────────────────────────────┐
│ Agent 4: CRITIC                                             │
│ Validates quality, triggers rework if needed                │
│ Output: Accept/Reject + confidence score                    │
└─────────────────────────────────────────────────────────────┘
                          ↓ If Accept
┌─────────────────────────────────────────────────────────────┐
│ Agent 5: PROMPT IMPROVER                                    │
│ Analyzes errors, updates prompts via reinforcement learning │
│ Output: Improved general + demographic prompts              │
└─────────────────────────────────────────────────────────────┘
```

### Key Concepts

| **General Prompt** | Universal patterns that apply to ALL demographics | "Debt aversion is 42-45% regardless of income" |
| **Specific Prompt** | Overrides for a specific demographic class | "Young demos: Digital +25pp, Cash -15pp" |
| **LOO Filtering** | Leave-One-Out: Exclude exact ground truth during training | Predicting "cash preference" → hide that exact row |
| **Proximal Evidence** | Closest matching data point (exact or near-exact) | "cash usage 33%" when predicting "cash preference" |
| **Monte Carlo Sampling** | Run prediction 5 times, average results | Reduces LLM noise by √5 = 2.24× |

---

## Data Preparation

### ACORN Dataset Structure

The pipeline expects this directory structure:

```
demographic_runs_ACORN/
├── young_dependents/                        ← One folder per demographic
│   ├── concepts_to_test.csv                 ← Questions to predict
│   ├── Flattened Data Inputs/               ← Quantitative evidence
│   │   └── ACORN_young_dependents.csv       ← Likert data
│   └── Textual Data Inputs/                 ← Qualitative evidence
│       └── young_dependents_profile.txt     ← Demographic profile
├── budgeting_elderly/
│   └── ... (same structure)
└── ... (20 more demographics)
```

### Required Files

#### 1. `concepts_to_test.csv` (Questions to predict)

```csv
Concept
I hate to borrow
I am very good at managing money
I like to use cash when making purchases
Make an effort to cut down on gas/electricity
I think brands should consider environmental sustainability
```

**Format:**
- Single column: `Concept`
- Each row is a question to predict

#### 2. `Flattened Data Inputs/ACORN_<demographic>.csv` (Quantitative evidence)

```csv
Category,Question,Answer,Value
Financial Attitudes,I hate to borrow,Strongly Agree,0.3512
Financial Attitudes,I hate to borrow,Agree,0.2143
Financial Attitudes,I hate to borrow,Neither,0.1876
Financial Attitudes,I hate to borrow,Disagree,0.1453
Financial Attitudes,I hate to borrow,Strongly Disagree,0.1016
Digital Behavior,Use mobile banking,Yes,0.6832
Digital Behavior,Use mobile banking,No,0.3168
```

**Format:**
- `Category`: Thematic grouping (e.g., "Financial Attitudes", "Digital Behavior")
- `Question`: The survey question
- `Answer`: Likert response (Strongly Agree/Agree/Neither/Disagree/Strongly Disagree) or binary (Yes/No)
- `Value`: Proportion (0-1 scale)

**Important:**
- Values must sum to 1.0 per question
- Include RELATED questions (not just the ones you're predicting)
- More context = better predictions

#### 3. `Textual Data Inputs/<demographic>_profile.txt` (Qualitative evidence)

```
Young Dependents (Age 18-35)

DEMOGRAPHIC PROFILE:
- Age: 18-35, predominantly 18-25
- Living situation: With parents or shared accommodation
- Income: Entry-level (£18K-£28K)
- Education: Students or recent graduates

PSYCHOGRAPHIC TRAITS:
- Digital natives - high smartphone adoption (95%+)
- Social media-driven purchase decisions
- Price-sensitive but convenience-oriented
- Limited brand loyalty, willing to switch

FINANCIAL BEHAVIOR:
- Low savings (living paycheck-to-paycheck)
- Use of overdrafts and credit cards common
- Reluctant to invest, prefer liquid savings
- High digital payment adoption (mobile wallets 68%)
```

**Format:**
- Free-form text
- Include demographics, psychographics, behaviors
- Use specific numbers when available ("68%" not "high")
- Organize into logical sections

---

## Running the Complete Pipeline

### Step 1: Pattern Discovery (Agent 1)

**Purpose:** Learn universal patterns and demographic-specific overrides from training data.

```bash
python run_pattern_discovery_acorn.py
```

**What it does:**
1. Loads training data (excludes 10 holdout questions)
2. Discovers patterns:
   - High-variance questions (e.g., "cash preference" varies 25-50%)
   - Concept type baselines (attitudes=37%, behaviors=45%)
   - Demographic effects (age, income, lifestyle)
3. Generates prompts:
   - `agent_estimator/estimator_agent/prompts/general_system_prompt.txt`
   - `agent_estimator/estimator_agent/prompts/demographic_guidance/*.txt`

**Expected output:**
```
Analyzing 2,200 training data points (22 demos × 100 questions)...
Discovered 42 universal patterns
Generated general system prompt (1,850 tokens)
Generated 22 demographic-specific prompts (avg 650 tokens each)
Saved to prompts/
```

**Time:** 10-15 minutes

### Step 2: Run Predictions (Agents 2, 3, 4)

**Purpose:** Make predictions on test questions using the learned prompts.

#### Option A: Single Demographic (Testing)

```bash
python run_ALL_handpicked_WITH_TARGET.py --demographic young_dependents
```

**What it does:**
1. Loads 10 holdout questions from `concepts_to_test.csv`
2. For each question:
   - **Agent 2 (IR):** Retrieves top 5 evidence sources
   - **Agent 3 (Estimator):** Makes 5 predictions, averages
   - **Agent 4 (Critic):** Validates, triggers rework if needed
3. Saves results to `demographic_runs_ACORN/young_dependents/predictions.csv`

**Expected output:**
```
Processing 10 concepts for young_dependents...
1/10: I hate to borrow
  IR Agent: Found 5 sources (avg relevance 0.87)
  Estimator: Run 5 times, aggregated
  Critic: ACCEPT (confidence 0.91)
2/10: I like to use cash
  IR Agent: Found 5 sources (avg relevance 0.81)
  Estimator: Run 5 times, aggregated
  Critic: REJECT (confidence 0.42) - reworking...
  Estimator: Retry with feedback
  Critic: ACCEPT (confidence 0.73)
...
Done! Results saved to predictions.csv
```

**Time:** 5-10 minutes (10 concepts × 5-10s each)

#### Option B: All Demographics (Production)

```bash
python run_all_acorn_classes.py
```

**What it does:**
- Runs predictions for all 22 demographics
- 22 × 10 = 220 predictions total

**Time:** 1-2 hours

**Expected output:**
```
Results saved to:
  demographic_runs_ACORN/young_dependents/predictions.csv
  demographic_runs_ACORN/budgeting_elderly/predictions.csv
  ...
  demographic_runs_ACORN/high_income_professionals/predictions.csv
```

### Step 3: Evaluate Performance

```bash
python evaluate_predictions.py
```

**What it does:**
1. Loads predictions from all demographics
2. Loads ground truth from `v10_detailed_all_21_classes.csv`
3. Calculates metrics:
   - R² (coefficient of determination)
   - MAE (mean absolute error)
   - Per-demographic breakdowns

**Expected output:**
```
Overall Performance:
  R² = 0.84
  MAE = 4.97%

Per-Demographic Performance:
  young_dependents: R² = 0.88, MAE = 3.2%
  budgeting_elderly: R² = 0.76, MAE = 6.8%
  high_income_professionals: R² = 0.92, MAE = 2.1%
  ...
```

### Step 4: Reinforcement Learning (Agent 5)

**Purpose:** Improve prompts by learning from errors.

```bash
python run_prompt_improver.py --iterations 5
```

**What it does:**
1. **Iteration 1:**
   - Run predictions with current prompts
   - Calculate performance (R² = 0.78, MAE = 6.2%)
   - Analyze errors: "Cash preference over-predicted by 15pp for young demos"
   - Root cause: "Ignoring digital native evidence"
   - Generate update: Add rule "Young demos: cash 25% not 40%"
   - Test updated prompt: R² = 0.81, MAE = 5.1%
   - **Accept** (improved)

2. **Iteration 2:**
   - Analyze remaining errors: "Environmental attitudes under-predicted"
   - Generate update: "Values-action gap: -15pp from attitudes to behaviors"
   - Test: R² = 0.83, MAE = 5.0%
   - **Accept**

3. **Iteration 3:**
   - No significant patterns found
   - Test: R² = 0.84, MAE = 4.97%
   - **Accept**

4. **Iteration 4:**
   - Test: R² = 0.83, MAE = 5.1%
   - **Reject** (worse) - rollback to iteration 3


---

## Replacing ACORN with Your Own Dataset

### Overview

To use your own dataset instead of ACORN, follow these steps:

1. Prepare your data in the required format
2. Set up the directory structure
3. Configure the data loader
4. Run the pipeline


## Training vs Testing Splits

### Philosophy

**Goal:** Learn generalizable patterns, not memorize answers.

**Approach:**
1. **Holdout Questions:** 10 questions never seen during training
2. **Leave-One-Out (LOO) Filtering:** When predicting a question, exclude exact match from evidence
3. **Cross-Class Validation:** Train on N-1 demographics, test on held-out demographic

