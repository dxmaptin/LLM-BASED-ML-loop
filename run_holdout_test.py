"""
Test Runner for Holdout Questions

Tests the newly generated prompts on the 10 holdout questions
that were excluded from training.
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

from agent_estimator.prompt_agent.data_prep import ACORNDataLoader


def prepare_holdout_test_concepts(loader: ACORNDataLoader, output_file: Path):
    """
    Prepare the 10 holdout questions for testing.

    Args:
        loader: ACORNDataLoader instance
        output_file: Where to save the test concepts CSV
    """
    print("\n" + "="*80)
    print("PREPARING HOLDOUT TEST SET")
    print("="*80)

    # Get holdout questions
    holdout_questions = [
        "I think brands should consider environmental sustainability when putting on events",
        "Make an effort to cut down on the use of gas / electricity at home",
        "Fuel consumption is the most important feature when buying a new car",
        "I don't like the idea of being in debt",
        "I am very good at managing money",
        "It is important to be well insured for everything",
        "Healthy Eating",
        "Financial security after retirement is your own responsibility",
        "Switching utilities suppliers is well worth the effort",
        "I like to use cash when making purchases"
    ]

    # Create concepts_to_test.csv for each class
    all_classes = loader.get_all_class_names()

    print(f"\nCreating test files for {len(all_classes)} classes...")
    print(f"Test questions: {len(holdout_questions)}")

    for class_name in all_classes:
        class_dir = Path("demographic_runs_ACORN") / class_name

        # Create concepts_to_test.csv
        concepts_file = class_dir / "concepts_to_test.csv"

        with open(concepts_file, 'w', encoding='utf-8') as f:
            # Write header (just one column with concepts)
            for question in holdout_questions:
                f.write(f"{question}\n")

        print(f"  ✓ {class_name}/concepts_to_test.csv")

    print(f"\n✓ Created test files for {len(all_classes)} classes")

    # Also save a master list
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("concept\n")
        for question in holdout_questions:
            f.write(f"{question}\n")

    print(f"✓ Master list saved to: {output_file}")

    return holdout_questions


def extract_ground_truth(loader: ACORNDataLoader, output_file: Path):
    """
    Extract ground truth values for holdout questions.

    Args:
        loader: ACORNDataLoader instance
        output_file: Where to save ground truth CSV
    """
    print("\n" + "="*80)
    print("EXTRACTING GROUND TRUTH FOR HOLDOUT QUESTIONS")
    print("="*80)

    # Load data WITH holdout questions
    test_data = loader.get_holdout_test_set()

    if len(test_data) == 0:
        print("WARNING: No holdout test data found!")
        return

    print(f"\nTest data: {len(test_data)} rows")
    print(f"Questions: {test_data['Question'].nunique()}")
    print(f"Classes: {test_data['class_name'].nunique()}")

    # For each class and question, extract the "topline" (total agreement)
    ground_truth = []

    for class_name in test_data['class_name'].unique():
        class_data = test_data[test_data['class_name'] == class_name]

        for question in class_data['Question'].unique():
            q_data = class_data[class_data['Question'] == question]

            # Try to find topline agreement
            # Look for answers that indicate agreement
            agreement_keywords = ['Agree', 'Yes', 'Strongly', 'Very', 'Definitely']

            agree_data = q_data[q_data['Answer'].str.contains('|'.join(agreement_keywords), case=False, na=False)]

            if len(agree_data) > 0:
                agree_data['Value'] = pd.to_numeric(agree_data['Value'], errors='coerce')
                topline = float(agree_data['Value'].sum())
            else:
                # If no clear agreement answers, use mean
                q_data['Value'] = pd.to_numeric(q_data['Value'], errors='coerce')
                topline = float(q_data['Value'].mean()) if len(q_data) > 0 else 0

            ground_truth.append({
                "class_name": class_name,
                "question": question,
                "topline_agreement": topline
            })

    # Save to CSV
    gt_df = pd.DataFrame(ground_truth)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    gt_df.to_csv(output_file, index=False)

    print(f"\n✓ Ground truth saved to: {output_file}")
    print(f"  Total entries: {len(gt_df)}")

    return gt_df


def run_predictions_on_holdout(model: str = "gpt-4o"):
    """
    Run predictions on holdout test set using new prompts.

    Args:
        model: Model to use for predictions
    """
    print("\n" + "="*80)
    print("RUNNING PREDICTIONS ON HOLDOUT TEST SET")
    print("="*80)
    print(f"Model: {model}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Import the runner
    from agent_estimator.orchestrator.runner import run_for_all_classes

    # Run predictions
    print("\nRunning predictions...")
    print("This may take 10-20 minutes for 22 classes × 10 questions = 220 predictions")
    print("="*80)

    results = run_for_all_classes(
        base_dir=Path("demographic_runs_ACORN"),
        model_name=model,
        max_workers=3  # Parallel processing
    )

    print("\n" + "="*80)
    print("PREDICTIONS COMPLETE")
    print("="*80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return results


def evaluate_results(ground_truth_file: Path, predictions_dir: Path, output_file: Path):
    """
    Evaluate predictions against ground truth.

    Args:
        ground_truth_file: Path to ground truth CSV
        predictions_dir: Directory with prediction results
        output_file: Where to save evaluation report
    """
    print("\n" + "="*80)
    print("EVALUATING RESULTS")
    print("="*80)

    # Load ground truth
    gt_df = pd.read_csv(ground_truth_file)
    print(f"\nGround truth: {len(gt_df)} entries")

    # Load predictions
    all_predictions = []

    for class_dir in predictions_dir.iterdir():
        if not class_dir.is_dir():
            continue

        results_file = class_dir / "results.csv"
        if not results_file.exists():
            continue

        pred_df = pd.read_csv(results_file)
        pred_df['class_name'] = class_dir.name
        all_predictions.append(pred_df)

    if not all_predictions:
        print("ERROR: No prediction results found!")
        return

    pred_df = pd.concat(all_predictions, ignore_index=True)
    print(f"Predictions: {len(pred_df)} entries")

    # Merge and calculate errors
    merged = gt_df.merge(
        pred_df,
        left_on=['class_name', 'question'],
        right_on=['class_name', 'concept'],
        how='inner'
    )

    merged['error'] = abs(merged['topline_agreement'] - merged['predicted_topline'] / 100)
    merged['error_pp'] = merged['error'] * 100

    # Calculate metrics
    overall_mae = merged['error_pp'].mean()
    overall_r2 = 1 - (merged['error'] ** 2).sum() / ((merged['topline_agreement'] - merged['topline_agreement'].mean()) ** 2).sum()

    # By class
    by_class = merged.groupby('class_name').agg({
        'error_pp': ['mean', 'std', 'min', 'max']
    }).round(2)

    # By question
    by_question = merged.groupby('question').agg({
        'error_pp': ['mean', 'std', 'min', 'max']
    }).round(2)

    # Save report
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("HOLDOUT TEST SET EVALUATION REPORT\n")
        f.write("="*80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("OVERALL METRICS\n")
        f.write("-"*80 + "\n")
        f.write(f"Mean Absolute Error: {overall_mae:.2f}pp\n")
        f.write(f"R² Score: {overall_r2:.3f}\n")
        f.write(f"Total predictions: {len(merged)}\n\n")

        f.write("BY CLASS\n")
        f.write("-"*80 + "\n")
        f.write(by_class.to_string())
        f.write("\n\n")

        f.write("BY QUESTION\n")
        f.write("-"*80 + "\n")
        f.write(by_question.to_string())
        f.write("\n\n")

        f.write("TOP 10 ERRORS\n")
        f.write("-"*80 + "\n")
        worst = merged.nlargest(10, 'error_pp')[['class_name', 'question', 'topline_agreement', 'predicted_topline', 'error_pp']]
        f.write(worst.to_string(index=False))
        f.write("\n")

    print(f"\n✓ Evaluation report saved to: {output_file}")
    print(f"\nOVERALL PERFORMANCE:")
    print(f"  Mean Absolute Error: {overall_mae:.2f}pp")
    print(f"  R² Score: {overall_r2:.3f}")

    return {
        "overall_mae": overall_mae,
        "overall_r2": overall_r2,
        "by_class": by_class,
        "by_question": by_question
    }


if __name__ == "__main__":
    # Step 1: Prepare test set
    loader = ACORNDataLoader(Path("demographic_runs_ACORN"))

    output_dir = Path("agent_estimator/prompt_agent/output/holdout_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare test concepts
    holdout_questions = prepare_holdout_test_concepts(
        loader,
        output_file=output_dir / "holdout_questions.csv"
    )

    # Extract ground truth
    ground_truth = extract_ground_truth(
        loader,
        output_file=output_dir / "ground_truth.csv"
    )

    print("\n" + "="*80)
    print("TEST SET PREPARATION COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("  1. Review concepts_to_test.csv files in each class directory")
    print("  2. Run predictions: python -m agent_estimator.orchestrator.runner")
    print("  3. Evaluate results: run the evaluate_results() function")
    print("="*80)
