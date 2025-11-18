#!/usr/bin/env python3
"""Diagnose potential overfitting - check if predictions are too good to be true."""

import pandas as pd
import numpy as np
import json
from pathlib import Path

# Load V4 results
with open("ACORN_v4_r2_results.json") as f:
    v4_results = json.load(f)

# Load ground truth
gt = pd.read_csv("ACORN_ground_truth_named.csv")

print("="*80)
print("OVERFITTING DIAGNOSTIC")
print("="*80)

# 1. Check if errors are suspiciously small
all_mae = [r["mae_v4"] for r in v4_results]
print(f"\n1. ERROR MAGNITUDE CHECK:")
print(f"   Mean MAE: {np.mean(all_mae)*100:.2f}pp")
print(f"   Median MAE: {np.median(all_mae)*100:.2f}pp")
print(f"   Min MAE: {np.min(all_mae)*100:.2f}pp")
print(f"   Max MAE: {np.max(all_mae)*100:.2f}pp")
print(f"\n   Interpretation:")
print(f"   - MAE < 5pp is excellent but possible with good data")
print(f"   - MAE < 2pp is suspicious (may indicate leakage)")
print(f"   - Mean MAE = {np.mean(all_mae)*100:.2f}pp {'[SUSPICIOUS]' if np.mean(all_mae)*100 < 2 else '[REASONABLE]'}")

# 2. Check R² distribution
all_r2 = [r["r2_v4"] for r in v4_results]
print(f"\n2. R² DISTRIBUTION:")
print(f"   Mean R²: {np.mean(all_r2):.3f}")
print(f"   Median R²: {np.median(all_r2):.3f}")
print(f"   Min R²: {np.min(all_r2):.3f}")
print(f"   Max R²: {np.max(all_r2):.3f}")
print(f"   Std Dev: {np.std(all_r2):.3f}")
print(f"\n   Interpretation:")
print(f"   - R² > 0.95 on ALL classes would be suspicious")
print(f"   - R² variance {np.std(all_r2):.3f} {'[LOW - suspicious]' if np.std(all_r2) < 0.05 else '[REASONABLE]'}")

# 3. Check improvement V3->V4
improvements = [r["r2_v4"] - r["r2_v3"] for r in v4_results if r["r2_v3"] is not None]
print(f"\n3. V3 -> V4 IMPROVEMENT:")
print(f"   Mean improvement: +{np.mean(improvements):.3f}")
print(f"   All improved: {all(i > 0 for i in improvements)}")
print(f"   Largest improvement: +{np.max(improvements):.3f}")
print(f"\n   Interpretation:")
print(f"   - Improvement > +0.20 is very large")
print(f"   - Mean improvement {np.mean(improvements):.3f} {'[SUSPICIOUS]' if np.mean(improvements) > 0.30 else '[LARGE BUT POSSIBLE]'}")

# 4. Compare to baseline
print(f"\n4. COMPARISON TO REASONABLE BASELINES:")
print(f"   Best published attitude prediction R²: ~0.50-0.70")
print(f"   Your V3 R²: 0.688 [REASONABLE]")
print(f"   Your V4 R²: {np.mean(all_r2):.3f} {'[UNUSUALLY HIGH]' if np.mean(all_r2) > 0.85 else '[HIGH BUT POSSIBLE]'}")

# 5. Check if V4 prompt might be memorizing
print(f"\n5. MEMORIZATION CHECK:")
print(f"   V3 was trained on ALL 18 classes")
print(f"   V4 was also trained on ALL 18 classes")
print(f"   → NO HELD-OUT TEST SET!")
print(f"   → This could explain high R² if prompt is overfitting to these specific classes")

print(f"\n6. RECOMMENDATION:")
if np.mean(all_r2) > 0.90 and np.mean(all_mae)*100 < 4:
    print(f"   [WARNING] Results are suspiciously good")
    print(f"   Possible explanations:")
    print(f"   1. Prompt is overfitting to the 18 training classes")
    print(f"   2. There's indirect data leakage we haven't found")
    print(f"   3. The task is genuinely easy (unlikely)")
    print(f"\n   SOLUTION: Test on held-out classes NOT used for prompt tuning")
else:
    print(f"   Results are good but within reasonable bounds")

print("="*80)
