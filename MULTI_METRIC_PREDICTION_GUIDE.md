# Multi-Metric Prediction - Quick Start Guide

## Overview

The `run_multi_metric_predictions.py` script predicts **all 11 metrics** for your holdout product concepts and outputs them in a **grouped CSV format** for easy analysis.

---

## Output Format

### CSV Structure (Grouped by Product, then Metric)

```csv
concept_id,product_name,metric_key,metric_name,predicted_value,actual_value,difference,error_percent,priority
exfoliating_scrub,Exfoliating Body Scrub,target_top2box_intent,Purchase Intent (Target),38.0,37.0,1.0,2.7,P1
exfoliating_scrub,Exfoliating Body Scrub,appeal_pcttop_2,Appeal,35.0,38.0,-3.0,7.9,P2
exfoliating_scrub,Exfoliating Body Scrub,uniqueness_pcttop_2,Uniqueness,42.0,40.0,2.0,5.0,P2
...
exfoliating_scrub,Exfoliating Body Scrub,star_rating,Overall Star Rating,65.0,N/A,N/A,N/A,P4
ph_sensitive_wash,pH Sensitive Skin Body Wash,target_top2box_intent,Purchase Intent (Target),40.0,29.0,11.0,37.9,P1
ph_sensitive_wash,pH Sensitive Skin Body Wash,appeal_pcttop_2,Appeal,38.0,37.0,1.0,2.7,P2
...
```

**Key features:**
- **Rows 1-11:** All metrics for Product 1
- **Rows 12-22:** All metrics for Product 2
- **Rows 23-33:** All metrics for Product 3
- **Rows 34-44:** All metrics for Product 4

**Columns:**
- `concept_id`: Unique product identifier
- `product_name`: Full product name
- `metric_key`: Metric variable name (for coding)
- `metric_name`: Human-readable metric name
- `predicted_value`: AI prediction (0-100 scale)
- `actual_value`: Ground truth from concept test
- `difference`: Predicted - Actual (positive = over-prediction)
- `error_percent`: Absolute error as % of actual value
- `priority`: P1 (primary), P2 (diagnostic), P3 (execution), P4 (behavioral)

---

## How to Run

### Step 1: Ensure Prerequisites

Make sure you've already run:
```bash
# One-time setup
python setup_witty_optimist_data.py

# Pattern discovery (Agent 1 training)
python run_pattern_discovery_witty_optimist.py
```

### Step 2: Run Multi-Metric Predictions

```bash
python run_multi_metric_predictions.py
```

**Expected runtime:** ~5-8 minutes (1-2 min per product × 4 products)

**What happens:**
1. Loads playbook (prediction rules)
2. Loads 4 holdout concepts with vision + verbatim data
3. For each concept:
   - Calls GPT-4o to predict all 11 metrics in one shot
   - Validates predictions with consistency checks
   - Displays results in terminal
4. Saves grouped CSV and detailed JSON
5. Calculates MAE per metric and overall stats

### Step 3: Review Results

**Output files created:**
- `project_data/witty_optimist_runs/multi_metric_predictions_YYYYMMDD_HHMMSS.csv`
- `project_data/witty_optimist_runs/multi_metric_predictions_detailed_YYYYMMDD_HHMMSS.json`

**Open CSV in Excel/Python:**
```python
import pandas as pd

df = pd.read_csv('project_data/witty_optimist_runs/multi_metric_predictions_20251118_143022.csv')

# View all predictions for one product
product_1 = df[df['product_name'] == 'Exfoliating Body Scrub and Massage Bar']
print(product_1)

# View one metric across all products
intent = df[df['metric_key'] == 'target_top2box_intent']
print(intent)

# Filter by priority
primary_metrics = df[df['priority'] == 'P1']
print(primary_metrics)
```

---

## Terminal Output Preview

