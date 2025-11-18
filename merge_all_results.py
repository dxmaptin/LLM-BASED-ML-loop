#!/usr/bin/env python3
"""Merge all demographic batch results into one final CSV."""

import pandas as pd
from pathlib import Path

# Input files
input_dir = Path("experimental_result_12demographics_10question")
batch_files = [
    input_dir / "results_all_demographics.csv",  # Original 3: secure_homeowners, starting_out, young_dependents
    input_dir / "results_batch_asset_rich_greys_budgeting_elderly_constrained_parents.csv",
    input_dir / "results_batch_families_juggling_finances_high_income_professionals_mid_life_pressed_renters.csv",
    input_dir / "results_batch_older_working_families_rising_metropolitans_road_to_retirement.csv",
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
output_file = input_dir / "final_results_all_12_demographics.csv"
merged_df.to_csv(output_file, index=False)

print(f"\n{'=' * 100}")
print(f"MERGED RESULTS SAVED TO: {output_file}")
print(f"{'=' * 100}")
print(f"\nTotal rows: {len(merged_df)}")
print(f"Total demographics: {merged_df['demographic'].nunique()}")
print(f"Demographics included: {sorted(merged_df['demographic'].unique())}")

# Calculate summary statistics per demographic
print(f"\n{'=' * 100}")
print("SUMMARY BY DEMOGRAPHIC")
print(f"{'=' * 100}")

for demographic in sorted(merged_df['demographic'].unique()):
    demo_df = merged_df[merged_df['demographic'] == demographic]
    mean_error = demo_df['absolute_error_pct'].mean()
    r_squared = demo_df['r_squared'].iloc[0] if 'r_squared' in demo_df.columns else None

    print(f"\n{demographic}:")
    print(f"  Questions: {len(demo_df)}")
    print(f"  Mean Absolute Error: {mean_error:.2f}%")
    if r_squared is not None:
        print(f"  R^2: {r_squared:.4f}")

# Overall statistics
print(f"\n{'=' * 100}")
print("OVERALL STATISTICS")
print(f"{'=' * 100}")
mean_error = merged_df['absolute_error_pct'].mean()
print(f"Overall Mean Absolute Error: {mean_error:.2f}%")
print(f"Total predictions: {len(merged_df)}")

print("\nDONE!")
