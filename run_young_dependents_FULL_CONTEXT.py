#!/usr/bin/env python3
"""
Run Young Dependents WITH FULL CONTEXT (not leave-one-out).
This tests whether our improvements work when proximal data IS available.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any, Dict

# Set model
os.environ["AGENT_ESTIMATOR_MODEL"] = "gpt-4o"

from agent_estimator.estimator_agent import EstimatorAgent
from agent_estimator.ir_agent import DataParsingAgent
from agent_estimator.common.config import BASE_DIR, LIKERT_ORDER, LIKERT_PRETTY

def main() -> None:
    """Run with FULL context to validate improvements."""

    print("=" * 100)
    print("TESTING WITH FULL CONTEXT (Proximal toplines INCLUDED)")
    print("=" * 100)
    print("This validates that our improvements work when exact data is available.")
    print("Expected: MAE < 10% (vs 15.8% in leave-one-out)")
    print("=" * 100)
    print()

    # Use the Young Dependents workspace WITH full context
    workspace = Path("demographic_runs/young_dependents/handpicked_context_workspace")
    if not workspace.exists():
        # Fall back to generating from existing context
        workspace = BASE_DIR

    parser = DataParsingAgent(workspace)
    estimator = EstimatorAgent()

    # Load ground truth from handpicked experiments
    ground_truth: Dict[str, float] = {}
    with Path("Handpicked_experiments_10.csv").open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Demographic"].strip() == "Young Dependents":
                concept = f"{row['Question'].strip()} - {row['Answer'].strip()}"
                ground_truth[concept] = float(row["Value"])

    if not ground_truth:
        print("ERROR: No Young Dependents data found in Handpicked_experiments_10.csv")
        return

    print(f"Found {len(ground_truth)} concepts with ground truth")
    print()

    # Concepts to test (matching the leave-one-out format)
    test_concepts = [
        "Attitudes - I like to look out for where my products are made or grown",
        "Attitudes - I make an effort to support local businesses",
        "Attitudes - Prefers to buy from brands which have a social and environmental commitment",
        "Contentment - Satisfied with: Life overall",
        "Environmental - Climate change is the biggest threat to civilisation",
        "Environmental - I always make an effort to recycle",
        "Environmental - I consider myself an environmentalist",
        "Financial Attitudes - I hate to borrow - I would much rather save up in advance",
        "Financial Attitudes - I trust financial price comparison sites",
        "Financial Attitudes - I would be happy to use the Internet to carry out day to day banking transactions",
    ]

    results = []
    runs_per_concept = 3  # Fewer runs since we're just validating

    for idx, concept in enumerate(test_concepts, 1):
        print(f"[{idx}/{len(test_concepts)}] {concept}")

        # Get FULL evidence bundle (includes proximal topline!)
        try:
            evidence = parser.prepare_concept_bundle(concept)
        except Exception as e:
            print(f"  ERROR preparing bundle: {e}")
            continue

        # Check if proximal topline was found
        proximal = evidence.get("proximal_topline")
        concept_type = evidence.get("concept_type", "unknown")
        print(f"  Proximal: {proximal:.4f if proximal else 'NOT FOUND'} | Type: {concept_type}")

        # Estimate
        result = estimator.estimate(
            concept=concept,
            evidence=evidence,
            runs=runs_per_concept,
            iteration=1,
            feedback="",
        )

        dist = result.aggregated_distribution
        sa = dist.get("strongly_agree", 0)
        a = dist.get("slightly_agree", 0)
        predicted = (sa + a) / 100.0

        # Get ground truth
        observed = ground_truth.get(concept)
        if observed is None:
            print(f"  WARNING: No ground truth for {concept}")
            continue

        error = abs(predicted - observed)
        print(f"  Observed: {observed:.3f} | Predicted: {predicted:.3f} | Error: {error:.3f} ({error*100:.1f}%)")
        print()

        results.append({
            "Concept": concept,
            "Observed": observed,
            "Predicted": predicted,
            "Error": error,
            "Proximal_topline": proximal,
            "Concept_type": concept_type,
            "SA": sa,
            "A": a,
            "N": dist.get("neither_agree_nor_disagree", 0),
            "SD": dist.get("slightly_disagree", 0),
            "SDD": dist.get("strongly_disagree", 0),
        })

    # Save results
    output_path = Path("demographic_runs/young_dependents/full_context_test_results.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["Concept", "Observed", "Predicted", "Error", "Proximal_topline",
                     "Concept_type", "SA", "A", "N", "SD", "SDD"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print()
    print("=" * 100)
    print("RESULTS SUMMARY")
    print("=" * 100)

    if results:
        mae = sum(r["Error"] for r in results) / len(results)
        with_proximal = [r for r in results if r["Proximal_topline"] is not None]
        without_proximal = [r for r in results if r["Proximal_topline"] is None]

        print(f"Total concepts: {len(results)}")
        print(f"Mean Absolute Error (MAE): {mae:.3f} ({mae*100:.1f}%)")
        print()
        print(f"With proximal topline: {len(with_proximal)}")
        if with_proximal:
            mae_prox = sum(r["Error"] for r in with_proximal) / len(with_proximal)
            print(f"  MAE: {mae_prox:.3f} ({mae_prox*100:.1f}%)")
        print()
        print(f"Without proximal topline: {len(without_proximal)}")
        if without_proximal:
            mae_no_prox = sum(r["Error"] for r in without_proximal) / len(without_proximal)
            print(f"  MAE: {mae_no_prox:.3f} ({mae_no_prox*100:.1f}%)")
        print()

        # Check if guardrails worked
        high_obs_high_pred = [r for r in with_proximal if r["Proximal_topline"] and r["Proximal_topline"] >= 0.70 and r["Predicted"] >= 0.65]
        low_obs_low_pred = [r for r in with_proximal if r["Proximal_topline"] and r["Proximal_topline"] <= 0.30 and r["Predicted"] <= 0.35]

        print(f"Guardrail validation:")
        print(f"  High proximal (≥0.70) → High predicted (≥0.65): {len(high_obs_high_pred)}/{len([r for r in with_proximal if r['Proximal_topline'] and r['Proximal_topline'] >= 0.70])}")
        print(f"  Low proximal (≤0.30) → Low predicted (≤0.35): {len(low_obs_low_pred)}/{len([r for r in with_proximal if r['Proximal_topline'] and r['Proximal_topline'] <= 0.30])}")

    print()
    print(f"Results saved to: {output_path}")
    print("=" * 100)


if __name__ == "__main__":
    main()
