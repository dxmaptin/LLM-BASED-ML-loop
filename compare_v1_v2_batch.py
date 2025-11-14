#!/usr/bin/env python3
"""Compare V1 vs V2 results for 6 test classes."""

import pandas as pd
import numpy as np
from pathlib import Path
import json

# Load ground truth
ground_truth_df = pd.read_csv("ACORN_ground_truth_22classes.csv")

# Map class names
CLASS_TO_DIR = {
    "Semi-Rural Maturity": "semi-rural_maturity",
    "Constrained Penisoners": "constrained_penisoners",
    "Upmarket Families": "upmarket_families",
    "Family Renters": "family_renters",
    "Stable Seniors": "stable_seniors",
    "Urban Diversity ": "urban_diversity"
}

CLASS_NAMES = list(CLASS_TO_DIR.keys())

def parse_results(file_path):
    """Parse estimator results."""
    lines = Path(file_path).read_text(encoding='utf-8').splitlines()
    predictions = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("### Concept:"):
            while i < len(lines) and not lines[i].startswith("Final distribution:"):
                i += 1
            if i < len(lines):
                i += 1
                sa, a = None, None
                for j in range(i, min(i + 10, len(lines))):
                    if "Strongly agree:" in lines[j]:
                        sa = float(lines[j].split(":")[-1].strip().rstrip('%'))
                    elif "Slightly agree:" in lines[j]:
                        a = float(lines[j].split(":")[-1].strip().rstrip('%'))
                    elif lines[j].startswith("Runs:"):
                        break
                if sa is not None and a is not None:
                    predictions.append((sa + a) / 100.0)
        i += 1
    if len(predictions) > 10:
        predictions = predictions[1:]
    return predictions[:10]

