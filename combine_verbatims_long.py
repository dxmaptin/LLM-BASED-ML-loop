"""
Combine all 3 verbatim files into a single long-format training dataset

Rules applied:
1. Reshape to long format (unpivot)
2. Extract Market from sheet name (UK/US)
3. Extract Sentiment from sheet name (Likes/Dislikes/Range)
4. Add Period tag (Jan24/FY25/FY26)
5. Stack all data
6. Light cleanup (trim, dedupe, drop nulls)
7. Standardize concept names
8. Create training format (Market, Sentiment, Concept, Verbatim)
9. Keep Period as metadata column (exclude from training)
"""

import pandas as pd
import numpy as np
import os
import re

# Configuration
BASE_DIR = r"C:\Users\d.zhang\Desktop\Experiments"
OUTPUT_DIR = os.path.join(BASE_DIR, "project_data", "verbatims_processed")

VERBATIM_FILES = {
    'Jan24': "Witty Optimist_S&G Jan'24 Verbatims V2.xlsx",
    'FY25': 'Witty Optimist_S&G FY25 Verbatims V2.xlsx',
    'FY26': 'Witty Optimist_S&G FY26 Verbatims V2.xlsx',
}


def extract_market_from_sheet(sheet_name):
    """Extract market from sheet name"""
    if 'UK' in sheet_name.upper():
        return 'UK'
    elif 'US' in sheet_name.upper():
        return 'US'
    else:
        return 'Unknown'


def extract_sentiment_from_sheet(sheet_name):
    """Extract sentiment from sheet name"""
    sheet_lower = sheet_name.lower()

    if 'like' in sheet_lower and 'dislike' not in sheet_lower:
        return 'Likes'
    elif 'dislike' in sheet_lower:
        return 'Dislikes'
    elif 'range' in sheet_lower:
        return 'Range'
    else:
        return 'Other'


def standardize_concept_name(concept_raw):
    """Standardize concept names"""
    if pd.isna(concept_raw):
        return None

    # Remove everything after colon and parentheses (e.g., ": (LIKES_STD) LIKES")
    concept = re.sub(r'\s*:\s*\(.*?\).*', '', str(concept_raw))

    # Trim whitespace
    concept = concept.strip()

    # Normalize case (Title Case)
    concept = concept.title()

    # Remove extra spaces
    concept = re.sub(r'\s+', ' ', concept)

    return concept


def reshape_file_to_long(file_path, period):
    """
    Reshape a single verbatim file to long format
    Returns: DataFrame with columns [Market, Sentiment, Concept, Verbatim, Period]
    """
    print(f"\n{'='*80}")
    print(f"Processing: {period} - {os.path.basename(file_path)}")
    print('='*80)

    xl = pd.ExcelFile(file_path)
    all_sheets_data = []

    for sheet_name in xl.sheet_names:
        print(f"\n  Sheet: {sheet_name}")

        # Extract metadata from sheet name
        market = extract_market_from_sheet(sheet_name)
        sentiment = extract_sentiment_from_sheet(sheet_name)

        print(f"    - Market: {market}, Sentiment: {sentiment}")

        # Read sheet
        df = pd.read_excel(xl, sheet_name=sheet_name)

        print(f"    - Shape: {df.shape}")

        # Each column is a concept, rows are verbatims
        # Unpivot to long format
        long_data = []

        for concept_col in df.columns:
            # Standardize concept name
            concept_clean = standardize_concept_name(concept_col)

            if concept_clean is None:
                continue

            # Get all verbatims for this concept (all non-null rows)
            verbatims = df[concept_col].dropna()

            for verbatim in verbatims:
                if pd.isna(verbatim) or str(verbatim).strip() == '':
                    continue

                long_data.append({
                    'Market': market,
                    'Sentiment': sentiment,
                    'Concept': concept_clean,
                    'Verbatim': str(verbatim).strip(),
                    'Period': period
                })

        print(f"    - Extracted: {len(long_data)} verbatims")
        all_sheets_data.extend(long_data)

    df_long = pd.DataFrame(all_sheets_data)
    print(f"\n  Total for {period}: {len(df_long)} verbatims")

    return df_long


