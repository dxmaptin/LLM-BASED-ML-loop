#!/usr/bin/env python3
"""Run Batch 2 & 3 together with V7.1 prompt."""

import json
import subprocess
from pathlib import Path
import time
import pandas as pd

# Load questions
with open('attitude_questions_train_test_split.json') as f:
    data = json.load(f)

batch2 = data['train_questions'][20:40]  # Questions 21-40
batch3 = data['train_questions'][40:51]  # Questions 41-51
all_questions = batch2 + batch3

print("="*80)
print(f"ML TRAINING - BATCH 2 & 3 COMBINED")
print("="*80)
print(f"Total questions: {len(all_questions)} (Batch 2: 20, Batch 3: 11)")
print(f"Prompt: V7.1 (with Batch 1 learnings)")
print("="*80)

# Load ground truth
CLASS_NAME = "aspiring_communities"
source_file = Path(f"demographic_runs_ACORN/{CLASS_NAME}/Flattened Data Inputs/ACORN_{CLASS_NAME}.csv")
source_df = pd.read_csv(source_file)
ground_truth = {row['Answer']: row['Value'] for _, row in source_df.iterrows()}

PYTHON = Path("venv/Scripts/python.exe")
CLASS_DIR = Path("demographic_runs_ACORN") / CLASS_NAME
output_dir = Path("batch2_3_results")
output_dir.mkdir(exist_ok=True)

results = []
start = time.time()

for i, q_data in enumerate(all_questions, 1):
    q = q_data['question']
    batch_num = 2 if i <= 20 else 3

    print(f"[{i}/{len(all_questions)}] (Batch {batch_num}) {q[:60]}...")

    if q not in ground_truth:
        print(f"  [SKIP] No ground truth")
        continue

    actual = ground_truth[q]

    # Create concepts file
    with open(CLASS_DIR / "concepts_to_test.csv", 'w') as f:
        f.write("Concept\n" + q + "\n")

    # Run IR + Estimator
    try:
        subprocess.run([str(PYTHON), "run_parser_for_dir.py", "--base-dir", str(CLASS_DIR)],
                      capture_output=True, timeout=120)

        est_out = output_dir / f"q{i:02d}_result.txt"
        subprocess.run([str(PYTHON), "run_estimator_from_context.py",
                       "--context", str(CLASS_DIR / "context_summary_generated.txt"),
                       "--output", str(est_out)],
                      capture_output=True, timeout=120)

        # Parse
        lines = est_out.read_text(encoding='utf-8').splitlines()
        sa = a = None
        for line in lines:
            if "Strongly agree:" in line:
                sa = float(line.split(":")[-1].strip().rstrip('%'))
            elif "Slightly agree:" in line:
                a = float(line.split(":")[-1].strip().rstrip('%'))

        if sa and a:
            pred = (sa + a) / 100.0
            err = pred - actual
            print(f"  GT:{actual*100:.1f}% Pred:{pred*100:.1f}% Err:{err*100:+.1f}pp")
            results.append({"question": q, "batch": batch_num, "actual": actual,
                          "predicted": pred, "error": err})
        else:
            print(f"  [FAIL] Parse error")
    except Exception as e:
        print(f"  [FAIL] {e}")

elapsed = time.time() - start

print(f"\n{'='*80}")
print(f"BATCHES 2 & 3 COMPLETE")
print(f"{'='*80}")
print(f"Success: {len(results)}/{len(all_questions)}")
print(f"Time: {elapsed/60:.1f} min")

if results:
    errors = [r['error'] * 100 for r in results]
    mae = sum(abs(e) for e in errors) / len(errors)
    bias = sum(errors) / len(errors)
    print(f"\nV7.1 Performance:")
    print(f"  MAE: {mae:.2f}pp (Batch 1 baseline was 15.78pp)")
    print(f"  Bias: {bias:+.2f}pp")

    batch2_results = [r for r in results if r['batch'] == 2]
    batch3_results = [r for r in results if r['batch'] == 3]

    if batch2_results:
        b2_mae = sum(abs(r['error']*100) for r in batch2_results) / len(batch2_results)
        print(f"  Batch 2 MAE: {b2_mae:.2f}pp")
    if batch3_results:
        b3_mae = sum(abs(r['error']*100) for r in batch3_results) / len(batch3_results)
        print(f"  Batch 3 MAE: {b3_mae:.2f}pp")

with open(output_dir / "results.json", 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: {output_dir}/results.json")
print("="*80)
