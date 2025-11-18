#!/usr/bin/env python3
"""Proper Batch 1 ML training - extract ground truth from source CSV and compare predictions."""

import json
import subprocess
from pathlib import Path
import time
import pandas as pd
import re

# Load train/test split
with open('attitude_questions_train_test_split.json') as f:
    data = json.load(f)

# Get Batch 1: first 20 training questions
batch1_questions = data['train_questions'][:20]

print("="*80)
print("ML TRAINING PIPELINE - BATCH 1 (PROPER)")
print("="*80)
print(f"Class: Aspiring Communities")
print(f"Questions: {len(batch1_questions)}")
print(f"Prompt: V7 Clean Baseline")
print("="*80)

# Load source CSV to get ground truth
CLASS_NAME = "aspiring_communities"
source_file = Path(f"demographic_runs_ACORN/{CLASS_NAME}/Flattened Data Inputs/ACORN_{CLASS_NAME}.csv")
source_df = pd.read_csv(source_file)

# Create ground truth lookup
ground_truth = {}
for _, row in source_df.iterrows():
    answer = row['Answer']
    value = row['Value']
    ground_truth[answer] = value

print(f"\nGround truth loaded: {len(ground_truth)} items")

# Setup
PYTHON = Path("venv/Scripts/python.exe")
CLASS_DIR = Path("demographic_runs_ACORN") / CLASS_NAME
output_dir = Path("batch1_results_proper")
output_dir.mkdir(exist_ok=True)

results = []
start_time = time.time()

for i, q_data in enumerate(batch1_questions, 1):
    question = q_data['question']

    print(f"\n[{i}/{len(batch1_questions)}] {question[:70]}...")

    # Get ground truth
    if question not in ground_truth:
        print(f"  [SKIP] No ground truth found")
        results.append({"question": question, "status": "no_ground_truth"})
        continue

    actual = ground_truth[question]
    print(f"  Ground truth: {actual*100:.1f}%")

    # Create concepts file
    concepts_file = CLASS_DIR / "concepts_to_test.csv"
    with open(concepts_file, 'w') as f:
        f.write("Concept\n")
        f.write(f"{question}\n")

    # Run IR Agent
    print(f"  Running IR Agent...")
    try:
        subprocess.run(
            [str(PYTHON), "run_parser_for_dir.py", "--base-dir", str(CLASS_DIR)],
            capture_output=True, timeout=180
        )
    except:
        print(f"  [FAIL] IR Agent failed")
        results.append({"question": question, "actual": actual, "status": "ir_failed"})
        continue

    # Run Estimator
    context_file = CLASS_DIR / "context_summary_generated.txt"
    estimator_output = output_dir / f"q{i:02d}_result.txt"

    print(f"  Running Estimator...")
    try:
        subprocess.run(
            [str(PYTHON), "run_estimator_from_context.py",
             "--context", str(context_file),
             "--output", str(estimator_output)],
            capture_output=True, timeout=180
        )
    except:
        print(f"  [FAIL] Estimator failed")
        results.append({"question": question, "actual": actual, "status": "est_failed"})
        continue

    # Parse prediction (SA+A%)
    try:
        lines = estimator_output.read_text(encoding='utf-8').splitlines()
        sa, a = None, None
        for j, line in enumerate(lines):
            if "Strongly agree:" in line:
                sa = float(line.split(":")[-1].strip().rstrip('%'))
            elif "Slightly agree:" in line:
                a = float(line.split(":")[-1].strip().rstrip('%'))

        if sa is not None and a is not None:
            predicted = (sa + a) / 100.0
            error = predicted - actual
            print(f"  Predicted: {predicted*100:.1f}%  |  Error: {error*100:+.1f}pp")

            results.append({
                "question": question,
                "semantic_type": q_data['semantic_type'],
                "actual": actual,
                "predicted": predicted,
                "error": error,
                "status": "success"
            })
        else:
            print(f"  [FAIL] Could not parse prediction")
            results.append({"question": question, "actual": actual, "status": "parse_failed"})

    except Exception as e:
        print(f"  [FAIL] {e}")
        results.append({"question": question, "actual": actual, "status": f"error: {e}"})

elapsed = time.time() - start_time

print(f"\n{'='*80}")
print("BATCH 1 COMPLETE")
print(f"{'='*80}")

successful = [r for r in results if r.get('status') == 'success']
print(f"Successful: {len(successful)}/{len(batch1_questions)}")
print(f"Time: {elapsed:.1f}s ({elapsed/60:.1f} min)")

if successful:
    errors = [r['error'] * 100 for r in successful]
    mae = sum(abs(e) for e in errors) / len(errors)
    bias = sum(errors) / len(errors)
    print(f"\nPerformance:")
    print(f"  MAE: {mae:.2f}pp")
    print(f"  Bias: {bias:+.2f}pp")

# Save results
with open(output_dir / "batch1_results.json", 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: {output_dir}/batch1_results.json")
print(f"Next: analyze_batch1_errors.py to learn patterns for V7.1")
print("="*80)
