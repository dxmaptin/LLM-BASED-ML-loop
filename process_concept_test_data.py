"""
Process Soap & Glory concept testing data pull
Creates clean, structured datasets ready for analysis and joins with vision extraction data

Processing steps:
1. Read with header=1
2. Filter to UK market only
3. Standardise column names to snake_case
4. Convert percentage columns to numeric
5. Create stable keys (concept_id, wave)
6. Extract targets and features
7. Produce wide and long formats
8. Run QA checks
"""

import pandas as pd
import numpy as np
import os
import re
from pathlib import Path

# Configuration
BASE_DIR = r"C:\Users\d.zhang\Desktop\Experiments"
INPUT_FILE = os.path.join(BASE_DIR, "Soap & Glory concept testing data pull.xlsx")
OUTPUT_DIR = os.path.join(BASE_DIR, "project_data", "concept_test_processed")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)


def slugify(text):
    """Convert text to slug format (lowercase with underscores)"""
    if pd.isna(text):
        return None
    # Convert to string and lowercase
    text = str(text).lower().strip()
    # Replace spaces and special characters with underscores
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text


def to_snake_case(col_name):
    """Convert column name to snake_case"""
    if pd.isna(col_name):
        return col_name
    # Remove special characters and convert to snake_case
    col_name = str(col_name).strip()
    # Replace % with pct and keep parentheses content
    col_name = col_name.replace('%', 'pct')
    # Keep parentheses content but remove the parentheses themselves
    col_name = re.sub(r'[()]', ' ', col_name)
    # Replace spaces, dots, and dashes with underscores
    col_name = re.sub(r'[-\s.]+', '_', col_name)
    # Remove consecutive underscores
    col_name = re.sub(r'_+', '_', col_name)
    # Convert to lowercase
    col_name = col_name.lower().strip('_')
    return col_name


def extract_numeric_from_percent(value):
    """Extract numeric value from percentage string"""
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float)):
        return float(value)
    # Remove % sign and convert to float
    if isinstance(value, str):
        value = value.strip().replace('%', '').strip()
        try:
            return float(value)
        except ValueError:
            return np.nan
    return np.nan


