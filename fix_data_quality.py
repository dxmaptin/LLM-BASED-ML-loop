"""
Data Quality Fix Script - Re-populate Vision and Verbatim Data for Holdout Concepts

ISSUES FOUND:
1. 3 out of 4 holdout concepts have NO vision data (only "No vision data found")
2. 1 concept (Glow On) has NO verbatim data
3. Raw data EXISTS in source files but wasn't properly matched

ROOT CAUSE:
- Concept ID naming mismatches between:
  * concept_test_wide.csv (e.g., "sgs_glow_on_gradual_tan_lotion")
  * vision_extraction_results.csv (uses image filenames)
  * verbatims (uses different naming)

FIX:
- Re-match all source data to holdout concepts
- Populate missing vision and verbatim files
"""

import pandas as pd
from pathlib import Path
import re

BASE_DIR = Path(".")
HOLDOUT_DIR = BASE_DIR / "project_data" / "witty_optimist_runs" / "holdout_concepts"

# Load source data
vision_df = pd.read_csv("project_data/concept_vision_data/processed_csv/results/vision_extraction_results.csv")
verbatims_df = pd.read_csv("project_data/verbatims_processed/verbatims_combined_long_full.csv")
concepts_df = pd.read_csv("project_data/concept_test_processed/concept_test_wide.csv")

print("="*80)
print("DATA QUALITY FIX - RE-POPULATING VISION AND VERBATIM DATA")
print("="*80)

# Mapping of concept IDs to source data identifiers
CONCEPT_MAPPINGS = {
    "exfoliationg_body_scrub_and_massage_bar": {
        "vision_match": "Exfoliationg Body Scrub and Massage Bar",
        "verbatim_match": "exfoliationg_body_scrub_and_massage_bar"
    },
    "ph_sensitive_skin_body_wash": {
        "vision_match": "pH Sensitive Skin Body Wash",  # May need fuzzy match
        "verbatim_match": "ph_sensitive_skin_body_wash"
    },
    "sgs_glow_on_gradual_tan_lotion": {
        "vision_match": "S&G's 'Glow On' Gradual Tan Lotion",
        "verbatim_match": "sgs_glow_on_gradual_tan_lotion"
    },
    "soap_glory_girls_night_out_refresh_queen": {
        "vision_match": "Refresh Queen",  # Partial match
        "verbatim_match": "soap_glory_girls_night_out_refresh_queen"
    }
}

print("\n=== Auditing Source Data ===\n")

# Check what's available in vision data
print("Vision Data Available:")
print(vision_df[['product_name']].drop_duplicates().to_string(index=False))

print("\n\nVerbatim Data Available:")
verbatim_concepts = verbatims_df['concept_id'].unique() if 'concept_id' in verbatims_df.columns else []
print(f"Unique concepts: {len(verbatim_concepts)}")

print("\n=== Processing Each Holdout Concept ===\n")

