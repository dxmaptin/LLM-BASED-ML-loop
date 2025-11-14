#!/usr/bin/env python3
"""Run LOO predictions on 10 NEW questions across all 12 demographics."""

import csv
import numpy as np
import pandas as pd
from pathlib import Path
from agent_estimator.ir_agent.parser import DataParsingAgent
from agent_estimator.estimator_agent.estimator import EstimatorAgent

# All 12 demographics
DEMOGRAPHICS = [
    "asset_rich_greys",
    "budgeting_elderly",
    "constrained_parents",
    "families_juggling_finances",
    "high_income_professionals",
    "mid_life_pressed_renters",
    "older_working_families",
    "rising_metropolitans",
    "road_to_retirement",
    "secure_homeowners",
    "starting_out",
    "young_dependents",
]

# Load test questions
TEST_QUESTIONS_FILE = "experimental_result_12demographics_10question/new_test_questions.csv"
with open(TEST_QUESTIONS_FILE, 'r', encoding='utf-8') as f:
    test_concepts = [line.strip() for line in f if line.strip()]

print(f"Loaded {len(test_concepts)} test questions:")
for i, concept in enumerate(test_concepts, 1):
    print(f"  {i}. {concept}")

# Output file
OUTPUT_DIR = Path("experimental_result_12demographics_10question")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "results_all_demographics.csv"

# LIKERT_ORDER for calculating SA+A
LIKERT_ORDER = ["strongly_agree", "slightly_agree", "neither", "slightly_disagree", "strongly_disagree"]

# Results storage
all_results = []

print("\n" + "=" * 100)
print("RUNNING LOO PREDICTIONS ON 10 NEW QUESTIONS ACROSS 12 DEMOGRAPHICS")
print("=" * 100)

for demographic in DEMOGRAPHICS:
    print(f"\n{'=' * 100}")
    print(f"DEMOGRAPHIC: {demographic.upper()}")
    print("=" * 100)

    # Try two possible folder structures:
    # 1. demographic_runs/{demographic}/handpicked_context_workspace (for young_dependents, starting_out, secure_homeowners)
    # 2. demographic_runs/{demographic} (for the other 9 demographics)

    base_dir_with_workspace = Path(f"demographic_runs/{demographic}/handpicked_context_workspace")
    base_dir_direct = Path(f"demographic_runs/{demographic}")

    if base_dir_with_workspace.exists():
        base_dir = base_dir_with_workspace
        csv_file = base_dir / "Flattened Data Inputs" / f"{demographic}.csv"
    elif base_dir_direct.exists():
        base_dir = base_dir_direct
        csv_file = base_dir / "Flattened Data Inputs" / f"{demographic}.csv"
    else:
        print(f"WARNING: No valid directory found for {demographic}")
        print(f"Skipping {demographic}")
        continue

    # Check if CSV exists
    if not csv_file.exists():
        print(f"WARNING: CSV file not found: {csv_file}")
        print(f"Skipping {demographic}")
        continue

    # Load actual values from CSV
    df = pd.read_csv(csv_file)

    # Create mapping of concept -> actual value
    actual_values = {}
    for concept in test_concepts:
        # Parse concept into Question and Option
        if " - " in concept:
            category, option = concept.split(" - ", 1)
            category = category.strip()
            option = option.strip()
        else:
            print(f"WARNING: Cannot parse concept '{concept}', skipping")
            continue

        # Find matching row in CSV
        matches = df[(df['Question'] == category) & (df['Option'] == option)]
        if len(matches) == 0:
            print(f"WARNING: No match found for '{concept}' in {demographic} CSV")
            actual_values[concept] = None
        elif len(matches) > 1:
            print(f"WARNING: Multiple matches found for '{concept}' in {demographic} CSV")
            actual_values[concept] = matches.iloc[0]['Value']
        else:
            actual_values[concept] = matches.iloc[0]['Value']

    # Initialize agents
    ir_agent = DataParsingAgent(base_dir)
    estimator = EstimatorAgent()

    # Run predictions for each concept
    for i, concept in enumerate(test_concepts, 1):
        print(f"\n[{i}/{len(test_concepts)}] Processing: {concept}")

        actual_value = actual_values.get(concept)
        if actual_value is None:
            print(f"  Skipping (no actual value found)")
            continue

        print(f"  Actual SA+A: {actual_value:.4f}")

        try:
            # Extract evidence with LOO filtering
            bundle = ir_agent.prepare_concept_bundle(concept, exclude_exact_match=True)

            # Check for leakage
            proximal = bundle.get("proximal_topline")
            if proximal is not None:
                print(f"  WARNING: Proximal topline leaked: {proximal:.4f}")

            # Run estimator (5 runs)
            result = estimator.estimate(
                concept=concept,
                evidence=bundle,
                runs=5,
                iteration=1,
            )

            # Calculate predicted SA+A (convert from percentage to proportion)
            dist = result.aggregated_distribution
            predicted = (dist.get("strongly_agree", 0) + dist.get("slightly_agree", 0)) / 100.0

            # Calculate error
            error = predicted - actual_value
            error_pct = abs(error) * 100

            print(f"  Predicted SA+A: {predicted:.4f}")
            print(f"  Error: {error_pct:.2f}%")

            # Store result
            all_results.append({
                "demographic": demographic,
                "question": concept,
                "actual_value": actual_value,
                "predicted_value": predicted,
                "difference": error,
                "absolute_error_pct": error_pct,
            })

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