def process_concept_data():
    """Main processing function"""

    print("\n" + "="*80)
    print("PROCESSING CONCEPT TEST DATA")
    print("="*80 + "\n")

    # Step 1: Read the data with header=1
    print("[1/8] Reading Excel file with header=1...")
    df = pd.read_excel(INPUT_FILE, sheet_name='Soap & Glory', header=1)
    print(f"  - Initial shape: {df.shape}")
    print(f"  - Columns: {len(df.columns)}")

    # Step 2: Drop all-NaN columns
    print("\n[2/8] Dropping all-NaN columns...")
    initial_cols = df.shape[1]
    df = df.dropna(axis=1, how='all')
    dropped_cols = initial_cols - df.shape[1]
    print(f"  - Dropped {dropped_cols} all-NaN columns")
    print(f"  - Remaining columns: {df.shape[1]}")

    # Step 3: Filter to UK market
    print("\n[3/8] Filtering to UK market...")
    print(f"  - Rows before filter: {len(df)}")
    print(f"  - Market distribution: {df['Market'].value_counts().to_dict()}")

    # Case-insensitive trim filter
    df['Market'] = df['Market'].str.strip()
    df_uk = df[df['Market'].str.upper() == 'UK'].copy()

    print(f"  - Rows after UK filter: {len(df_uk)}")
    print(f"  - Rows filtered out: {len(df) - len(df_uk)}")

    # Step 4: Standardise column names
    print("\n[4/8] Standardising column names to snake_case...")
    original_columns = df_uk.columns.tolist()
    df_uk.columns = [to_snake_case(col) for col in df_uk.columns]

    # Show column mapping
    print("  - Column name mapping (first 10):")
    for orig, new in list(zip(original_columns, df_uk.columns))[:10]:
        if orig != new:
            print(f"    {orig} -> {new}")

    # Step 5: Select and rename key columns
    print("\n[5/8] Selecting and renaming key columns...")

    # Map to expected column names (after to_snake_case transformation)
    # Note: "Pur. Intent (%Top 2)" becomes "pur_intent_pcttop_2"
    column_mapping = {
        'concept_name': 'concept_name',
        'project': 'wave',
        'brand': 'brand',
        'franchise_name': 'franchise_name',
        'category': 'category',
        'date_of_testing': 'date_of_testing',
        'market': 'market',
        # Target column (will be renamed)
        'pur_intent_pcttop_2': 'target_top2box_intent',
        'pur_intent_pcttop': 'pur_intent_pcttop',  # Fallback
        # Feature columns (KPIs) - keep as-is
        'appeal_pcttop_2': 'appeal_pcttop_2',
        'uniqueness_pcttop_2': 'uniqueness_pcttop_2',
        'relevance_pcttop_2': 'relevance_pcttop_2',
        'excitement_pcttop_2': 'excitement_pcttop_2',
        'price_value_pcttop_2': 'price_value_pcttop_2',
        'believability_pcttop': 'believability_pcttop',
        'understanding_pcttop_3': 'understanding_pcttop_3',
        'star_rating': 'star_rating',
        'trial': 'trial',
        'inc_trial_brand': 'inc_trial_brand',
        'priced_or_unpriced': 'is_priced',
    }

    # Select columns that exist
    available_columns = {}
    for old_col, new_col in column_mapping.items():
        if old_col in df_uk.columns:
            available_columns[old_col] = new_col
        else:
            print(f"  - Warning: Column '{old_col}' not found")

    df_clean = df_uk[list(available_columns.keys())].copy()
    df_clean.rename(columns=available_columns, inplace=True)

    print(f"  - Selected {len(df_clean.columns)} columns")
    print(f"  - Columns: {list(df_clean.columns)}")

    # Step 6: Create stable keys
    print("\n[6/8] Creating stable keys (concept_id, wave)...")

    # concept_id = slug(concept_name)
    df_clean['concept_id'] = df_clean['concept_name'].apply(slugify)

    # wave = slug(project), fallback to date_of_testing
    if 'wave' in df_clean.columns:
        df_clean['wave_original'] = df_clean['wave']
        df_clean['wave'] = df_clean['wave'].apply(slugify)

        # Fill missing wave with date
        if 'date_of_testing' in df_clean.columns:
            missing_wave = df_clean['wave'].isna()
            df_clean.loc[missing_wave, 'wave'] = df_clean.loc[missing_wave, 'date_of_testing'].apply(
                lambda x: slugify(str(x)) if pd.notna(x) else None
            )

    print(f"  - Created concept_id for {df_clean['concept_id'].notna().sum()} concepts")
    print(f"  - Created wave for {df_clean['wave'].notna().sum()} concepts")
    print(f"  - Unique concept_ids: {df_clean['concept_id'].nunique()}")
    print(f"  - Unique waves: {df_clean['wave'].nunique()}")

    # Step 7: Process target column
    print("\n[7/8] Processing target and converting percentages to numeric...")

    # Determine target column (prefer pur_intent_pcttop_2, fallback to pur_intent_pcttop)
    if 'target_top2box_intent' in df_clean.columns and df_clean['target_top2box_intent'].notna().sum() > 0:
        print("  - Using 'target_top2box_intent' (pur_intent_pcttop_2) as main target")
    elif 'pur_intent_pcttop' in df_clean.columns:
        print("  - Falling back to 'pur_intent_pcttop' as target")
        df_clean['target_top2box_intent'] = df_clean['pur_intent_pcttop']
    else:
        print("  - WARNING: No target column found!")

    # Convert percentage columns to numeric
    percent_columns = [col for col in df_clean.columns if 'pct' in col or col in ['star_rating', 'trial', 'inc_trial_brand']]

    for col in percent_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(extract_numeric_from_percent)

    # Convert is_priced to boolean
    if 'is_priced' in df_clean.columns:
        df_clean['is_priced'] = df_clean['is_priced'].str.lower().isin(['priced', 'yes', 'y', '1', 'true'])

    print(f"  - Converted {len(percent_columns)} percentage/numeric columns")

    # Step 8: Create wide format (concept-level)
    print("\n[8/8] Creating output formats...")

    # Reorder columns: keys first, then metadata, then KPIs
    key_cols = ['wave', 'concept_id', 'concept_name']
    meta_cols = ['brand', 'franchise_name', 'category', 'is_priced']
    meta_cols = [c for c in meta_cols if c in df_clean.columns]

    kpi_cols = [
        'target_top2box_intent',
        'appeal_pcttop_2',
        'uniqueness_pcttop_2',
        'relevance_pcttop_2',
        'excitement_pcttop_2',
        'price_value_pcttop_2',
        'believability_pcttop',
        'understanding_pcttop_3',
        'star_rating',
        'trial',
        'inc_trial_brand',
    ]
    kpi_cols = [c for c in kpi_cols if c in df_clean.columns]

    # Wide format
    wide_cols = key_cols + meta_cols + kpi_cols
    df_wide = df_clean[wide_cols].copy()

    print(f"  - Wide format shape: {df_wide.shape}")

    # Long/tidy format
    id_vars = key_cols + meta_cols
    value_vars = kpi_cols

    df_long = df_wide.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='metric',
        value_name='value'
    )

    # Remove rows with missing values
    df_long = df_long.dropna(subset=['value'])

    print(f"  - Long/tidy format shape: {df_long.shape}")

    return df_clean, df_wide, df_long


