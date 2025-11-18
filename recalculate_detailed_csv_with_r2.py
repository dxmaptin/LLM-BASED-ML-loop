"""
Recalculate detailed CSV:
- Remove 'performance' and 'question_category' columns
- Add R² per class (calculated from that class's predictions)
"""

import pandas as pd
import numpy as np

# Load current detailed CSV
df = pd.read_csv('v10_detailed_question_by_question.csv')

print(f"Original CSV: {len(df)} rows, {len(df.columns)} columns")
print(f"Columns: {list(df.columns)}")

# Calculate R² for each class
def calculate_r2(actuals, predictions):
    """Calculate R² score"""
    mean_actual = np.mean(actuals)
    ss_tot = np.sum((actuals - mean_actual) ** 2)
    ss_res = np.sum((actuals - predictions) ** 2)

    if ss_tot == 0:
        return 0

    return 1 - (ss_res / ss_tot)

# Calculate R² per class
class_r2 = {}
for class_name in df['class'].unique():
    class_df = df[df['class'] == class_name]
    r2 = calculate_r2(
        class_df['actual'].values,
        class_df['predicted'].values
    )
    class_r2[class_name] = r2

# Add R² column to dataframe
df['class_r2'] = df['class'].map(class_r2)

# Remove unwanted columns
columns_to_remove = ['performance', 'question_category']
df_new = df.drop(columns=[col for col in columns_to_remove if col in df.columns])

# Reorder columns for better readability
column_order = ['class', 'class_r2', 'question', 'question_short', 'predicted', 'actual', 'error']
df_new = df_new[column_order]

# Sort by class (alphabetically) and question
df_new = df_new.sort_values(['class', 'question'])

# Save new CSV
output_file = 'v10_detailed_with_r2.csv'
df_new.to_csv(output_file, index=False)

print(f"\nNew CSV: {len(df_new)} rows, {len(df_new.columns)} columns")
print(f"Columns: {list(df_new.columns)}")

# Show summary
print("\n" + "="*80)
print("R² BY CLASS")
print("="*80)

class_summary = df_new.groupby('class').agg({
    'class_r2': 'first',
    'error': 'mean',
    'question': 'count'
}).round(4)

class_summary.columns = ['R²', 'Avg Error', 'Questions']
class_summary = class_summary.sort_values('R²', ascending=False)

print(class_summary.to_string())

print("\n" + "="*80)
print(f"Average R² across {len(class_summary)} classes: {class_summary['R²'].mean():.4f}")
print(f"Classes with R² > 0.7: {len(class_summary[class_summary['R²'] > 0.7])}/{len(class_summary)}")
print("="*80)

print(f"\n✓ Updated CSV saved to: {output_file}")
