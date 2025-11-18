"""
Setup ACORN data for the prediction pipeline.

This script:
1. Extracts 10 attitude-related questions from ACORN data
2. Creates handpicked concepts CSV
3. Creates ground truth CSV with actual scores across all 22 classes
4. Sets up demographic_runs_ACORN folder structure with class-specific CSVs
"""

import pandas as pd
import os
import shutil
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent
ACORN_EXCEL = BASE_DIR / "ACORN Flattened Data_C.xlsx"
ACORN_TEXT = BASE_DIR / "Accorn.txt"
OUTPUT_DIR = BASE_DIR / "demographic_runs_ACORN"

# Load ACORN data
print("Loading ACORN data...")
df = pd.read_excel(ACORN_EXCEL)

# Get all ACORN classes (22 demographics, exclude last empty column)
acorn_classes = [col for col in df.columns[3:] if not col.startswith('Unnamed')]
print(f"Found {len(acorn_classes)} ACORN classes")

# ============================================================================
# STEP 1: Select 10 Attitude Questions
# ============================================================================

print("\n=== STEP 1: Selecting 10 Attitude Questions ===")

# Define attitude-related questions to extract
attitude_questions = [
    # Environment
    ("Environment", "Attitudes", "I think brands should consider environmental sustainability when putting on events"),
    ("Environment", "Action", "Make an effort to cut down on the use of gas / electricity at home"),
    ("Environment", "Attitudes", "Fuel consumption is the most important feature when buying a new car"),

    # Financial Attitudes
    ("Finance", "Financial Attitudes", "I don't like the idea of being in debt"),
    ("Finance", "Financial Attitudes", "I am very good at managing money"),
    ("Finance", "Financial Attitudes", "It is important to be well insured for everything"),

    # Shopping Attitudes
    ("Shopping", "Attitudes", "Price is more important than quality"),
    ("Shopping", "Attitudes", "I prefer to buy products from brands I know"),

    # Lifestyle/Social
    ("Lifestyle", "Interests & Hobbies", "Healthy Eating"),
    ("Social Capital", "Social Capital", "I feel I belong to this neighbourhood"),
]

# Extract the selected questions
selected_data = []
for category, question, answer in attitude_questions:
    # Find matching rows
    mask = (df['Category'] == category) & (df['Question'] == question) & (df['Answer'] == answer)
    if mask.sum() > 0:
        selected_data.append(df[mask].iloc[0])
        print(f"[OK] Found: {category} - {answer}")
    else:
        # Try partial match
        mask = (df['Category'] == category) & (df['Answer'].str.contains(answer[:30], na=False, case=False))
        if mask.sum() > 0:
            selected_data.append(df[mask].iloc[0])
            print(f"[OK] Found (partial): {category} - {answer}")
        else:
            print(f"[SKIP] Not found: {category} - {answer}")

# If we don't have 10, add more from available attitude questions
if len(selected_data) < 10:
    print(f"\nNeed {10 - len(selected_data)} more questions. Adding from available attitudes...")

    # Get Financial Attitudes
    fin_att = df[df['Question'] == 'Financial Attitudes']
    added = 0
    for idx, row in fin_att.iterrows():
        if added >= (10 - len(selected_data)):
            break
        # Check if this answer is already in selected_data
        is_duplicate = any(str(existing['Answer']) == str(row['Answer']) for existing in selected_data if 'Answer' in existing)
        if not is_duplicate:
            selected_data.append(row)
            print(f"[OK] Added: {row['Answer']}")
            added += 1

print(f"\nTotal selected: {len(selected_data)} questions")

# ============================================================================
# STEP 2: Create Handpicked Concepts CSV
# ============================================================================

print("\n=== STEP 2: Creating Handpicked Concepts CSV ===")

handpicked_csv = BASE_DIR / "Handpicked_ACORN_10.csv"