def run_qa_checks(df_wide, df_long):
    """Run quality assurance checks"""

    print("\n" + "="*80)
    print("QA CHECKS")
    print("="*80 + "\n")

    qa_results = {}

    # Check 1: Row counts
    print("[CHECK 1] Row counts")
    print(f"  - Wide format rows: {len(df_wide)}")
    print(f"  - Long format rows: {len(df_long)}")
    qa_results['wide_rows'] = len(df_wide)
    qa_results['long_rows'] = len(df_long)

    # Check 2: Percentage columns numeric with realistic ranges
    print("\n[CHECK 2] Numeric percentage columns in realistic ranges (0-100)")
    percent_cols = [col for col in df_wide.columns if 'pct' in col or col in ['star_rating', 'trial', 'inc_trial_brand']]

    issues = []
    for col in percent_cols:
        if col in df_wide.columns:
            non_null = df_wide[col].dropna()
            if len(non_null) > 0:
                min_val = non_null.min()
                max_val = non_null.max()
                out_of_range = ((non_null < 0) | (non_null > 100)).sum()

                status = "OK" if out_of_range == 0 and min_val >= 0 and max_val <= 100 else "WARNING"
                print(f"  - {col}: min={min_val:.1f}, max={max_val:.1f}, out_of_range={out_of_range} [{status}]")

                if out_of_range > 0:
                    issues.append(f"{col} has {out_of_range} values out of range")

    qa_results['percent_range_issues'] = issues

    # Check 3: Unique (wave, concept_id) pairs
    print("\n[CHECK 3] Unique (wave, concept_id) pairs")
    unique_pairs = df_wide.groupby(['wave', 'concept_id']).size()
    duplicates = unique_pairs[unique_pairs > 1]

    print(f"  - Total (wave, concept_id) pairs: {len(unique_pairs)}")
    print(f"  - Duplicate pairs: {len(duplicates)}")

    if len(duplicates) > 0:
        print("  - WARNING: Found duplicate (wave, concept_id) pairs:")
        for (wave, concept_id), count in duplicates.items():
            print(f"    ({wave}, {concept_id}): {count} occurrences")
    else:
        print("  - OK: All (wave, concept_id) pairs are unique")

    qa_results['duplicate_pairs'] = len(duplicates)

    # Check 4: Concepts per wave
    print("\n[CHECK 4] Concepts per wave")
    concepts_per_wave = df_wide.groupby('wave')['concept_id'].nunique()
    print(f"  - Number of waves: {len(concepts_per_wave)}")
    for wave, count in concepts_per_wave.items():
        print(f"    {wave}: {count} concepts")

    qa_results['waves'] = len(concepts_per_wave)
    qa_results['concepts_per_wave'] = concepts_per_wave.to_dict()

    # Check 5: Missing data summary
    print("\n[CHECK 5] Missing data summary")
    missing_summary = df_wide.isnull().sum()
    missing_pct = (missing_summary / len(df_wide) * 100).round(1)

    print(f"  - Columns with missing data:")
    for col, count in missing_summary[missing_summary > 0].items():
        print(f"    {col}: {count} ({missing_pct[col]}%)")

    # Check 6: Target column availability
    print("\n[CHECK 6] Target column (target_top2box_intent)")
    if 'target_top2box_intent' in df_wide.columns:
        non_null_target = df_wide['target_top2box_intent'].notna().sum()
        pct_available = (non_null_target / len(df_wide) * 100)
        print(f"  - Available: {non_null_target}/{len(df_wide)} ({pct_available:.1f}%)")
        print(f"  - Mean: {df_wide['target_top2box_intent'].mean():.2f}")
        print(f"  - Std: {df_wide['target_top2box_intent'].std():.2f}")
    else:
        print("  - WARNING: Target column not found!")

    return qa_results


