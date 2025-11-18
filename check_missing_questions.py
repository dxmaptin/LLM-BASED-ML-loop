"""
Check which questions are missing for the 3 classes that only had 5 questions.
"""

import pandas as pd

# Load the ground truth CSV
df = pd.read_csv('ACORN_ground_truth_named.csv')

# Check the 3 classes (with trailing spaces)
test_classes = ['Limited Budgets ', 'Traditional Homeowners ', 'Urban Diversity ']

for cls in test_classes:
    print(f'\n{"="*80}')
    print(f'{cls.strip()}:')
    print(f'{"="*80}')

    row = df[df['Class'] == cls]

    if len(row) > 0:
        row = row.iloc[0]

        # Check each question column
        for i, col in enumerate(df.columns[1:], 1):  # Skip 'Class' column
            val = row[col]
            has_value = pd.notna(val) and val != '' and val != 0
            status = "✓ HAS DATA" if has_value else "✗ MISSING"

            if has_value:
                print(f'  Q{i:2d} [{status}]: {col[:60]:60s} = {val*100:.1f}%')
            else:
                print(f'  Q{i:2d} [{status}]: {col[:60]:60s}')

# Also check the test script to see which questions it was looking for
print(f'\n\n{"="*80}')
print("QUESTIONS USED IN TEST SCRIPT:")
print(f'{"="*80}')

test_questions = [
    "I think brands should consider environmental sustainability when developing products and services",
    "Make an effort to cut down on the use of gas / electricity in the home",
    "Fuel consumption is the most important feature when choosing a new car",
    "I don't like the idea of being in debt",
    "I am very good at managing money",
    "It is important to be well insured for everything",
    "Healthy Eating",
    "Financial security after retirement is your own responsibility not that of the state",
    "Switching utilities suppliers is well worth the effort for the savings you can make",
    "I like to use cash when making purchases"
]

for i, q in enumerate(test_questions, 1):
    print(f'{i:2d}. {q}')
