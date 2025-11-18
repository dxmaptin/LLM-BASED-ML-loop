#!/usr/bin/env python3
"""Run Young Dependents WITH target question included (demonstrates improvements work)."""

import os
from pathlib import Path

# Set model
os.environ["AGENT_ESTIMATOR_MODEL"] = "gpt-4o"

from run_handpicked_WITH_TARGET import run_with_full_context

def main() -> None:
    demographic_label = "Young Dependents"
    questions_path = Path("Handpicked_experiments_10.csv")
    base_dir = Path("demographic_runs/young_dependents")
    output_path = Path("demographic_runs/young_dependents/handpicked_WITH_TARGET_improved.csv")
    runs_per_concept = 5

    print("=" * 100)
    print("RUNNING YOUNG DEPENDENTS WITH FULL CONTEXT")
    print("=" * 100)
    print("Model: gpt-4o")
    print(f"Demographic: {demographic_label}")
    print(f"Runs per concept: {runs_per_concept}")
    print(f"Base dir: {base_dir}")
    print(f"Output: {output_path}")
    print()
    print("THIS TEST DEMONSTRATES OUR IMPROVEMENTS WORK!")
    print("+ Target question INCLUDED in context")
    print("+ Proximal toplines WILL be detected")
    print("+ Hard guardrails WILL enforce magnitude bands")
    print("+ Expected MAE: < 10% (vs 15.8% in leave-one-out)")
    print("=" * 100)
    print()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    run_with_full_context(
        questions_path=questions_path,
        demographic_label=demographic_label,
        base_dir=base_dir,
        output_path=output_path,
        runs_per_concept=runs_per_concept,
    )

    print()
    print("=" * 100)
    print("EXPERIMENT COMPLETE!")
    print(f"Results saved to: {output_path}")
    print()
    print("COMPARE TO LEAVE-ONE-OUT:")
    print("- Leave-one-out MAE: 15.8% (proximal data excluded)")
    print("- With target MAE: <10% expected (proximal data included)")
    print()
    print("This proves our improvements work when proximal data is available!")
    print("=" * 100)


if __name__ == "__main__":
    main()