def save_outputs(df_clean, df_wide, df_long, qa_results):
    """Save all outputs"""

    print("\n" + "="*80)
    print("SAVING OUTPUTS")
    print("="*80 + "\n")

    # Save wide format
    wide_path = os.path.join(OUTPUT_DIR, "concept_test_wide.csv")
    df_wide.to_csv(wide_path, index=False)
    print(f"[1/4] Saved wide format: {wide_path}")
    print(f"      Shape: {df_wide.shape}")

    # Save long format
    long_path = os.path.join(OUTPUT_DIR, "concept_test_long.csv")
    df_long.to_csv(long_path, index=False)
    print(f"\n[2/4] Saved long/tidy format: {long_path}")
    print(f"      Shape: {df_long.shape}")

    # Save full cleaned data (with all original columns)
    full_path = os.path.join(OUTPUT_DIR, "concept_test_full_cleaned.csv")
    df_clean.to_csv(full_path, index=False)
    print(f"\n[3/4] Saved full cleaned data: {full_path}")
    print(f"      Shape: {df_clean.shape}")

    # Save QA report
    qa_path = os.path.join(OUTPUT_DIR, "QA_REPORT.txt")
    with open(qa_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write("CONCEPT TEST DATA - QA REPORT\n")
        f.write("="*80 + "\n\n")

        f.write("SUMMARY\n")
        f.write("-"*80 + "\n")
        f.write(f"Wide format rows: {qa_results['wide_rows']}\n")
        f.write(f"Long format rows: {qa_results['long_rows']}\n")
        f.write(f"Number of waves: {qa_results['waves']}\n")
        f.write(f"Duplicate (wave, concept_id) pairs: {qa_results['duplicate_pairs']}\n\n")

        f.write("CONCEPTS PER WAVE\n")
        f.write("-"*80 + "\n")
        for wave, count in qa_results['concepts_per_wave'].items():
            f.write(f"  {wave}: {count} concepts\n")

        if qa_results['percent_range_issues']:
            f.write("\nPERCENTAGE RANGE ISSUES\n")
            f.write("-"*80 + "\n")
            for issue in qa_results['percent_range_issues']:
                f.write(f"  {issue}\n")
        else:
            f.write("\nAll percentage columns in valid range (0-100)\n")

    print(f"\n[4/4] Saved QA report: {qa_path}")

    print("\n" + "="*80)
    print("PROCESSING COMPLETE!")
    print("="*80)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"\nFiles created:")
    print(f"  1. concept_test_wide.csv - One row per concept with all KPIs")
    print(f"  2. concept_test_long.csv - Tidy format for easy joins/plots")
    print(f"  3. concept_test_full_cleaned.csv - Full cleaned dataset")
    print(f"  4. QA_REPORT.txt - Quality assurance summary")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    # Process the data
    df_clean, df_wide, df_long = process_concept_data()

    # Run QA checks
    qa_results = run_qa_checks(df_wide, df_long)

    # Save outputs
    save_outputs(df_clean, df_wide, df_long, qa_results)
