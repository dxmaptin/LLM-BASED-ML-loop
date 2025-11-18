#!/usr/bin/env python3
"""Automated iteration loop to improve prompts until all classes achieve R² > 0.7."""

import subprocess
import sys
from pathlib import Path
import time
import json

PYTHON = Path("venv/Scripts/python.exe")
TARGET_R2 = 0.7
MAX_ITERATIONS = 10  # Safety limit

print("="*80)
print("AUTOMATED REINFORCEMENT LEARNING ITERATION")
print("="*80)
print(f"Target: All classes achieve R² > {TARGET_R2}")
print(f"Max iterations: {MAX_ITERATIONS}")
print("="*80)

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n[RUNNING] {description}...")
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[FAIL] {description}")
        print(result.stderr[:500])
        return False

    print(f"[OK] {description}")
    return True

def get_underperforming_count():
    """Get number of underperforming classes from latest analysis."""
    try:
        with open("v3_underperforming_classes.json", "r") as f:
            underperforming = json.load(f)
        return len(underperforming)
    except FileNotFoundError:
        return None

def check_all_classes_pass():
    """Check if all classes achieved target R²."""
    try:
        with open("ACORN_v3_r2_results.json", "r") as f:
            results = json.load(f)

        below_target = [r for r in results if r["r2"] < TARGET_R2]
        return len(below_target) == 0, len(below_target)
    except FileNotFoundError:
        return False, None

# Iteration loop
for iteration in range(1, MAX_ITERATIONS + 1):
    print(f"\n{'='*80}")
    print(f"ITERATION {iteration}")
    print(f"{'='*80}")

    # Step 1: Calculate R² for current version
    print(f"\nStep 1: Calculate R² for all classes")
    if not run_command([str(PYTHON), "calculate_r2_v3_full.py"], "R² calculation"):
        print("ERROR: R² calculation failed")
        break

    # Step 2: Check if target achieved
    all_pass, num_below = check_all_classes_pass()

    if all_pass:
        print(f"\n{'='*80}")
        print("TARGET ACHIEVED!")
        print(f"All {22} classes now have R² >= {TARGET_R2}")
        print(f"Iterations required: {iteration}")
        print(f"{'='*80}")
        break

    print(f"\n{num_below} classes still below R² = {TARGET_R2}")

    # Step 3: Analyze errors
    print(f"\nStep 2: Analyze errors for underperforming classes")
    if not run_command([str(PYTHON), "analyze_v3_errors_detailed.py"], "Error analysis"):
        print("ERROR: Error analysis failed")
        break

    # Step 4: Manual prompt improvement required
    print(f"\n{'='*80}")
    print("PROMPT IMPROVEMENT REQUIRED")
    print(f"{'='*80}")
    print(f"Based on the error analysis:")
    print(f"  1. Review: v3_error_analysis_detailed.json")
    print(f"  2. Update: agent_estimator/estimator_agent/prompts/general_system_prompt.txt")
    print(f"  3. Save as: general_system_prompt_v{iteration+3}.txt")
    print(f"  4. Press Enter when ready to test V{iteration+3}...")

    input()  # Wait for user to update prompt

    # Step 5: Run improved prompt on underperforming classes
    print(f"\nStep 3: Run V{iteration+3} on underperforming classes")
    if not run_command([str(PYTHON), "run_v4_iteration.py"], f"V{iteration+3} iteration"):
        print("ERROR: Iteration run failed")
        break

    print(f"\nIteration {iteration} complete. Starting next iteration...")

else:
    print(f"\n{'='*80}")
    print("MAX ITERATIONS REACHED")
    print(f"{'='*80}")
    print(f"Completed {MAX_ITERATIONS} iterations without achieving target.")
    print(f"Final R² results saved in ACORN_v3_r2_results.json")
    print(f"{'='*80}")
