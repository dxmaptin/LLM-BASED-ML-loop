"""
Rebuild detailed CSV with:
- Full question text (no truncation)
- Question type/value instead of question_short
- Keep class_r2
- Remove question_short
"""

import pandas as pd
import numpy as np

# Define question types and their shortened values
QUESTION_MAPPING = {
    "I think brands should consider environmental susta...": {
        "full": "I think brands should consider environmental sustainability when developing products and services",
        "value": "Environmental sustainability"
    },
    "Make an effort to cut down on the use of gas / ele...": {
        "full": "Make an effort to cut down on the use of gas / electricity in the home",
        "value": "Energy saving"
    },
    "Fuel consumption is the most important feature whe...": {
        "full": "Fuel consumption is the most important feature when choosing a new car",
        "value": "Fuel consumption"
    },
    "I don't like the idea of being in debt": {
        "full": "I don't like the idea of being in debt",
        "value": "Debt aversion"
    },
    "I am very good at managing money": {
        "full": "I am very good at managing money",
        "value": "Money management"
    },
    "It is important to be well insured for everything": {
        "full": "It is important to be well insured for everything",
        "value": "Insurance importance"
    },
    "Healthy Eating": {
        "full": "Healthy Eating",
        "value": "Healthy eating"
    },
    "Financial security after retirement is your own re...": {
        "full": "Financial security after retirement is your own responsibility not that of the state",
        "value": "Retirement responsibility"
    },
    "Switching utilities suppliers is well worth the ef...": {
        "full": "Switching utilities suppliers is well worth the effort for the savings you can make",
        "value": "Switching providers"
    },
    "I like to use cash when making purchases": {
        "full": "I like to use cash when making purchases",
        "value": "Cash preference"
    }
}

# Map values to question types
VALUE_TO_TYPE = {
    "Environmental sustainability": "Environmental Attitudes",
    "Energy saving": "Energy Behavior",
    "Fuel consumption": "Transport",
    "Debt aversion": "Debt Attitudes",
    "Money management": "Financial Confidence",
    "Insurance importance": "Insurance Attitudes",
    "Healthy eating": "Health Behavior",
    "Retirement responsibility": "Retirement Attitudes",
    "Switching providers": "Switching Behavior",
    "Cash preference": "Payment Preferences"
}

# Load current detailed CSV
df = pd.read_csv('v10_detailed_with_r2.csv')

print(f"Original CSV: {len(df)} rows")

# Add full question text
def get_full_question(q):
    for short_q, mapping in QUESTION_MAPPING.items():
        if q.startswith(short_q[:30]) or short_q.startswith(q[:30]):
            return mapping["full"]
    return q

# Add question value
def get_question_value(q):
    for short_q, mapping in QUESTION_MAPPING.items():
        if q.startswith(short_q[:30]) or short_q.startswith(q[:30]):
            return mapping["value"]
    # Fallback to question_short if exists
    return q

# Add question type
def get_question_type(value):
    return VALUE_TO_TYPE.get(value, "Other")

# Apply mappings
df['question_full'] = df['question'].apply(get_full_question)
df['question_value'] = df['question'].apply(get_question_value)
df['question_type'] = df['question_value'].apply(get_question_type)

# Create new dataframe with desired columns
df_new = df[[
    'class',
    'class_r2',
    'question_type',
    'question_value',
    'question_full',
    'predicted',
    'actual',
    'error'
]]

# Sort by class and question value
df_new = df_new.sort_values(['class', 'question_value'])

# Save
output_file = 'v10_detailed_final.csv'
df_new.to_csv(output_file, index=False)

print(f"New CSV: {len(df_new)} rows, {len(df_new.columns)} columns")
print(f"Columns: {list(df_new.columns)}")

# Show sample
print("\nFirst 3 rows:")
print(df_new.head(3).to_string())

print(f"\nSaved to: {output_file}")