def combine_all_verbatims():
    """Main function to combine all verbatim files"""

    print("\n" + "="*80)
    print("COMBINING ALL VERBATIMS TO LONG FORMAT")
    print("="*80 + "\n")

    all_data = []

    # Process each file
    for period, filename in VERBATIM_FILES.items():
        file_path = os.path.join(BASE_DIR, filename)

        if not os.path.exists(file_path):
            print(f"WARNING: File not found: {filename}")
            continue

        df_period = reshape_file_to_long(file_path, period)
        all_data.append(df_period)

    # Stack all data
    print(f"\n{'='*80}")
    print("STACKING ALL DATA")
    print('='*80)

    df_combined = pd.concat(all_data, ignore_index=True)

    print(f"\n  Initial combined rows: {len(df_combined)}")
    print(f"  Columns: {list(df_combined.columns)}")

    # Light cleanup
    print(f"\n{'='*80}")
    print("CLEANING UP")
    print('='*80)

    # 1. Trim whitespace
    print("\n[1/5] Trimming whitespace...")
    df_combined['Verbatim'] = df_combined['Verbatim'].str.strip()
    df_combined['Concept'] = df_combined['Concept'].str.strip()

    # 2. Drop empty/NaN verbatims
    print("[2/5] Dropping empty verbatims...")
    initial_count = len(df_combined)
    df_combined = df_combined[df_combined['Verbatim'].notna()]
    df_combined = df_combined[df_combined['Verbatim'] != '']
    dropped = initial_count - len(df_combined)
    print(f"  - Dropped {dropped} empty verbatims")

    # 3. Drop rows with Unknown market
    print("[3/5] Filtering markets...")
    df_combined = df_combined[df_combined['Market'].isin(['UK', 'US'])]
    print(f"  - Kept only UK/US data")

    # 4. Dedupe
    print("[4/5] Deduplicating...")
    initial_count = len(df_combined)
    df_combined = df_combined.drop_duplicates(subset=['Market', 'Sentiment', 'Concept', 'Verbatim'])
    dupes_removed = initial_count - len(df_combined)
    print(f"  - Removed {dupes_removed} duplicate verbatims")

    # 5. Sort
    print("[5/5] Sorting...")
    df_combined = df_combined.sort_values(['Period', 'Market', 'Sentiment', 'Concept']).reset_index(drop=True)

    print(f"\n  Final combined rows: {len(df_combined)}")

    # Statistics
    print(f"\n{'='*80}")
    print("STATISTICS")
    print('='*80)

    print(f"\n[By Period]")
    print(df_combined['Period'].value_counts().sort_index())

    print(f"\n[By Market]")
    print(df_combined['Market'].value_counts())

    print(f"\n[By Sentiment]")
    print(df_combined['Sentiment'].value_counts())

    print(f"\n[By Period × Market]")
    print(pd.crosstab(df_combined['Period'], df_combined['Market']))

    print(f"\n[By Period × Sentiment]")
    print(pd.crosstab(df_combined['Period'], df_combined['Sentiment']))

    print(f"\n[Unique Concepts]")
    print(f"  Total: {df_combined['Concept'].nunique()}")
    print(f"\n  Top 10 concepts by verbatim count:")
    top_concepts = df_combined['Concept'].value_counts().head(10)
    for concept, count in top_concepts.items():
        # Clean concept name for console output
        concept_clean = str(concept).encode('ascii', errors='ignore').decode('ascii')
        print(f"    {concept_clean}: {count}")

    return df_combined


def create_training_format(df_combined):
    """
    Create training-ready format
    Training columns: Market, Sentiment, Concept, Verbatim
    Period kept as metadata (not for training)
    """

    print(f"\n{'='*80}")
    print("CREATING TRAINING FORMAT")
    print('='*80)

    # Full dataset (with Period for analysis)
    df_full = df_combined[['Market', 'Sentiment', 'Concept', 'Verbatim', 'Period']].copy()

    # Training dataset (without Period)
    df_train = df_combined[['Market', 'Sentiment', 'Concept', 'Verbatim']].copy()

    print(f"\n  Full dataset (with Period): {df_full.shape}")
    print(f"  Training dataset (no Period): {df_train.shape}")

    print(f"\n  Training columns: {list(df_train.columns)}")
    print(f"  Metadata column (Period) kept separately for QA/drift checks")

    return df_full, df_train


