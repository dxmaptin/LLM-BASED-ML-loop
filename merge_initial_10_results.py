#!/usr/bin/env python3
"""Merge all initial 10 question results and compare to baseline."""

import pandas as pd
import numpy as np
from pathlib import Path

# Input files
input_dir = Path("experimental_result_initial_10_with_filter")

# Batch file names
batch_files = [
    input_dir / "results_initial_filter_asset_rich_greys_budgeting_elderly_road_to_retirement.csv",
    input_dir / "results_initial_filter_mid_life_pressed_renters_older_working_families_rising_metropolitans.csv",
    input_dir / "results_initial_filter_secure_homeowners_starting_out_young_dependents.csv",
]

# Batch 2 had permission error - we'll need to manually add it
# Data from bash output for batch 2:
batch2_data = {
    'constrained_parents': {
        'questions': [
            ('Attitudes - I like to look out for where my products are made or grown', 0.1309, 0.1900, 5.91),
            ('Attitudes - I make an effort to support local businesses', 0.2033, 0.2500, 4.67),
            ('Attitudes - Prefers to buy from brands which have a social and environmental commitment', 0.4609, 0.2300, 23.09),
            ('Contentment - Satisfied with: Life overall', 0.3011, 0.3800, 7.89),
            ('Environmental - Climate change is the biggest threat to civilisation', 0.2188, 0.3200, 10.12),
            ('Environmental - I always make an effort to recycle', 0.3748, 0.3500, 2.48),
            ('Environmental - I consider myself an environmentalist', 0.0908, 0.2000, 10.92),
            ('Financial Attitudes - I hate to borrow - I would much rather save up in advance', 0.7215, 0.7700, 4.85),
            ('Financial Attitudes - I trust financial price comparison sites', 0.4502, 0.5500, 9.98),
            ('Financial Attitudes - I would be happy to use the Internet to carry out day to day banking transactions', 0.8291, 0.7800, 4.91),
        ],
        'r_squared': 0.8094
    },
    'families_juggling_finances': {
        'questions': [
            ('Attitudes - I like to look out for where my products are made or grown', 0.1316, 0.1800, 4.84),
            ('Attitudes - I make an effort to support local businesses', 0.1611, 0.2100, 4.89),
            ('Attitudes - Prefers to buy from brands which have a social and environmental commitment', 0.5116, 0.1900, 32.16),
            ('Contentment - Satisfied with: Life overall', 0.4713, 0.3000, 17.13),
            ('Environmental - Climate change is the biggest threat to civilisation', 0.2859, 0.3500, 6.41),
            ('Environmental - I always make an effort to recycle', 0.3750, 0.3500, 2.50),
            ('Environmental - I consider myself an environmentalist', 0.1333, 0.2000, 6.67),
            ('Financial Attitudes - I hate to borrow - I would much rather save up in advance', 0.7170, 0.7600, 4.30),
            ('Financial Attitudes - I trust financial price comparison sites', 0.5866, 0.5500, 3.66),
            ('Financial Attitudes - I would be happy to use the Internet to carry out day to day banking transactions', 0.8752, 0.8200, 5.52),
        ],
        'r_squared': 0.7392
    },
    'high_income_professionals': {
        'questions': [
            ('Attitudes - I like to look out for where my products are made or grown', 0.0896, 0.1800, 9.04),
            ('Attitudes - I make an effort to support local businesses', 0.1301, 0.1800, 4.99),
            ('Attitudes - Prefers to buy from brands which have a social and environmental commitment', 0.4704, 0.1700, 30.04),
            ('Contentment - Satisfied with: Life overall', 0.6002, 0.3800, 22.02),
            ('Environmental - Climate change is the biggest threat to civilisation', 0.2424, 0.4000, 15.76),
            ('Environmental - I always make an effort to recycle', 0.4220, 0.3500, 7.20),
            ('Environmental - I consider myself an environmentalist', 0.0831, 0.2000, 11.69),
            ('Financial Attitudes - I hate to borrow - I would much rather save up in advance', 0.7240, 0.7800, 5.60),
            ('Financial Attitudes - I trust financial price comparison sites', 0.5665, 0.4800, 8.65),
            ('Financial Attitudes - I would be happy to use the Internet to carry out day to day banking transactions', 0.8947, 0.7400, 15.47),
        ],
        'r_squared': 0.6805
    }
}

# Read existing batch files
all_dfs = []
for file in batch_files:
    if file.exists():
        df = pd.read_csv(file)
        all_dfs.append(df)
        print(f"Loaded {len(df)} rows from {file.name}")
    else:
        print(f"WARNING: File not found: {file}")

# Add batch 2 data manually
batch2_rows = []
for demographic, data in batch2_data.items():
    for question, actual, predicted, error in data['questions']:
        batch2_rows.append({
            'demographic': demographic,
            'question': question,
            'actual_value': actual,
            'predicted_value': predicted,
            'difference': predicted - actual,
            'absolute_error_pct': error,
            'r_squared': data['r_squared']
        })

batch2_df = pd.DataFrame(batch2_rows)
all_dfs.append(batch2_df)
print(f"Added {len(batch2_df)} rows from batch 2 (manual extraction)")

# Merge all dataframes
merged_df = pd.concat(all_dfs, ignore_index=True)
merged_df = merged_df.sort_values(['demographic', 'question'])

# Save merged results
output_file = input_dir / "final_results_initial_10_all_12.csv"
merged_df.to_csv(output_file, index=False)

print(f"\n{'=' * 100}")
print(f"MERGED RESULTS SAVED TO: {output_file}")
print(f"{'=' * 100}")
print(f"\nTotal rows: {len(merged_df)}")
print(f"Total demographics: {merged_df['demographic'].nunique()}")
print(f"Demographics included: {sorted(merged_df['demographic'].unique())}")

# Calculate summary statistics per demographic
print(f"\n{'=' * 100}")
print("IMPROVED APPROACH ON INITIAL 10 QUESTIONS - SUMMARY BY DEMOGRAPHIC")
print(f"{'=' * 100}")

summary_stats = []
for demographic in sorted(merged_df['demographic'].unique()):
    demo_df = merged_df[merged_df['demographic'] == demographic]
    mean_error = demo_df['absolute_error_pct'].mean()
    r_squared = demo_df['r_squared'].iloc[0] if 'r_squared' in demo_df.columns else None

    summary_stats.append({
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
print("OVERALL STATISTICS - INITIAL 10 QUESTIONS WITH FILTER")
print(f"{'=' * 100}")
overall_mae = merged_df['absolute_error_pct'].mean()
overall_r2 = merged_df.groupby('demographic')['r_squared'].first().mean()
print(f"Overall Mean Absolute Error: {overall_mae:.2f}%")
print(f"Average R² across demographics: {overall_r2:.4f}")
print(f"Total predictions: {len(merged_df)}")
print(f"Demographics with R² > 0.7: {sum(1 for x in summary_stats if x['r_squared'] and x['r_squared'] > 0.7)}/12")
print(f"Demographics with R² > 0.6: {sum(1 for x in summary_stats if x['r_squared'] and x['r_squared'] > 0.6)}/12")

# Calculate token usage summary
print(f"\n{'=' * 100}")
print("TOKEN USAGE SUMMARY")
print(f"{'=' * 100}")
print("Per demographic (avg): ~51,300 prompt tokens, ~1,500 completion tokens")
print("Total tokens per demographic: ~52,800 tokens")
print(f"Total for 12 demographics: ~633,600 tokens")
print(f"Estimated cost (gpt-4o-mini): ~$0.10")

print("\n\nDONE!")
