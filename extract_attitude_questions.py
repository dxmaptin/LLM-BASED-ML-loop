#!/usr/bin/env python3
"""Extract all attitude questions from source data and create train/test split."""

import pandas as pd
from pathlib import Path
import json

# Load source data from one class to get the question structure
source_file = Path('demographic_runs_ACORN/aspiring_communities/Flattened Data Inputs/ACORN_aspiring_communities.csv')
source = pd.read_csv(source_file)

print("="*80)
print("EXTRACTING ATTITUDE QUESTIONS FROM SOURCE DATA")
print("="*80)

# Extract attitude-like questions from different categories
attitude_questions = []

# 1. Environment > Attitudes
env_attitudes = source[(source['Category'] == 'Environment') & (source['Question'] == 'Attitudes')]
for answer in env_attitudes['Answer'].unique():
    attitude_questions.append({
        'question': answer,
        'category': 'Environment',
        'semantic_type': 'Environmental Attitude'
    })

# 2. Environment > Action (behaviors)
env_actions = source[(source['Category'] == 'Environment') & (source['Question'] == 'Action')]
for answer in env_actions['Answer'].unique():
    attitude_questions.append({
        'question': answer,
        'category': 'Environment',
        'semantic_type': 'Environmental Behavior'
    })

# 3. Lifestyle > Interests & Hobbies (preferences)
lifestyle_interests = source[(source['Category'] == 'Lifestyle') & (source['Question'] == 'Interests & Hobbies')]
for answer in lifestyle_interests['Answer'].unique():
    attitude_questions.append({
        'question': answer,
        'category': 'Lifestyle',
        'semantic_type': 'Interest/Hobby'
    })

# 4. Lifestyle > Eating Habits
eating = source[(source['Category'] == 'Lifestyle') & (source['Question'] == 'Eating Habits')]
for answer in eating['Answer'].unique():
    attitude_questions.append({
        'question': answer,
        'category': 'Lifestyle',
        'semantic_type': 'Health Behavior'
    })

# 5. Finance-related attitudes (from Finance category Question='Attitudes' if it exists)
# Check if Finance has attitudes
finance_data = source[source['Category'].str.contains('Finance', na=False)]
if 'Attitudes' in finance_data['Question'].values:
    fin_attitudes = finance_data[finance_data['Question'] == 'Attitudes']
    for answer in fin_attitudes['Answer'].unique():
        attitude_questions.append({
            'question': answer,
            'category': 'Finance',
            'semantic_type': 'Financial Attitude'
        })

print(f"\nTotal attitude questions extracted: {len(attitude_questions)}")

# Show breakdown by semantic type
semantic_counts = {}
for q in attitude_questions:
    sem_type = q['semantic_type']
    semantic_counts[sem_type] = semantic_counts.get(sem_type, 0) + 1

print("\nBreakdown by semantic type:")
for sem_type, count in semantic_counts.items():
    print(f"  {sem_type}: {count} questions")

# Our target 10 ACORN questions (TEST SET - NEVER USE FOR TRAINING)
test_set = [
    "I think brands should consider environmental sustainability when putting on events",
    "Make an effort to cut down on the use of gas / electricity at home",
    "Fuel consumption is the most important feature when buying a new car",
    "I don't like the idea of being in debt",
    "I am very good at managing money",
    "It is important to be well insured for everything",
    "Healthy Eating",
    "Financial security after retirement is your own responsibility",
    "Switching utilities suppliers is well worth the effort",
    "I like to use cash when making purchases"
]

# Remove any test set questions from training pool
train_questions = [q for q in attitude_questions if q['question'] not in test_set]

print(f"\n\nAFTER REMOVING TEST SET:")
print(f"  Training pool: {len(train_questions)} questions")
print(f"  Test set: {len(test_set)} questions (HELD OUT)")

# Display all training questions
print("\n" + "="*80)
print("TRAINING QUESTIONS (will be used in batches):")
print("="*80)
for i, q in enumerate(train_questions, 1):
    print(f"{i}. [{q['semantic_type']}] {q['question']}")

# Save to file
output = {
    'train_questions': train_questions,
    'test_questions': [{'question': q, 'semantic_type': 'Target'} for q in test_set],
    'total_train': len(train_questions),
    'total_test': len(test_set)
}

with open('attitude_questions_train_test_split.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\n" + "="*80)
print(f"Saved train/test split to: attitude_questions_train_test_split.json")
print("="*80)

# If we have < 100 training questions, we'll need to batch them
if len(train_questions) < 100:
    print(f"\nNOTE: Only {len(train_questions)} training questions available (< 100 target)")
    print(f"Strategy: Run in batches, recycle questions after each iteration")

    # Calculate batching strategy
    batch_size = 20
    num_batches = (len(train_questions) + batch_size - 1) // batch_size
    print(f"\nBatching strategy:")
    print(f"  Batch size: {batch_size}")
    print(f"  Number of batches: {num_batches}")
    print(f"  Questions per batch: {[min(batch_size, len(train_questions) - i*batch_size) for i in range(num_batches)]}")
