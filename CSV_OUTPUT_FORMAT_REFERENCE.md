# Multi-Metric Prediction - CSV Output Format

## Quick Visual Reference

### CSV Structure

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         GROUPED BY PRODUCT                                   │
│                                                                              │
│  Product 1 (Rows 1-11)                                                      │
│  ├─ Row  1: Purchase Intent      | Predicted: 38  | Actual: 37  | Diff: +1  │
│  ├─ Row  2: Appeal               | Predicted: 35  | Actual: 38  | Diff: -3  │
│  ├─ Row  3: Uniqueness           | Predicted: 42  | Actual: 40  | Diff: +2  │
│  ├─ Row  4: Relevance            | Predicted: 38  | Actual: 36  | Diff: +2  │
│  ├─ Row  5: Excitement           | Predicted: 68  | Actual: 64  | Diff: +4  │
│  ├─ Row  6: Price/Value          | Predicted: 48  | Actual: 45  | Diff: +3  │
│  ├─ Row  7: Believability        | Predicted: 36  | Actual: 34  | Diff: +2  │
│  ├─ Row  8: Understanding        | Predicted: 62  | Actual: 60  | Diff: +2  │
│  ├─ Row  9: Trial Intent         | Predicted: 40  | Actual: 27  | Diff: +13 │
│  ├─ Row 10: Incremental Trial    | Predicted: 28  | Actual: 25  | Diff: +3  │
│  └─ Row 11: Star Rating          | Predicted: 60  | Actual: N/A | Diff: N/A │
│                                                                              │
│  Product 2 (Rows 12-22)                                                     │
│  ├─ Row 12: Purchase Intent      | Predicted: 40  | Actual: 29  | Diff: +11 │
│  ├─ Row 13: Appeal               | ...                                       │
│  └─ ...                                                                      │
│                                                                              │
│  Product 3 (Rows 23-33)                                                     │
│  Product 4 (Rows 34-44)                                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Column Definitions

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `concept_id` | string | Unique product identifier | `exfoliationg_body_scrub_and_massage_bar` |
| `product_name` | string | Full product name | `Exfoliating Body Scrub and Massage Bar` |
| `metric_key` | string | Variable name for coding | `target_top2box_intent` |
| `metric_name` | string | Human-readable name | `Purchase Intent (Target)` |
| `predicted_value` | float | AI prediction (0-100) | `38.0` |
| `actual_value` | float | Ground truth from test | `37.0` |
| `difference` | float | Predicted - Actual | `1.0` |
| `error_percent` | float | |Difference| / Actual × 100 | `2.7` |
| `priority` | string | P1/P2/P3/P4 tier | `P1` |

---

## How to Use in Excel

### Step 1: Import CSV

1. Open Excel
2. File > Import > CSV
3. Select `multi_metric_predictions_YYYYMMDD_HHMMSS.csv`
4. Use default delimiters

### Step 2: Create Pivot Table

**Layout:**
- **Rows:** `product_name`, then `metric_name`
- **Columns:** None (or `priority` for grouping)
- **Values:** `predicted_value`, `actual_value`, `difference`

**Result:**
```
Product Name                        | Predicted | Actual | Difference
====================================|===========|========|============
Exfoliating Body Scrub              |           |        |
  Purchase Intent (Target)          |   38.0    |  37.0  |   +1.0
  Appeal                            |   35.0    |  38.0  |   -3.0
  Uniqueness                        |   42.0    |  40.0  |   +2.0
  ...                               |    ...    |   ...  |    ...
pH Sensitive Skin Body Wash         |           |        |
  Purchase Intent (Target)          |   40.0    |  29.0  |  +11.0
  ...                               |    ...    |   ...  |    ...
```

### Step 3: Add Conditional Formatting

**Highlight large errors:**
1. Select `difference` column
2. Conditional Formatting > Color Scales
3. Red (large errors) → Yellow (medium) → Green (small errors)

**Or use Icon Sets:**
- ✓ Green checkmark: |difference| ≤ 5
- ⚠ Yellow warning: 5 < |difference| ≤ 10
- ✗ Red X: |difference| > 10

### Step 4: Create Charts

**Chart 1: Predicted vs Actual (Scatter)**
- X-axis: `actual_value`
- Y-axis: `predicted_value`
- Add diagonal line (y=x) for perfect predictions
- Points above line = over-predictions
- Points below line = under-predictions

**Chart 2: Error by Metric (Bar)**
- X-axis: `metric_name`
- Y-axis: Average absolute `difference`
- Sort by error descending
- Identify hardest metrics to predict

**Chart 3: Error by Product (Bar)**
- X-axis: `product_name`
- Y-axis: Average absolute `difference`
- Sort by error descending
- Identify hardest products to predict

---

## How to Use in Python/Pandas

### Load and Explore

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('multi_metric_predictions_YYYYMMDD_HHMMSS.csv')

