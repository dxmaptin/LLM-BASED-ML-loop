import pandas as pd
import sys

files = [
    "Witty Optimist_S&G Jan'24 Verbatims V2.xlsx",
    "Witty Optimist_S&G FY25 Verbatims V2.xlsx",
    "Witty Optimist_S&G FY26 Verbatims V2.xlsx"
]

output_file = "verbatim_inspection.txt"

with open(output_file, 'w', encoding='utf-8') as out:
    for f in files:
        out.write("\n" + "="*80 + "\n")
        out.write(f"FILE: {f}\n")
        out.write("="*80 + "\n")

        xl = pd.ExcelFile(f)
        out.write(f"\nSheet names: {xl.sheet_names}\n")

        # Read first UK sheet
        uk_sheets = [s for s in xl.sheet_names if 'UK' in s.upper()]
        if uk_sheets:
            sheet_name = uk_sheets[0]
            out.write(f"\nExamining sheet: {sheet_name}\n")

            df = pd.read_excel(xl, sheet_name=sheet_name, nrows=5)
            out.write(f"\nShape: {df.shape}\n")
            out.write(f"\nColumns ({len(df.columns)}):\n")
            for i, col in enumerate(df.columns, 1):
                # Clean column name for display
                col_clean = str(col).encode('ascii', errors='ignore').decode('ascii')
                out.write(f"  {i:2}. {col_clean}\n")

            out.write(f"\nFirst row sample:\n")
            for col in list(df.columns)[:min(8, len(df.columns))]:
                val = str(df[col].iloc[0])[:100] if pd.notna(df[col].iloc[0]) else "NaN"
                col_clean = str(col).encode('ascii', errors='ignore').decode('ascii')
                out.write(f"  {col_clean}: {val}\n")

print(f"Inspection complete. See {output_file}")
