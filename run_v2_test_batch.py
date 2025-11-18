#!/usr/bin/env python3
"""Run V2 prompt on 6 test classes and compare with V1 results."""

import subprocess
import sys
from pathlib import Path
import time

# Select 6 diverse classes: 2 best performers, 2 worst, 2 middle from V1
TEST_CLASSES = [
    "semi-rural_maturity",        # Best V1 performer (R² = 0.04)
    "constrained_penisoners",     # 2nd best (R² = -0.14)
    "upmarket_families",          # Middle performer (R² = -0.17)
    "family_renters",             # Middle performer (R² = -0.17)
    "stable_seniors",             # Worst performer (R² = -0.53)
    "urban_diversity"             # 2nd worst (R² = -0.67)
]

BASE_DIR = Path("demographic_runs_ACORN")
PYTHON = Path("venv/Scripts/python.exe")

print("="*80)
print("RUNNING V2 PROMPT ON 6 TEST CLASSES")
print("="*80)
print(f"\nTest classes selected:")
for i, cls in enumerate(TEST_CLASSES, 1):
    print(f"  {i}. {cls}")
print(f"\nEstimated time: ~30 minutes (6 classes × 5 min each)")
print("="*80)

results = []
failed_classes = []

for idx, class_name in enumerate(TEST_CLASSES, 1):
    print(f"\n[{idx}/6] Processing: {class_name}")
    print("-" * 80)

    class_dir = BASE_DIR / class_name
    context_file = class_dir / "context_summary_generated.txt"
    estimator_output = class_dir / "estimator_results_ACORN_v2.txt"

    # Check if context file exists
    if not context_file.exists():
        print(f"  [FAIL] Context file not found: {context_file}")
        failed_classes.append((class_name, "No context file"))
        continue

    # Run Estimator + Critic with V2 prompt
    print(f"  [1/1] Running Estimator + Critic (V2 prompt)...")
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
            "time": estimator_time
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
print("V2 TEST BATCH COMPLETE")
print("="*80)

print(f"\n[OK] Successfully processed: {len(results)}/6 classes")
print(f"[FAIL] Failed: {len(failed_classes)} classes")

if failed_classes:
    print("\nFailed classes:")
    for class_name, reason in failed_classes:
        print(f"  - {class_name}: {reason}")

if results:
    total_time = sum(r["time"] for r in results)
    avg_time = total_time / len(results)
    print(f"\nTotal processing time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"Average time per class: {avg_time:.1f}s")

print("\n" + "="*80)
print("Next step: Run compare_v1_v2_batch.py to compute R² improvements")
print("="*80)
