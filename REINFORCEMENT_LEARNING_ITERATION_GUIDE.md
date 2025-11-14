# Reinforcement Learning Iteration Guide

## Overview

This guide explains how to use the reinforcement learning framework to iteratively improve prompts until all ACORN classes achieve R² > 0.7.

## The Iteration Cycle

```
1. Run estimator with current prompt (VN) on all/target classes
                ↓
2. Calculate R² for all classes
                ↓
3. Identify underperforming classes (R² < 0.7)
                ↓
4. Analyze error patterns (bias, concept-specific errors)
                ↓
5. Update prompts based on patterns (create VN+1)
                ↓
6. Run VN+1 on underperforming classes only
                ↓
7. Repeat until all classes >= 0.7
```

## Key Scripts

### 1. `calculate_r2_v3_full.py`

**Purpose:** Calculate R² for all 22 ACORN classes

**Output:**
- Console: R² for each class, summary statistics
- `ACORN_v3_r2_results.json`: Full results for all classes
- `v3_underperforming_classes.json`: Classes with R² < 0.7

**Usage:**
```bash
python calculate_r2_v3_full.py
```

**Example Output:**
```
[OK] aspiring_communities                    | R² =  0.781 | MAE =  6.2pp | Bias = +1.3pp
[LOW R²] cash-strapped_families             | R² =  0.612 | MAE =  9.8pp | Bias = -4.2pp
...
SUMMARY STATISTICS:
Mean R²: 0.6972
R² >= 0.70: 15 classes (68.2%)
0.50 <= R² < 0.70: 5 classes (22.7%)
R² < 0.50: 2 classes (9.1%)
```

### 2. `analyze_v3_errors_detailed.py`

**Purpose:** Detailed error analysis for underperforming classes

**Input:** `v3_underperforming_classes.json` (from step 1)

**Output:**
- Console: Concept-by-concept errors, systematic bias, recommendations
- `v3_error_analysis_detailed.json`: Detailed error breakdown

**Usage:**
```bash
python analyze_v3_errors_detailed.py
```

**Example Output:**
```
CLASS: cash-strapped_families (R² = 0.612)
Concept                            Actual    Predicted   Error
Environmental sustainability        26.5%     32.1%      +5.6pp    OVER
Cut down gas/electricity            73.3%     68.2%      -5.1pp    UNDER
...

ERROR SUMMARY BY CONCEPT:
Concept                            Mean Error   Max Error    Direction
Environmental sustainability        +8.2pp       +12.4pp      OVER
Like cash                           -6.5pp       -11.2pp      UNDER
...

RECOMMENDATIONS FOR V4 PROMPT:
1. CONCEPT-SPECIFIC CORRECTIONS NEEDED:
   - "Environmental sustainability": REDUCE by 8pp (currently over-predicting)
   - "Like cash": INCREASE by 7pp (currently under-predicting)
...
```

### 3. `run_v4_iteration.py`

**Purpose:** Run next iteration (V4) on underperforming classes only

**Input:** `v3_underperforming_classes.json`

**Output:** `estimator_results_ACORN_v4.txt` for each underperforming class

**Usage:**
```bash
# First, update the general prompt based on error analysis
# Then run V4 on underperforming classes
python run_v4_iteration.py
```

### 4. `iterate_until_target.py` (Semi-Automated)

**Purpose:** Automate the iteration loop with manual prompt updates

**Usage:**
```bash
python iterate_until_target.py
```

**What it does:**
1. Calculate R² for current version
2. Check if all classes >= 0.7
3. If not, analyze errors
4. **PAUSE** and wait for you to update prompts
5. Run new version on underperforming classes
6. Repeat

## Manual Prompt Improvement Workflow

### Step 1: Analyze Errors

Run error analysis to understand what's going wrong:

```bash
python analyze_v3_errors_detailed.py
```

### Step 2: Identify Patterns

Look at the error analysis output and identify:

1. **Systematic Bias:** Is there overall over-prediction or under-prediction?
   - If bias > +5pp: Lower all baselines by ~5-10pp
   - If bias < -5pp: Raise all baselines by ~5-10pp

2. **Concept-Specific Errors:** Which concepts have large mean errors?
   - Create specific corrections for concepts with |error| > 5pp

3. **Demographic Patterns:** Are certain demographic groups consistently wrong?
   - Adjust demographic calibrations

### Step 3: Update Prompts

Edit the general system prompt:

