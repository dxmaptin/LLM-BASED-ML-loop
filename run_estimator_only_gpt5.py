#!/usr/bin/env python3
"""Run estimator-only on all 12 demographics with GPT-5 using existing contextual summaries."""

import sys
import pandas as pd
from pathlib import Path
from agent_estimator.estimator_agent.estimator import EstimatorAgent
from agent_estimator.common.openai_utils import get_token_usage_log, reset_token_usage

# List of all 12 demographics
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
    "young_dependents"
]

def process_demographic_batch(demographics_list, output_file):
    """Process a batch of demographics and save results."""

    # Load test questions
    test_questions_file = Path("experimental_result_12demographics_10question/new_test_questions.csv")
    with open(test_questions_file, 'r') as f:
        test_questions = [line.strip() for line in f if line.strip()]

    print(f"\n{'='*100}")
    print(f"Processing {len(demographics_list)} demographics with {len(test_questions)} test questions")
    print(f"Using GPT-5 for estimator")
    print(f"{'='*100}\n")

    all_results = []

    # Initialize estimator with GPT-5
    estimator = EstimatorAgent(model="gpt-5")

    for demographic in demographics_list:
        print(f"\n{'='*100}")
        print(f"PROCESSING: {demographic.upper()}")
        print(f"{'='*100}\n")

        # Reset token usage for this demographic
        reset_token_usage()

        base_dir = Path(f"demographic_runs/{demographic}")

        # Check which folder structure exists
        contextual_workspace = base_dir / "handpicked_context_workspace"
        if not contextual_workspace.exists():
            contextual_workspace = base_dir / "context_workspace"

        if not contextual_workspace.exists():
            print(f"ERROR: No contextual workspace found for {demographic}")
            continue

        # Load actual values
        actual_file = base_dir / "handpicked_concepts.csv"
        if not actual_file.exists():
            actual_file = base_dir / "concepts.csv"

        with open(actual_file, 'r') as f:
            all_concepts = [line.strip() for line in f if line.strip()]

        # Create lookup for actual values
        actual_df = pd.read_csv(base_dir / "likert_summary.csv")
        actual_lookup = {}
        for _, row in actual_df.iterrows():
            concept = row['Concept']
            # Calculate "Agree" percentage (SA + A)
            agree_pct = (row.get('Strongly Agree', 0) + row.get('Slightly Agree', 0)) / 100.0
            actual_lookup[concept] = agree_pct

        # Process each test question
        for question in test_questions:
            print(f"\nProcessing question: {question}")

            # Load contextual summary for this question
            summary_file = contextual_workspace / f"{question}.txt"
            if not summary_file.exists():
                print(f"  WARNING: No contextual summary found, skipping...")
                continue

            with open(summary_file, 'r') as f:
                contextual_summary = f.read()

            # Run estimator
            try:
                distribution = estimator.estimate_distribution(question, contextual_summary)

                # Calculate predicted "Agree" percentage
                predicted = (distribution.get("strongly_agree", 0) + distribution.get("slightly_agree", 0)) / 100.0

                # Get actual value
                actual = actual_lookup.get(question)

                if actual is None:
                    print(f"  WARNING: No actual value found for {question}")
                    continue

                # Calculate metrics
                difference = predicted - actual
                abs_error_pct = abs(difference) * 100

                print(f"  Actual: {actual*100:.1f}% | Predicted: {predicted*100:.1f}% | Error: {abs_error_pct:.1f}%")

                all_results.append({
                    'demographic': demographic,
                    'question': question,
                    'actual_value': actual,
                    'predicted_value': predicted,
                    'difference': difference,
                    'absolute_error_pct': abs_error_pct
                })

            except Exception as e:
                print(f"  ERROR estimating {question}: {e}")
                continue

        # Print token usage for this demographic
        token_log = get_token_usage_log()
        print(f"\n{'='*60}")
        print(f"TOKEN USAGE FOR {demographic.upper()}:")
        print(f"  Total requests: {token_log.requests}")
        print(f"  Prompt tokens: {token_log.prompt_tokens:,}")
        print(f"  Completion tokens: {token_log.completion_tokens:,}")
        print(f"  Total tokens: {token_log.total_tokens:,}")
        print(f"{'='*60}\n")

    # Calculate R² for each demographic
    results_df = pd.DataFrame(all_results)

    # Calculate R² per demographic
    for demographic in demographics_list:
        demo_df = results_df[results_df['demographic'] == demographic]
        if len(demo_df) == 0:
            continue

        actual_values = demo_df['actual_value'].values
        predicted_values = demo_df['predicted_value'].values

        # Calculate R²
        ss_res = ((actual_values - predicted_values) ** 2).sum()
        ss_tot = ((actual_values - actual_values.mean()) ** 2).sum()
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Add R² to all rows for this demographic
        results_df.loc[results_df['demographic'] == demographic, 'r_squared'] = r_squared

    # Save results
    results_df.to_csv(output_file, index=False)

    print(f"\n{'='*100}")
    print(f"RESULTS SAVED TO: {output_file}")
    print(f"{'='*100}\n")

    # Print summary statistics
    for demographic in demographics_list:
        demo_df = results_df[results_df['demographic'] == demographic]
        if len(demo_df) == 0:
            continue
        mean_error = demo_df['absolute_error_pct'].mean()
        r_squared = demo_df['r_squared'].iloc[0]
        print(f"{demographic}: MAE={mean_error:.2f}%, R²={r_squared:.4f}")

    overall_mae = results_df['absolute_error_pct'].mean()
    print(f"\nOverall MAE: {overall_mae:.2f}%")

    return results_df


if __name__ == "__main__":
    # Process all 12 demographics
    if len(sys.argv) > 1:
        # Process specific demographics from command line
        demographics_to_process = sys.argv[1:]
        output_file = Path("experimental_result_12demographics_10question") / f"results_gpt5_estimator_only_{'_'.join(demographics_to_process)}.csv"
    else:
        # Process all demographics
        demographics_to_process = DEMOGRAPHICS
        output_file = Path("experimental_result_12demographics_10question") / "results_gpt5_estimator_only_all_12.csv"

    results = process_demographic_batch(demographics_to_process, output_file)

    print("\nDONE!")
