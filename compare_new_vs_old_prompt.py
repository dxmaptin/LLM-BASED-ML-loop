"""
Compare new generated prompt vs old prompt on exclusive_addresses class.
"""

import json
import pandas as pd
from pathlib import Path
from sklearn.metrics import r2_score, mean_absolute_error
import shutil

from agent_estimator.estimator_agent.estimator import EstimatorAgent


def run_test_with_prompt(class_name: str, prompt_file: Path, label: str):
    """Run prediction test with a specific prompt."""

    print(f"\n{'='*80}")
    print(f"Testing: {label}")
    print(f"{'='*80}")
    print(f"Prompt: {prompt_file}")
    print(f"Class: {class_name}")

    # Load ground truth
    gt_file = Path(f"demographic_runs_ACORN/{class_name}/ground_truth.csv")

    if not gt_file.exists():
        # Try to find it in ACORN ground truth
        acorn_gt = Path("ACORN_ground_truth_named.csv")
        if not acorn_gt.exists():
            print(f"ERROR: Ground truth not found")
            return None

        gt_df = pd.read_csv(acorn_gt)
        # Filter for this class
        gt_df = gt_df[gt_df['Class'] == class_name]
    else:
        gt_df = pd.read_csv(gt_file)

    print(f"\nGround truth: {len(gt_df)} questions")

    # Temporarily copy prompt to active location
    target_prompt = Path("agent_estimator/estimator_agent/prompts/general_system_prompt.txt")
    backup_prompt = Path("agent_estimator/estimator_agent/prompts/general_system_prompt.txt.backup")

    # Backup existing prompt
    if target_prompt.exists():
        shutil.copy2(target_prompt, backup_prompt)

    # Copy test prompt
    shutil.copy2(prompt_file, target_prompt)

    print(f"\nRunning predictions with {label}...")

    # Run predictions (simulate - just test on first 5 questions)
    test_questions = gt_df['Question'].head(5).tolist() if 'Question' in gt_df.columns else gt_df['Concept'].head(5).tolist()

    print(f"Testing on {len(test_questions)} sample questions")

    predictions = []
    actuals = []

    estimator = EstimatorAgent(model="gpt-4o")

    # Load context
    base_dir = Path(f"demographic_runs_ACORN/{class_name}")
    quant_file = base_dir / "Flattened Data Inputs" / f"ACORN_{class_name}.csv"
    qual_file = base_dir / "Textual Data Inputs" / f"{class_name}_profile.txt"

    if not quant_file.exists():
        print("ERROR: Data files not found")
        # Restore prompt
        if backup_prompt.exists():
            shutil.copy2(backup_prompt, target_prompt)
            backup_prompt.unlink()
        return None

    # Load context
    qual_text = qual_file.read_text(encoding='utf-8', errors='ignore')
    df_quant = pd.read_csv(quant_file)

    # Create simple evidence
    evidence = {
        "quant_summary": df_quant.head(50).to_string(),
        "textual_summary": qual_text[:2000],
        "weight_hints": []
    }

    for i, question in enumerate(test_questions, 1):
        print(f"  [{i}/{len(test_questions)}] {question[:50]}...")

        try:
            # Estimate
            result = estimator.estimate(
                concept=question,
                evidence=evidence,
                runs=1,
                iteration=1,
                feedback=""
            )

            # Get prediction
            dist = result.get('distribution', {})
            pred_topline = dist.get('SA', 0) + dist.get('A', 0)

            # Get actual
            if 'Question' in gt_df.columns:
                actual_row = gt_df[gt_df['Question'] == question]
            else:
                actual_row = gt_df[gt_df['Concept'] == question]

            if len(actual_row) > 0:
                actual_topline = actual_row['Topline'].iloc[0] if 'Topline' in actual_row.columns else actual_row['topline_agreement'].iloc[0]

                predictions.append(pred_topline / 100)  # Convert to 0-1
                actuals.append(actual_topline)

                error = abs(pred_topline/100 - actual_topline)
                print(f"    Predicted: {pred_topline:.1f}% | Actual: {actual_topline*100:.1f}% | Error: {error*100:.1f}pp")

        except Exception as e:
            print(f"    ERROR: {e}")

    # Restore original prompt
    if backup_prompt.exists():
        shutil.copy2(backup_prompt, target_prompt)
        backup_prompt.unlink()

    if len(predictions) == 0:
        print("\nNo successful predictions")
        return None

    # Calculate metrics
    r2 = r2_score(actuals, predictions)
    mae = mean_absolute_error(actuals, predictions)

    print(f"\n{'='*80}")
    print(f"RESULTS FOR {label}")
    print(f"{'='*80}")
    print(f"R² Score: {r2:.4f}")
    print(f"MAE: {mae*100:.2f}pp")
    print(f"Sample size: {len(predictions)} questions")

    return {
        "label": label,
        "r2": r2,
        "mae": mae,
        "n": len(predictions),
        "predictions": predictions,
        "actuals": actuals
    }


def main():
    """Main comparison."""

    class_name = "exclusive_addresses"

    print("="*80)
    print("COMPARING NEW GENERATED PROMPT VS OLD PROMPT")
    print("="*80)
    print(f"\nTest Class: {class_name}")
    print(f"Old v4 Result: R² = 0.94, MAE = 4.06%")
    print("\nWill test on 5 sample questions to quickly compare")

    # Test 1: New generated prompt
    new_prompt = Path("agent_estimator/prompt_agent/output/prompts/general_system_prompt.txt")

    if not new_prompt.exists():
        print(f"\nERROR: New prompt not found at {new_prompt}")
        return

    result_new = run_test_with_prompt(class_name, new_prompt, "NEW Generated Prompt")

    # Test 2: Old prompt (if exists)
    old_prompt = Path("agent_estimator/estimator_agent/prompts/general_system_prompt.txt.old")

    if not old_prompt.exists():
        # Check if there's a v4 prompt
        v4_prompt = Path("agent_estimator/estimator_agent/prompts/general_system_prompt_v4.txt")
        if v4_prompt.exists():
            old_prompt = v4_prompt
        else:
            print("\nNo old prompt found for comparison")
            old_prompt = None

    if old_prompt:
        result_old = run_test_with_prompt(class_name, old_prompt, "OLD Manual Prompt")
    else:
        result_old = None

    # Summary
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)

    if result_new:
        print(f"\nNEW Generated Prompt:")
        print(f"  R² = {result_new['r2']:.4f}")
        print(f"  MAE = {result_new['mae']*100:.2f}pp")
        print(f"  Sample size = {result_new['n']}")

    if result_old:
        print(f"\nOLD Manual Prompt:")
        print(f"  R² = {result_old['r2']:.4f}")
        print(f"  MAE = {result_old['mae']*100:.2f}pp")
        print(f"  Sample size = {result_old['n']}")

        if result_new:
            r2_change = result_new['r2'] - result_old['r2']
            mae_change = (result_old['mae'] - result_new['mae']) * 100

            print(f"\nChange:")
            print(f"  R² change: {r2_change:+.4f}")
            print(f"  MAE change: {mae_change:+.2f}pp {'(better)' if mae_change > 0 else '(worse)'}")

    print(f"\nFull v4 benchmark for {class_name}: R² = 0.94, MAE = 4.06%")
    print("Note: This is a quick test on 5 questions. Full evaluation needs all questions.")
    print("="*80)


if __name__ == "__main__":
    main()
