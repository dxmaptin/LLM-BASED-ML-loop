# ACORN Data Setup - Complete

## Overview

Successfully created the complete ACORN pipeline structure with 22 demographic classes, replicating the FRESCO workflow.

## What Was Created

### 1. Handpicked Concepts (10 Attitude Questions)

**File:** `Handpicked_ACORN_10.csv`

| # | Concept | Category |
|---|---------|----------|
| 1 | I think brands should consider environmental sustainability when putting on events | Environment |
| 2 | Make an effort to cut down on the use of gas / electricity at home | Environment |
| 3 | Fuel consumption is the most important feature when buying a new car | Environment |
| 4 | I don't like the idea of being in debt | Financial Attitudes |
| 5 | I am very good at managing money | Financial Attitudes |
| 6 | It is important to be well insured for everything | Financial Attitudes |
| 7 | Healthy Eating | Lifestyle |
| 8 | Financial security after retirement is your own responsibility | Financial Attitudes |
| 9 | Switching utilities suppliers is well worth the effort | Financial Attitudes |
| 10 | I like to use cash when making purchases | Financial Attitudes |

### 2. Ground Truth Files

**Files Created:**
- `ACORN_ground_truth_22classes.csv` - Numeric concept IDs (Concept_1 ... Concept_10)
- `ACORN_ground_truth_named.csv` - Full concept names as column headers

**Format:** 22 rows (classes) × 10 columns (concepts) + Class name column

Each cell contains the actual percentage/value for that class-concept combination from the ACORN survey data.

### 3. Folder Structure

**Main Directory:** `demographic_runs_ACORN/`

**22 Class Subdirectories Created:**

1. `exclusive_addresses/`
2. `flourishing_capital/`
3. `upmarket_families/`
4. `commuter-belt_wealth/`
5. `prosperous_professionals/`
6. `mature_success/`
7. `settled_suburbia/`
8. `metropolitan_surroundings/`
9. `up-and-coming_urbanites/`
10. `aspiring_communities/`
11. `semi-rural_maturity/`
12. `traditional_homeowners/`
13. `family_renters/`
14. `urban_diversity/`
15. `stable_seniors/`
16. `tenant_living/`
17. `limited_budgets/`
18. `hard-up_households/`
19. `cash-strapped_families/`
20. `constrained_penisoners/`
21. `challenging_circumstances/`
22. `not_private_households/`

### 4. Each Class Directory Contains

```
<class_name>/
├── concepts_to_test.csv               (10 handpicked questions)
├── Flattened Data Inputs/
│   └── ACORN_<class_name>.csv        (Class-specific quantitative data)
└── Textual Data Inputs/
    └── <class_name>_profile.txt      (Pen portrait from Accorn.txt)
```

**Example: `exclusive_addresses/`**
- Contains only data for "Exclusive Addresses" class
- Ready for IR → Estimator → Critic pipeline
- Same format as FRESCO demographic_runs

---

## Data Format Details

### concepts_to_test.csv (Each Class)
```csv
Concept
I think brands should consider environmental sustainability...
Make an effort to cut down on the use of gas / electricity...
...
```

### Flattened Data Inputs CSV (Class-Specific)
```csv
Category,Question,Answer,Value
Population,Age,Age 0 - 4,0.0396883
Environment,Action,Make an effort...,0.7234
Finance,Financial Attitudes,I don't like debt...,0.6543
...
```

- **Category:** High-level grouping (Environment, Finance, etc.)
- **Question:** Specific question type
- **Answer:** Specific response option
- **Value:** Percentage/proportion for this class

### Ground Truth CSV
```csv
Class,Concept_1,Concept_2,...,Concept_10
Exclusive Addresses,0.7234,0.6432,...,0.5123
Flourishing Capital,0.6891,0.7012,...,0.4987
...
```

---

## Next Steps: Running the Pipeline

### Step 1: Run Predictions for One Class (Test)

```bash
cd "c:\Users\d.zhang\Desktop\Experiments"

# Test with one class first
python -c "
from agent_estimator.orchestrator.runner import run_agentic_pipeline

run_agentic_pipeline(
    concepts_csv='demographic_runs_ACORN/exclusive_addresses/concepts_to_test.csv',
    demographic='exclusive_addresses',
    output_csv='demographic_runs_ACORN/exclusive_addresses/predictions.csv',
    runs_per_iteration=5,
    max_iterations=3,
    data_dirs={
        'quant': 'demographic_runs_ACORN/exclusive_addresses/Flattened Data Inputs',
        'qual': 'demographic_runs_ACORN/exclusive_addresses/Textual Data Inputs'
    }
)
"
```

### Step 2: Create Batch Runner for All 22 Classes

Create `run_ACORN_all_classes.py`:

```python
from agent_estimator.orchestrator.runner import run_agentic_pipeline
from pathlib import Path

BASE_DIR = Path("demographic_runs_ACORN")

acorn_classes = [
    "exclusive_addresses",
    "flourishing_capital",
    "upmarket_families",
    # ... all 22 classes
]

for acorn_class in acorn_classes:
    print(f"\n{'='*70}")
    print(f"Processing: {acorn_class}")
    print('='*70)

    class_dir = BASE_DIR / acorn_class

    run_agentic_pipeline(
        concepts_csv=class_dir / "concepts_to_test.csv",
        demographic=acorn_class,
        output_csv=class_dir / "predictions.csv",
        runs_csv=class_dir / "predictions_runs.csv",
        runs_per_iteration=5,
        max_iterations=3,
        data_dirs={
            'quant': class_dir / "Flattened Data Inputs",
            'qual': class_dir / "Textual Data Inputs"
        }
    )

    print(f"✓ Completed: {acorn_class}")
```

### Step 3: Evaluate Results