# Format: just the concept text (like FRESCO format)
concepts = []
for row in selected_data[:10]:  # Ensure exactly 10
    # Create concept string
    if pd.notna(row['Answer']):
        concept = str(row['Answer'])
    else:
        concept = f"{row['Question']}"
    concepts.append(concept)

# Save handpicked concepts
pd.DataFrame({'Concept': concepts}).to_csv(handpicked_csv, index=False)
print(f"[OK] Created: {handpicked_csv}")
print(f"  Concepts: {len(concepts)}")

# ============================================================================
# STEP 3: Create Ground Truth CSV (All 22 Classes)
# ============================================================================

print("\n=== STEP 3: Creating Ground Truth CSV ===")

ground_truth_csv = BASE_DIR / "ACORN_ground_truth_22classes.csv"

# Create ground truth with classes on Y-axis, concepts on columns
# Format: Class, Concept1_value, Concept2_value, ...

ground_truth_data = []
for acorn_class in acorn_classes:
    row_data = {'Class': acorn_class}

    for i, data_row in enumerate(selected_data[:10], 1):
        # Get the value for this class
        concept_name = f"Concept_{i}"
        value = data_row[acorn_class] if acorn_class in data_row else None
        row_data[concept_name] = value

    ground_truth_data.append(row_data)

ground_truth_df = pd.DataFrame(ground_truth_data)
ground_truth_df.to_csv(ground_truth_csv, index=False)
print(f"[OK] Created: {ground_truth_csv}")
print(f"  Classes: {len(acorn_classes)}")
print(f"  Concepts: {len(selected_data[:10])}")

# Also create version with concept names as column headers
ground_truth_named_csv = BASE_DIR / "ACORN_ground_truth_named.csv"
ground_truth_named = {'Class': acorn_classes}
for i, (concept, data_row) in enumerate(zip(concepts[:10], selected_data[:10]), 1):
    # Truncate long concept names
    short_concept = concept[:50] + "..." if len(concept) > 50 else concept
    ground_truth_named[short_concept] = [data_row[cls] for cls in acorn_classes]

pd.DataFrame(ground_truth_named).to_csv(ground_truth_named_csv, index=False)
print(f"[OK] Created: {ground_truth_named_csv} (with concept names)")

# ============================================================================
# STEP 4: Create demographic_runs_ACORN Folder Structure
# ============================================================================

print("\n=== STEP 4: Creating Folder Structure ===")

# Create main ACORN directory
OUTPUT_DIR.mkdir(exist_ok=True)
print(f"[OK] Created: {OUTPUT_DIR}")

# For each ACORN class, create subdirectory with necessary files
for acorn_class in acorn_classes:
    # Normalize class name for folder (replace spaces/special chars)
    folder_name = acorn_class.strip().replace(' ', '_').replace('/', '_').lower()
    class_dir = OUTPUT_DIR / folder_name

    # Create class directory
    class_dir.mkdir(exist_ok=True)

    # 1. Copy handpicked concepts CSV
    handpicked_dest = class_dir / "concepts_to_test.csv"
    shutil.copy(handpicked_csv, handpicked_dest)

    # 2. Create class-specific data directories
    flattened_dir = class_dir / "Flattened Data Inputs"
    textual_dir = class_dir / "Textual Data Inputs"
    flattened_dir.mkdir(exist_ok=True)
    textual_dir.mkdir(exist_ok=True)

    # 3. Create class-specific CSV with ONLY this class's data
    class_csv = flattened_dir / f"ACORN_{folder_name}.csv"

    # Filter full ACORN data to only include this class
    class_specific_df = df[['Category', 'Question', 'Answer', acorn_class]].copy()
    class_specific_df.columns = ['Category', 'Question', 'Answer', 'Value']
    class_specific_df.to_csv(class_csv, index=False)

    # 4. Extract class-specific pen portrait from Accorn.txt
    # (Will do this in next step - for now create placeholder)
    pen_portrait_file = textual_dir / f"{folder_name}_profile.txt"
    with open(pen_portrait_file, 'w') as f:
        f.write(f"{acorn_class}\n")
        f.write("="*50 + "\n\n")
        f.write(f"ACORN Class: {acorn_class}\n\n")
        f.write("[Pen portrait to be extracted from Accorn.txt]\n")

    print(f"[OK] Created structure for: {folder_name}")

