"""
Fix Verbatim Data - Properly match and populate verbatim files for holdout concepts
"""

import pandas as pd
from pathlib import Path

HOLDOUT_DIR = Path("project_data/witty_optimist_runs/holdout_concepts")

# Load verbatims
verbatims_df = pd.read_csv('project_data/verbatims_processed/verbatims_combined_long_full.csv')

print("="*80)
print("FIXING VERBATIM DATA FOR HOLDOUT CONCEPTS")
print("="*80)

# Mapping of folder names to verbatim concept names
VERBATIM_MAPPINGS = {
    "exfoliationg_body_scrub_and_massage_bar": "Exfoliationg Body Scrub And Massage Bar",
    "ph_sensitive_skin_body_wash": "pH Sensitive Skin Body Wash",
    "sandgs_glow_on_gradual_tan_lotion": "S&G's 'Glow On' Gradual Tan Lotion",  # May need fuzzy match
    "soap_and_glory_girls_night_out_refresh_queen": "Girl's Night Out Refresh Queen"
}

for folder_name, verbatim_concept_name in VERBATIM_MAPPINGS.items():
    concept_dir = HOLDOUT_DIR / folder_name

    if not concept_dir.exists():
        print(f"\n⚠️  Folder not found: {folder_name}")
        continue

    print(f"\n{'='*80}")
    print(f"Processing: {folder_name}")

    # Try exact match first
    matches = verbatims_df[verbatims_df['Concept'] == verbatim_concept_name]

    # Try case-insensitive partial match if exact fails
    if len(matches) == 0:
        matches = verbatims_df[verbatims_df['Concept'].str.contains(verbatim_concept_name, case=False, na=False)]

    # Try with key words
    if len(matches) == 0:
        key_words = [w for w in verbatim_concept_name.split() if len(w) > 4]
        for word in key_words:
            matches = verbatims_df[verbatims_df['Concept'].str.contains(word, case=False, na=False)]
            if len(matches) > 0:
                print(f"  Found via keyword: '{word}'")
                break

    if len(matches) == 0:
        print(f"  ❌ No verbatims found for '{verbatim_concept_name}'")
        continue

    print(f"  ✓ Found {len(matches)} verbatims")

    # Separate likes and dislikes
    likes = matches[matches['Sentiment'].str.lower().str.contains('like', na=False)]
    dislikes = matches[matches['Sentiment'].str.lower().str.contains('dislike', na=False)]

    print(f"    Likes: {len(likes)}, Dislikes: {len(dislikes)}")

    # Write verbatim file
    verbatim_file = concept_dir / "Textual Data Inputs" / "verbatims_summary.txt"

    verbatim_content = f"""VERBATIM FEEDBACK: {verbatim_concept_name}
================================================================================

LIKES ({len(likes)} responses):
--------------------------------------------------------------------------------
"""

    for idx, row in likes.iterrows():
        text = row['Verbatim']
        if pd.notna(text) and str(text).strip() and str(text).lower() != 'nothing':
            verbatim_content += f"• {text}\n"

    verbatim_content += f"""

DISLIKES ({len(dislikes)} responses):
--------------------------------------------------------------------------------
"""

    for idx, row in dislikes.iterrows():
        text = row['Verbatim']
        if pd.notna(text) and str(text).strip() and str(text).lower() != 'nothing':
            verbatim_content += f"• {text}\n"

    with open(verbatim_file, 'w', encoding='utf-8') as f:
        f.write(verbatim_content)

    print(f"  → Updated verbatims_summary.txt ({len(verbatim_content)} chars)")

print("\n" + "="*80)
print("VERBATIM DATA FIX COMPLETE!")
print("="*80)
