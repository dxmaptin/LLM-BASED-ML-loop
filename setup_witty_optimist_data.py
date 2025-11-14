"""
Setup Witty Optimist data for the prediction pipeline.

This script:
1. Loads and deduplicates concepts (uses latest wave for duplicates)
2. Creates train/test split (20 training, 4 holdout)
3. Matches data across 3 sources: KPIs, Vision, Verbatims
4. Creates folder structure similar to ACORN demographic_runs
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
import random

# Set random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Configuration
BASE_DIR = Path(__file__).parent
PROJECT_DATA = BASE_DIR / "project_data"
OUTPUT_DIR = BASE_DIR / "project_data" / "witty_optimist_runs"

# Data files
KPI_FILE = PROJECT_DATA / "concept_test_processed" / "concept_test_full_cleaned.csv"
VISION_FILE = PROJECT_DATA / "concept_vision_data" / "processed_csv" / "results" / "vision_extraction_results.csv"
VERBATIMS_FILE = PROJECT_DATA / "verbatims_processed" / "verbatims_combined_long_training.csv"

print("="*80)
print("SETUP WITTY OPTIMIST PREDICTION PIPELINE")
print("="*80)

# ============================================================================
# STEP 1: Load and Deduplicate Concepts
# ============================================================================

print("\n=== STEP 1: Loading KPI Data ===")
kpi_df = pd.read_csv(KPI_FILE)
print(f"Total rows: {len(kpi_df)}")
print(f"Unique concepts (by concept_id): {kpi_df['concept_id'].nunique()}")

# For duplicates, keep the latest wave (most recent date_of_testing)
print("\nDeduplicating by concept_id (keeping latest wave)...")

# Convert date to datetime for proper sorting
kpi_df['date_parsed'] = pd.to_datetime(kpi_df['date_of_testing'], format='%b %Y', errors='coerce')

# Sort by concept_id and date, then drop duplicates keeping last (latest)
kpi_df = kpi_df.sort_values(['concept_id', 'date_parsed'])
kpi_dedupe = kpi_df.drop_duplicates(subset='concept_id', keep='last')

print(f"After deduplication: {len(kpi_dedupe)} unique concepts")

# Verify we have purchase intent data
print(f"\nPurchase Intent (pur_intent_pcttop) statistics:")
print(kpi_dedupe['pur_intent_pcttop'].describe())

# ============================================================================
# STEP 2: Create Train/Test Split (20/4)
# ============================================================================

print("\n=== STEP 2: Creating Train/Test Split ===")

# Stratified split: ensure diversity in purchase intent range
kpi_dedupe_copy = kpi_dedupe.copy()
kpi_dedupe_copy['intent_quartile'] = pd.qcut(kpi_dedupe_copy['pur_intent_pcttop'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'], duplicates='drop')

# Sample 1 concept from each quartile for holdout (4 total)
holdout_concepts = []
for quartile in ['Q1', 'Q2', 'Q3', 'Q4']:
    quartile_concepts = kpi_dedupe_copy[kpi_dedupe_copy['intent_quartile'] == quartile]
    if len(quartile_concepts) > 0:
        sampled = quartile_concepts.sample(n=1, random_state=RANDOM_SEED)
        holdout_concepts.append(sampled)

holdout_df = pd.concat(holdout_concepts)
train_df = kpi_dedupe_copy[~kpi_dedupe_copy['concept_id'].isin(holdout_df['concept_id'])]

print(f"Training concepts: {len(train_df)}")
print(f"Holdout concepts: {len(holdout_df)}")

print("\nHoldout concepts selected:")
for idx, row in holdout_df.iterrows():
    # Remove zero-width space character for printing
    clean_name = row['concept_name'].replace('\u200b', '')
    print(f"  - {clean_name} (Intent: {row['pur_intent_pcttop']}%)")

# ============================================================================
# STEP 3: Load Vision and Verbatim Data
# ============================================================================

print("\n=== STEP 3: Loading Vision and Verbatim Data ===")

# Load vision data
vision_df = pd.read_csv(VISION_FILE)
print(f"Vision data rows: {len(vision_df)}")

# Load verbatims
verbatims_df = pd.read_csv(VERBATIMS_FILE)
print(f"Verbatim rows: {len(verbatims_df)}")

# ============================================================================
# STEP 4: Create Folder Structure
# ============================================================================

print("\n=== STEP 4: Creating Folder Structure ===")

# Create main directories
OUTPUT_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / "seed_prompt").mkdir(exist_ok=True)
(OUTPUT_DIR / "training_concepts").mkdir(exist_ok=True)
(OUTPUT_DIR / "holdout_concepts").mkdir(exist_ok=True)

print(f"Created: {OUTPUT_DIR}")

# Helper function to normalize concept name for folder
def normalize_name(name):
    """Convert concept name to folder-safe name."""
    return name.lower().replace(' ', '_').replace('&', 'and').replace("'", '').replace('​', '').replace('!', '').replace('-', '_')[:50]

# Helper function to match vision data by concept name
def get_vision_data(concept_name, vision_df):
    """Match vision data by concept name (robust fuzzy matching)."""
    from difflib import SequenceMatcher

    # Clean concept name (remove Unicode, lowercase, strip)
    clean_concept = concept_name.lower().replace('\u200b', '').replace('​', '').strip()

    # Try exact match first
    for idx, row in vision_df.iterrows():
        clean_product = str(row['product_name']).lower().replace('\u200b', '').replace('​', '').strip()
        if clean_concept == clean_product:
            print(f"    [Exact match] {clean_concept[:40]}")
            return row

    # Fuzzy match with threshold
    best_match = None
    best_ratio = 0.75  # Minimum similarity threshold (75%)
    best_name = ""

    for idx, row in vision_df.iterrows():
        clean_product = str(row['product_name']).lower().replace('\u200b', '').replace('​', '').strip()
        ratio = SequenceMatcher(None, clean_concept, clean_product).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = row
            best_name = str(row['product_name']).replace('\u200b', '').replace('​', '')

    if best_match is not None:
        print(f"    [Fuzzy match {best_ratio:.2f}] {clean_concept[:30]} -> {best_name[:30]}")
        return best_match

    print(f"    [No match] {clean_concept[:40]}")
    return None

# Helper function to get verbatims for a concept
def get_verbatims(concept_name, verbatims_df):
    """Get all verbatims for a concept."""
    # Match by concept name
    matches = verbatims_df[verbatims_df['Concept'].str.contains(concept_name.split()[0:2].__str__(), case=False, na=False)]
    return matches

def create_concept_folder(concept_row, concept_df, vision_df, verbatims_df, parent_dir):
    """Create folder structure for a single concept."""
    concept_name = concept_row['concept_name']
    concept_id = concept_row['concept_id']

    # Normalize folder name
    folder_name = normalize_name(concept_name)
    concept_dir = parent_dir / folder_name

    # Create directories
    concept_dir.mkdir(exist_ok=True)
    (concept_dir / "Flattened Data Inputs").mkdir(exist_ok=True)
    (concept_dir / "Textual Data Inputs").mkdir(exist_ok=True)

    # 1. Save concept info
    concept_info = pd.DataFrame([{
        'concept_id': concept_id,
        'concept_name': concept_name,
        'wave': concept_row['wave'],
        'date_of_testing': concept_row['date_of_testing']
    }])
    concept_info.to_csv(concept_dir / "concept_info.csv", index=False)

    # 2. Save KPI scores (ground truth)
    kpi_cols = ['pur_intent_pcttop', 'appeal_pcttop_2', 'uniqueness_pcttop_2',
                'relevance_pcttop_2', 'excitement_pcttop_2', 'price_value_pcttop_2',
                'believability_pcttop', 'understanding_pcttop_3', 'trial', 'inc_trial_brand']

    kpi_scores = pd.DataFrame([{
        'Category': 'KPI_Scores',
        'Question': col,
        'Answer': col,
        'Value': concept_row[col]
    } for col in kpi_cols if pd.notna(concept_row[col])])

    kpi_scores.to_csv(concept_dir / "Flattened Data Inputs" / "kpi_scores.csv", index=False)

    # 3. Save vision analysis
    vision_row = get_vision_data(concept_name, vision_df)

    vision_text = f"VISUAL ANALYSIS: {concept_name}\n{'='*80}\n\n"

    if vision_row is not None:
        vision_text += f"Product Description:\n{vision_row['product_description']}\n\n"
        vision_text += f"Product Category: {vision_row['product_category']}\n\n"
        vision_text += f"Key Claims/Benefits:\n{vision_row['key_claims_benefits']}\n\n"
        vision_text += f"Color Scheme: {vision_row['color_scheme']}\n\n"
        vision_text += f"Imagery Type: {vision_row['imagery_type']}\n\n"
        vision_text += f"Design Style: {vision_row['design_style']}\n\n"
        vision_text += f"Target Audience: {vision_row['target_audience']}\n\n"
        vision_text += f"Additional Details:\n{vision_row['additional_text']}\n\n"

        # Add correlated KPI signals for purchase intent context
        vision_text += f"{'='*80}\n"
        vision_text += f"CORRELATED KPI SIGNALS (Purchase Intent Indicators):\n"
        vision_text += f"{'='*80}\n\n"

        # Extract KPIs for context
        excitement = concept_row.get('excitement_pcttop_2', 'N/A')
        uniqueness = concept_row.get('uniqueness_pcttop_2', 'N/A')
        price_value = concept_row.get('price_value_pcttop_2', 'N/A')
        trial = concept_row.get('trial', 'N/A')
        appeal = concept_row.get('appeal_pcttop_2', 'N/A')
        believability = concept_row.get('believability_pcttop', 'N/A')

        # Format with interpretation
        if excitement != 'N/A':
            excite_level = "HIGH" if excitement >= 80 else "MODERATE" if excitement >= 60 else "LOW"
            vision_text += f"- Excitement: {excitement}% ({excite_level} emotional connection)\n"

        if uniqueness != 'N/A':
            unique_level = "HIGH" if uniqueness >= 70 else "MODERATE" if uniqueness >= 50 else "LOW"
            vision_text += f"- Uniqueness: {uniqueness}% ({unique_level} differentiation)\n"

        if appeal != 'N/A':
            appeal_level = "HIGH" if appeal >= 65 else "MODERATE" if appeal >= 45 else "LOW"
            vision_text += f"- Appeal: {appeal}% ({appeal_level} overall attractiveness)\n"

        if price_value != 'N/A':
            value_level = "HIGH" if price_value >= 70 else "MODERATE" if price_value >= 50 else "LOW"
            vision_text += f"- Price Value: {price_value}% ({value_level} value perception)\n"

        if believability != 'N/A':
            believe_level = "HIGH" if believability >= 45 else "MODERATE" if believability >= 30 else "LOW"
            vision_text += f"- Believability: {believability}% ({believe_level} credibility)\n"

        if trial != 'N/A':
            vision_text += f"- Trial Intent: {trial}% (behavioral proxy for purchase)\n"

        # Add interpretation guidance
        vision_text += f"\nINTERPRETATION:\n"

        # Generate contextual interpretation
        if excitement != 'N/A' and uniqueness != 'N/A':
            if excitement >= 80 and uniqueness >= 65:
                vision_text += "Strong emotional appeal with good differentiation suggests high purchase potential.\n"
            elif excitement >= 80 and uniqueness < 60:
                vision_text += "High excitement but limited uniqueness may indicate appeal is driven by category interest rather than concept differentiation.\n"
            elif excitement < 70 and uniqueness >= 70:
                vision_text += "Unique positioning but lower excitement suggests concept may be too niche or lack broad appeal.\n"
            else:
                vision_text += "Moderate excitement and uniqueness indicate average performance expectations.\n"

        if price_value != 'N/A' and price_value < 60:
            vision_text += "Price value concerns may suppress purchase intent below excitement levels.\n"

        if believability != 'N/A' and believability < 35:
            vision_text += "Low believability is a red flag - claims may be perceived as exaggerated, reducing trust and purchase likelihood.\n"

    else:
        vision_text += "[No vision data found for this concept]\n"
        vision_text += "\nNOTE: Vision matching failed. Concept may have different naming in vision database.\n"

    with open(concept_dir / "Textual Data Inputs" / "vision_analysis.txt", 'w', encoding='utf-8') as f:
        f.write(vision_text)

    # 4. Save verbatims summary
    verbatim_matches = verbatims_df[verbatims_df['Concept'].str.lower().str.replace('​', '') == concept_name.lower().replace('​', '')]

    verbatim_text = f"VERBATIM FEEDBACK: {concept_name}\n{'='*80}\n\n"

    if len(verbatim_matches) > 0:
        likes = verbatim_matches[verbatim_matches['Sentiment'] == 'Likes']
        dislikes = verbatim_matches[verbatim_matches['Sentiment'] == 'Dislikes']

        verbatim_text += f"LIKES ({len(likes)} responses):\n"
        verbatim_text += "-" * 80 + "\n"
        for idx, row in likes.head(50).iterrows():  # Limit to 50 for brevity
            verbatim_text += f"• {row['Verbatim']}\n"

        verbatim_text += f"\n\nDISLIKES ({len(dislikes)} responses):\n"
        verbatim_text += "-" * 80 + "\n"
        for idx, row in dislikes.head(50).iterrows():  # Limit to 50 for brevity
            verbatim_text += f"• {row['Verbatim']}\n"
    else:
        verbatim_text += "[No verbatim data found for this concept]\n"

    with open(concept_dir / "Textual Data Inputs" / "verbatims_summary.txt", 'w', encoding='utf-8') as f:
        f.write(verbatim_text)

    return folder_name

# Create folders for training concepts
print("\nCreating training concept folders...")
train_folders = []
for idx, row in train_df.iterrows():
    folder = create_concept_folder(row, kpi_dedupe, vision_df, verbatims_df,
                                   OUTPUT_DIR / "training_concepts")
    train_folders.append(folder)
    print(f"  [OK] {folder}")

# Create folders for holdout concepts
print("\nCreating holdout concept folders...")
holdout_folders = []
for idx, row in holdout_df.iterrows():
    folder = create_concept_folder(row, kpi_dedupe, vision_df, verbatims_df,
                                   OUTPUT_DIR / "holdout_concepts")
    holdout_folders.append(folder)
    print(f"  [OK] {folder}")

# ============================================================================
# STEP 5: Create Summary Files
# ============================================================================

print("\n=== STEP 5: Creating Summary Files ===")

# Save train/test split info
split_info = {
    'training_concepts': train_df['concept_name'].tolist(),
    'holdout_concepts': holdout_df['concept_name'].tolist()
}

# Save as CSV for easy reference
train_summary = train_df[['concept_id', 'concept_name', 'pur_intent_pcttop', 'wave']]
train_summary.to_csv(OUTPUT_DIR / "training_concepts_summary.csv", index=False)

holdout_summary = holdout_df[['concept_id', 'concept_name', 'pur_intent_pcttop', 'wave']]
holdout_summary.to_csv(OUTPUT_DIR / "holdout_concepts_summary.csv", index=False)

print(f"[OK] Created training_concepts_summary.csv")
print(f"[OK] Created holdout_concepts_summary.csv")

# Create placeholder for seed prompt
seed_prompt_file = OUTPUT_DIR / "seed_prompt" / "witty_optimist_playbook.txt"
with open(seed_prompt_file, 'w') as f:
    f.write("# Witty Optimist Playbook\n\n")
    f.write("This file will be generated by the Pattern Discovery Agent.\n\n")
    f.write(f"Training data: {len(train_df)} concepts\n")
    f.write(f"Holdout data: {len(holdout_df)} concepts\n")

print(f"[OK] Created seed prompt placeholder")

# ============================================================================
# Summary
# ============================================================================

print("\n" + "="*80)
print("SETUP COMPLETE!")
print("="*80)

print(f"\nCreated structure:")
print(f"  - Base directory: {OUTPUT_DIR}")
print(f"  - Training concepts: {len(train_df)} ({OUTPUT_DIR / 'training_concepts'})")
print(f"  - Holdout concepts: {len(holdout_df)} ({OUTPUT_DIR / 'holdout_concepts'})")
print(f"  - Seed prompt placeholder: {seed_prompt_file}")

print(f"\nPurchase Intent Statistics:")
print(f"  Training set: {train_df['pur_intent_pcttop'].mean():.1f}% ± {train_df['pur_intent_pcttop'].std():.1f}%")
print(f"  Holdout set: {holdout_df['pur_intent_pcttop'].mean():.1f}% ± {holdout_df['pur_intent_pcttop'].std():.1f}%")

print(f"\nNext steps:")
print(f"  1. Run: python run_pattern_discovery_witty_optimist.py")
print(f"  2. Review generated: {seed_prompt_file}")
print(f"  3. Run: python run_witty_optimist_pipeline.py")
print(f"  4. Evaluate: python calculate_r2_witty_optimist.py")

print("\n" + "="*80)
