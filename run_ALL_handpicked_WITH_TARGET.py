#!/usr/bin/env python3
"""
Run ALL handpicked experiments (all demographics) WITH full context.
Uses GPT-4o with improved proximal detection and guardrails.
"""

import os
from pathlib import Path
import csv

# Set model to GPT-4o
os.environ["AGENT_ESTIMATOR_MODEL"] = "gpt-4o"

from run_handpicked_WITH_TARGET import run_with_full_context

def get_demographics_from_csv(csv_path: Path) -> list[str]:
    """Extract unique demographics from handpicked CSV."""
    demographics = set()
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            demo = row.get("Demographic", "").strip()
            if demo:
                demographics.add(demo)
    return sorted(demographics)


def slugify(value: str) -> str:
    """Convert demographic name to slug."""
    import re
    slug = re.sub(r"[^\w]+", "_", value.strip().lower())
    return re.sub(r"_+", "_", slug).strip("_") or "segment"


def main() -> None:
    questions_path = Path("Handpicked_experiments_10.csv")

    if not questions_path.exists():
        print(f"ERROR: {questions_path} not found!")
        return

    print("=" * 100)
    print("RUNNING ALL HANDPICKED EXPERIMENTS WITH FULL CONTEXT")
    print("=" * 100)
    print("Model: GPT-4o (with improved proximal detection)")
    print("Runs per concept: 5")
    print("Mode: WITH TARGET (not leave-one-out)")
    print()
    print("KEY IMPROVEMENTS ACTIVE:")
    print("+ Proximal topline detection and enforcement")
    print("+ Hard guardrails for magnitude bands")
    print("+ Concept type inference and allocation")
    print("+ Conflict dampening")
    print("=" * 100)
    print()

    # Get all demographics
    demographics = get_demographics_from_csv(questions_path)
    print(f"Found {len(demographics)} demographics:")
    for demo in demographics:
        print(f"  - {demo}")
    print()

    # Process each demographic
    results_summary = []

    for idx, demographic_label in enumerate(demographics, 1):
        print()
        print("=" * 100)
        print(f"[{idx}/{len(demographics)}] PROCESSING: {demographic_label}")
        print("=" * 100)

        slug = slugify(demographic_label)

        # Try demographic-specific directory first, fall back to main directory
        base_dir = Path("demographic_runs") / slug
        if not (base_dir / "Flattened Data Inputs").exists():
            base_dir = Path(".")
            print(f"Using main data directory (no demographic-specific folder found)")
        else:
            print(f"Using demographic-specific directory: {base_dir}")

        output_path = Path("demographic_runs") / slug / "handpicked_WITH_TARGET_improved_ALL.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            run_with_full_context(
                questions_path=questions_path,
                demographic_label=demographic_label,
                base_dir=base_dir,
                output_path=output_path,
                runs_per_concept=5,
            )
            results_summary.append({
                "demographic": demographic_label,
                "status": "SUCCESS",
                "output": str(output_path),
            })
        except Exception as e:
            print(f"ERROR processing {demographic_label}: {e}")
            results_summary.append({
                "demographic": demographic_label,
                "status": f"ERROR: {e}",
                "output": "N/A",
            })
            continue

    # Final summary
    print()
    print("=" * 100)
    print("ALL DEMOGRAPHICS COMPLETE - SUMMARY")
    print("=" * 100)
    print()

    successful = [r for r in results_summary if r["status"] == "SUCCESS"]
    failed = [r for r in results_summary if r["status"] != "SUCCESS"]

    print(f"Total demographics: {len(results_summary)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print()

    if successful:
        print("SUCCESSFUL RUNS:")
        for result in successful:
            print(f"  ✓ {result['demographic']}")
            print(f"    Output: {result['output']}")
        print()

    if failed:
        print("FAILED RUNS:")
        for result in failed:
            print(f"  ✗ {result['demographic']}")
            print(f"    Error: {result['status']}")
        print()

    print("=" * 100)
    print("NEXT STEPS:")
    print("1. Review individual demographic CSV files")
    print("2. Compare MAE across demographics")
    print("3. Check proximal topline detection rates")
    print("4. Validate guardrails enforced correctly")
    print("=" * 100)


if __name__ == "__main__":
    main()