def calc_metrics(preds, actual):
    """Calculate R², correlation, MAE, RMSE, bias."""
    ss_res = np.sum((np.array(actual) - np.array(preds)) ** 2)
    ss_tot = np.sum((np.array(actual) - np.mean(actual)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    corr = np.corrcoef(preds, actual)[0, 1]
    mae = np.mean(np.abs(np.array(preds) - np.array(actual)))
    rmse = np.sqrt(np.mean((np.array(preds) - np.array(actual)) ** 2))
    bias = np.mean(np.array(preds) - np.array(actual))
    return r2, corr, mae, rmse, bias

print("="*100)
print("V1 vs V2 COMPARISON - 6 TEST CLASSES")
print("="*100)

all_v1_preds = []
all_v2_preds = []
all_ground_truth = []
class_results = []

for class_name in CLASS_NAMES:
    dir_name = CLASS_TO_DIR[class_name]

    # Get ground truth
    gt_row = ground_truth_df[ground_truth_df['Class'] == class_name]
    if len(gt_row) == 0:
        print(f"\n[SKIP] {class_name}: No ground truth found")
        continue

    ground_truth = []
    for i in range(1, 11):
        ground_truth.append(gt_row[f'Concept_{i}'].values[0])

    # Parse V1 and V2 results
    v1_file = Path(f"demographic_runs_ACORN/{dir_name}/estimator_results_ACORN.txt")
    v2_file = Path(f"demographic_runs_ACORN/{dir_name}/estimator_results_ACORN_v2.txt")

    if not v1_file.exists():
        print(f"\n[SKIP] {class_name}: No V1 results")
        continue
    if not v2_file.exists():
        print(f"\n[SKIP] {class_name}: No V2 results")
        continue

    v1_preds = parse_results(v1_file)
    v2_preds = parse_results(v2_file)

    # Calculate metrics
    v1_r2, v1_corr, v1_mae, v1_rmse, v1_bias = calc_metrics(v1_preds, ground_truth)
    v2_r2, v2_corr, v2_mae, v2_rmse, v2_bias = calc_metrics(v2_preds, ground_truth)

    class_results.append({
        "class": class_name,
        "v1_r2": v1_r2,
        "v2_r2": v2_r2,
        "v1_mae": v1_mae,
        "v2_mae": v2_mae,
        "v1_bias": v1_bias,
        "v2_bias": v2_bias
    })

    # Accumulate for overall stats
    all_v1_preds.extend(v1_preds)
    all_v2_preds.extend(v2_preds)
    all_ground_truth.extend(ground_truth)

    print(f"\n{class_name:35}")
    print(f"  V1: R2={v1_r2:7.4f}  MAE={v1_mae*100:5.2f}pp  Bias={v1_bias*100:+6.2f}pp")
    print(f"  V2: R2={v2_r2:7.4f}  MAE={v2_mae*100:5.2f}pp  Bias={v2_bias*100:+6.2f}pp")
    print(f"  Change: R2={v2_r2-v1_r2:+7.4f}  MAE={-(v2_mae-v1_mae)*100:+5.2f}pp  Bias={-(v2_bias-v1_bias)*100:+6.2f}pp")

# Overall metrics
v1_overall = calc_metrics(all_v1_preds, all_ground_truth)
v2_overall = calc_metrics(all_v2_preds, all_ground_truth)

print(f"\n{'='*100}")
print("OVERALL PERFORMANCE (6 CLASSES, 60 PREDICTIONS)")
print(f"{'='*100}")
print(f"\n{'METRIC':<25} {'V1':<15} {'V2':<15} {'Change':<15} {'Status'}")
print("-"*100)

metrics = [
    ("R²", v1_overall[0], v2_overall[0]),
    ("Correlation", v1_overall[1], v2_overall[1]),
    ("MAE (pp)", v1_overall[2]*100, v2_overall[2]*100),
    ("RMSE (pp)", v1_overall[3]*100, v2_overall[3]*100),
    ("Bias (pp)", v1_overall[4]*100, v2_overall[4]*100)
]

for name, v1_val, v2_val in metrics:
    change = v2_val - v1_val
    if name in ["MAE (pp)", "RMSE (pp)", "Bias (pp)"]:
        status = "BETTER" if abs(v2_val) < abs(v1_val) else "WORSE"
    else:
        status = "BETTER" if v2_val > v1_val else "WORSE"

    print(f"{name:<25} {v1_val:>10.4f}     {v2_val:>10.4f}     {change:>+10.4f}     {status}")

# Count improvements
r2_improved = sum(1 for r in class_results if r["v2_r2"] > r["v1_r2"])
mae_improved = sum(1 for r in class_results if abs(r["v2_mae"]) < abs(r["v1_mae"]))
bias_improved = sum(1 for r in class_results if abs(r["v2_bias"]) < abs(r["v1_bias"]))

print(f"\n{'='*100}")
print("CLASS-LEVEL IMPROVEMENTS")
print(f"{'='*100}")
print(f"R² improved:    {r2_improved}/6 classes")
print(f"MAE improved:   {mae_improved}/6 classes")
print(f"Bias improved:  {bias_improved}/6 classes")

# Best/worst improvements
sorted_by_r2_change = sorted(class_results, key=lambda x: x["v2_r2"] - x["v1_r2"], reverse=True)

print(f"\n{'='*100}")
print("TOP 3 R² IMPROVEMENTS")
print(f"{'='*100}")
for i, r in enumerate(sorted_by_r2_change[:3], 1):
    print(f"{i}. {r['class']:35} {r['v1_r2']:7.4f} -> {r['v2_r2']:7.4f} ({r['v2_r2']-r['v1_r2']:+.4f})")

print(f"\n{'='*100}")
print("SUMMARY")
print(f"{'='*100}")

if v2_overall[0] > v1_overall[0]:
    print(f"SUCCESS: V2 improved overall R² by {v2_overall[0]-v1_overall[0]:.4f}")
else:
    print(f"ISSUE: V2 decreased R² by {v1_overall[0]-v2_overall[0]:.4f}")

if abs(v2_overall[4]) < abs(v1_overall[4]):
    print(f"SUCCESS: V2 reduced bias by {(abs(v1_overall[4])-abs(v2_overall[4]))*100:.2f}pp")
else:
    print(f"ISSUE: V2 increased bias by {(abs(v2_overall[4])-abs(v1_overall[4]))*100:.2f}pp")

if v2_overall[2] < v1_overall[2]:
    print(f"SUCCESS: V2 reduced MAE by {(v1_overall[2]-v2_overall[2])*100:.2f}pp")
else:
    print(f"ISSUE: V2 increased MAE by {(v2_overall[2]-v1_overall[2])*100:.2f}pp")

print(f"\n{'='*100}")