Compare predictions vs ground truth:

```python
import pandas as pd
from sklearn.metrics import r2_score, mean_absolute_error

# Load ground truth
gt = pd.read_csv('ACORN_ground_truth_22classes.csv')

# Load predictions for a class
pred = pd.read_csv('demographic_runs_ACORN/exclusive_addresses/predictions.csv')

# Calculate metrics
# (Convert prediction distributions to agreement percentages)
pred['predicted_agree'] = pred['SA'] + pred['A']

# Compare with ground truth for this class
# ... (similar to FRESCO evaluation)
```

### Step 4: Reinforcement Learning Loop

After initial run, analyze errors and create ACORN-specific prompts:

1. **Calculate errors** per class
2. **Identify patterns** (e.g., wealthy vs budget-constrained classes)
3. **Create demographic-specific prompts** in `agent_estimator/estimator_agent/prompts.py`

```python
DEMOGRAPHIC_PROMPTS["exclusive_addresses"] = """
[Profile]
Ultra-wealthy, no financial concerns, luxury-focused

[Learned Calibrations]
- Environmental attitudes: +15pp (high concern despite high carbon footprint)
- Financial conservatism: Mixed (wealthy but may take risks)
- Premium brands: +25pp (quality over price)
- Digital adoption: Moderate (delegate to staff)
"""

DEMOGRAPHIC_PROMPTS["cash-strapped_families"] = """
[Profile]
Very limited budgets, financial stress, pragmatic

[Learned Calibrations]
- Financial attitudes: High agreement with caution (+20pp)
- Price sensitivity: Very high (+30pp for budget options)
- Premium brands: Low (-25pp, value-focused)
- Financial security: High concern (+20pp)
"""
```

4. **Re-run** predictions with updated prompts
5. **Iterate** until target accuracy achieved

---

## Comparison: ACORN vs FRESCO

| Aspect | FRESCO | ACORN |
|--------|--------|-------|
| **Classes** | 12 UK segments | 22 UK segments |
| **Focus** | Income/lifestyle groups | Granular geodemographic |
| **Questions** | 10 handpicked | 10 handpicked |
| **Data Format** | Identical | Identical |
| **Folder Structure** | `demographic_runs/` | `demographic_runs_ACORN/` |
| **Pipeline** | IR → Estimator → Critic | Same |

---

## Files Created (Summary)

```
Experiments/
├── Handpicked_ACORN_10.csv                    ← 10 attitude questions
├── ACORN_ground_truth_22classes.csv           ← Ground truth (numeric IDs)
├── ACORN_ground_truth_named.csv               ← Ground truth (named)
├── setup_acorn_data.py                        ← Setup script (reusable)
├── ACORN_SETUP_COMPLETE.md                    ← This file
│
└── demographic_runs_ACORN/                    ← Main directory
    ├── exclusive_addresses/
    │   ├── concepts_to_test.csv
    │   ├── Flattened Data Inputs/
    │   │   └── ACORN_exclusive_addresses.csv
    │   └── Textual Data Inputs/
    │       └── exclusive_addresses_profile.txt
    │
    ├── flourishing_capital/
    │   ├── concepts_to_test.csv
    │   ├── Flattened Data Inputs/
    │   │   └── ACORN_flourishing_capital.csv
    │   └── Textual Data Inputs/
    │       └── flourishing_capital_profile.txt
    │
    └── ... (20 more classes)
```

---

## Quick Start Commands

**1. Verify Setup:**
```bash
ls demographic_runs_ACORN/
# Should show 22 directories

ls demographic_runs_ACORN/exclusive_addresses/
# Should show: concepts_to_test.csv, Flattened Data Inputs/, Textual Data Inputs/
```

**2. Check Handpicked Concepts:**
```bash
cat Handpicked_ACORN_10.csv
# Should show 10 attitude questions
```

**3. Check Ground Truth:**
```bash
head ACORN_ground_truth_22classes.csv
# Should show 22 rows (classes) with Concept_1...Concept_10 columns
```

**4. Test One Class:**
```bash
python run_ACORN_single_class.py exclusive_addresses
```

**5. Run All 22 Classes:**
```bash
python run_ACORN_all_classes.py
```

---

## Troubleshooting

### Issue: Pen portraits not extracted

**Solution:** The pen portrait extraction relies on parsing `Accorn.txt`. If sections weren't found, manually copy relevant sections from the text file.

### Issue: CSV format mismatch

**Solution:** Verify that `ACORN Flattened Data_C.xlsx` follows the same format as `CACI Flattened Data_C.xlsx` used for FRESCO.

### Issue: Missing data for a class

**Solution:** Check if the class exists in the Excel file. Some classes may have empty/null data.

---

## Expected Accuracy (Initial Baseline)

Based on FRESCO results (before RL training):

- **Baseline (no demographic prompts):** ~62-68% R² (~16% MAE)
- **After RL (with demographic prompts):** ~80-88% R² (~5-8% MAE)
- **Top performers:** >90% R² (<4% MAE)

ACORN has 22 classes (vs FRESCO's 12), so expect:
- More variation in performance across classes
- Richer vs poorer classes may have distinct patterns
- Urban vs rural classes may differ significantly

---

## Status: ✓ READY FOR PIPELINE EXECUTION

All files created and verified. You can now:

1. ✅ Run predictions on any/all 22 ACORN classes
2. ✅ Evaluate against ground truth
3. ✅ Train demographic-specific prompts via RL loop
4. ✅ Compare ACORN vs FRESCO performance

**Next immediate action:** Run test prediction on one class to verify the pipeline works correctly.

---

*Setup completed: October 29, 2025*
*Script: `setup_acorn_data.py`*
*Total classes: 22*
*Total concepts: 10*
