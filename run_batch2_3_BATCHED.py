#!/usr/bin/env python3
"""Run Batch 2 & 3 as TRUE batches (all questions in one IR + Estimator run)."""

import json
import subprocess
from pathlib import Path
import time
import pandas as pd

# Load questions
with open('attitude_questions_train_test_split.json') as f:
    data = json.load(f)

batch2 = data['train_questions'][20:40]  # 20 questions
batch3 = data['train_questions'][40:51]  # 11 questions

print("="*80)
print("ML TRAINING - BATCH 2 & 3 (TRUE BATCHING)")
print("="*80)
print("V7.1 prompt active (with Batch 1 learnings)")
print("="*80)

# Load ground truth
CLASS_NAME = "aspiring_communities"
source_file = Path(f"demographic_runs_ACORN/{CLASS_NAME}/Flattened Data Inputs/ACORN_{CLASS_NAME}.csv")
source_df = pd.read_csv(source_file)
ground_truth = {row['Answer']: row['Value'] for _, row in source_df.iterrows()}

PYTHON = Path("venv/Scripts/python.exe")
CLASS_DIR = Path("demographic_runs_ACORN") / CLASS_NAME

def run_batch(batch_questions, batch_name, output_file):
    """Run a batch of questions with single IR + Estimator call."""
    print(f"\n{'='*80}")
    print(f"PROCESSING {batch_name} ({len(batch_questions)} questions)")
    print(f"{'='*80}")

    # Create concepts file with ALL questions
    concepts_file = CLASS_DIR / "concepts_to_test.csv"
    with open(concepts_file, 'w') as f:
        f.write("Concept\n")
        for q in batch_questions:
            f.write(f"{q['question']}\n")

    print(f"Created concepts file with {len(batch_questions)} questions")

    # Run IR Agent ONCE for all questions
    print(f"Running IR Agent (extracting evidence for all questions)...")
    start = time.time()
    ir_result = subprocess.run(
        [str(PYTHON), "run_parser_for_dir.py", "--base-dir", str(CLASS_DIR)],
        capture_output=True, timeout=300
    )
    ir_time = time.time() - start
    print(f"  IR Agent complete ({ir_time:.1f}s)")

    if ir_result.returncode != 0:
        print(f"  [FAIL] IR Agent failed!")
        return []

    # Run Estimator ONCE for all questions
    print(f"Running Estimator (predicting all questions)...")
    context_file = CLASS_DIR / "context_summary_generated.txt"
    est_start = time.time()
    est_result = subprocess.run(
        [str(PYTHON), "run_estimator_from_context.py",
         "--context", str(context_file),
         "--output", str(output_file)],
        capture_output=True, timeout=1200
    )
    est_time = time.time() - est_start
    print(f"  Estimator complete ({est_time:.1f}s)")

    if est_result.returncode != 0:
        print(f"  [FAIL] Estimator failed!")
        return []

    # Parse all predictions
    print(f"Parsing predictions...")
    lines = output_file.read_text(encoding='utf-8').splitlines()

    results = []
    i = 0
    concept_idx = 0

    while i < len(lines) and concept_idx < len(batch_questions):
        if lines[i].startswith("### Concept:"):
            concept_name = lines[i].split("### Concept:", 1)[1].strip()

            # Find distribution
            while i < len(lines) and not lines[i].startswith("Final distribution:"):
                i += 1

            if i < len(lines):
                i += 1
                sa, a = None, None
                for j in range(i, min(i + 10, len(lines))):
                    if "Strongly agree:" in lines[j]:
                        sa = float(lines[j].split(":")[-1].strip().rstrip('%'))
                    elif "Slightly agree:" in lines[j]:
                        a = float(lines[j].split(":")[-1].strip().rstrip('%'))
                    elif lines[j].startswith("Runs:"):
                        break

                if sa is not None and a is not None:
                    pred = (sa + a) / 100.0
                    actual_q = batch_questions[concept_idx]['question']

                    if actual_q in ground_truth:
                        actual = ground_truth[actual_q]
                        error = pred - actual
                        results.append({
                            "question": actual_q,
                            "actual": actual,
                            "predicted": pred,
                            "error": error
                        })
                        print(f"  {concept_idx+1}. {actual_q[:50]}... GT:{actual*100:.1f}% Pred:{pred*100:.1f}% Err:{error*100:+.1f}pp")

            concept_idx += 1
        i += 1

    total_time = ir_time + est_time
    print(f"\n{batch_name} complete: {len(results)}/{len(batch_questions)} success in {total_time:.1f}s")
    return results

# Run Batch 2
batch2_results = run_batch(batch2, "BATCH 2", Path("batch2_results_batched.txt"))

# Run Batch 3
batch3_results = run_batch(batch3, "BATCH 3", Path("batch3_results_batched.txt"))

# Combined analysis
all_results = batch2_results + batch3_results

print(f"\n{'='*80}")
print("BATCHES 2 & 3 COMPLETE")
print(f"{'='*80}")
print(f"Total success: {len(all_results)}/{len(batch2)+len(batch3)}")

if all_results:
    errors = [r['error'] * 100 for r in all_results]
    mae = sum(abs(e) for e in errors) / len(errors)
    bias = sum(errors) / len(errors)

    print(f"\nV7.1 Performance on Batches 2 & 3:")
    print(f"  MAE: {mae:.2f}pp")
    print(f"  Bias: {bias:+.2f}pp")
    print(f"  (Batch 1 baseline was MAE=15.78pp)")

    if batch2_results:
        b2_mae = sum(abs(r['error']*100) for r in batch2_results) / len(batch2_results)
        print(f"\n  Batch 2 MAE: {b2_mae:.2f}pp ({len(batch2_results)} questions)")
    if batch3_results:
        b3_mae = sum(abs(r['error']*100) for r in batch3_results) / len(batch3_results)
        print(f"  Batch 3 MAE: {b3_mae:.2f}pp ({len(batch3_results)} questions)")

# Save
with open("batch2_3_results_batched.json", 'w') as f:
    json.dump({"batch2": batch2_results, "batch3": batch3_results}, f, indent=2)

print(f"\nResults saved to: batch2_3_results_batched.json")
print("="*80)
