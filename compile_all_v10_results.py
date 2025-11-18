"""
Compile all v10 results from different test runs into one comprehensive CSV.
"""

import pandas as pd

# Results from previous tests (manually compiled)
PREVIOUS_RESULTS = [
    # Training set - poor classes
    {"class": "cash-strapped_families", "r2": 0.8178, "mae": 5.53, "excellent": 4, "total": 10, "test_group": "poor"},
    {"class": "hard-up_households", "r2": 0.8297, "mae": 5.80, "excellent": 4, "total": 10, "test_group": "poor"},
    {"class": "challenging_circumstances", "r2": 0.8364, "mae": 5.54, "excellent": 2, "total": 10, "test_group": "poor"},

    # Training set - senior classes
    {"class": "stable_seniors", "r2": 0.7993, "mae": 7.12, "excellent": 3, "total": 10, "test_group": "senior"},
    {"class": "constrained_penisoners", "r2": 0.7607, "mae": 7.36, "excellent": 1, "total": 10, "test_group": "senior"},

    # Test set - exclusive addresses
    {"class": "exclusive_addresses", "r2": 0.8471, "mae": 4.81, "excellent": 8, "total": 10, "test_group": "affluent"},
]

def main():
    print("Compiling all v10 results...")

    # Load the results from the recent test run
    df_recent = pd.read_csv("v10_remaining_classes_results.csv")
    df_recent["test_group"] = "various"  # These were the remaining classes

    # Combine with previous results
    df_previous = pd.DataFrame(PREVIOUS_RESULTS)

    # Merge all results
    df_all = pd.concat([df_previous, df_recent], ignore_index=True)

    # Add derived columns
    df_all["pass_r2_0.7"] = df_all["r2"] > 0.7
    df_all["excellent_pct"] = (df_all["excellent"] / df_all["total"] * 100).round(1)

    # Add status categorization
    def categorize_status(r2):
        if r2 > 0.9:
            return "EXCELLENT"
        elif r2 > 0.85:
            return "GREAT"
        elif r2 > 0.75:
            return "GOOD"
        elif r2 > 0.7:
            return "PASS"
        elif r2 > 0.65:
            return "WARN"
        else:
            return "FAIL"

    df_all["status"] = df_all["r2"].apply(categorize_status)

    # Sort by R2 descending
    df_all = df_all.sort_values("r2", ascending=False)

    # Save comprehensive results
    output_file = "v10_all_classes_comprehensive_results.csv"
    df_all.to_csv(output_file, index=False)

    print(f"\nSaved comprehensive results to: {output_file}")
    print(f"Total classes: {len(df_all)}")
    print(f"\nBreakdown by status:")
    print(df_all["status"].value_counts().sort_index())

    print(f"\nOverall statistics:")
    print(f"  Average R2: {df_all['r2'].mean():.4f}")
    print(f"  Average MAE: {df_all['mae'].mean():.2f}pp")
    print(f"  Median R2: {df_all['r2'].median():.4f}")
    print(f"  Pass rate (R2 > 0.7): {df_all['pass_r2_0.7'].sum()}/{len(df_all)} ({df_all['pass_r2_0.7'].mean()*100:.1f}%)")

    # Show top 10 and bottom 5
    print(f"\nTop 10 performers:")
    print(df_all.head(10)[["class", "r2", "mae", "status"]].to_string(index=False))

    print(f"\nBottom 5 performers:")
    print(df_all.tail(5)[["class", "r2", "mae", "status"]].to_string(index=False))

    # Group by test_group
    print(f"\nPerformance by demographic group:")
    group_stats = df_all.groupby("test_group").agg({
        "r2": ["mean", "min", "max"],
        "mae": "mean",
        "class": "count"
    }).round(4)
    print(group_stats)

if __name__ == "__main__":
    main()
