"""
Compile detailed question-by-question results for V10 across all ACORN classes.
Creates a comprehensive CSV with one row per (class, question) combination.
"""

import pandas as pd
import re
from pathlib import Path

# All test questions (from ground truth CSV)
TEST_QUESTIONS = [
    "I think brands should consider environmental susta...",
    "Make an effort to cut down on the use of gas / ele...",
    "Fuel consumption is the most important feature whe...",
    "I don't like the idea of being in debt",
    "I am very good at managing money",
    "It is important to be well insured for everything",
    "Healthy Eating",
    "Financial security after retirement is your own re...",
    "Switching utilities suppliers is well worth the ef...",
    "I like to use cash when making purchases"
]

# Shortened question names for display
QUESTION_SHORT_NAMES = {
    "I think brands should consider environmental susta...": "Environmental sustainability",
    "Make an effort to cut down on the use of gas / ele...": "Energy saving",
    "Fuel consumption is the most important feature whe...": "Fuel consumption",
    "I don't like the idea of being in debt": "Debt aversion",
    "I am very good at managing money": "Money management",
    "It is important to be well insured for everything": "Insurance importance",
    "Healthy Eating": "Healthy eating",
    "Financial security after retirement is your own re...": "Retirement responsibility",
    "Switching utilities suppliers is well worth the ef...": "Switching providers",
    "I like to use cash when making purchases": "Cash preference"
}

def load_ground_truth():
    """Load ground truth data from CSV"""
    df = pd.read_csv("ACORN_ground_truth_named.csv")
    ground_truth = {}

    for _, row in df.iterrows():
        class_name_orig = row['Class'].lower().replace(' ', '_')
        class_name_hyphen = row['Class'].lower().replace(' ', '-')

        for class_name in [class_name_orig, class_name_hyphen]:
            if class_name not in ground_truth:
                ground_truth[class_name] = {}

            for question in TEST_QUESTIONS:
                if question in row:
                    value = row[question]
                    # Convert to percentage (data is in decimal format 0-1)
                    if pd.notna(value):
                        ground_truth[class_name][question] = float(value) * 100

    return ground_truth

def parse_test_output(filepath):
    """Parse test output file and extract all predictions"""
    results = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by class sections
        class_sections = re.split(r'Testing: (\S+)', content)[1:]  # Skip first empty element

        for i in range(0, len(class_sections), 2):
            if i + 1 >= len(class_sections):
                break

            class_name = class_sections[i]
            section_content = class_sections[i + 1]

            # Skip if no ground truth
            if "NO GROUND TRUTH" in section_content:
                continue

            # Parse each question line
            # Format: "[1/10] Question text...\n  Pred:  XX.X% | Actual:  XX.X% | Error:  XX.Xpp [STATUS]"
            question_lines = re.findall(
                r'\[\d+/10\] (.+?)\n\s+Pred:\s+([\d.]+)%\s+\|\s+Actual:\s+([\d.]+)%\s+\|\s+Error:\s+([\d.]+)pp',
                section_content
            )

            for question_text, pred, actual, error in question_lines:
                question_text = question_text.strip()

                # Match with full question names
                matched_question = None
                for full_q in TEST_QUESTIONS:
                    if question_text in full_q or full_q in question_text:
                        matched_question = full_q
                        break

                if not matched_question:
                    # Try partial matching
                    for full_q in TEST_QUESTIONS:
                        if question_text[:30] in full_q or full_q[:30] in question_text:
                            matched_question = full_q
                            break

                if matched_question:
                    pred_val = float(pred)
                    actual_val = float(actual)
                    error_val = float(error)

                    # Categorize performance
                    if error_val <= 3:
                        performance = "EXCELLENT"
                    elif error_val <= 5:
                        performance = "GOOD"
                    elif error_val <= 10:
                        performance = "FAIR"
                    else:
                        performance = "POOR"

                    results.append({
                        'class': class_name,
                        'question': matched_question,
                        'question_short': QUESTION_SHORT_NAMES.get(matched_question, matched_question),
                        'predicted': round(pred_val, 2),
                        'actual': round(actual_val, 2),
                        'error': round(error_val, 2),
                        'performance': performance
                    })

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        import traceback
        traceback.print_exc()

    return results