```
================================================================================
MULTI-METRIC PREDICTION PIPELINE
================================================================================

Predicting 11 metrics for holdout concepts
Output will be grouped by product, then by metric

=== STEP 1: Loading Playbook ===
[OK] Loaded playbook: 4521 characters

=== STEP 2: Loading Holdout Concepts ===
  [OK] Loaded: Exfoliating Body Scrub and Massage Bar
  [OK] Loaded: pH Sensitive Skin Body Wash
  [OK] Loaded: S&G's Glow On Gradual Tan Lotion
  [OK] Loaded: Soap & Glory Girl's Night Out Refresh Queen

Total holdout concepts: 4

=== STEP 3: Running Multi-Metric Predictions ===

================================================================================
[1/4] Predicting All Metrics: Exfoliating Body Scrub and Massage Bar
================================================================================

  Calling GPT-4o for prediction...

  Predictions Complete!
  ----------------------------------------------------------------------------
  Metric                         Predicted     Actual       Diff
  ----------------------------------------------------------------------------
  Purchase Intent (Target)            38.0       37.0       +1.0 ✓
  Appeal                              35.0       38.0       -3.0 ✓
  Uniqueness                          42.0       40.0       +2.0 ✓
  Relevance                           38.0       36.0       +2.0 ✓
  Excitement                          68.0       64.0       +4.0 ✓
  Price/Value                         48.0       45.0       +3.0 ✓
  Believability                       36.0       34.0       +2.0 ✓
  Understanding                       62.0       60.0       +2.0 ✓
  Trial Intent                        40.0       27.0      +13.0 ✗
  Incremental Trial                   28.0       25.0       +3.0 ✓
  Overall Star Rating                 60.0        N/A        N/A ?
  ----------------------------------------------------------------------------

...

================================================================================
=== STEP 4: Generating Grouped CSV Output ===
================================================================================

[OK] Saved grouped CSV: project_data/witty_optimist_runs/multi_metric_predictions_20251118_143022.csv
     Format: 4 products × 11 metrics = 44 rows
[OK] Saved detailed JSON: project_data/witty_optimist_runs/multi_metric_predictions_detailed_20251118_143022.json

================================================================================
=== STEP 5: Summary Statistics ===
================================================================================

Mean Absolute Error (MAE) by Metric:
------------------------------------------------------------
Metric                                    MAE        N
------------------------------------------------------------
Purchase Intent (Target)                 5.50pp       4
Appeal                                   3.25pp       4
Uniqueness                               6.75pp       4
Relevance                                4.00pp       4
Excitement                               5.25pp       4
Price/Value                              8.50pp       4
Believability                            3.75pp       4
Understanding                            4.25pp       4
Trial Intent                             9.00pp       4
Incremental Trial                        5.50pp       4
Overall Star Rating                       N/A         0
============================================================

Overall Performance:
  Total predictions: 44
  Valid predictions: 40
  Overall MAE: 5.59 percentage points
  Overall RMSE: 7.12 percentage points
  Within 5pp: 24/40 (60.0%)
  Within 10pp: 35/40 (87.5%)

================================================================================
=== Sample Output (First Product, All Metrics) ===
================================================================================

Product: Exfoliating Body Scrub and Massage Bar

   concept_id                    product_name              metric_key  ...
exfoliating_scrub  Exfoliating Body Scrub  target_top2box_intent  ...
exfoliating_scrub  Exfoliating Body Scrub       appeal_pcttop_2  ...
...

================================================================================
PREDICTION COMPLETE!
================================================================================

Output file: project_data/witty_optimist_runs/multi_metric_predictions_20251118_143022.csv
Detailed reasoning: project_data/witty_optimist_runs/multi_metric_predictions_detailed_20251118_143022.json

Next steps:
  1. Review predictions in Excel or pandas
  2. Analyze error patterns by metric
  3. Refine playbook based on systematic errors
  4. Re-run with updated playbook
```

---

## Analysis Examples

### Example 1: Find Worst Predictions

```python
import pandas as pd

df = pd.read_csv('multi_metric_predictions.csv')

# Sort by absolute error
worst = df[df['difference'].notna()].copy()
worst['abs_error'] = worst['difference'].abs()
worst_10 = worst.nlargest(10, 'abs_error')[['product_name', 'metric_name', 'predicted_value', 'actual_value', 'difference']]

print("Top 10 Worst Predictions:")
print(worst_10)
```

### Example 2: Compare Products

```python
# Aggregate by product
product_summary = df.groupby('product_name').agg({
    'difference': lambda x: x.abs().mean(),
    'predicted_value': 'mean',
    'actual_value': 'mean'
}).round(1)

product_summary.columns = ['MAE', 'Avg Predicted', 'Avg Actual']
print(product_summary.sort_values('MAE'))
```

### Example 3: Metric Performance Comparison

```python
# Which metrics are easiest/hardest to predict?
metric_performance = df[df['difference'].notna()].groupby('metric_name').agg({
    'difference': lambda x: x.abs().mean(),
    'error_percent': 'mean'
}).round(2)

metric_performance.columns = ['MAE (pp)', 'MAPE (%)']
print(metric_performance.sort_values('MAE (pp)'))
```