for concept_dir in sorted(HOLDOUT_DIR.iterdir()):
    if not concept_dir.is_dir():
        continue

    concept_id = concept_dir.name
    print(f"\n{'='*80}")
    print(f"Processing: {concept_id}")
    print('='*80)

    # Load concept info
    concept_info_file = concept_dir / "concept_info.csv"
    if concept_info_file.exists():
        concept_info = pd.read_csv(concept_info_file)
        concept_name = concept_info.iloc[0]['concept_name']
        print(f"Concept Name: {concept_name}")
    else:
        print("⚠️  No concept_info.csv found")
        continue

    # ============================================================================
    # FIX VISION DATA
    # ============================================================================

    vision_file = concept_dir / "Textual Data Inputs" / "vision_analysis.txt"

    # Try to find vision data
    vision_match = None

    # Strategy 1: Exact product name match
    exact_match = vision_df[vision_df['product_name'].str.lower() == concept_name.lower()]
    if len(exact_match) > 0:
        vision_match = exact_match.iloc[0]
        print(f"✓ Vision: Found exact match")

    # Strategy 2: Partial name match
    if vision_match is None:
        for idx, row in vision_df.iterrows():
            product_name = str(row['product_name']).lower()
            # Check if concept name contains key words from product name
            key_words = [w for w in product_name.split() if len(w) > 3]
            if len(key_words) > 0 and any(word in concept_name.lower() for word in key_words):
                vision_match = row
                print(f"✓ Vision: Found partial match - {row['product_name']}")
                break

    # Strategy 3: Manual mapping
    if vision_match is None and concept_id in CONCEPT_MAPPINGS:
        search_term = CONCEPT_MAPPINGS[concept_id]['vision_match']
        partial_match = vision_df[vision_df['product_name'].str.contains(search_term, case=False, na=False)]
        if len(partial_match) > 0:
            vision_match = partial_match.iloc[0]
            print(f"✓ Vision: Found via mapping - {vision_match['product_name']}")

    # Write vision data
    if vision_match is not None:
        vision_content = f"""VISUAL ANALYSIS: {concept_name}
================================================================================

Product Description:
{vision_match.get('product_description', 'N/A')}

Product Category: {vision_match.get('product_category', 'N/A')}

Key Claims/Benefits:
{vision_match.get('key_claims_benefits', 'N/A')}

Color Scheme: {vision_match.get('color_scheme', 'N/A')}

Imagery Type: {vision_match.get('imagery_type', 'N/A')}

Design Style: {vision_match.get('design_style', 'N/A')}

Target Audience: {vision_match.get('target_audience', 'N/A')}

Additional Details:
{vision_match.get('additional_text', 'N/A')}
"""

        with open(vision_file, 'w', encoding='utf-8') as f:
            f.write(vision_content)
        print(f"  → Updated vision_analysis.txt ({len(vision_content)} chars)")
    else:
        print(f"  ❌ No vision data found - keeping placeholder")

    # ============================================================================
    # FIX VERBATIM DATA
    # ============================================================================

    verbatim_file = concept_dir / "Textual Data Inputs" / "verbatims_summary.txt"

    # Try to find verbatim data
    verbatim_match = None

    if 'concept_id' in verbatims_df.columns:
        # Direct match
        exact_verbatim = verbatims_df[verbatims_df['concept_id'] == concept_id]
        if len(exact_verbatim) > 0:
            verbatim_match = exact_verbatim
            print(f"✓ Verbatim: Found {len(verbatim_match)} responses")

        # Try with underscores removed
        if verbatim_match is None or len(verbatim_match) == 0:
            normalized_id = concept_id.replace('_', '')
            for vid in verbatims_df['concept_id'].unique():
                if vid.replace('_', '') == normalized_id:
                    verbatim_match = verbatims_df[verbatims_df['concept_id'] == vid]
                    print(f"✓ Verbatim: Found via normalization - {len(verbatim_match)} responses")
                    break

    # Write verbatim data
    if verbatim_match is not None and len(verbatim_match) > 0:
        # Separate likes and dislikes
        likes = verbatim_match[verbatim_match['sentiment'] == 'like'] if 'sentiment' in verbatim_match.columns else verbatim_match[verbatim_match['response_type'] == 'like'] if 'response_type' in verbatim_match.columns else verbatim_match[verbatim_match['question_type'].str.contains('like', case=False, na=False)]
        dislikes = verbatim_match[verbatim_match['sentiment'] == 'dislike'] if 'sentiment' in verbatim_match.columns else verbatim_match[verbatim_match['response_type'] == 'dislike'] if 'response_type' in verbatim_match.columns else verbatim_match[verbatim_match['question_type'].str.contains('dislike', case=False, na=False)]

        verbatim_content = f"""VERBATIM FEEDBACK: {concept_name}
================================================================================

LIKES ({len(likes)} responses):
--------------------------------------------------------------------------------
"""

        for idx, row in likes.head(100).iterrows():
            text = row.get('verbatim', row.get('response', row.get('text', '')))
            if pd.notna(text) and text.strip():
                verbatim_content += f"• {text}\n"

        verbatim_content += f"""

DISLIKES ({len(dislikes)} responses):
--------------------------------------------------------------------------------
"""

        for idx, row in dislikes.head(100).iterrows():
            text = row.get('verbatim', row.get('response', row.get('text', '')))
            if pd.notna(text) and text.strip():
                verbatim_content += f"• {text}\n"

        with open(verbatim_file, 'w', encoding='utf-8') as f:
            f.write(verbatim_content)
        print(f"  → Updated verbatims_summary.txt ({len(likes)} likes, {len(dislikes)} dislikes)")
    else:
        print(f"  ❌ No verbatim data found - keeping placeholder")

print("\n" + "="*80)
print("DATA QUALITY FIX COMPLETE!")
print("="*80)
print("\nNext step: Re-run predictions with properly matched data")
print("Command: python run_multi_metric_predictions_v3_meta.py")
