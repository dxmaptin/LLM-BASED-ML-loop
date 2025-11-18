# System Architecture - 5-Agent Prediction System

## Overview

The system uses 5 specialized AI agents working together to predict consumer behaviors across 22 demographic groups with 84% accuracy.

---

## The 5 Agents

### Agent 1: Pattern Extractor

**What it does:**
Analyzes all available survey data (text files and CSV responses) to discover patterns and create prediction instructions.

**Process:**
1. Reads thousands of past survey responses across all 22 demographic groups
2. Identifies recurring themes and behavioral patterns
3. Creates a **general prompt** - universal rules that apply to everyone (e.g., "Everyone dislikes wasting money")
4. Creates **class-specific prompts** - unique rules for each demographic (e.g., "Young people prefer digital payments")
5. Builds a Likert scale mapping to convert patterns into percentage predictions

**Outputs:**
- General prompt: Universal prediction rules
- 22 class-specific prompts: Demographic-specific adjustments
- Baseline mappings: Starting points for different question types

**Example:**
- General rule discovered: "Debt aversion is 42-45% for ALL demographics"
- Class-specific rule: "Young people -15pp on debt aversion, seniors +20pp"

---

### Agent 2: Data Extractor

**What it does:**
When you ask a question, this agent searches all available data and pulls the most relevant evidence to support the prediction.

**Process:**
1. Takes the question you want to predict (e.g., "I prefer to pay with cash")
2. Searches CSV files using semantic similarity (meaning-based matching)
3. Searches text profiles using keyword matching
4. Scores each piece of evidence by relevance (0-1 scale)
5. Builds an evidence bundle with the top 10-15 most relevant sources
6. **Training mode:** Excludes the exact answer to prevent cheating

**Outputs:**
- Evidence bundle: 10-15 relevant data points with relevance scores
- Mix of quantitative (CSV numbers) and qualitative (text descriptions)

**Example:**
For "I prefer to pay with cash" in young demographics:
- Evidence 1 (relevance: 0.95): "33% prefer cash for everyday purchases"
- Evidence 2 (relevance: 0.88): "63% use digital wallets regularly"
- Evidence 3 (relevance: 0.72): "Digital natives, cash usage declining"

**Why training mode matters:**
If we're testing how well the system works, we can't let it see the actual answer. The Data Extractor finds RELATED questions but excludes the exact question being predicted.

---

### Agent 3: Estimator

**What it does:**
Makes the actual prediction by combining the learned patterns with the retrieved evidence.

**Process:**
1. Receives the general prompt (universal rules)
2. Receives the class-specific prompt (demographic adjustments)
3. Receives the evidence bundle (relevant data)
4. Applies a 7-step decision process:
   - Identify demographic characteristics
   - Classify question type (attitude vs behavior)
   - Apply baseline prediction
   - Adjust based on evidence
   - Apply demographic modifiers
   - Sanity check (avoid unreasonable predictions)
   - Generate final distribution
5. Outputs both the prediction AND the reasoning behind it

**Key feature: Hierarchical prompting**
- Class-specific prompts can OVERRIDE general prompts
- If young people behave differently on a specific question, the class prompt wins
- Allows balancing universal truths with demographic nuances

**Outputs:**
- Prediction: Percentage distribution across 5 Likert scale options
- Reasoning: Step-by-step explanation of how it reached this prediction
- Topline: Single percentage (strongly agree + slightly agree)

**Example:**
Question: "I prefer to pay with cash" for young_dependents
- General baseline: 45% (behavior baseline)
- Class-specific override: 25% (digital natives)
- Evidence adjustment: 25% (matches evidence of 33% and digital wallet 63%)
- Final prediction: 25%
- Reasoning: "Evidence shows low cash usage, digital native characteristics, specific override applies"

---

### Agent 4: Critic

**What it does:**
Quality control - validates that the Estimator's prediction is trustworthy and not made up.

**Process:**
1. Checks if prediction is grounded in actual evidence (did it cite real sources?)
2. Assesses confidence based on evidence quality and quantity
3. Validates the prediction makes sense (no impossible distributions)
4. Decides: ACCEPT (high confidence) or REWORK (low confidence)
5. If REWORK, triggers the Estimator to try again with feedback

