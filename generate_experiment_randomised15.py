import pandas as pd
from pathlib import Path

DATASET_PATH = Path('CACI Fresco Flattened Data_C.xlsx')
CONCEPTS_PATH = Path('concepts_to_test.csv')
OUTPUT_PATH = Path('experiment_result_randomised15.csv')

if not DATASET_PATH.exists():
    raise FileNotFoundError(f'Missing dataset: {DATASET_PATH}')
if not CONCEPTS_PATH.exists():
    raise FileNotFoundError(f'Missing concepts list: {CONCEPTS_PATH}')

df = pd.read_excel(DATASET_PATH)
df['Category'] = df['Category'].astype(str).str.strip()
df['Question'] = df['Question'].astype(str).str.strip()
df['Answer'] = df['Answer'].astype(str).str.strip()
value_columns = [col for col in df.columns if col not in {'Category', 'Question', 'Answer'}]

concept_pairs = []
for raw_line in CONCEPTS_PATH.read_text(encoding='utf-8').splitlines():
    line = raw_line.strip()
    if not line:
        continue
    if ':' in line:
        category, question = line.split(':', 1)
        concept_pairs.append((category.strip(), question.strip()))
    else:
        concept_pairs.append(('', line))

records = []
for category, question in concept_pairs:
    subset = df[(df['Category'] == category) & (df['Question'] == question)]
    if subset.empty:
        raise ValueError(f'No rows found for concept: {category}: {question}')
    for _, row in subset.iterrows():
        option = row['Answer']
        for demo in value_columns:
            records.append({
                'Question': category,
                'Option': option,
                'Demographic': demo,
                'Value': row[demo],
            })

out_df = pd.DataFrame(records, columns=['Question', 'Option', 'Demographic', 'Value'])
out_df.to_csv(OUTPUT_PATH, index=False)
print(f'Wrote {len(out_df)} rows to {OUTPUT_PATH}')
