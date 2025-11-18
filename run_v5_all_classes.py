#!/usr/bin/env python3
"""Run V5 (general) prompt on all 22 ACORN classes."""

import subprocess
import sys
from pathlib import Path
import time

BASE_DIR = Path("demographic_runs_ACORN")
PYTHON = Path("venv/Scripts/python.exe")

ACORN_CLASSES = [
    "aspiring_communities", "cash-strapped_families", "challenging_circumstances",
    "commuter-belt_wealth", "constrained_penisoners", "exclusive_addresses",
    "family_renters", "flourishing_capital", "hard-up_households",
    "limited_budgets", "mature_success", "metropolitan_surroundings",
    "not_private_households", "prosperous_professionals", "semi-rural_maturity",
    "settled_suburbia", "stable_seniors", "tenant_living",
    "traditional_homeowners", "up-and-coming_urbanites", "upmarket_families",
    "urban_diversity"
]

print("="*80)
print("RUNNING V5 (GENERAL) PROMPT ON ALL 22 ACORN CLASSES")
print("="*80)

results = []
failed_classes = []

for idx, class_name in enumerate(ACORN_CLASSES, 1):
    print(f"\n[{idx}/{len(ACORN_CLASSES)}] Processing: {class_name}")

    class_dir = BASE_DIR / class_name
    context_file = class_dir / "context_summary_generated.txt"
    estimator_output = class_dir / "estimator_results_ACORN_v5.txt"

    if not context_file.exists():
        print(f"  [FAIL] Context file not found")
        failed_classes.append((class_name, "No context file"))
        continue

    if estimator_output.exists():
        print(f"  [SKIP] V5 already exists")
        results.append({"class": class_name, "time": 0, "status": "cached"})
        continue

    print(f"  Running...")
    start_time = time.time()

    try:
        result = subprocess.run(
            [str(PYTHON), "run_estimator_from_context.py",
             "--context", str(context_file),
             "--output", str(estimator_output)],
            capture_output=True, text=True, timeout=600
        )

        if result.returncode != 0:
            print(f"  [FAIL]")
            failed_classes.append((class_name, "Estimator failed"))
            continue

        elapsed = time.time() - start_time
        print(f"  [OK] ({elapsed:.1f}s)")
        results.append({"class": class_name, "time": elapsed, "status": "new"})

    except subprocess.TimeoutExpired:
        print(f"  [FAIL] Timeout")
        failed_classes.append((class_name, "Timeout"))
        continue
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed_classes.append((class_name, f"Error: {e}"))
        continue

print("\n" + "="*80)
print("V5 RUN COMPLETE")
print("="*80)
print(f"Processed: {len(results)}/{len(ACORN_CLASSES)}")
print(f"Failed: {len(failed_classes)}")