**Confidence scoring:**
- HIGH: Strong evidence (relevance >0.90), multiple consistent sources
- MEDIUM: Decent evidence (relevance 0.70-0.90), some variance
- LOW: Weak evidence (relevance <0.70), conflicting sources

**Rework trigger:**
- Confidence below threshold → Estimator must re-predict
- Evidence contradicts prediction → Estimator must re-predict
- Maximum 3 attempts per question

**Outputs:**
- Validation result: PASS or FAIL
- Confidence score: HIGH, MEDIUM, or LOW
- Recommendation: ACCEPT or REWORK
- Feedback: What went wrong (if applicable)

**Example - Rework scenario:**
- Estimator predicts: 65% cash preference
- Critic: "All evidence shows <30% cash usage. Prediction contradicts evidence."
- Confidence: LOW
- Decision: REWORK
- Estimator tries again: 28% cash preference
- Critic: "Consistent with evidence"
- Decision: ACCEPT

---

### Agent 5: Prompt Improver

**What it does:**
Learns from mistakes by comparing predictions to actual results, then rewrites the instruction prompts to improve future accuracy.

**Process:**
1. Collects all predictions made by the system
2. Compares them to ground truth (actual survey results)
3. Identifies error patterns (which questions fail? which demographics struggle?)
4. Analyzes root causes (why did it fail?)
5. Reviews Critic feedback (were predictions low confidence?)
6. Generates updated prompts:
   - Updates general prompt if universal pattern was wrong
   - Updates class-specific prompt if demographic rule was wrong
7. Tests new prompts to verify improvement
8. Accepts if better, rolls back if worse

**Example improvement cycle:**

**Iteration 1 Results:**
- Debt aversion for poor demographics: Predicted 70%, Actual 43% (27pp error)
- Pattern: Consistently over-predicting for ALL poor demographics

**Root Cause Analysis:**
- Stereotype assumption: "Poor people hate debt"
- Reality: Everyone has moderate debt aversion (42-45%)
- Fix: Change baseline from 70% to 42-45% for ALL demographics

**Prompt Update:**
- OLD: "Poor demographics: +25pp debt aversion"
- NEW: "UNIVERSAL: Debt aversion 42-45% for ALL income levels"

**Iteration 2 Results:**
- Debt aversion for poor demographics: Predicted 43%, Actual 43% (0pp error!)
- Improvement accepted, system updated

**Prevents overfitting:**
The Prompt Improver watches for memorization (learning specific answers) vs generalization (learning true patterns). If accuracy improves on training data but drops on test data, changes are rolled back.

---

## How They Work Together

### Workflow: Making a Prediction

```
YOU ASK A QUESTION
"Will millennials prefer sustainable brands?"
    ↓
AGENT 2: Data Extractor
Searches all data, finds 12 relevant sources
Scores by relevance: 0.95, 0.88, 0.82...
    ↓
AGENT 3: Estimator
Reads general prompt + millennial-specific prompt
Reviews evidence (12 sources)
Makes prediction: 45% will prefer sustainable brands
Explains reasoning: "Environmental values high (60%) but action gap (-15pp) = 45%"
    ↓
AGENT 4: Critic
Checks: Did it cite real evidence? YES
Checks: Is confidence high? YES (0.87)
Checks: Does prediction make sense? YES
Decision: ACCEPT
    ↓
RUN 5 TIMES, AVERAGE RESULTS
Final prediction: 45% ± 2%
    ↓
OUTPUT TO YOU
"45% of millennials prefer sustainable brands"
+ Confidence: HIGH
+ Evidence used: [list of 12 sources]
```

### Workflow: Learning from Mistakes

```
TESTING PHASE
Run predictions on 10 test questions
Compare to actual survey results
    ↓
AGENT 5: Prompt Improver
Finds pattern: Cash preference over-predicted by 18pp
Root cause: Digital adoption underestimated
    ↓
GENERATES PROMPT UPDATE
OLD: "Cash preference baseline: 55%"
NEW: "Cash preference baseline: 35% (digital adoption widespread)"
    ↓
TEST NEW PROMPT
Re-run predictions with updated instructions
    ↓
VALIDATION
Error reduced from 18pp → 6pp
Improvement accepted!
    ↓
AGENT 1: Pattern Extractor
Saves updated prompt for future use
```

