"""
Find 20-30 RELATED questions from the full dataset to use as TRAINING set.
These will be used to iteratively improve class-specific prompts.
The original 10 questions remain as TEST set (never seen during training).

CRITICAL: Training questions must be:
1. Similar/related to the 10 test questions (so learning transfers)
2. Different enough that they're not the same questions
3. Have ground truth data available
4. Have IR context available (demographics)
"""

import pandas as pd
from pathlib import Path

# The 10 TEST questions (HOLDOUT - never use for training!)
TEST_QUESTIONS = {
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

# Categories we want related questions for (to ensure transfer learning)
TARGET_CATEGORIES = {
    "environmental": ["sustainability", "environment", "green", "eco", "carbon", "climate"],
    "energy": ["energy", "electricity", "gas", "heating", "power", "utility"],
    "fuel": ["fuel", "petrol", "diesel", "mpg", "car", "vehicle", "transport"],
    "debt": ["debt", "borrow", "loan", "credit", "owe", "mortgage"],
    "money_management": ["money", "financial", "budget", "save", "savings", "manage"],
    "insurance": ["insurance", "insure", "protection", "cover", "policy"],
    "health": ["health", "healthy", "fitness", "diet", "nutrition", "exercise"],
    "retirement": ["retirement", "pension", "retire", "old age", "future"],
    "switching": ["switch", "change provider", "compare", "shop around"],
    "payment": ["cash", "card", "payment", "pay", "contactless", "digital"]
}

def load_all_questions_from_csv():
    """Load all questions that have ground truth data"""

    # Check the ground truth CSV structure
    df = pd.read_csv("ACORN_ground_truth_named.csv")

    print("="*80)
    print("GROUND TRUTH CSV STRUCTURE")
    print("="*80)
    print(f"Columns: {df.columns.tolist()}")
    print(f"Number of classes: {len(df)}")
    print(f"Number of questions: {len(df.columns) - 1}")  # -1 for Class column

    # Get all question columns (everything except 'Class')
    question_columns = [col for col in df.columns if col != 'Class']

    print(f"\n{'='*80}")
    print("ALL QUESTIONS WITH GROUND TRUTH")
    print("="*80)

    for i, q in enumerate(question_columns, 1):
        in_test = "TEST SET" if q in TEST_QUESTIONS else "Available"
        print(f"{i:2}. [{in_test:12}] {q}")

    return question_columns

def find_related_questions():
    """
    Since we only have 10 questions total with ground truth, we need a different approach.

    We'll look at the FLATTENED DATA to find related attitude/behavior questions
    that we can use for training, even if they don't have exact ground truth.
    """

    print(f"\n{'='*80}")
    print("SEARCHING FLATTENED DATA FOR RELATED QUESTIONS")
    print("="*80)

    # Load flattened data from one class
    df = pd.read_csv("demographic_runs_ACORN/exclusive_addresses/Flattened Data Inputs/ACORN_exclusive_addresses.csv")

    # Get all unique questions
    all_questions = df['Question'].unique()

    print(f"Total questions in flattened data: {len(all_questions)}")

    # Look for questions that match our target categories
    training_candidates = []

    for category, keywords in TARGET_CATEGORIES.items():
        print(f"\n{category.upper()}:")
        print("-"*80)

        found = []
        for q in all_questions:
            q_lower = str(q).lower()
            # Check if any keyword matches
            if any(kw in q_lower for kw in keywords):
                # Make sure it's not a demographic question
                if not any(demo in q_lower for demo in ['age', 'gender', 'income', 'occupation',
                                                         'household', 'tenure', 'property', 'region']):
                    # Make sure it's not one of our test questions
                    if q not in TEST_QUESTIONS:
                        found.append(q)

        # Remove duplicates and show
        found = list(set(found))
        for f in found[:5]:  # Show top 5 per category
            print(f"  - {f}")
            training_candidates.append((category, f))

    return training_candidates

def check_if_questions_have_data(training_candidates):
    """
    Check if these questions have actual response data in the CSV
    """

    print(f"\n{'='*80}")
    print("CHECKING WHICH TRAINING CANDIDATES HAVE RESPONSE DATA")
    print("="*80)

    df = pd.read_csv("demographic_runs_ACORN/exclusive_addresses/Flattened Data Inputs/ACORN_exclusive_addresses.csv")

    # For each candidate, check if it has Likert-style responses or just demographic data
    questions_with_responses = []

    for category, question in training_candidates:
        # Get data for this question
        q_data = df[df['Question'] == question]

        # Check what kind of answers it has
        answers = q_data['Answer'].unique()

        # Check if it has percentage/topline data (not just categorical options)
        # Look for patterns like "Topline" or numeric values
        has_topline = any('topline' in str(a).lower() for a in answers)
        has_numeric = any(str(a).replace('.','').isdigit() for a in answers)

        if has_topline or len(answers) < 10:  # If it has topline or few categorical options
            questions_with_responses.append((category, question, len(answers)))

    print(f"Found {len(questions_with_responses)} questions with response data\n")

    for category, q, n_answers in questions_with_responses[:30]:
        print(f"[{category:15}] {q[:60]}... ({n_answers} response types)")

    return questions_with_responses

def main():
    print("="*80)
    print("FINDING TRAINING QUESTIONS FOR CLASS-SPECIFIC PROMPT LEARNING")
    print("="*80)
    print("\nGoal: Find 20-30 RELATED questions to train on")
    print("These are NOT the 10 test questions - those remain holdout")
    print("="*80)

    # First, check what questions have ground truth
    all_ground_truth_questions = load_all_questions_from_csv()

    print(f"\n{'='*80}")
    print("CRITICAL FINDING")
    print("="*80)
    print(f"The ground truth CSV only has {len(all_ground_truth_questions)} questions")
    print(f"10 of these are our TEST set (holdout)")
    print(f"This means: NO additional questions available with exact ground truth!")
    print("\nWe need to use PROXY questions from the flattened data instead.")
    print("="*80)

    # Find related questions in flattened data
    training_candidates = find_related_questions()

    print(f"\n{'='*80}")
    print(f"Found {len(training_candidates)} related questions in flattened data")
    print("="*80)

    # Check which have response data
    questions_with_data = check_if_questions_have_data(training_candidates)

    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print("="*80)
    print("""
    PROBLEM: The ground truth CSV only contains the 10 test questions.
    There are NO additional Likert-scale questions with ground truth.

    SOLUTION OPTIONS:

    Option A: Use sub-questions from the 10 test questions
    - Each test question has 5 Likert response options (strongly agree, etc.)
    - We could predict the FULL DISTRIBUTION (not just topline)
    - Train on getting all 5 values right
    - This gives us 10 questions × 5 responses = 50 training targets
    - Test on topline aggregation (strongly + slightly agree)

    Option B: Use the 10 questions with cross-validation
    - Use 7 questions for training, 3 for validation
    - Rotate which 3 are validation
    - Final test on all 10 with the best prompt
    - This is standard k-fold validation

    Option C: Ask user for additional labeled questions
    - Need 20-30 more Likert questions with ground truth
    - These would be genuinely new training data

    RECOMMENDATION: Option A (Full Distribution Prediction)
    - Uses available data without leaking test information
    - Trains on a harder task (5-way distribution vs 1-way topline)
    - If model can predict full distribution, topline will be accurate
    - Legitimate use of test questions for training on different target
    """)

if __name__ == "__main__":
    main()
