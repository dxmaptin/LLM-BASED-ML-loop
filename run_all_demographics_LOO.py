#!/usr/bin/env python3
"""Run LOO estimation across all demographics and calculate R²."""

import csv
from pathlib import Path
from agent_estimator.ir_agent.parser import DataParsingAgent
from agent_estimator.estimator_agent.estimator import EstimatorAgent
import numpy as np

def calculate_r_squared(actuals, predictions):
    """Calculate R² coefficient of determination."""
    actuals = np.array(actuals)
    predictions = np.array(predictions)

    # Mean of actual values
    mean_actual = np.mean(actuals)

    # Total sum of squares
    ss_tot = np.sum((actuals - mean_actual) ** 2)

    # Residual sum of squares
    ss_res = np.sum((actuals - predictions) ** 2)

    # R²
    r_squared = 1 - (ss_res / ss_tot)

    return r_squared

def run_demographic(demographic_label, base_dir, questions_path, output_file):
    """Run estimation for one demographic."""
    print(f"\n{'=' * 100}")
    print(f"RUNNING: {demographic_label}")
    print(f"{'=' * 100}\n")

    # Load concepts from CSV
    concepts_data = []
    with questions_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            demo = row.get("Demographic", "").replace("\n", " ").strip()
            demo_normalized = " ".join(demo.split())
            if demo_normalized == demographic_label:
                concept = row.get("Concept", "").strip()
                value = float(row.get("Value", 0))
                if concept:
                    concepts_data.append({"concept": concept, "actual_value": value})

    if not concepts_data:
        print(f"No concepts found for {demographic_label}")
        return None

    print(f"Found {len(concepts_data)} concepts")

    # Initialize agents
    from agent_estimator.ir_agent.parser import _bundle_inputs
    _bundle_inputs.cache_clear()

    ir_agent = DataParsingAgent(base_dir)
    estimator = EstimatorAgent()

    # Run estimates
    results = []
    for idx, data in enumerate(concepts_data, 1):
        concept = data["concept"]
        actual_value = data["actual_value"]

        print(f"  [{idx}/{len(concepts_data)}] {concept[:60]}...", end=" ")

        bundle = ir_agent.prepare_concept_bundle(concept, exclude_exact_match=True)

        result = estimator.estimate(
            concept=concept,
            evidence=bundle,
            runs=5,
            iteration=1,
            feedback=""
        )

        predicted_dist = result.aggregated_distribution
        predicted_topline = (predicted_dist.get("strongly_agree", 0) + predicted_dist.get("slightly_agree", 0)) / 100.0
        error = abs(actual_value - predicted_topline)

        print(f"Actual: {actual_value:.1%}, Predicted: {predicted_topline:.1%}, Error: {error:.1%}")

        results.append({
            "demographic": demographic_label,
            "concept": concept,
            "actual_topline": actual_value,
            "predicted_topline": predicted_topline,
            "error": error,
            "SA": predicted_dist.get("strongly_agree", 0),
            "A": predicted_dist.get("slightly_agree", 0),
            "N": predicted_dist.get("neither_agree_nor_disagree", 0),
            "D": predicted_dist.get("slightly_disagree", 0),
            "SD": predicted_dist.get("strongly_disagree", 0),
        })

    # Calculate metrics
    actuals = [r["actual_topline"] for r in results]
    predictions = [r["predicted_topline"] for r in results]
    errors = [r["error"] for r in results]

    avg_error = np.mean(errors)
    r_squared = calculate_r_squared(actuals, predictions)

    print(f"\n{demographic_label} Results:")
    print(f"  Average Error: {avg_error:.4f} ({avg_error*100:.2f}%)")
    print(f"  R²: {r_squared:.4f}")

    # Write to CSV
    with output_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "demographic", "concept", "actual_topline", "predicted_topline", "error",
            "SA", "A", "N", "D", "SD"
        ])
        writer.writeheader()
        writer.writerows(results)

    return {
        "demographic": demographic_label,
        "n_concepts": len(results),
        "avg_error": avg_error,
        "r_squared": r_squared,
        "results": results
    }

def main():
    questions_path = Path("Handpicked_experiments_10.csv")

    demographics = [
        {
            "label": "Young Dependents",
            "base_dir": Path("demographic_runs/young_dependents/handpicked_context_workspace"),
            "output": Path("demographic_runs/young_dependents/results_LOO_final.csv")
        },
        {
            "label": "Starting Out",
            "base_dir": Path("demographic_runs/starting_out/handpicked_context_workspace"),
            "output": Path("demographic_runs/starting_out/results_LOO_final.csv")
        },
        {
            "label": "Secure Homeowners",
            "base_dir": Path("demographic_runs/secure_homeowners/handpicked_context_workspace"),
            "output": Path("demographic_runs/secure_homeowners/results_LOO_final.csv")
        },
    ]

    print("=" * 100)
    print("RUNNING LOO ESTIMATION ACROSS ALL DEMOGRAPHICS")
    print("=" * 100)

    all_results = []
    all_actuals = []
    all_predictions = []

    for demo_config in demographics:
        result = run_demographic(
            demo_config["label"],
            demo_config["base_dir"],
            questions_path,
            demo_config["output"]
        )

        if result:
            all_results.append(result)
            all_actuals.extend([r["actual_topline"] for r in result["results"]])
            all_predictions.extend([r["predicted_topline"] for r in result["results"]])

    # Overall metrics
    print(f"\n{'=' * 100}")
    print("OVERALL RESULTS ACROSS ALL DEMOGRAPHICS")
    print(f"{'=' * 100}\n")

    overall_avg_error = np.mean([r["avg_error"] for r in all_results])
    overall_r_squared = calculate_r_squared(all_actuals, all_predictions)
    total_concepts = sum([r["n_concepts"] for r in all_results])

    print(f"Total concepts tested: {total_concepts}")
    print(f"Overall average error: {overall_avg_error:.4f} ({overall_avg_error*100:.2f}%)")
    print(f"Overall R²: {overall_r_squared:.4f}")
    print()

    # Per-demographic summary
    print("Per-demographic breakdown:")
    for result in all_results:
        print(f"  {result['demographic']:20} | n={result['n_concepts']:2} | Avg Error: {result['avg_error']*100:5.2f}% | R²: {result['r_squared']:.4f}")

    print(f"\n{'=' * 100}")
    print(f"TARGET: R² ≥ 0.75")
    print(f"CURRENT: R² = {overall_r_squared:.4f}")
    print(f"GAP: {0.75 - overall_r_squared:.4f}")
    print(f"{'=' * 100}\n")

    # Save combined results
    combined_output = Path("demographic_runs/ALL_DEMOGRAPHICS_LOO_results.csv")
    all_data = []
    for result in all_results:
        all_data.extend(result["results"])

    with combined_output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "demographic", "concept", "actual_topline", "predicted_topline", "error",
            "SA", "A", "N", "D", "SD"
        ])
        writer.writeheader()
        writer.writerows(all_data)

    print(f"Combined results saved to: {combined_output}")

if __name__ == "__main__":
    main()
