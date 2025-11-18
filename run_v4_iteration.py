#!/usr/bin/env python3
"""Run V4 prompt on underperforming classes from V3."""

import subprocess
import sys
from pathlib import Path
import time
import json

BASE_DIR = Path("demographic_runs_ACORN")
PYTHON = Path("venv/Scripts/python.exe")

# Load underperforming classes
try:
    with open("v3_underperforming_classes.json", "r") as f:
        underperforming = json.load(f)
except FileNotFoundError:
    print("ERROR: v3_underperforming_classes.json not found.")
    print("Please run calculate_r2_v3_full.py first.")
    exit(1)

if not underperforming:
    print("No underperforming classes found! All classes achieved R² >= 0.7")
    exit(0)

underperforming_classes = [item["class"] for item in underperforming]

print("="*80)
print("RUNNING V4 PROMPT ON UNDERPERFORMING CLASSES")
print("="*80)
print(f"\nClasses to process: {len(underperforming_classes)}")
for i, cls in enumerate(underperforming_classes, 1):
    print(f"  {i}. {cls}")
print(f"\nEstimated time: ~{len(underperforming_classes) * 5} minutes")
print("="*80)

results = []
failed_classes = []

for idx, class_name in enumerate(underperforming_classes, 1):
    print(f"\n[{idx}/{len(underperforming_classes)}] Processing: {class_name}")
    print("-" * 80)

    class_dir = BASE_DIR / class_name
    context_file = class_dir / "context_summary_generated.txt"
    estimator_output = class_dir / "estimator_results_ACORN_v4.txt"

    if not context_file.exists():
        print(f"  [FAIL] Context file not found")
        failed_classes.append((class_name, "No context file"))
        continue

    # Check if V4 already exists (skip if done)
    if estimator_output.exists():
        print(f"  [SKIP] V4 already exists")
        results.append({"class": class_name, "time": 0, "status": "cached"})
        continue

    print(f"  Running Estimator + Critic (V4 prompt)...")
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
print("V4 ITERATION COMPLETE")
print("="*80)

new_runs = [r for r in results if r["status"] == "new"]
cached_runs = [r for r in results if r["status"] == "cached"]

print(f"\n[OK] Successfully processed: {len(results)}/{len(underperforming_classes)} classes")
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
print("Next step: calculate_r2_v4.py to compute R² improvements")
print("="*80)
