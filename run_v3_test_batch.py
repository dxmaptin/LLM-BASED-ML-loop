#!/usr/bin/env python3
"""Run V3 prompt on 6 test classes."""

import subprocess
from pathlib import Path
import time

TEST_CLASSES = [
    "semi-rural_maturity",
    "constrained_penisoners",
    "upmarket_families",
    "family_renters",
    "stable_seniors",
    "urban_diversity"
]

BASE_DIR = Path("demographic_runs_ACORN")
PYTHON = Path("venv/Scripts/python.exe")

print("="*80)
print("RUNNING V3 PROMPT ON 6 TEST CLASSES")
print("="*80)

for idx, class_name in enumerate(TEST_CLASSES, 1):
    print(f"\n[{idx}/6] Processing: {class_name}")
    print("-" * 80)

    class_dir = BASE_DIR / class_name
    context_file = class_dir / "context_summary_generated.txt"
    estimator_output = class_dir / "estimator_results_ACORN_v3.txt"

    if not context_file.exists():
        print(f"  [FAIL] Context file not found")
        continue

    print(f"  Running Estimator + Critic (V3 prompt)...")
    start_time = time.time()

    try:
        result = subprocess.run(
            [str(PYTHON), "run_estimator_from_context.py",
             "--context", str(context_file),
             "--output", str(estimator_output)],
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode != 0:
            print(f"  [FAIL] Error: {result.stderr[:200]}")
            continue

        elapsed = time.time() - start_time
        print(f"  [OK] Completed ({elapsed:.1f}s)")

    except Exception as e:
        print(f"  [FAIL] {e}")

print("\n" + "="*80)
print("V3 TEST BATCH COMPLETE")
print("="*80)
