#!/usr/bin/env python3
"""Run just Batch 3 (11 questions)."""

import json, subprocess, pandas as pd, time
from pathlib import Path

with open('attitude_questions_train_test_split.json') as f:
    batch3 = json.load(f)['train_questions'][40:51]

CLASS_NAME = "aspiring_communities"
source = pd.read_csv(f"demographic_runs_ACORN/{CLASS_NAME}/Flattened Data Inputs/ACORN_{CLASS_NAME}.csv")
gt = {row['Answer']: row['Value'] for _, row in source.iterrows()}

PYTHON, CLASS_DIR = Path("venv/Scripts/python.exe"), Path(f"demographic_runs_ACORN/{CLASS_NAME}")

print(f"BATCH 3: {len(batch3)} questions")

# Create concepts file
with open(CLASS_DIR / "concepts_to_test.csv", 'w') as f:
    f.write("Concept\n")
    for q in batch3:
        f.write(f"{q['question']}\n")

# Run IR
print("Running IR Agent...")
subprocess.run([str(PYTHON), "run_parser_for_dir.py", "--base-dir", str(CLASS_DIR)],
               capture_output=True, timeout=300)

# Run Estimator
print("Running Estimator...")
out = Path("batch3_result.txt")
subprocess.run([str(PYTHON), "run_estimator_from_context.py",
               "--context", str(CLASS_DIR / "context_summary_generated.txt"),
               "--output", str(out)], capture_output=True, timeout=1200)

# Parse
lines, results, idx = out.read_text(encoding='utf-8').splitlines(), [], 0
i = 0
while i < len(lines) and idx < len(batch3):
    if lines[i].startswith("### Concept:"):
        while i < len(lines) and not lines[i].startswith("Final distribution:"):
            i += 1
        if i < len(lines):
            i += 1
            sa = a = None
            for j in range(i, min(i+10, len(lines))):
                if "Strongly agree:" in lines[j]:
                    sa = float(lines[j].split(":")[-1].strip().rstrip('%'))
                elif "Slightly agree:" in lines[j]:
                    a = float(lines[j].split(":")[-1].strip().rstrip('%'))
            if sa and a:
                q = batch3[idx]['question']
                if q in gt:
                    pred, actual = (sa+a)/100, gt[q]
                    err = pred - actual
                    print(f"{idx+1}. {q[:50]}... GT:{actual*100:.1f}% Pred:{pred*100:.1f}% Err:{err*100:+.1f}pp")
                    results.append({"question": q, "actual": actual, "predicted": pred, "error": err})
        idx += 1
    i += 1

mae = sum(abs(r['error']*100) for r in results) / len(results) if results else 0
print(f"\nBatch 3: {len(results)}/11 success, MAE={mae:.2f}pp")

with open("batch3_results.json", 'w') as f:
    json.dump(results, f, indent=2)