# Quick overview
print(df.head(22))  # First 2 products
print(df.info())
print(df.describe())
```

### Analysis 1: Product-Level Summary

```python
# Average error per product
product_summary = df.groupby('product_name').agg({
    'difference': lambda x: x.abs().mean(),
    'predicted_value': 'mean',
    'actual_value': 'mean'
}).round(1)

product_summary.columns = ['Avg Error (pp)', 'Avg Predicted', 'Avg Actual']
print(product_summary.sort_values('Avg Error (pp)'))
```

**Output:**
```
                                    Avg Error (pp)  Avg Predicted  Avg Actual
Girl's Night Out Refresh Queen                1.5           62.3        61.8
Exfoliating Body Scrub                        3.2           45.1        43.9
Glow On Gradual Tan Lotion                    6.8           48.7        55.5
pH Sensitive Skin Body Wash                   7.1           42.3        35.2
```

### Analysis 2: Metric-Level Summary

```python
# Average error per metric
metric_summary = df[df['difference'].notna()].groupby('metric_name').agg({
    'difference': lambda x: x.abs().mean(),
    'error_percent': 'mean'
}).round(2)

metric_summary.columns = ['MAE (pp)', 'MAPE (%)']
print(metric_summary.sort_values('MAE (pp)'))
```

**Output:**
```
                            MAE (pp)  MAPE (%)
Believability                   3.75      9.8
Appeal                          3.25      7.2
Understanding                   4.25      6.1
Purchase Intent (Target)        5.50      8.3
Trial Intent                    9.00     18.5
```

### Analysis 3: Predicted vs Actual Scatter Plot

```python
import matplotlib.pyplot as plt

# Filter valid predictions
valid = df[df['difference'].notna()]

# Create scatter plot
plt.figure(figsize=(10, 10))
plt.scatter(valid['actual_value'], valid['predicted_value'],
            alpha=0.6, s=100, c=valid['priority'].map({
                'P1': 'red', 'P2': 'blue', 'P3': 'green', 'P4': 'orange'
            }))

# Add diagonal line (perfect prediction)
max_val = max(valid['actual_value'].max(), valid['predicted_value'].max())
plt.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, label='Perfect Prediction')

# Add ±5pp and ±10pp zones
plt.fill_between([0, max_val], [0, max_val-5], [0, max_val+5], alpha=0.1, color='green', label='±5pp')
plt.fill_between([0, max_val], [0, max_val-10], [0, max_val+10], alpha=0.05, color='yellow', label='±10pp')

plt.xlabel('Actual Value', fontsize=12)
plt.ylabel('Predicted Value', fontsize=12)
plt.title('Multi-Metric Predictions: Predicted vs Actual', fontsize=14)
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('predicted_vs_actual.png', dpi=300)
plt.show()
```

### Analysis 4: Error Heatmap

```python
import seaborn as sns

# Pivot to get products × metrics
heatmap_data = df.pivot(index='product_name', columns='metric_name', values='difference')

# Plot heatmap
plt.figure(figsize=(14, 6))
sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlGn_r',
            center=0, vmin=-15, vmax=15, cbar_kws={'label': 'Error (pp)'})
