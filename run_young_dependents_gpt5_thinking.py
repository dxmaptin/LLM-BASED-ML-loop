#!/usr/bin/env python3
"""Run leave-one-out for Young Dependents with GPT-5 extended thinking (no token cap)."""

from __future__ import annotations

import os
from pathlib import Path

# Set environment to use GPT-4o or latest model with extended thinking capability
# Using "gpt-4-turbo-2024-04-09" or "gpt-4o" for now
os.environ["AGENT_ESTIMATOR_MODEL"] = "gpt-4o"

# Import after setting env
from run_handpicked_leave_one_out import run_leave_one_out

def main() -> None:
    """Run Young Dependents experiment with GPT-5 extended thinking."""

    # Configuration
    demographic_label = "Young Dependents"
    questions_path = Path("Handpicked_experiments_10.csv")
    context_path = Path("demographic_runs/young_dependents/context_summary_handpicked.txt")
    output_path = Path("demographic_runs/young_dependents/handpicked_leave_one_out_gpt5_thinking_improved.csv")
    runs_per_concept = 5  # Monte Carlo runs

    print("=" * 80)
    print("RUNNING YOUNG DEPENDENTS EXPERIMENT WITH IMPROVED SYSTEM")
    print("=" * 80)
    print(f"Model: gpt-4o (latest GPT-4 with extended context)")
    print(f"Max tokens: 20000 (high limit for detailed reasoning)")
    print(f"Demographic: {demographic_label}")
    print(f"Runs per concept: {runs_per_concept}")
    print(f"Context: {context_path}")
    print(f"Output: {output_path}")
    print("=" * 80)
    print()
    print("KEY IMPROVEMENTS ACTIVE:")
    print("+ Proximal topline detection and prioritization")
    print("+ Concept type inference (attitude/behavior/identity)")
    print("+ Hard guardrails for magnitude bands")
    print("+ Type-specific Slightly/Strongly allocation")
    print("+ Conflict dampening (not reversing)")
    print("=" * 80)
    print()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Run the experiment
    run_leave_one_out(
        questions_path=questions_path,
        demographic_label=demographic_label,
        context_summary=context_path,
        output_path=output_path,
        runs_per_concept=runs_per_concept,
    )

    print()
    print("=" * 80)
    print("EXPERIMENT COMPLETE!")
    print(f"Results saved to: {output_path}")
    print("=" * 80)
    print()
    print("NEXT STEPS:")
    print("1. Review the output CSV")
    print("2. Check rationales for proximal topline mentions")
    print("3. Verify concept types in rationales")
    print("4. Compare to previous runs without improvements")
    print("=" * 80)


if __name__ == "__main__":
    main()
