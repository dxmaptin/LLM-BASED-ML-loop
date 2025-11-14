#!/usr/bin/env python3
"""Run full pipeline for all 22 ACORN classes and calculate R²."""

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
print("RUNNING FULL PIPELINE FOR ALL 22 ACORN CLASSES")
print("="*80)
print(f"\nTotal classes: {len(ACORN_CLASSES)}")
print(f"Pipeline steps per class:")
print("  1. IR Agent (Data Extraction)")
print("  2. Estimator Agent (Predictions)")
print("  3. Critic Agent (Validation)")
print("\nEstimated time: ~60-90 minutes for all 22 classes")
print("="*80)

results = []
failed_classes = []

for idx, class_name in enumerate(ACORN_CLASSES, 1):
    print(f"\n[{idx}/22] Processing: {class_name}")
    print("-" * 80)

    class_dir = BASE_DIR / class_name
    context_file = class_dir / "context_summary_generated.txt"
    estimator_output = class_dir / "estimator_results_ACORN.txt"

    # Check if class directory exists
    if not class_dir.exists():
        print(f"  ❌ ERROR: Directory not found: {class_dir}")
        failed_classes.append((class_name, "Directory not found"))
        continue

    # Step 1: Run IR Agent (Data Extraction)
    print(f"  [1/2] Running IR Agent...")
    start_time = time.time()

    try:
        result = subprocess.run(
            [str(PYTHON), "run_parser_for_dir.py", "--base-dir", str(class_dir)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )

        if result.returncode != 0:
            print(f"  [FAIL] IR Agent failed:")
            print(f"     {result.stderr[:200]}")
            failed_classes.append((class_name, "IR Agent failed"))
            continue

        if not context_file.exists():
            print(f"  [FAIL] Context file not generated: {context_file}")
            failed_classes.append((class_name, "Context file not created"))
            continue

        ir_time = time.time() - start_time
        print(f"  [OK] IR Agent completed ({ir_time:.1f}s)")

    except subprocess.TimeoutExpired:
        print(f"  [FAIL] IR Agent timeout (>5 minutes)")
        failed_classes.append((class_name, "IR Agent timeout"))
        continue
    except Exception as e:
        print(f"  [FAIL] IR Agent error: {e}")
        failed_classes.append((class_name, f"IR Agent error: {e}"))
        continue

    # Step 2: Run Estimator + Critic
    print(f"  [2/2] Running Estimator + Critic...")
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
            timeout=600  # 10 minutes timeout
        )

        if result.returncode != 0:
            print(f"  [FAIL] Estimator failed:")
            print(f"     {result.stderr[:200]}")
            failed_classes.append((class_name, "Estimator failed"))
            continue

        if not estimator_output.exists():
            print(f"  [FAIL] Estimator results not generated")
            failed_classes.append((class_name, "Estimator output not created"))
            continue

        estimator_time = time.time() - start_time
        print(f"  [OK] Estimator + Critic completed ({estimator_time:.1f}s)")

        results.append({
            "class": class_name,
            "ir_time": ir_time,
            "estimator_time": estimator_time,
            "total_time": ir_time + estimator_time
        })

    except subprocess.TimeoutExpired:
        print(f"  [FAIL] Estimator timeout (>10 minutes)")
        failed_classes.append((class_name, "Estimator timeout"))
        continue
    except Exception as e:
        print(f"  [FAIL] Estimator error: {e}")
        failed_classes.append((class_name, f"Estimator error: {e}"))
        continue

print("\n" + "="*80)
print("PIPELINE EXECUTION COMPLETE")
print("="*80)

print(f"\n[OK] Successfully processed: {len(results)}/{len(ACORN_CLASSES)} classes")
print(f"[FAIL] Failed: {len(failed_classes)} classes")

if failed_classes:
    print("\nFailed classes:")
    for class_name, reason in failed_classes:
        print(f"  - {class_name}: {reason}")

if results:
    total_time = sum(r["total_time"] for r in results)
    avg_time = total_time / len(results)
    print(f"\nTotal processing time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"Average time per class: {avg_time:.1f}s")

print("\n" + "="*80)
print("Next step: Run calculate_r2_all_acorn.py to compute R² for all classes")
print("="*80)