# ============================================================================
# STEP 5: Extract and Save Pen Portraits
# ============================================================================

print("\n=== STEP 5: Extracting Pen Portraits ===")

# Read the Accorn.txt file
with open(ACORN_TEXT, 'r', encoding='utf-8') as f:
    accorn_text = f.read()

# Map ACORN class codes (1A, 1B, etc.) to folder names
# This requires manual mapping based on the Accorn.txt structure
acorn_code_mapping = {
    '1A': 'exclusive_addresses',
    '1B': 'flourishing_capital',
    '2A': 'upmarket_families',
    '2B': 'commuter-belt_wealth',
    '3A': 'prosperous_professionals',
    '3B': 'mature_success',
    '4A': 'settled_suburbia',
    '4B': 'metropolitan_surroundings',
    '5A': 'up-and-coming_urbanites',
    '5B': 'aspiring_communities',
    '6A': 'semi-rural_maturity',
    '6B': 'traditional_homeowners',
    '7A': 'family_renters',
    '7B': 'urban_diversity',
    '8A': 'stable_seniors',
    '8B': 'tenant_living',
    '9A': 'limited_budgets',
    '9B': 'hard-up_households',
    '10A': 'cash-strapped_families',
    '10B': 'constrained_penisoners',
    '11': 'challenging_circumstances',
    '12': 'not_private_households'
}

# For each code, extract section from text
for code, folder_name in acorn_code_mapping.items():
    class_dir = OUTPUT_DIR / folder_name
    if not class_dir.exists():
        continue

    # Find section in text (sections start with code pattern like "1A —")
    section_start = accorn_text.find(f"\n{code} —") if len(code) <= 2 else accorn_text.find(f"\n{code}")
    if section_start == -1:
        section_start = accorn_text.find(f"{code} —")

    if section_start != -1:
        # Find next section (next code)
        # Get all codes and find the next one
        codes = list(acorn_code_mapping.keys())
        current_idx = codes.index(code)

        section_end = len(accorn_text)
        if current_idx + 1 < len(codes):
            next_code = codes[current_idx + 1]
            next_start = accorn_text.find(f"\n{next_code} —", section_start + 1)
            if next_start == -1:
                next_start = accorn_text.find(f"\n{next_code}", section_start + 1)
            if next_start != -1:
                section_end = next_start

        # Extract section text
        section_text = accorn_text[section_start:section_end].strip()

        # Save to pen portrait file
        pen_portrait_file = class_dir / "Textual Data Inputs" / f"{folder_name}_profile.txt"
        with open(pen_portrait_file, 'w', encoding='utf-8') as f:
            f.write(section_text)

        print(f"[OK] Extracted pen portrait for: {folder_name}")
    else:
        print(f"[SKIP] Could not find section for: {code} ({folder_name})")

# ============================================================================
# Summary
# ============================================================================

print("\n" + "="*70)
print("SETUP COMPLETE!")
print("="*70)
print(f"\nCreated files:")
print(f"  1. {handpicked_csv}")
print(f"  2. {ground_truth_csv}")
print(f"  3. {ground_truth_named_csv}")
print(f"  4. {OUTPUT_DIR}/ with {len(acorn_classes)} class subdirectories")
print(f"\nEach class directory contains:")
print(f"  - concepts_to_test.csv (10 handpicked attitude questions)")
print(f"  - Flattened Data Inputs/ACORN_<class>.csv (class-specific data)")
print(f"  - Textual Data Inputs/<class>_profile.txt (pen portrait)")
print(f"\nNext steps:")
print(f"  1. Review the handpicked concepts and ground truth")
print(f"  2. Run the prediction pipeline on each ACORN class")
print(f"  3. Train demographic-specific prompts using RL loop")
print("\n" + "="*70)
