#!/usr/bin/env python3
"""
Run Young Dependents estimation with LOO-filtered context.
This tests TRUE prediction ability (exact matches excluded from context).
"""

import csv
from pathlib import Path
from agent_estimator.orchestrator.runner import DataParsingAgent
from agent_estimator.estimator_agent.estimator import EstimatorAgent

def parse_actual_distribution(value: float) -> dict:
    """Convert topline value to rough distribution for comparison."""
    if value >= 0.7:
        return {"SA": 0.40, "A": 0.35, "N": 0.15, "D": 0.07, "SD": 0.03}
    elif value >= 0.5:
        return {"SA": 0.25, "A": 0.30, "N": 0.25, "D": 0.15, "SD": 0.05}
    elif value >= 0.3:
        return {"SA": 0.15, "A": 0.25, "N": 0.30, "D": 0.20, "SD": 0.10}
    else:
        return {"SA": 0.05, "A": 0.15, "N": 0.25, "D": 0.30, "SD": 0.25}

def calculate_mae(actual_dist: dict, predicted_dist: dict) -> float:
    """Calculate Mean Absolute Error between two distributions."""
    categories = ["SA", "A", "N", "D", "SD"]
    total_error = sum(abs(actual_dist.get(cat, 0) - predicted_dist.get(cat, 0)) for cat in categories)
    return total_error / len(categories)

def main():
    # Paths
    demographic_label = "Young Dependents"
    questions_path = Path("Handpicked_experiments_10.csv")
    context_file = Path("demographic_runs/young_dependents/context_summary_LOO_filtered.txt")
    output_file = Path("demographic_runs/young_dependents/results_LOO.csv")

    print("=" * 100)
    print("YOUNG DEPENDENTS ESTIMATION WITH LOO-FILTERED CONTEXT")
    print("=" * 100)
    print(f"Context file: {context_file}")
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

    # Load context file and parse bundles
    print("Parsing LOO-filtered context file...")
    bundles = {}

    with context_file.open("r", encoding="utf-8") as f:
        content = f.read()

    # Simple parsing of the context file to extract evidence per concept
    import re
    concept_blocks = re.split(r'={100}\nCONCEPT \d+/\d+: ', content)[1:]

    for block in concept_blocks:
        lines = block.split("\n")
        concept = lines[0].strip()

        # Extract quantitative summary
        quant_match = re.search(r'QUANTITATIVE SUMMARY:\n-+\n(.*?)\n\nTEXTUAL SUMMARY:', block, re.DOTALL)
        quant_summary = quant_match.group(1).strip() if quant_match else ""

        # Extract textual summary
        text_match = re.search(r'TEXTUAL SUMMARY:\n-+\n(.*?)\n\nMETADATA:', block, re.DOTALL)
        textual_summary = text_match.group(1).strip() if text_match else ""

        # Extract concept type
        type_match = re.search(r'Concept Type: (\w+)', block)
        concept_type = type_match.group(1) if type_match else "attitude"

        bundles[concept] = {
            "quant_summary": quant_summary,
            "textual_summary": textual_summary,
            "weight_hints": [],
            "concept_type": concept_type,
            "proximal_topline": None,  # Should be None for LOO
        }

    print(f"Loaded {len(bundles)} concept bundles from context file")
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

        if concept not in bundles:
            print(f"[{idx}/{len(concepts_data)}] WARNING: No bundle found for {concept[:60]}...")
            continue

        print(f"[{idx}/{len(concepts_data)}] Estimating: {concept[:60]}...")
        print(f"  Actual topline: {actual_value:.4f}")

        bundle = bundles[concept]

        # Run estimation (5 runs for aggregation)
        result = estimator.estimate(
            concept=concept,
            evidence=bundle,
            runs=5,
            iteration=1,
            feedback=""
        )

        predicted_dist = result.aggregated_distribution
        predicted_topline = predicted_dist.get("SA", 0) + predicted_dist.get("A", 0)

        print(f"  Predicted topline: {predicted_topline:.4f}")
        print(f"  Error: {abs(actual_value - predicted_topline):.4f}")
        print(f"  Distribution: SA={predicted_dist.get('SA', 0):.2%}, A={predicted_dist.get('A', 0):.2%}, N={predicted_dist.get('N', 0):.2%}, D={predicted_dist.get('D', 0):.2%}, SD={predicted_dist.get('SD', 0):.2%}")

        # Calculate MAE
        actual_dist = parse_actual_distribution(actual_value)
        mae = calculate_mae(actual_dist, predicted_dist)

        results.append({
            "concept": concept,
            "actual_topline": actual_value,
            "predicted_topline": predicted_topline,
            "error": abs(actual_value - predicted_topline),
            "mae": mae,
            "SA": predicted_dist.get("SA", 0),
            "A": predicted_dist.get("A", 0),
            "N": predicted_dist.get("N", 0),
            "D": predicted_dist.get("D", 0),
            "SD": predicted_dist.get("SD", 0),
        })
        print()

    # Calculate aggregate metrics
    avg_error = sum(r["error"] for r in results) / len(results)
    avg_mae = sum(r["mae"] for r in results) / len(results)

    print("=" * 100)
    print("RESULTS SUMMARY")
    print("=" * 100)
    print(f"Total concepts: {len(results)}")
    print(f"Average topline error: {avg_error:.4f} ({avg_error*100:.2f}%)")
    print(f"Average MAE: {avg_mae:.4f} ({avg_mae*100:.2f}%)")
    print()

    # Write results to CSV
    print(f"Writing results to {output_file}...")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "concept", "actual_topline", "predicted_topline", "error", "mae",
            "SA", "A", "N", "D", "SD"
        ])
        writer.writeheader()
        writer.writerows(results)

    print("Done!")
    print("=" * 100)

if __name__ == "__main__":
    main()
