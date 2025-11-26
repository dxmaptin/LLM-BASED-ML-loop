"""
Find all Likert scale questions in the dataset (the ones with agree/disagree).
These are the actual attitude questions we can test on.
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

# Load flattened data
df = pd.read_csv("demographic_runs_ACORN/exclusive_addresses/Flattened Data Inputs/ACORN_exclusive_addresses.csv")

# Find rows with Likert scale answers
likert_answers = ['Strongly Agree', 'Slightly Agree', 'Neither', 'Slightly Disagree', 'Strongly Disagree']
likert_rows = df[df['Answer'].isin(likert_answers)]

# Get unique questions from these rows
likert_questions = likert_rows['Question'].unique()

print(f"Found {len(likert_questions)} Likert scale questions\n")
print(f"Used questions: {len(USED_QUESTIONS)}\n")
print("="*80)

# Filter out already used ones
new_questions = [q for q in likert_questions if q not in USED_QUESTIONS]

print(f"NEW Likert questions available: {len(new_questions)}\n")
print("="*80)

for i, q in enumerate(new_questions[:50], 1):
    print(f"{i:3}. {q}")

print(f"\n{'='*80}")
print(f"Total NEW questions: {len(new_questions)}")
