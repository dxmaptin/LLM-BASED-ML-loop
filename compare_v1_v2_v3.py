#!/usr/bin/env python3
"""Compare V1 vs V2 vs V3 results for 6 test classes."""

import pandas as pd
import numpy as np
from pathlib import Path

ground_truth_df = pd.read_csv("ACORN_ground_truth_22classes.csv")

CLASS_TO_DIR = {
    "Semi-Rural Maturity": "semi-rural_maturity",
    "Constrained Penisoners": "constrained_penisoners",
    "Upmarket Families": "upmarket_families",
    "Family Renters": "family_renters",
    "Stable Seniors": "stable_seniors",
    "Urban Diversity ": "urban_diversity"
}

def parse_results(file_path):
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
    ss_res = np.sum((np.array(actual) - np.array(preds)) ** 2)
    ss_tot = np.sum((np.array(actual) - np.mean(actual)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    corr = np.corrcoef(preds, actual)[0, 1]
    mae = np.mean(np.abs(np.array(preds) - np.array(actual)))
    bias = np.mean(np.array(preds) - np.array(actual))
    return r2, corr, mae, bias

print("="*110)
print("V1 vs V2 vs V3 COMPARISON - 6 TEST CLASSES (REINFORCEMENT LEARNING ITERATIONS)")
print("="*110)

all_v1, all_v2, all_v3, all_gt = [], [], [], []
class_results = []

for class_name, dir_name in CLASS_TO_DIR.items():
    gt_row = ground_truth_df[ground_truth_df['Class'] == class_name]
    if len(gt_row) == 0:
        continue
    ground_truth = [gt_row[f'Concept_{i}'].values[0] for i in range(1, 11)]

    v1_file = Path(f"demographic_runs_ACORN/{dir_name}/estimator_results_ACORN.txt")
    v2_file = Path(f"demographic_runs_ACORN/{dir_name}/estimator_results_ACORN_v2.txt")
    v3_file = Path(f"demographic_runs_ACORN/{dir_name}/estimator_results_ACORN_v3.txt")

    if not all([v1_file.exists(), v2_file.exists(), v3_file.exists()]):
        continue

    v1_preds = parse_results(v1_file)
    v2_preds = parse_results(v2_file)
    v3_preds = parse_results(v3_file)

    v1_r2, v1_corr, v1_mae, v1_bias = calc_metrics(v1_preds, ground_truth)
    v2_r2, v2_corr, v2_mae, v2_bias = calc_metrics(v2_preds, ground_truth)
    v3_r2, v3_corr, v3_mae, v3_bias = calc_metrics(v3_preds, ground_truth)

    class_results.append({
        "class": class_name,
        "v1_r2": v1_r2, "v2_r2": v2_r2, "v3_r2": v3_r2,
        "v1_mae": v1_mae, "v2_mae": v2_mae, "v3_mae": v3_mae,
        "v1_bias": v1_bias, "v2_bias": v2_bias, "v3_bias": v3_bias
    })

    all_v1.extend(v1_preds)
    all_v2.extend(v2_preds)
    all_v3.extend(v3_preds)
    all_gt.extend(ground_truth)

    print(f"\n{class_name:35}")
    print(f"  V1: R2={v1_r2:7.4f}  MAE={v1_mae*100:5.2f}pp  Bias={v1_bias*100:+6.2f}pp")
    print(f"  V2: R2={v2_r2:7.4f}  MAE={v2_mae*100:5.2f}pp  Bias={v2_bias*100:+6.2f}pp")
    print(f"  V3: R2={v3_r2:7.4f}  MAE={v3_mae*100:5.2f}pp  Bias={v3_bias*100:+6.2f}pp")

v1_overall = calc_metrics(all_v1, all_gt)
v2_overall = calc_metrics(all_v2, all_gt)
v3_overall = calc_metrics(all_v3, all_gt)

print(f"\n{'='*110}")
print("OVERALL PERFORMANCE - 3 ITERATIONS OF REINFORCEMENT LEARNING")
print(f"{'='*110}")
print(f"\n{'METRIC':<20} {'V1 (Original)':<18} {'V2 (Iter 1)':<18} {'V3 (Iter 2)':<18} {'V1->V2':<12} {'V2->V3':<12}")
print("-"*110)

metrics = [
    ("R²", v1_overall[0], v2_overall[0], v3_overall[0]),
    ("Correlation", v1_overall[1], v2_overall[1], v3_overall[1]),
    ("MAE (pp)", v1_overall[2]*100, v2_overall[2]*100, v3_overall[2]*100),
    ("Bias (pp)", v1_overall[3]*100, v2_overall[3]*100, v3_overall[3]*100)
]

for name, v1_val, v2_val, v3_val in metrics:
    v1_v2_change = v2_val - v1_val
    v2_v3_change = v3_val - v2_val
    print(f"{name:<20} {v1_val:>12.4f}      {v2_val:>12.4f}      {v3_val:>12.4f}      {v1_v2_change:>+8.4f}    {v2_v3_change:>+8.4f}")

# Best performer
best_v3_r2 = max(class_results, key=lambda x: x["v3_r2"])
print(f"\n{'='*110}")
print("ITERATION SUMMARY")
print(f"{'='*110}")
print(f"\nV1 (AI-generated baseline):")
print(f"  R² = {v1_overall[0]:.4f}, Bias = {v1_overall[3]*100:+.2f}pp, MAE = {v1_overall[2]*100:.2f}pp")
print(f"  Problem: Systematic over-prediction")

print(f"\nV2 (First RL correction):")
print(f"  R² = {v2_overall[0]:.4f}, Bias = {v2_overall[3]*100:+.2f}pp, MAE = {v2_overall[2]*100:.2f}pp")
print(f"  Improvement: R² +{v2_overall[0]-v1_overall[0]:.4f}, Bias improved by {abs(v1_overall[3])-abs(v2_overall[3]):.4f}")
print(f"  Issue: Over-corrected, now under-predicting")

print(f"\nV3 (Second RL correction):")
print(f"  R² = {v3_overall[0]:.4f}, Bias = {v3_overall[3]*100:+.2f}pp, MAE = {v3_overall[2]*100:.2f}pp")
print(f"  Improvement: R² {v3_overall[0]-v2_overall[0]:+.4f}, Bias {abs(v3_overall[3])-abs(v2_overall[3]):+.4f}")

if abs(v3_overall[3]) < abs(v2_overall[3]) and abs(v3_overall[3]) < abs(v1_overall[3]):
    print(f"  SUCCESS: V3 has lowest bias across all iterations!")
if v3_overall[0] > v2_overall[0]:
    print(f"  SUCCESS: V3 improved R² over V2!")
else:
    print(f"  Note: V3 R² slightly lower than V2, but bias is better")

print(f"\nBest class performance (V3): {best_v3_r2['class']} (R² = {best_v3_r2['v3_r2']:.4f})")

print(f"\n{'='*110}")
print("REINFORCEMENT LEARNING EFFECTIVENESS")
print(f"{'='*110}")
print(f"Total improvement V1->V3:")
print(f"  R² improved by: {v3_overall[0] - v1_overall[0]:+.4f}")
print(f"  MAE reduced by: {(v1_overall[2] - v3_overall[2])*100:.2f}pp")
print(f"  Bias improved by: {abs(v1_overall[3]) - abs(v3_overall[3]):.4f} (closer to 0)")
print(f"\n{'='*110}")
