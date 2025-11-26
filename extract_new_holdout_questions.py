"""
Extract all available questions from the dataset and select 10 NEW ones
that were NOT in the original test set.
"""

import pandas as pd

# Original 10 test questions (CANNOT use these)
USED_QUESTIONS = {
    "I think brands should consider environmental sustainability when putting on events",
    "Make an effort to cut down on the use of gas / electricity at home",
    "Fuel consumption is the most important feature when buying a car",
    "I don't like the idea of being in debt",
    "I am very good at managing money",
    "It is important to be well insured for everything",
    "Healthy Eating",
    "Financial security after retirement is your own responsibility, not the government's",
    "Switching utilities suppliers is well worth the effort",
    "I like to use cash when making purchases"
}

# Load the flattened data
df = pd.read_csv("demographic_runs_ACORN/exclusive_addresses/Flattened Data Inputs/ACORN_exclusive_addresses.csv")

# Get unique questions
all_questions = df['Question'].unique()

print(f"Total questions in dataset: {len(all_questions)}")
print(f"Used questions: {len(USED_QUESTIONS)}")
print("\n" + "="*80)

# Filter to attitude/behavior questions (not demographics)
attitude_questions = []
for q in all_questions:
    q_lower = str(q).lower()
    # Filter out demographics
    if any(demo in q_lower for demo in ['age', 'gender', 'income', 'occupation', 'household',
                                         'tenure', 'property', 'region', 'ethnicity', 'religion',
                                         'education', 'marital', 'children', 'employment']):
        continue
    # Must be reasonably long (actual questions, not categories)
    if len(str(q)) < 15:
        continue
    # Not already used
    if q in USED_QUESTIONS:
        continue

    attitude_questions.append(q)

print(f"\nAttitude/behavior questions available (excluding used): {len(attitude_questions)}")
print("\n" + "="*80)
print("SAMPLE OF AVAILABLE QUESTIONS:")
print("="*80)

# Show first 50
for i, q in enumerate(attitude_questions[:50], 1):
    print(f"{i:3}. {q}")

print(f"\n{'='*80}")
print(f"Total attitude questions: {len(attitude_questions)}")
print("\nNow I'll select 10 diverse questions for new holdout set...")
