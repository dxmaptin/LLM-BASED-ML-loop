#!/usr/bin/env python3
"""Run V3 prompt on all 22 ACORN classes."""

import subprocess
import sys
from pathlib import Path
import time

# All 22 ACORN classes
ACORN_CLASSES = [
    "aspiring_communities",
    "cash-strapped_families",
    "challenging_circumstances",
    "commuter-belt_wealth",
    "constrained_penisoners",
    "exclusive_addresses",
    "family_renters",
    "flourishing_capital",
    "hard-up_households",
    "limited_budgets",
    "mature_success",
    "metropolitan_surroundings",
    "not_private_households",
    "prosperous_professionals",
    "semi-rural_maturity",
    "settled_suburbia",
    "stable_seniors",
    "tenant_living",
    "traditional_homeowners",
    "up-and-coming_urbanites",
    "upmarket_families",
    "urban_diversity"
]

BASE_DIR = Path("demographic_runs_ACORN")
PYTHON = Path("venv/Scripts/python.exe")

print("="*80)
print("RUNNING V3 PROMPT ON ALL 22 ACORN CLASSES")
print("="*80)
print(f"\nTotal classes: {len(ACORN_CLASSES)}")
print(f"Estimated time: ~2-3 hours")
print("="*80)

results = []
failed_classes = []

for idx, class_name in enumerate(ACORN_CLASSES, 1):
    print(f"\n[{idx}/22] Processing: {class_name}")
    print("-" * 80)

    class_dir = BASE_DIR / class_name
    context_file = class_dir / "context_summary_generated.txt"
    estimator_output = class_dir / "estimator_results_ACORN_v3.txt"

    if not context_file.exists():
        print(f"  [SKIP] No context file")
        failed_classes.append((class_name, "No context file"))
        continue

    # Check if V3 already exists (skip if done)
    if estimator_output.exists():
        print(f"  [SKIP] V3 already exists")
        results.append({"class": class_name, "time": 0, "status": "cached"})
        continue

    print(f"  Running Estimator + Critic (V3 prompt)...")
    start_time = time.time()

    try:
        result = subprocess.run(
            [
                str(PYTHON), "run_estimator_from_context.py",
                "--context", str(context_file),
                "--output", str(estimator_output)
            ],
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode != 0:
            print(f"  [FAIL] Estimator failed:")
            print(f"     {result.stderr[:200]}")
            failed_classes.append((class_name, "Estimator failed"))
            continue

        if not estimator_output.exists():
            print(f"  [FAIL] Results not generated")
            failed_classes.append((class_name, "Output not created"))
            continue

        elapsed = time.time() - start_time
        print(f"  [OK] Completed ({elapsed:.1f}s)")
        results.append({"class": class_name, "time": elapsed, "status": "new"})

    except subprocess.TimeoutExpired:
        print(f"  [FAIL] Timeout (>10 minutes)")
        failed_classes.append((class_name, "Timeout"))
        continue
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        failed_classes.append((class_name, f"Error: {e}"))
        continue

print("\n" + "="*80)
print("V3 FULL DATASET RUN COMPLETE")
print("="*80)

new_runs = [r for r in results if r["status"] == "new"]
cached_runs = [r for r in results if r["status"] == "cached"]

print(f"\n[OK] Successfully processed: {len(results)}/{len(ACORN_CLASSES)} classes")
print(f"  New runs: {len(new_runs)}")
print(f"  Cached (already done): {len(cached_runs)}")
print(f"[FAIL] Failed: {len(failed_classes)} classes")

if failed_classes:
    print("\nFailed classes:")
    for class_name, reason in failed_classes:
        print(f"  - {class_name}: {reason}")

if new_runs:
    total_time = sum(r["time"] for r in new_runs)
    avg_time = total_time / len(new_runs)
    print(f"\nNew processing time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"Average time per class: {avg_time:.1f}s")

print("\n" + "="*80)
print("Next step: calculate_r2_v3_full.py to compute R² for all V3 predictions")
print("="*80)
