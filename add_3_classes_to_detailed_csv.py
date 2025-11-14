"""
Add the 3 newly tested classes to the detailed CSV.
Parse v10_missing_3_results.txt and merge with existing data.
"""

import pandas as pd
import re
import numpy as np

# Question mapping for full text and values
QUESTION_MAPPING = {
    "I think brands should consider environmental susta": {
        "full": "I think brands should consider environmental sustainability when developing products and services",
        "value": "Environmental sustainability",
        "type": "Environmental Attitudes"
    },
    "Make an effort to cut down on the use of gas / ele": {
        "full": "Make an effort to cut down on the use of gas / electricity in the home",
        "value": "Energy saving",
        "type": "Energy Behavior"
    },
    "Fuel consumption is the most important feature whe": {
        "full": "Fuel consumption is the most important feature when choosing a new car",
        "value": "Fuel consumption",
        "type": "Transport"
    },
    "I don't like the idea of being in debt": {
        "full": "I don't like the idea of being in debt",
        "value": "Debt aversion",
        "type": "Debt Attitudes"
    },
    "I am very good at managing money": {
        "full": "I am very good at managing money",
        "value": "Money management",
        "type": "Financial Confidence"
    },
    "It is important to be well insured for everything": {
        "full": "It is important to be well insured for everything",
        "value": "Insurance importance",
        "type": "Insurance Attitudes"
    },
    "Healthy Eating": {
        "full": "Healthy Eating",
        "value": "Healthy eating",
        "type": "Health Behavior"
    },
    "Financial security after retirement is your own re": {
        "full": "Financial security after retirement is your own responsibility not that of the state",
        "value": "Retirement responsibility",
        "type": "Retirement Attitudes"
    },
    "Switching utilities suppliers is well worth the ef": {
        "full": "Switching utilities suppliers is well worth the effort for the savings you can make",
        "value": "Switching providers",
        "type": "Switching Behavior"
    },
    "I like to use cash when making purchases": {
        "full": "I like to use cash when making purchases",
        "value": "Cash preference",
        "type": "Payment Preferences"
    }
}

def match_question(question_text):
    """Match question text to full mapping"""
    for key, mapping in QUESTION_MAPPING.items():
        if key in question_text or question_text in key:
            return mapping
    return None

def parse_missing_classes_output(filepath):
    """Parse the v10_missing_3_results.txt file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    results = []

    # Extract class sections
    class_sections = re.split(r'Testing: (\S+)', content)[1:]

    for i in range(0, len(class_sections), 2):
        if i + 1 >= len(class_sections):
            break

        class_name = class_sections[i]
        section_content = class_sections[i + 1]

        # Extract R² score
        r2_match = re.search(r'R2: ([\d.]+)', section_content)
        r2 = float(r2_match.group(1)) if r2_match else None

        # Parse question lines
        question_lines = re.findall(
            r'\[\d+/\d+\] (.+?)\n\s+Pred:\s+([\d.]+)%\s+\|\s+Actual:\s+([\d.]+)%\s+\|\s+Error:\s+([\d.]+)pp',
            section_content
        )

        for question_text, pred, actual, error in question_lines:
            question_text = question_text.strip()

            # Match to full question
            mapping = match_question(question_text)

            if mapping:
                results.append({
                    'class': class_name,
                    'class_r2': r2,
                    'question_type': mapping['type'],
                    'question_value': mapping['value'],
                    'question_full': mapping['full'],
                    'predicted': float(pred),
                    'actual': float(actual),
                    'error': float(error)
                })

    return results

# Load existing detailed CSV
df_existing = pd.read_csv('v10_detailed_final.csv')
print(f"Existing CSV: {len(df_existing)} rows from {df_existing['class'].nunique()} classes")

# Parse new results
new_results = parse_missing_classes_output('v10_missing_3_results.txt')
df_new = pd.DataFrame(new_results)
print(f"New results: {len(df_new)} rows from {df_new['class'].nunique()} classes")

# Check class names in new data
print(f"\nNew classes: {sorted(df_new['class'].unique())}")

# Combine
df_combined = pd.concat([df_existing, df_new], ignore_index=True)

# Sort by class and question value
df_combined = df_combined.sort_values(['class', 'question_value'])

# Save
output_file = 'v10_detailed_all_21_classes.csv'
df_combined.to_csv(output_file, index=False)

print(f"\n{'='*80}")
print("COMBINED RESULTS")
print(f"{'='*80}")
print(f"Total rows: {len(df_combined)}")
print(f"Total classes: {df_combined['class'].nunique()}")
print(f"Classes: {sorted(df_combined['class'].unique())}")

# Show R² summary
print(f"\n{'='*80}")
print("R² BY CLASS (ALL 21 CLASSES)")
print(f"{'='*80}")

class_summary = df_combined.groupby('class').agg({
    'class_r2': 'first',
    'error': 'mean',
    'question_value': 'count'
}).round(4)

class_summary.columns = ['R²', 'Avg Error', 'Questions']
class_summary = class_summary.sort_values('R²', ascending=False)
print(class_summary.to_string())

print(f"\n{'='*80}")
print(f"Average R² across {len(class_summary)} classes: {class_summary['R²'].mean():.4f}")
print(f"Classes with R² > 0.7: {len(class_summary[class_summary['R²'] > 0.7])}/{len(class_summary)}")
print(f"Classes with all 10 questions: {len(class_summary[class_summary['Questions'] == 10])}")
print(f"Classes with partial data (5 questions): {len(class_summary[class_summary['Questions'] == 5])}")
print(f"{'='*80}")

print(f"\nSaved to: {output_file}")