def save_outputs(df_full, df_train):
    """Save output files"""

    print(f"\n{'='*80}")
    print("SAVING OUTPUTS")
    print('='*80)

    # 1. Full dataset with Period
    full_path = os.path.join(OUTPUT_DIR, "verbatims_combined_long_full.csv")
    df_full.to_csv(full_path, index=False, encoding='utf-8')
    print(f"\n[1/3] Saved: {full_path}")
    print(f"      Shape: {df_full.shape}")
    print(f"      Columns: {list(df_full.columns)}")

    # 2. Training dataset (no Period)
    train_path = os.path.join(OUTPUT_DIR, "verbatims_combined_long_training.csv")
    df_train.to_csv(train_path, index=False, encoding='utf-8')
    print(f"\n[2/3] Saved: {train_path}")
    print(f"      Shape: {df_train.shape}")
    print(f"      Columns: {list(df_train.columns)}")
    print(f"      Ready for model training!")

    # 3. Summary stats
    summary_path = os.path.join(OUTPUT_DIR, "verbatims_combined_summary.txt")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("COMBINED VERBATIMS - SUMMARY\n")
        f.write("="*80 + "\n\n")

        f.write("DATASET SIZES\n")
        f.write("-"*80 + "\n")
        f.write(f"Full dataset (with Period): {df_full.shape[0]:,} rows\n")
        f.write(f"Training dataset (no Period): {df_train.shape[0]:,} rows\n\n")

        f.write("PERIOD DISTRIBUTION\n")
        f.write("-"*80 + "\n")
        for period, count in df_full['Period'].value_counts().sort_index().items():
            f.write(f"  {period}: {count:,} verbatims\n")

        f.write("\nMARKET DISTRIBUTION\n")
        f.write("-"*80 + "\n")
        for market, count in df_full['Market'].value_counts().items():
            f.write(f"  {market}: {count:,} verbatims\n")

        f.write("\nSENTIMENT DISTRIBUTION\n")
        f.write("-"*80 + "\n")
        for sentiment, count in df_full['Sentiment'].value_counts().items():
            f.write(f"  {sentiment}: {count:,} verbatims\n")

        f.write(f"\nUNIQUE CONCEPTS: {df_full['Concept'].nunique()}\n")

        f.write("\nTOP 10 CONCEPTS\n")
        f.write("-"*80 + "\n")
        top_concepts = df_full['Concept'].value_counts().head(10)
        for i, (concept, count) in enumerate(top_concepts.items(), 1):
            f.write(f"  {i:2}. {concept}: {count} verbatims\n")

        f.write("\n" + "="*80 + "\n")
        f.write("TRAINING FORMAT\n")
        f.write("="*80 + "\n\n")
        f.write("Training columns (exclude Period):\n")
        f.write("  1. Market (UK/US)\n")
        f.write("  2. Sentiment (Likes/Dislikes/Range)\n")
        f.write("  3. Concept (standardized name)\n")
        f.write("  4. Verbatim (cleaned text)\n\n")
        f.write("Period kept as metadata for:\n")
        f.write("  - QA checks\n")
        f.write("  - Temporal drift analysis\n")
        f.write("  - Train/test splits by wave\n")

    print(f"\n[3/3] Saved: {summary_path}")

    print("\n" + "="*80)
    print("COMBINING COMPLETE!")
    print("="*80)
    print(f"\nOutput files:")
    print(f"  1. verbatims_combined_long_full.csv - Full dataset with Period")
    print(f"  2. verbatims_combined_long_training.csv - Training format (no Period)")
    print(f"  3. verbatims_combined_summary.txt - Statistics summary")
    print(f"\nLocation: {OUTPUT_DIR}")
    print("\n" + "="*80 + "\n")


def main():
    """Main execution"""

    # Combine all verbatims
    df_combined = combine_all_verbatims()

    # Create training format
    df_full, df_train = create_training_format(df_combined)

    # Save outputs
    save_outputs(df_full, df_train)


if __name__ == "__main__":
    main()