plt.title('Prediction Errors by Product and Metric', fontsize=14)
plt.xlabel('Metric', fontsize=12)
plt.ylabel('Product', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('error_heatmap.png', dpi=300)
plt.show()
```

### Analysis 5: Calculate R² per Metric

```python
from sklearn.metrics import r2_score

# Calculate R² for each metric
r2_scores = []

for metric in df['metric_key'].unique():
    metric_data = df[df['metric_key'] == metric]
    valid = metric_data[metric_data['actual_value'].notna() & metric_data['predicted_value'].notna()]

    if len(valid) > 1:
        r2 = r2_score(valid['actual_value'], valid['predicted_value'])
        mae = valid['difference'].abs().mean()

        r2_scores.append({
            'metric': metric_data.iloc[0]['metric_name'],
            'r2': r2,
            'mae': mae,
            'n': len(valid)
        })

r2_df = pd.DataFrame(r2_scores).sort_values('r2', ascending=False)
print(r2_df)
```

**Output:**
```
                        metric    r2   mae  n
Appeal                    0.78  3.25  4
Purchase Intent (Target)  0.68  5.50  4
Understanding             0.62  4.25  4
Excitement                0.45  5.25  4
Trial Intent             -0.12  9.00  4  # Negative R² = worse than baseline!
```

---

## Common Data Patterns to Look For

### Pattern 1: Consistent Over/Under-Prediction

**Check:**
```python
df.groupby('metric_name')['difference'].mean()
```

**If all differences are positive:** Model systematically over-predicts
**If all differences are negative:** Model systematically under-predicts

**Fix:** Adjust baseline in playbook

### Pattern 2: High Variance in Errors

**Check:**
```python
df.groupby('metric_name')['difference'].std()
```

**If high std:** Model is inconsistent (sometimes high, sometimes low)

**Fix:** Add more specific rules to playbook

### Pattern 3: Correlated Errors

**Check:**
```python
# Do errors on Appeal correlate with errors on Intent?
appeal_errors = df[df['metric_key'] == 'appeal_pcttop_2'].set_index('product_name')['difference']
intent_errors = df[df['metric_key'] == 'target_top2box_intent'].set_index('product_name')['difference']

correlation = appeal_errors.corr(intent_errors)
print(f"Appeal-Intent Error Correlation: {correlation:.2f}")
```

**If high correlation:** Model makes same mistakes across related metrics
**Fix:** Improve shared features (e.g., vision analysis)

### Pattern 4: Priority-Based Performance

**Check:**
```python
df.groupby('priority')['difference'].apply(lambda x: x.abs().mean())
```

**Expected:**
- P1 (primary): Medium MAE (~5pp)
- P2 (perceptual): Low MAE (~3-4pp) - easier to predict
- P3 (execution): High MAE (~6-8pp) - harder to predict
- P4 (behavioral): High MAE (~7-10pp) - depends on P1-P3

---

## Export Options

### Option 1: Wide Format (Products as Rows, Metrics as Columns)

```python
wide_df = df.pivot(index='product_name', columns='metric_name', values='predicted_value')
wide_df.to_csv('predictions_wide_format.csv')
```

**Result:**
```
product_name,Purchase Intent,Appeal,Uniqueness,...
Exfoliating Scrub,38.0,35.0,42.0,...
pH Sensitive Wash,40.0,38.0,35.0,...
```

### Option 2: Comparison Table

```python
comparison = df[['product_name', 'metric_name', 'predicted_value', 'actual_value', 'difference']]
comparison.to_csv('predictions_comparison.csv', index=False)
```

### Option 3: JSON for Further Processing

```python
import json

grouped = {}
for _, row in df.iterrows():
    product = row['product_name']
    if product not in grouped:
        grouped[product] = {}

    grouped[product][row['metric_key']] = {
        'predicted': row['predicted_value'],
        'actual': row['actual_value'],
        'difference': row['difference']
    }

with open('predictions.json', 'w') as f:
    json.dump(grouped, f, indent=2)
```

---

## Interpretation Guidelines

### Good Predictions (Error ≤ 5pp)

✅ **Example:** Predicted: 38%, Actual: 37%, Diff: +1pp

**Interpretation:** Model has strong understanding of this metric/product

**Action:** Use as reference example in playbook

### Acceptable Predictions (5pp < Error ≤ 10pp)

⚠️ **Example:** Predicted: 40%, Actual: 48%, Diff: -8pp

**Interpretation:** Model is in right ballpark but missing nuance

**Action:** Review reasoning, identify what signal was missed

### Poor Predictions (Error > 10pp)

✗ **Example:** Predicted: 40%, Actual: 29%, Diff: +11pp

**Interpretation:** Model fundamentally misunderstood something

**Action:**
1. Check if ground truth is correct
2. Review vision/verbatim data quality
3. Add explicit rule to playbook
4. Consider this a learning example

---

## Summary Statistics to Report

**For each experiment run, report:**

1. **Overall MAE:** Average absolute error across all predictions
2. **MAE by Priority:** Separate MAE for P1/P2/P3/P4 metrics
3. **% within 5pp:** Percentage of predictions with error ≤ 5pp
4. **% within 10pp:** Percentage of predictions with error ≤ 10pp
5. **R² by Metric:** Variance explained for each metric
6. **Best/Worst Product:** Which product had lowest/highest average error
7. **Best/Worst Metric:** Which metric had lowest/highest MAE

**Example Summary:**
```
Multi-Metric Prediction Results
================================
Date: 2025-11-18
Products: 4
Metrics: 11
Total Predictions: 44 (40 valid)

Overall Performance:
- MAE: 5.59pp
- RMSE: 7.12pp
- Within 5pp: 60.0% (24/40)
- Within 10pp: 87.5% (35/40)

By Priority:
- P1 (Primary): MAE = 5.50pp
- P2 (Diagnostic): MAE = 4.81pp
- P3 (Execution): MAE = 5.50pp
- P4 (Behavioral): MAE = 7.25pp

Best Performing:
- Product: Girl's Night Out Refresh Queen (MAE = 1.5pp)
- Metric: Believability (MAE = 3.75pp)

Worst Performing:
- Product: pH Sensitive Skin Body Wash (MAE = 7.1pp)
- Metric: Trial Intent (MAE = 9.00pp)
```

---

**Last Updated:** 2025-11-18
**Script:** `run_multi_metric_predictions.py`
**Guide:** `MULTI_METRIC_PREDICTION_GUIDE.md`
