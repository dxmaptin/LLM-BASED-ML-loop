#!/usr/bin/env python3
"""
Run Young Dependents estimation with LOO-filtered context (proper implementation).
Uses IR agent directly to get properly structured evidence bundles.
"""

import csv
from pathlib import Path
from agent_estimator.ir_agent.parser import DataParsingAgent
from agent_estimator.estimator_agent.estimator import EstimatorAgent

def calculate_mae(actual_value: float, predicted_dist: dict) -> float:
    """Calculate MAE based on topline prediction."""
    predicted_topline = predicted_dist.get("SA", 0) + predicted_dist.get("A", 0)
    return abs(actual_value - predicted_topline)

def main():
    # Paths
    demographic_label = "Young Dependents"
    questions_path = Path("Handpicked_experiments_10.csv")
    base_dir = Path("demographic_runs/young_dependents/handpicked_context_workspace")
    output_file = Path("demographic_runs/young_dependents/results_LOO.csv")

    print("=" * 100)
    print("YOUNG DEPENDENTS ESTIMATION WITH LOO-FILTERED CONTEXT")
    print("=" * 100)
    print(f"Base directory: {base_dir}")
    print(f"Output file: {output_file}")
    print()
    print("LOO FILTERING:")
    print("+ Exact matches EXCLUDED from context")
    print("+ Only proxy/related questions used as evidence")
    print("+ Tests TRUE prediction ability (not format conversion)")
    print("=" * 100)
    print()

    # Load concepts and actual values from CSV
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

    print(f"Found {len(concepts_data)} concepts for {demographic_label}")
    print()

    # Initialize IR agent with LOO filtering
    print("Initializing IR agent with LOO filtering...")
    from agent_estimator.ir_agent.parser import _bundle_inputs
    _bundle_inputs.cache_clear()  # Clear cache to ensure fresh data

    ir_agent = DataParsingAgent(base_dir)
    print("IR agent initialized.")
    print()

    # Initialize estimator
    print("Initializing estimator agent...")
    estimator = EstimatorAgent()
    print("Estimator initialized.")
    print()

    # Run estimates
    results = []
    print("Running estimates...")
    print("-" * 100)

    for idx, data in enumerate(concepts_data, 1):
        concept = data["concept"]
        actual_value = data["actual_value"]

        print(f"[{idx}/{len(concepts_data)}] Estimating: {concept[:60]}...")
        print(f"  Actual topline: {actual_value:.4f}")

        # Get evidence bundle with LOO filtering enabled
        bundle = ir_agent.prepare_concept_bundle(concept, exclude_exact_match=True)

        # Check if we have evidence
        has_quant = bool(bundle.get("quant_summary", "").strip())
        has_text = bool(bundle.get("textual_summary", "").strip())
        print(f"  Evidence: Quant={'Yes' if has_quant else 'No'}, Text={'Yes' if has_text else 'No'}")

        # Run estimation (5 runs for aggregation)
        result = estimator.estimate(
            concept=concept,
            evidence=bundle,
            runs=5,
            iteration=1,
            feedback=""
        )

        predicted_dist = result.aggregated_distribution
        # Use correct LIKERT_ORDER keys (underscore format)
        predicted_topline = (predicted_dist.get("strongly_agree", 0) + predicted_dist.get("slightly_agree", 0)) / 100.0

        error = abs(actual_value - predicted_topline)
        print(f"  Predicted topline: {predicted_topline:.4f}")
        print(f"  Error: {error:.4f} ({error*100:.2f}%)")
        print(f"  Distribution: SA={predicted_dist.get('strongly_agree', 0)}%, A={predicted_dist.get('slightly_agree', 0)}%, N={predicted_dist.get('neither_agree_nor_disagree', 0)}%, D={predicted_dist.get('slightly_disagree', 0)}%, SD={predicted_dist.get('strongly_disagree', 0)}%")

        results.append({
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
        print()

    # Calculate aggregate metrics
    avg_error = sum(r["error"] for r in results) / len(results)

    print("=" * 100)
    print("RESULTS SUMMARY")
    print("=" * 100)
    print(f"Total concepts: {len(results)}")
    print(f"Average topline error: {avg_error:.4f} ({avg_error*100:.2f}%)")
    print()

    # Show top 5 best and worst predictions
    sorted_results = sorted(results, key=lambda x: x["error"])
    print("TOP 5 BEST PREDICTIONS:")
    for i, r in enumerate(sorted_results[:5], 1):
        print(f"  {i}. {r['concept'][:60]}... | Error: {r['error']:.4f}")
    print()

    print("TOP 5 WORST PREDICTIONS:")
    for i, r in enumerate(sorted_results[-5:][::-1], 1):
        print(f"  {i}. {r['concept'][:60]}... | Error: {r['error']:.4f}")
    print()

    # Write results to CSV
    print(f"Writing results to {output_file}...")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "concept", "actual_topline", "predicted_topline", "error",
            "SA", "A", "N", "D", "SD"
        ])
        writer.writeheader()
        writer.writerows(results)

    print("Done!")
    print("=" * 100)

if __name__ == "__main__":
    main()
