#!/usr/bin/env python3
"""Compare V1 vs V2 prompt performance on aspiring_communities."""

import pandas as pd
import numpy as np
from pathlib import Path

# Ground truth for aspiring_communities
ground_truth = [0.2648, 0.7329, 0.1338, 0.4310, 0.5797, 0.1052, 0.3813, 0.6287, 0.3374, 0.3048]

CONCEPTS = [
    "Environmental sustainability",
    "Cut down gas/electricity",
    "Fuel consumption important",
    "Don't like debt",
    "Good at managing money",
    "Well insured",
    "Healthy eating",
    "Retirement responsibility",
    "Switching utilities",
    "Like cash"
]

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

# Parse both versions
v1_preds = parse_results("demographic_runs_ACORN/aspiring_communities/estimator_results_ACORN.txt")
v2_preds = parse_results("demographic_runs_ACORN/aspiring_communities/estimator_results_ACORN_v2.txt")

print("="*90)
print("V1 vs V2 PROMPT COMPARISON - aspiring_communities")
print("="*90)

# Calculate metrics for both
def calc_metrics(preds, actual):
    ss_res = np.sum((np.array(actual) - np.array(preds)) ** 2)
    ss_tot = np.sum((np.array(actual) - np.mean(actual)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    corr = np.corrcoef(preds, actual)[0, 1]
    mae = np.mean(np.abs(np.array(preds) - np.array(actual)))
    rmse = np.sqrt(np.mean((np.array(preds) - np.array(actual)) ** 2))
    bias = np.mean(np.array(preds) - np.array(actual))
    return r2, corr, mae, rmse, bias

v1_r2, v1_corr, v1_mae, v1_rmse, v1_bias = calc_metrics(v1_preds, ground_truth)
v2_r2, v2_corr, v2_mae, v2_rmse, v2_bias = calc_metrics(v2_preds, ground_truth)

print(f"\n{'METRIC':<25} {'V1 (Original)':<20} {'V2 (Improved)':<20} {'Change':<15}")
print("-"*90)
print(f"{'R²':<25} {v1_r2:>8.4f}           {v2_r2:>8.4f}           {v2_r2-v1_r2:>+7.4f}")
print(f"{'Correlation':<25} {v1_corr:>8.4f}           {v2_corr:>8.4f}           {v2_corr-v1_corr:>+7.4f}")
print(f"{'MAE (pp)':<25} {v1_mae*100:>8.2f}           {v2_mae*100:>8.2f}           {(v2_mae-v1_mae)*100:>+7.2f}")
print(f"{'RMSE (pp)':<25} {v1_rmse*100:>8.2f}           {v2_rmse*100:>8.2f}           {(v2_rmse-v1_rmse)*100:>+7.2f}")
print(f"{'Bias (pp)':<25} {v1_bias*100:>+8.2f}          {v2_bias*100:>+8.2f}          {(v2_bias-v1_bias)*100:>+7.2f}")

print(f"\n{'='*90}")
print("CONCEPT-BY-CONCEPT COMPARISON")
print(f"{'='*90}")
print(f"{'Concept':<35} {'Actual':<10} {'V1':<10} {'V2':<10} {'V1 Err':<10} {'V2 Err':<10} {'Improv':<10}")
print("-"*90)

for i, concept in enumerate(CONCEPTS):
    actual = ground_truth[i] * 100
    v1 = v1_preds[i] * 100
    v2 = v2_preds[i] * 100
    v1_err = v1 - actual
    v2_err = v2 - actual
    improvement = v1_err - v2_err  # Positive = V2 is better

    status = "BETTER" if abs(v2_err) < abs(v1_err) else "WORSE"
    print(f"{concept[:33]:<35} {actual:>6.1f}%   {v1:>6.1f}%   {v2:>6.1f}%   {v1_err:>+6.1f}pp   {v2_err:>+6.1f}pp   {improvement:>+6.1f}pp {status}")

# Summary
better_count = sum(1 for i in range(10) if abs(v2_preds[i] - ground_truth[i]) < abs(v1_preds[i] - ground_truth[i]))
worse_count = sum(1 for i in range(10) if abs(v2_preds[i] - ground_truth[i]) > abs(v1_preds[i] - ground_truth[i]))

print(f"\n{'='*90}")
print("SUMMARY")
print(f"{'='*90}")
print(f"Concepts improved (V2 better): {better_count}/10")
print(f"Concepts worsened (V2 worse):  {worse_count}/10")
print(f"\nOverall R² change: {v1_r2:.4f} → {v2_r2:.4f} ({v2_r2-v1_r2:+.4f})")
print(f"Overall bias change: {v1_bias*100:+.2f}pp → {v2_bias*100:+.2f}pp ({(v2_bias-v1_bias)*100:+.2f}pp)")

if v2_r2 > v1_r2:
    print(f"\n✓ V2 IMPROVED R² by {(v2_r2-v1_r2):.4f}")
else:
    print(f"\n✗ V2 WORSENED R² by {(v1_r2-v2_r2):.4f}")

if abs(v2_bias) < abs(v1_bias):
    print(f"✓ V2 REDUCED bias by {(abs(v1_bias)-abs(v2_bias))*100:.2f}pp")
else:
    print(f"✗ V2 INCREASED bias by {(abs(v2_bias)-abs(v1_bias))*100:.2f}pp")

print(f"\n{'='*90}")
