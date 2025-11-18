#!/usr/bin/env python3
"""Merge all improved prompt batch results and compare to baseline."""

import pandas as pd
from pathlib import Path

# Input files
input_dir = Path("experimental_result_12demographics_10question")
batch_files = [
    input_dir / "results_batch_improved_prompts_asset_rich_greys_budgeting_elderly_road_to_retirement.csv",
    input_dir / "results_batch_improved_prompts_constrained_parents_families_juggling_finances_high_income_professionals.csv",
    input_dir / "results_batch_improved_prompts_mid_life_pressed_renters_older_working_families_rising_metropolitans.csv",
    input_dir / "results_batch_improved_prompts_secure_homeowners_starting_out_young_dependents.csv",
]

# Read and merge all CSVs
all_dfs = []
for file in batch_files:
    if file.exists():
        df = pd.read_csv(file)
        all_dfs.append(df)
        print(f"Loaded {len(df)} rows from {file.name}")
    else:
        print(f"WARNING: File not found: {file}")

# Merge all dataframes
merged_df = pd.concat(all_dfs, ignore_index=True)

# Sort by demographic and question
merged_df = merged_df.sort_values(['demographic', 'question'])

# Save merged results
output_file = input_dir / "final_results_improved_prompts_all_12.csv"
merged_df.to_csv(output_file, index=False)

print(f"\n{'=' * 100}")
print(f"MERGED RESULTS SAVED TO: {output_file}")
print(f"{'=' * 100}")
print(f"\nTotal rows: {len(merged_df)}")
print(f"Total demographics: {merged_df['demographic'].nunique()}")
print(f"Demographics included: {sorted(merged_df['demographic'].unique())}")

# Calculate summary statistics per demographic
print(f"\n{'=' * 100}")
print("IMPROVED APPROACH - SUMMARY BY DEMOGRAPHIC")
print(f"{'=' * 100}")

improved_summary = []
for demographic in sorted(merged_df['demographic'].unique()):
    demo_df = merged_df[merged_df['demographic'] == demographic]
    mean_error = demo_df['absolute_error_pct'].mean()
    r_squared = demo_df['r_squared'].iloc[0] if 'r_squared' in demo_df.columns else None

    improved_summary.append({
        'demographic': demographic,
        'mean_error': mean_error,
        'r_squared': r_squared
    })

    print(f"\n{demographic}:")
    print(f"  Questions: {len(demo_df)}")
    print(f"  Mean Absolute Error: {mean_error:.2f}%")
    if r_squared is not None:
        print(f"  R²: {r_squared:.4f}")

# Overall statistics
print(f"\n{'=' * 100}")
print("IMPROVED APPROACH - OVERALL STATISTICS")
print(f"{'=' * 100}")
overall_mae = merged_df['absolute_error_pct'].mean()
overall_r2 = merged_df.groupby('demographic')['r_squared'].first().mean()
print(f"Overall Mean Absolute Error: {overall_mae:.2f}%")
print(f"Average R² across demographics: {overall_r2:.4f}")
print(f"Total predictions: {len(merged_df)}")
print(f"Demographics with R² > 0.7: {sum(1 for x in improved_summary if x['r_squared'] and x['r_squared'] > 0.7)}/12")
print(f"Demographics with R² > 0.6: {sum(1 for x in improved_summary if x['r_squared'] and x['r_squared'] > 0.6)}/12")

# Load baseline results for comparison
baseline_file = input_dir / "final_results_all_12_demographics.csv"
if baseline_file.exists():
    baseline_df = pd.read_csv(baseline_file)

    print(f"\n{'=' * 100}")
    print("BASELINE VS IMPROVED COMPARISON")
    print(f"{'=' * 100}")
    print(f"{'Demographic':<30} {'Baseline R²':>12} {'Improved R²':>12} {'Change':>10} {'Baseline MAE':>13} {'Improved MAE':>13} {'MAE Change':>12}")
    print("=" * 100)

    for demographic in sorted(merged_df['demographic'].unique()):
        baseline_demo = baseline_df[baseline_df['demographic'] == demographic]
        improved_demo = merged_df[merged_df['demographic'] == demographic]

        if len(baseline_demo) > 0:
            baseline_r2 = baseline_demo['r_squared'].iloc[0]
            baseline_mae = baseline_demo['absolute_error_pct'].mean()
            improved_r2 = improved_demo['r_squared'].iloc[0]
            improved_mae = improved_demo['absolute_error_pct'].mean()

            r2_change = improved_r2 - baseline_r2
            mae_change = improved_mae - baseline_mae

            r2_symbol = "+" if r2_change > 0 else "-" if r2_change < 0 else "="
            mae_symbol = "-" if mae_change < 0 else "+" if mae_change > 0 else "="

            print(f"{demographic:<30} {baseline_r2:>12.4f} {improved_r2:>12.4f} {r2_symbol}{abs(r2_change):>9.4f} {baseline_mae:>12.2f}% {improved_mae:>12.2f}% {mae_symbol}{abs(mae_change):>10.2f}%")

    # Overall comparison
    baseline_overall_mae = baseline_df['absolute_error_pct'].mean()
    baseline_overall_r2 = baseline_df.groupby('demographic')['r_squared'].first().mean()

    print("=" * 100)
    print(f"{'OVERALL':<30} {baseline_overall_r2:>12.4f} {overall_r2:>12.4f} {'+':>1}{abs(overall_r2 - baseline_overall_r2):>9.4f} {baseline_overall_mae:>12.2f}% {overall_mae:>12.2f}% {'-':>1}{abs(overall_mae - baseline_overall_mae):>10.2f}%")

    print(f"\n{'=' * 100}")
    print("KEY IMPROVEMENTS")
    print(f"{'=' * 100}")
    print(f"Average R² improved from {baseline_overall_r2:.4f} to {overall_r2:.4f} (+{overall_r2 - baseline_overall_r2:.4f})")
    print(f"Average MAE improved from {baseline_overall_mae:.2f}% to {overall_mae:.2f}% (-{baseline_overall_mae - overall_mae:.2f}%)")

    # Count demographics that improved
    improved_count = 0
    for demographic in sorted(merged_df['demographic'].unique()):
        baseline_demo = baseline_df[baseline_df['demographic'] == demographic]
        improved_demo = merged_df[merged_df['demographic'] == demographic]
        if len(baseline_demo) > 0:
            if improved_demo['r_squared'].iloc[0] > baseline_demo['r_squared'].iloc[0]:
                improved_count += 1

    print(f"Demographics that improved: {improved_count}/12")

    # Identify worst performers
    print(f"\n{'=' * 100}")
    print("DEMOGRAPHICS STILL NEEDING IMPROVEMENT (R² < 0.7)")
    print(f"{'=' * 100}")
    for item in improved_summary:
        if item['r_squared'] and item['r_squared'] < 0.7:
            print(f"{item['demographic']}: R²={item['r_squared']:.4f}, MAE={item['mean_error']:.2f}%")

print("\n\nDONE!")