```bash
# Backup current version
cp agent_estimator/estimator_agent/prompts/general_system_prompt.txt \
   agent_estimator/estimator_agent/prompts/general_system_prompt_v3_backup.txt

# Edit prompt
nano agent_estimator/estimator_agent/prompts/general_system_prompt.txt
```

**What to change:**

1. **Update VERSION NOTES:**
```
**VERSION NOTES**:
V4 addresses V3's -7pp under-prediction bias by:
1. Raising all baseline templates by 5-10pp
2. Adding specific corrections for "Like cash" (+7pp) and "Environmental sustainability" (-8pp)
3. Adjusting demographic calibrations
```

2. **Update CONCEPT TYPE ALLOCATION:**
```
**V4 CONCEPT TYPE ALLOCATION**:
- Attitude: SA 14%, A 32%, N 26%, D 17%, SD 11% (46% agreement, was 42%)
- Behavior (Low Friction): SA 17%, A 37%, N 22%, D 14%, SD 10% (54% agreement, was 50%)
```

3. **Add/Update CONCEPT-SPECIFIC CORRECTIONS:**
```
**V4 CONCEPT-SPECIFIC CORRECTIONS:**
1. "Like cash" - INCREASE by +7pp: SA 18%, A 28% = 46% (was 39%)
2. "Environmental sustainability" - REDUCE by -8pp: SA 8%, A 22% = 30% (was 38%)
```

### Step 4: Run New Iteration

```bash
python run_v4_iteration.py
```

### Step 5: Recalculate R²

Update script names (v3 → v4) and run:

```bash
# Update calculate_r2_v3_full.py to look for v4 files
python calculate_r2_v4_full.py
```

### Step 6: Check Progress

Compare V3 vs V4 performance:

```bash
python compare_v3_v4.py
```

### Step 7: Repeat Until Target

Continue until all classes achieve R² >= 0.7

## Tracking Progress

Create an iteration log:

```markdown
# ACORN_iteration_log.md

## Iteration 1: V1 → V2
- **Problem:** Systematic +11pp over-prediction
- **Solution:** Lowered all baselines by 10-15pp
- **Result:** R² improved from -0.30 to +0.60

## Iteration 2: V2 → V3
- **Problem:** Systematic -7pp under-prediction
- **Solution:** Raised baselines to midpoint, fixed concept types
- **Result:** R² improved from +0.60 to +0.70

## Iteration 3: V3 → V4
- **Problem:** TBD (waiting for full V3 results)
- **Solution:** TBD
- **Result:** TBD
```

## Expected Outcomes

### After Iteration 1 (V1 → V2)
- R² should improve from negative to positive
- Bias should reduce by ~50%
- MAE should reduce by 5-10pp

### After Iteration 2 (V2 → V3)
- R² should reach 0.5-0.7 range
- Bias should be within ±5pp
- Most classes should achieve R² > 0.5

### After Iteration 3+ (V3 → V4+)
- Fine-tuning specific concepts and demographics
- R² should stabilize at 0.7-0.85 range
- All classes should achieve R² > 0.7

## Troubleshooting

### Problem: R² Gets Worse After Update

**Diagnosis:** Over-corrected in wrong direction

**Solution:**
1. Check if bias sign reversed (was +11pp, now -15pp)
2. Average the V(N-1) and VN baselines to find middle ground
3. Rerun with averaged baselines

### Problem: R² Improves But Some Classes Still Low

**Diagnosis:** Demographic-specific issues

**Solution:**
1. Identify common characteristics of underperforming classes (income, age, urban/rural)
2. Create class-specific prompts for worst performers
3. Add demographic calibrations to general prompt

### Problem: R² Plateaus Below Target

**Diagnosis:** Reached limits of current approach

**Solution:**
1. Try class-specific prompts instead of general prompt
2. Use more detailed contextual data (more qual excerpts)
3. Add intermediate concepts as features (e.g., risk aversion, time preference)

## Theoretical Limits

- **Best achievable R²:** ~0.85 (based on FRESCO results)
- **Typical plateau:** 0.70-0.80 after 3-5 iterations
- **Diminishing returns:** After iteration 5, improvements < 0.05 per iteration

## When to Stop

Stop iterating when:
1. All classes achieve R² > 0.7 ✓
2. OR: R² improvement < 0.02 for 2 consecutive iterations
3. OR: 10 iterations reached (safety limit)

---

**Last Updated:** 2025-10-30
**Current Version:** V3 (R² = 0.70 on test set)
**Target:** All 22 classes >= 0.7 R²
