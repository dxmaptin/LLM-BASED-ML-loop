import re
from pathlib import Path
import pandas as pd

DATASET_PATH = Path('CACI Fresco Flattened Data_C.xlsx')
CONCEPTS_PATH = Path('concepts_to_test.csv')
RUNS_ROOT = Path('demographic_runs')

if not DATASET_PATH.exists():
    raise FileNotFoundError(f'Missing dataset: {DATASET_PATH}')
if not CONCEPTS_PATH.exists():
    raise FileNotFoundError(f'Missing concepts list: {CONCEPTS_PATH}')
if not RUNS_ROOT.exists():
    raise FileNotFoundError(f'Missing demographic runs folder: {RUNS_ROOT}')

def slugify(name: str) -> str:
    slug = re.sub(r"[^\w]+", "_", name.strip().lower())
    return re.sub(r"_+", "_", slug).strip("_") or "segment"

def parse_concepts(path: Path):
    pairs = set()
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        if ':' in line:
            category, question = line.split(':', 1)
            pairs.add((category.strip(), question.strip()))
        else:
            pairs.add(("", line.strip()))
    return pairs

concept_pairs = parse_concepts(CONCEPTS_PATH)

raw_df = pd.read_excel(DATASET_PATH)
raw_df['Category'] = raw_df['Category'].astype(str).str.strip()
raw_df['Question'] = raw_df['Question'].astype(str).str.strip()
raw_df['Answer'] = raw_df['Answer'].astype(str).str.strip()

mask = raw_df.apply(lambda row: (row['Category'], row['Question']) not in concept_pairs, axis=1)
filtered_df = raw_df[mask].copy()

value_columns = [col for col in filtered_df.columns if col not in {'Category', 'Question', 'Answer'}]

if not value_columns:
    raise ValueError('No demographic columns detected after filtering.')

for column in value_columns:
    slug = slugify(column)
    run_dir = RUNS_ROOT / slug
    if not run_dir.exists():
        run_dir.mkdir(parents=True, exist_ok=True)
    flattened_dir = run_dir / 'Flattened Data Inputs'
    flattened_dir.mkdir(parents=True, exist_ok=True)
    output_path = flattened_dir / f'{slug}.csv'
    subset = filtered_df[['Question', 'Answer', column]].copy()
    subset = subset.rename(columns={'Answer': 'Option', column: 'Value'})
    subset.to_csv(output_path, index=False)
    print(f'Wrote {output_path}')