print("\n" + "=" * 100)
print("ALL PREDICTIONS COMPLETE - CALCULATING SUMMARY STATISTICS")
print("=" * 100)

# Calculate R^2 per demographic
results_df = pd.DataFrame(all_results)

summary_stats = []
for demographic in DEMOGRAPHICS:
    demo_results = results_df[results_df['demographic'] == demographic]

    if len(demo_results) == 0:
        print(f"\n{demographic}: No results")
        continue

    actuals = demo_results['actual_value'].values
    predictions = demo_results['predicted_value'].values

    # Calculate R^2
    mean_actual = np.mean(actuals)
    ss_tot = np.sum((actuals - mean_actual) ** 2)
    ss_res = np.sum((actuals - predictions) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # Calculate mean absolute error
    mae = np.mean(demo_results['absolute_error_pct'].values)

    print(f"\n{demographic}:")
    print(f"  Questions: {len(demo_results)}")
    print(f"  Mean Absolute Error: {mae:.2f}%")
    print(f"  R^2: {r_squared:.4f}")

    summary_stats.append({
        "demographic": demographic,
        "n_questions": len(demo_results),
        "mean_absolute_error_pct": mae,
        "r_squared": r_squared,
    })

# Add R^2 to each row in results
results_with_r2 = []
r2_map = {stat['demographic']: stat['r_squared'] for stat in summary_stats}
for result in all_results:
    result['r_squared'] = r2_map.get(result['demographic'], None)
    results_with_r2.append(result)

# Save results to CSV
with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['demographic', 'question', 'actual_value', 'predicted_value', 'difference', 'absolute_error_pct', 'r_squared']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results_with_r2)

print(f"\n{'=' * 100}")
print(f"RESULTS SAVED TO: {OUTPUT_FILE}")
print("=" * 100)

# Calculate overall statistics
overall_mae = np.mean([r['absolute_error_pct'] for r in all_results])
overall_actuals = np.array([r['actual_value'] for r in all_results])
overall_predictions = np.array([r['predicted_value'] for r in all_results])
overall_mean = np.mean(overall_actuals)
overall_ss_tot = np.sum((overall_actuals - overall_mean) ** 2)
overall_ss_res = np.sum((overall_actuals - overall_predictions) ** 2)
overall_r2 = 1 - (overall_ss_res / overall_ss_tot) if overall_ss_tot > 0 else 0

print(f"\nOVERALL STATISTICS (across all {len(all_results)} predictions):")
print(f"  Mean Absolute Error: {overall_mae:.2f}%")
print(f"  R^2: {overall_r2:.4f}")
print(f"  Total predictions: {len(all_results)}")

# Save summary statistics
summary_file = OUTPUT_DIR / "summary_by_demographic.csv"
pd.DataFrame(summary_stats).to_csv(summary_file, index=False)
print(f"\nSummary statistics saved to: {summary_file}")

print("\nDONE!")
