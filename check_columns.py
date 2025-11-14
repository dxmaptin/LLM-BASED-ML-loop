import pandas as pd
import re

def to_snake_case(col_name):
    col_name = str(col_name).strip()
    col_name = col_name.replace('%', 'pct')
    col_name = re.sub(r'\([^)]*\)', '', col_name)
    col_name = re.sub(r'[-\s.]+', '_', col_name)
    col_name = re.sub(r'_+', '_', col_name)
    return col_name.lower().strip('_')

df = pd.read_excel('Soap & Glory concept testing data pull.xlsx', sheet_name='Soap & Glory', header=1)
print("Original columns -> Transformed columns:\n")
for orig, trans in zip(list(df.columns), [to_snake_case(col) for col in df.columns]):
    print(f"{orig:40} -> {trans}")
