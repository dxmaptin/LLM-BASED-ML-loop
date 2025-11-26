"""
List all available questions in the dataset to select new holdout set.
"""

from pathlib import Path
import json

data_dir = Path("demographic_runs_ACORN/exclusive_addresses/Flattened Data Inputs")

# Get all JSON files
json_files = list(data_dir.glob("*.json"))

print(f"Found {len(json_files)} question files\n")
print("="*80)

questions = []
for f in json_files[:50]:  # Show first 50
    # Read the file to get the question
    try:
        data = json.loads(f.read_text(encoding='utf-8'))
        question = data.get('question', f.stem)
        questions.append(question)
        print(f"{len(questions):3}. {question[:70]}...")
    except:
        continue

print(f"\n{'='*80}")
print(f"Total: {len(questions)} questions available")