def main():
    print("Loading ground truth data...")
    ground_truth = load_ground_truth()

    all_results = []

    # Define all test runs and their output files
    test_files = [
        "v10_training_results.txt",
        "v10_remaining_results.txt"
    ]

    print("\nExtracting detailed results from test outputs...")
    for output_file in test_files:
        if Path(output_file).exists():
            print(f"  Processing {output_file}...")
            results = parse_test_output(output_file)
            all_results.extend(results)
            print(f"    Extracted {len(results)} predictions")
        else:
            print(f"    Warning: {output_file} not found")

    if not all_results:
        print("\n❌ No results extracted! Check that test output files exist.")
        return

    # Create DataFrame
    df = pd.DataFrame(all_results)

    # Sort by class and question
    df = df.sort_values(['class', 'question'])

    # Add question category
    def categorize_question(q):
        if 'environmental' in q.lower() or 'brands' in q.lower():
            return 'Environmental Attitudes'
        elif 'energy' in q.lower() or 'gas' in q.lower() or 'standby' in q.lower():
            return 'Energy Behavior'
        elif 'fuel' in q.lower() or 'petrol' in q.lower():
            return 'Transport'
        elif 'debt' in q.lower():
            return 'Debt Attitudes'
        elif 'managing money' in q.lower():
            return 'Financial Confidence'
        elif 'insurance' in q.lower():
            return 'Insurance Attitudes'
        elif 'healthy' in q.lower():
            return 'Health Behavior'
        elif 'retirement' in q.lower():
            return 'Retirement Attitudes'
        elif 'switching' in q.lower():
            return 'Switching Behavior'
        elif 'cash' in q.lower():
            return 'Payment Preferences'
        else:
            return 'Other'

    df['question_category'] = df['question'].apply(categorize_question)

    # Save detailed results
    output_file = "v10_detailed_question_by_question.csv"
    df.to_csv(output_file, index=False)

    print(f"\n✓ Detailed results saved to: {output_file}")
    print(f"  Total rows: {len(df)}")
    print(f"  Classes: {len(df['class'].unique())}")
    print(f"  Questions: {len(df['question'].unique())}")

    # Generate summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    print(f"\nTotal predictions: {len(df)}")
    print(f"Classes: {len(df['class'].unique())}")
    print(f"Questions: {len(df['question'].unique())}")

    print("\nPerformance Distribution:")
    perf_counts = df['performance'].value_counts()
    for perf in ['EXCELLENT', 'GOOD', 'FAIR', 'POOR']:
        if perf in perf_counts:
            count = perf_counts[perf]
            pct = count / len(df) * 100
            print(f"  {perf:12s}: {count:3d} ({pct:5.1f}%)")

    print("\nAverage Error by Question Category:")
    category_stats = df.groupby('question_category').agg({
        'error': ['mean', 'std', 'count']
    }).round(2)
    print(category_stats)

    print("\nAverage Error by Question:")
    question_stats = df.groupby('question_short')['error'].agg(['mean', 'std', 'count']).round(2)
    question_stats = question_stats.sort_values('mean', ascending=False)
    print(question_stats.to_string())

    print("\nWorst Performing Question Overall:")
    worst_q = question_stats.sort_values('mean', ascending=False).head(3)
    print(worst_q)

    print("\nBest Performing Question Overall:")
    best_q = question_stats.sort_values('mean', ascending=True).head(3)
    print(best_q)

    print("\nWorst Individual Predictions (Error > 15pp):")
    worst = df[df['error'] > 15].sort_values('error', ascending=False)
    if len(worst) > 0:
        print(worst[['class', 'question_short', 'predicted', 'actual', 'error']].head(10).to_string(index=False))
    else:
        print("  None! All predictions within 15pp")

    # Analysis by class wealth level
    print("\n" + "="*80)
    print("ANALYSIS BY DEMOGRAPHIC TYPE")
    print("="*80)

    # Categorize classes
    affluent_classes = ['exclusive_addresses', 'flourishing_capital', 'upmarket_families',
                       'commuter-belt_wealth', 'prosperous_professionals', 'mature_success']
    poor_classes = ['cash-strapped_families', 'hard-up_households', 'challenging_circumstances']
    senior_classes = ['stable_seniors', 'constrained_penisoners', 'semi-rural_maturity']

    for group_name, class_list in [
        ('Affluent', affluent_classes),
        ('Poor', poor_classes),
        ('Senior', senior_classes)
    ]:
        group_df = df[df['class'].isin(class_list)]
        if len(group_df) > 0:
            print(f"\n{group_name} Classes (n={len(group_df)}):")
            print(f"  Average Error: {group_df['error'].mean():.2f}pp")
            print(f"  Excellent: {len(group_df[group_df['performance']=='EXCELLENT'])/len(group_df)*100:.1f}%")

            # Worst questions for this group
            worst_for_group = group_df.groupby('question_short')['error'].mean().sort_values(ascending=False).head(3)
            print(f"  Worst questions:")
            for q, err in worst_for_group.items():
                print(f"    {q}: {err:.2f}pp")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
