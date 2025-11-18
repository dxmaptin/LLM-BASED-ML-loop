#!/usr/bin/env python3
"""Run Batch 1 (first 20 training questions) on Aspiring Communities - ML Training Pipeline."""

import json
import subprocess
import sys
from pathlib import Path
import time

# Load train/test split
with open('attitude_questions_train_test_split.json') as f:
    data = json.load(f)

# Get Batch 1: first 20 training questions
batch1_questions = data['train_questions'][:20]

print("="*80)
print("ML TRAINING PIPELINE - BATCH 1")
print("="*80)
print(f"Class: Aspiring Communities")
print(f"Questions: 20 (Batch 1 of 3)")
print(f"Prompt: V7 Clean Baseline")
print(f"Output: batch1_results/")
print("="*80)

# Show questions
print("\nBatch 1 Questions:")
for i, q in enumerate(batch1_questions, 1):
    print(f"{i}. [{q['semantic_type']}] {q['question'][:60]}...")

# Create output directory
output_dir = Path("batch1_results")
output_dir.mkdir(exist_ok=True)

PYTHON = Path("venv/Scripts/python.exe")
CLASS_NAME = "aspiring_communities"
CLASS_DIR = Path("demographic_runs_ACORN") / CLASS_NAME

print(f"\n{'='*80}")
print("STARTING BATCH 1 PROCESSING...")
print(f"{'='*80}\n")

results = []
start_time = time.time()

for i, q_data in enumerate(batch1_questions, 1):
    question = q_data['question']
    sem_type = q_data['semantic_type']

    print(f"[{i}/20] Processing: {question[:60]}...")

    # For now, we need to adapt to using the existing IR Agent structure
    # The IR Agent expects questions to be in concepts_to_test.csv
    # We'll create a temporary concepts file for this question

    temp_concepts_file = CLASS_DIR / "concepts_to_test_temp.csv"
    with open(temp_concepts_file, 'w') as f:
        f.write("Concept\n")
        f.write(f"{question}\n")

    # Run IR Agent for this question
    print(f"  Running IR Agent...")
    try:
        ir_result = subprocess.run(
            [str(PYTHON), "run_parser_for_dir.py",
             "--base-dir", str(CLASS_DIR),
             "--concepts-file", "concepts_to_test_temp.csv"],
            capture_output=True,
            text=True,
            timeout=300
        )

        if ir_result.returncode != 0:
            print(f"  [FAIL] IR Agent failed")
            results.append({"question": question, "status": "ir_failed"})
            continue

    except subprocess.TimeoutExpired:
        print(f"  [FAIL] IR Agent timeout")
        results.append({"question": question, "status": "ir_timeout"})
        continue

    # Run Estimator
    context_file = CLASS_DIR / "context_summary_generated.txt"
    output_file = output_dir / f"question_{i:02d}_result.txt"

    print(f"  Running Estimator...")
    try:
        est_result = subprocess.run(
            [str(PYTHON), "run_estimator_from_context.py",
             "--context", str(context_file),
             "--output", str(output_file)],
            capture_output=True,
            text=True,
            timeout=300
        )

        if est_result.returncode != 0:
            print(f"  [FAIL] Estimator failed")
            results.append({"question": question, "status": "est_failed"})
            continue

        print(f"  [OK] Completed")
        results.append({
            "question": question,
            "semantic_type": sem_type,
            "status": "success",
            "output_file": str(output_file)
        })

    except subprocess.TimeoutExpired:
        print(f"  [FAIL] Estimator timeout")
        results.append({"question": question, "status": "est_timeout"})
        continue

elapsed = time.time() - start_time

print(f"\n{'='*80}")
print("BATCH 1 COMPLETE")
print(f"{'='*80}")
print(f"Successful: {len([r for r in results if r['status'] == 'success'])}/20")
print(f"Failed: {len([r for r in results if r['status'] != 'success'])}/20")
print(f"Time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
print(f"\nResults saved to: {output_dir}/")

# Save results summary
with open(output_dir / "batch1_summary.json", 'w') as f:
    json.dump({
        "batch": 1,
        "class": CLASS_NAME,
        "prompt_version": "V7",
        "total_questions": 20,
        "results": results,
        "elapsed_seconds": elapsed
    }, f, indent=2)

print(f"\nNext step: Analyze errors with analyze_batch1_errors.py")
print("="*80)
