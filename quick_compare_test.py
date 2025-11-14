"""
Quick comparison: Test new generated prompt on exclusive_addresses class.
Uses the 10 holdout questions.
"""

import json
import pandas as pd
from pathlib import Path
from sklearn.metrics import r2_score, mean_absolute_error

from agent_estimator.estimator_agent.estimator import EstimatorAgent


def main():
    """Quick test on exclusive_addresses."""

    class_name = "exclusive_addresses"

    print("="*80)
    print("QUICK TEST: NEW GENERATED PROMPT")
    print("="*80)
    print(f"\nClass: {class_name}")
    print(f"Baseline (v4): R² = 0.94, MAE = 4.06%")
    print("\nTesting on 10 holdout questions with NEW auto-generated prompt")
    print("="*80)

    # Load ground truth
    gt_file = Path("ACORN_ground_truth_named.csv")
    gt_df = pd.read_csv(gt_file)

    # Find the row for exclusive_addresses (case-insensitive match)
    class_match = gt_df[gt_df['Class'].str.lower().str.replace(' ', '_') == class_name.lower()]

    if len(class_match) == 0:
        print(f"ERROR: Class {class_name} not found in ground truth")
        print(f"Available classes: {gt_df['Class'].tolist()}")
        return

    # Get the 10 holdout questions (column names)
    question_cols = [col for col in gt_df.columns if col != 'Class']
    print(f"\nFound {len(question_cols)} test questions")

    # Load context for this class
    base_dir = Path(f"demographic_runs_ACORN/{class_name}")
    quant_file = base_dir / "Flattened Data Inputs" / f"ACORN_{class_name}.csv"
    qual_file = base_dir / "Textual Data Inputs" / f"{class_name}_profile.txt"

    if not quant_file.exists() or not qual_file.exists():
        print(f"ERROR: Data files not found for {class_name}")
        return

    # Load context
    qual_text = qual_file.read_text(encoding='utf-8', errors='ignore')
    df_quant = pd.read_csv(quant_file)

    # Create evidence
    evidence = {
        "quant_summary": df_quant.head(100).to_string(),
        "textual_summary": qual_text[:2000],
        "weight_hints": []
    }

    # Initialize estimator (will use the new deployed prompt)
    estimator = EstimatorAgent(model="gpt-4o")

    predictions = []
    actuals = []
    results_detail = []

    print("\nRunning predictions...")
    print("-"*80)

    for i, q_col in enumerate(question_cols, 1):
        # Get actual value
        actual = class_match[q_col].iloc[0]

        # Expand abbreviated question name
        question_map = {
            "I think brands should consider environmental susta...": "I think brands should consider environmental sustainability when putting on events",
            "Make an effort to cut down on the use of gas / ele...": "Make an effort to cut down on the use of gas / electricity at home",
            "Fuel consumption is the most important feature whe...": "Fuel consumption is the most important feature when buying a new car",
            "I don't like the idea of being in debt": "I don't like the idea of being in debt",
            "I am very good at managing money": "I am very good at managing money",
            "It is important to be well insured for everything": "It is important to be well insured for everything",
            "Healthy Eating": "Healthy Eating",
            "Financial security after retirement is your own re...": "Financial security after retirement is your own responsibility",
            "Switching utilities suppliers is well worth the ef...": "Switching utilities suppliers is well worth the effort",
            "I like to use cash when making purchases": "I like to use cash when making purchases"
        }

        full_question = question_map.get(q_col, q_col)

        print(f"[{i}/{len(question_cols)}] {full_question[:55]}...")

        try:
            # Run estimation
            result = estimator.estimate(
                concept=full_question,
                evidence=evidence,
                runs=1,
                iteration=1,
                feedback=""
            )

            # Extract prediction from EstimationResult object
            dist = result.aggregated_distribution

            # Debug: print the distribution
            if i == 1:
                print(f"  DEBUG - Distribution: {dist}")
                print(f"  DEBUG - Runs: {len(result.runs)}")
                if result.runs:
                    print(f"  DEBUG - First run: {result.runs[0]}")

            pred_topline = (dist.get('strongly_agree', 0) + dist.get('slightly_agree', 0)) / 100  # Convert to 0-1

            predictions.append(pred_topline)
            actuals.append(actual)

            error = abs(pred_topline - actual) * 100

            print(f"  Predicted: {pred_topline*100:.1f}% | Actual: {actual*100:.1f}% | Error: {error:.1f}pp | Confidence: {result.avg_confidence:.0f}")

            results_detail.append({
                "question": full_question,
                "predicted": pred_topline,
                "actual": actual,
                "error": error,
                "confidence": result.avg_confidence
            })

        except Exception as e:
            print(f"  ERROR: {str(e)[:80]}")

    # Calculate metrics
    if len(predictions) > 0:
        r2 = r2_score(actuals, predictions)
        mae = mean_absolute_error(actuals, predictions) * 100

        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(f"\nR² Score: {r2:.4f}")
        print(f"MAE: {mae:.2f}pp")
        print(f"Sample size: {len(predictions)} questions")

        print(f"\nComparison to v4 baseline:")
        print(f"  v4: R² = 0.94, MAE = 4.06%")
        print(f"  New: R² = {r2:.4f}, MAE = {mae:.2f}%")
        print(f"  Change: R² {r2 - 0.94:+.4f}, MAE {mae - 4.06:+.2f}pp")

        # Save results
        output = {
            "class": class_name,
            "r2": r2,
            "mae": mae,
            "n_questions": len(predictions),
            "detail": results_detail
        }

        output_file = Path("agent_estimator/prompt_agent/output/quick_test_result.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\nDetailed results saved to: {output_file}")

    else:
        print("\nNo successful predictions")

    print("="*80)


if __name__ == "__main__":
    main()