---

## Why 5 Agents? (Evolution from 3-Agent System)

### Previous System (FRESCO Dataset)
**3 Agents:**
1. Data Extractor (same)
2. Estimator (same)
3. Critic (same)

**Worked for:**
- 12 simpler demographic groups
- Limited question types
- More straightforward patterns

### New Challenge (ACORN Dataset)
**Complexity increase:**
- 12 → 22 demographic groups
- More diverse question types
- More nuanced behavioral patterns

**Problem with 3 agents:**
- Too simple, couldn't capture complexity
- Risk of **underfitting** (missing important patterns)
- Manual prompt engineering took weeks per iteration

### Solution: Add 2 Agents

**Agent 1: Pattern Extractor**
- Automates the learning process
- Discovers patterns humans might miss
- Faster than manual prompt engineering

**Agent 5: Prompt Improver**
- Continuous learning loop
- Systematically fixes mistakes
- Prevents overfitting while maximizing accuracy

**Result:**
- 3-agent system: 67% accuracy (struggled with complexity)
- 5-agent system: 84% accuracy (handles complexity well)

---

## Key Design Principles

### 1. Separation of Concerns
Each agent has ONE job:
- Pattern Extractor: Learn
- Data Extractor: Find evidence
- Estimator: Predict
- Critic: Validate
- Prompt Improver: Improve

No overlap, no confusion.

### 2. Evidence-Based Reasoning
Every prediction MUST cite real evidence. The Critic rejects anything made up.

### 3. Hierarchical Prompting
General rules + specific overrides = flexibility without chaos

### 4. Quality Gating
Low confidence predictions are rejected and retried. No guesses in production.

### 5. Continuous Improvement
System gets better over time by learning from mistakes automatically.

---

## Real-World Analogy

Think of launching a new product in 22 different markets:

**Agent 1 (Pattern Extractor)** = Market researcher
- Studies all past launches, identifies what works universally vs locally

**Agent 2 (Data Extractor)** = Intelligence analyst
- For each market, gathers relevant competitive data and consumer insights

**Agent 3 (Estimator)** = Strategy consultant
- Uses research + intelligence to recommend: "Launch at $X price point, expect Y% adoption"

**Agent 4 (Critic)** = Risk officer
- Reviews recommendation: "Is this based on real data or gut feel? How confident are we?"

**Agent 5 (Prompt Improver)** = Post-mortem analyst
- After launch, compares results to predictions, updates strategy playbook for next time

All 5 roles are necessary. Remove any one and quality suffers.

---

## Performance Impact

### With All 5 Agents
- Accuracy: 84%
- Low-income demographics: 83% (was 29%)
- Automated learning: Weeks → Hours
- Continuous improvement: Built-in

### Without Agent 1 (Pattern Extractor)
- Manual prompt engineering: Weeks per iteration
- Human bias in pattern identification
- Misses non-obvious patterns (like debt stereotype)

### Without Agent 5 (Prompt Improver)
- No systematic learning from mistakes
- Errors persist across iterations
- Manual analysis required for each failure

### Without Agent 4 (Critic)
- Low-confidence predictions slip through
- Made-up data not caught
- Quality inconsistent

**All 5 agents are essential for production-quality performance.**

---

## Summary

The 5-agent architecture achieves 84% accuracy through:

1. **Automated pattern discovery** (Agent 1) - Faster than humans, finds non-obvious patterns
2. **Quality evidence retrieval** (Agent 2) - Grounds predictions in real data
3. **Structured reasoning** (Agent 3) - Systematic, explainable predictions
4. **Quality validation** (Agent 4) - Catches errors before they reach users
5. **Continuous learning** (Agent 5) - Gets better over time automatically

**The result:** Production-ready system that predicts consumer behavior at 1/1000th the cost of traditional research with 84% accuracy.

---

**Status:** Production Ready
**Version:** V10 (Universal Baseline Corrections)
**Performance:** 84% accuracy across 22 demographics
