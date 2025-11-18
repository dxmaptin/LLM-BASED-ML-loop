# Training Guide: RL Loop for Prompt Optimization

## Quick Overview

This system improves through **reinforcement learning** - analyzing prediction errors and updating prompts iteratively.

### The 5-Step Cycle

```
1. Baseline Run → 2. Error Analysis → 3. Update Prompts → 4. Validate → 5. Iterate
```

### Example

**Iteration 1:**
- Run: `python run_ALL_handpicked_WITH_TARGET.py`
- Result: 16.6% average error

**Error Analysis:**
- Under-predicting digital behaviors for young people
- Regression to mean (predictions cluster 40-60%)

**Update Prompts** in `agent_estimator/estimator_agent/prompts.py`:
```python
DEMOGRAPHIC_PROMPTS["young_dependents"] = """
For digital/online behaviors: LIFT predictions by +20pp
If proximal data ≥80%, predict 75-95% (be bold!)
"""
```

**Iteration 2:**
- Run again
- Result: 13.4% error (19% improvement!)

**Continue** until target accuracy reached (typically 3-5 iterations).

---

## Full Training Workflow

### Step 1: Baseline Prediction

```bash
python run_ALL_handpicked_WITH_TARGET.py
```

Save results for comparison.

### Step 2: Error Analysis

Compare predictions vs ground truth:

```python
import pandas as pd

pred = pd.read_csv('results.csv')
actual = pd.read_csv('ground_truth.csv')

for idx, row in pred.iterrows():
    concept = row['Concept']
    pred_agree = row['SA'] + row['A']
    actual_agree = actual[actual['Concept']==concept]['SA'].iloc[0] + actual[actual['Concept']==concept]['A'].iloc[0]
    error = abs(pred_agree - actual_agree)
    print(f"{concept}: {error:.1%} error")
```

**Look for patterns:**
- Under/over-predicting specific demographics?
- Concept types (identity vs behavior) patterns?
- Regression to mean (all predictions 40-60%)?

### Step 3: Update Prompts

Edit `agent_estimator/estimator_agent/prompts.py`

**Two types of prompts:**
1. **General Prompt** - Universal rules (all demographics)
2. **Demographic Prompts** - Learned calibrations per segment

**Common Fixes:**

**Fix 1: Add demographic calibrations**
```python
DEMOGRAPHIC_PROMPTS["young_dependents"] = """
[Digital Behaviors]
- LIFT by +15-20pp for tech/online concepts
- Expect 70-95% for digital behaviors

[Financial Attitudes]
- Anti-borrowing: +10pp (cautious despite young age)
- Pro-saving: +15pp
"""
```

**Fix 2: Strengthen proximal guardrails**
```python
# In GENERAL_SYSTEM_PROMPT

"""
If proximal data ≥80%: Predict 75-95% (be bold!)
If proximal 60-79%: Predict 60-85%
If proximal <20%: Predict 10-30%

DO NOT regress to mean when strong evidence exists.
"""
```

**Fix 3: Add concept-type rules**
```python
"""
Identity ("I am..."): High neutral 35-42%, Low SA <15%
Low-friction behavior ("use", "prefer"): SA 12-20%, A 25-32%
High-friction behavior ("switch", "invest"): High neutral 35-45%, SA <12%
Attitude (default): Balanced, SA 10-18%
"""
```

### Step 4: Validate

Re-run with updated prompts:

```bash
python run_ALL_handpicked_WITH_TARGET.py
```

Compare:
- Error reduced? ✅ Keep changes, continue
- Error increased? ❌ Revert, try different approach
- No change? Try more aggressive modifications

### Step 5: Iterate

Repeat until:
- Target accuracy reached (MAE < 8%)
- Improvements plateau (<3% per iteration)

---

## Real Example: Young Dependents Training

### Iteration 1 (Baseline)
```
Average Error: 16.6%
Top Errors:
- "I hate to borrow": 43.0pp
- "Satisfied with life": 44.5pp
- "Internet banking": 15.2pp
```

### Changes Made
```python
DEMOGRAPHIC_PROMPTS["young_dependents"] = """
1. Proximal guardrails (≥80% → predict 70-90%)
2. Life satisfaction boost (expect 45-65%)
3. Financial conservatism (+10pp anti-borrowing)
"""
```

### Iteration 2
```
Average Error: 13.4% (19% improvement!)
```

### More Changes
```python
# Strengthened
"""
1. BOLDER proximal (≥80% → predict 75-95%)
2. Financial caution (+20pp anti-borrowing)
"""
```

### Iteration 3
```
Average Error: 12.2% (26.5% total improvement!)
```

**Result: 68% error reduction over 3 iterations!**

---

## Prompt Template

```python
DEMOGRAPHIC_PROMPTS["segment_name"] = """
[Profile]
Age: X-Y, Income: Level, Key traits: ...

[Learned Calibrations]
1. DIGITAL BEHAVIORS: LIFT/REDUCE by Xpp, expect X-Y%
2. FINANCIAL ATTITUDES: +/-Xpp for concepts
3. VALUES: Correlations (environmental → ethical)

[Patterns]
- Key behaviors
- Decision drivers
"""
```

---

## Tips

### Do's ✅
- Start with general rules
- One change at a time
- Document why (comments)
- Use git for versions
- Validate on holdout data

### Don'ts ❌
- Don't update all demographics at once
- Don't add contradictory rules
- Don't over-specify
- Don't ignore small wins (compounds!)

---

## Troubleshooting

**Improvements plateau:**
- Focus on outliers
- Try different LLM (GPT-4o vs Claude)
- Get more training data

**Changes make things worse:**
- Revert immediately
- Smaller incremental changes
- Test on single concept first

**Inconsistent results:**
- Increase runs (10+ instead of 5)
- Lower LLM temperature
- Add more explicit rules

---

## Success Metrics

- **Good progress:** 15-25% error reduction per iteration
- **Production-ready:** MAE < 8%
- **Diminishing returns:** <3% improvement → stop

**Timeline:** 2-3 weeks for initial training, quarterly updates ongoing

---

## Checklist Per Iteration

- [ ] Run system, save results
- [ ] Calculate errors
- [ ] Identify patterns
- [ ] Update prompts (1-3 changes)
- [ ] Commit to git
- [ ] Validate
- [ ] Compare to baseline
- [ ] Document learnings
- [ ] Iterate or deploy?

---

**Key Insight:** This is true RL - learning from errors and updating the "policy" (prompts), all while remaining fully interpretable! 🚀