### Example 4: Priority-Based Analysis

```python
# Performance by metric priority
priority_perf = df[df['difference'].notna()].groupby('priority').agg({
    'difference': lambda x: x.abs().mean()
}).round(2)

print("MAE by Priority:")
print(priority_perf)
# Expected: P2 metrics (perceptual) easier than P3 (execution)
```

---

## Understanding the Detailed JSON Output

The JSON file contains full reasoning for each prediction:

```json
[
  {
    "concept_id": "exfoliationg_body_scrub_and_massage_bar",
    "concept_name": "Exfoliating Body Scrub and Massage Bar",
    "metrics": [
      {
        "metric_key": "target_top2box_intent",
        "metric_name": "Purchase Intent (Target)",
        "predicted": 38.0,
        "actual": 37.0,
        "difference": 1.0,
        "error_percent": 2.7
      },
      ...
    ],
    "overall_confidence": 75,
    "reasoning": {
      "overall_assessment": "Concept shows moderate appeal with innovative dual-function...",
      "key_strengths": [
        "Innovative exfoliation + massage combination",
        "Vegan and skin-friendly positioning",
        "Multiple scent options"
      ],
      "key_weaknesses": [
        "Moderate uniqueness vs competitors",
        "Price value perception unclear",
        "Limited proof points for efficacy"
      ],
      "consistency_check": "Trial (40%) aligns with intent (38%). Appeal (35%) is slightly lower than expected given intent, suggesting niche positioning."
    }
  },
  ...
]
```

**Use this for:**
- Understanding WHY the model made certain predictions
- Identifying systematic biases in reasoning
- Improving the playbook with specific examples

---

## Troubleshooting

### Issue: Missing actual values (showing N/A)

**Cause:** Metric not available in ground truth data

**Fix:** Check `concept_test_wide.csv` - some metrics may not have been measured for all concepts

### Issue: Large errors on specific metrics

**Common culprits:**
- `price_value_pcttop_2`: Highly dependent on whether pricing was shown
- `inc_trial_brand`: Requires brand loyalty context not in data
- `trial`: Sometimes diverges from intent due to trial barriers

**Fix:** Update playbook with metric-specific rules

### Issue: Script fails with API error

**Check:**
1. OpenAI API key is set: `echo $OPENAI_API_KEY`
2. You have sufficient API credits
3. Internet connection is stable

**Retry:** Script uses temperature=0.3 for consistency, so retrying should give similar results

---

## Customization Options

### Predict Subset of Metrics

Edit the `METRIC_ORDER` list in the script:

```python
# Only predict core metrics
METRIC_ORDER = [
    "target_top2box_intent",
    "appeal_pcttop_2",
    "uniqueness_pcttop_2",
    "excitement_pcttop_2"
]
```

### Change Model

Replace `gpt-4o` with another model:

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",  # Cheaper, faster, slightly less accurate
    # or model="gpt-4-turbo"
    ...
)
```

### Adjust Temperature

```python
temperature=0.1,  # More deterministic (less variation)
# or
temperature=0.5,  # More creative (more variation)
```

**Recommendation:** Keep at 0.2-0.3 for balanced predictions

---

## Cost Estimation

**Per product prediction:**
- Input tokens: ~6,000 (playbook + concept data)
- Output tokens: ~800 (11 metric predictions + reasoning)
- Cost per product (GPT-4o): ~$0.05

**For 4 holdout products:** ~$0.20 total

**For 20 training products:** ~$1.00 total

---

## Next Steps After Running

1. **Review CSV in Excel**
   - Pivot table: Products (rows) × Metrics (columns)
   - Conditional formatting for errors > 10pp

2. **Identify Error Patterns**
   - Which product types are hard to predict?
   - Which metrics consistently over/under-predict?

3. **Update Playbook**
   - Add rules for systematic errors
   - Include examples from best predictions

4. **Re-run and Compare**
   - Track improvement across iterations
   - Calculate R² improvement

5. **Expand to More Products**
   - Add more training concepts
   - Test on new holdout set

---

**Created:** 2025-11-18
**Script:** `run_multi_metric_predictions.py`
**See also:** `BLUEPRINT_EXPERIMENT_FRAMEWORK.md`, `METRICS_REFERENCE_SHEET.md`
