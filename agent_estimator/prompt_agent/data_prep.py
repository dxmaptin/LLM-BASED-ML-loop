"""
Data Preparation for Prompt Discovery

Loads ACORN dataset and filters out holdout questions for testing.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Set
import json


# The 10 holdout questions to exclude from training
HOLDOUT_QUESTIONS = [
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


class ACORNDataLoader:
    """Load and prepare ACORN dataset for prompt discovery."""

    def __init__(self, acorn_dir: Path):
        """
        Initialize data loader.

        Args:
            acorn_dir: Path to demographic_runs_ACORN directory
        """
        self.acorn_dir = Path(acorn_dir)
        self.holdout_questions = set(HOLDOUT_QUESTIONS)

    def load_all_classes(self, include_holdout: bool = False) -> pd.DataFrame:
        """
        Load data from all ACORN classes.

        Args:
            include_holdout: If False, filter out holdout questions

        Returns:
            DataFrame with all class data combined
        """
        all_data = []

        # Find all class directories
        class_dirs = [d for d in self.acorn_dir.iterdir() if d.is_dir()]

        print(f"Loading data from {len(class_dirs)} ACORN classes...")

        for class_dir in sorted(class_dirs):
            # Load quantitative data
            csv_path = class_dir / "Flattened Data Inputs" / f"ACORN_{class_dir.name}.csv"

            if not csv_path.exists():
                print(f"  Warning: No CSV found for {class_dir.name}")
                continue

            df = pd.read_csv(csv_path)
            df['class_name'] = class_dir.name

            # Filter out holdout questions if requested
            if not include_holdout:
                original_len = len(df)
                df = df[~df['Question'].isin(self.holdout_questions)]
                filtered = original_len - len(df)
                if filtered > 0:
                    print(f"  {class_dir.name}: Filtered {filtered} holdout question rows")

            all_data.append(df)

        combined = pd.concat(all_data, ignore_index=True)
        print(f"Loaded {len(combined)} total rows from {len(class_dirs)} classes")

        if not include_holdout:
            print(f"Holdout questions excluded: {len(self.holdout_questions)}")

        return combined

    def load_class_data(self, class_name: str, include_holdout: bool = False) -> pd.DataFrame:
        """
        Load data for a specific class.

        Args:
            class_name: Name of ACORN class
            include_holdout: If False, filter out holdout questions

        Returns:
            DataFrame for that class
        """
        csv_path = self.acorn_dir / class_name / "Flattened Data Inputs" / f"ACORN_{class_name}.csv"

        if not csv_path.exists():
            raise FileNotFoundError(f"No data found for {class_name}")

        df = pd.read_csv(csv_path)
        df['class_name'] = class_name

        if not include_holdout:
            df = df[~df['Question'].isin(self.holdout_questions)]

        return df

    def load_class_profile(self, class_name: str) -> str:
        """
        Load qualitative profile (pen portrait) for a class.

        Args:
            class_name: Name of ACORN class

        Returns:
            Profile text
        """
        txt_path = self.acorn_dir / class_name / "Textual Data Inputs" / f"{class_name}_profile.txt"

        if not txt_path.exists():
            return f"No profile available for {class_name}"

        with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def get_all_class_names(self) -> List[str]:
        """Get list of all ACORN class names."""
        class_dirs = [d.name for d in self.acorn_dir.iterdir() if d.is_dir()]
        return sorted(class_dirs)

    def get_holdout_test_set(self) -> pd.DataFrame:
        """
        Load ONLY the holdout questions for testing.

        Returns:
            DataFrame with only holdout question data
        """
        all_data = []
        class_dirs = [d for d in self.acorn_dir.iterdir() if d.is_dir()]

        for class_dir in sorted(class_dirs):
            csv_path = class_dir / "Flattened Data Inputs" / f"ACORN_{class_dir.name}.csv"

            if not csv_path.exists():
                continue

            df = pd.read_csv(csv_path)
            df['class_name'] = class_dir.name

            # Keep ONLY holdout questions
            df = df[df['Question'].isin(self.holdout_questions)]

            if len(df) > 0:
                all_data.append(df)

        if not all_data:
            return pd.DataFrame()

        combined = pd.concat(all_data, ignore_index=True)
        print(f"Test set: {len(combined)} rows from {len(self.holdout_questions)} holdout questions")

        return combined

    def analyze_dataset_stats(self) -> Dict:
        """
        Analyze basic statistics about the dataset.

        Returns:
            Dictionary with statistics
        """
        train_data = self.load_all_classes(include_holdout=False)
        test_data = self.get_holdout_test_set()

        stats = {
            "total_classes": len(self.get_all_class_names()),
            "holdout_questions": len(self.holdout_questions),
            "train_rows": len(train_data),
            "test_rows": len(test_data),
            "train_unique_questions": train_data['Question'].nunique() if len(train_data) > 0 else 0,
            "test_unique_questions": test_data['Question'].nunique() if len(test_data) > 0 else 0,
            "categories": train_data['Category'].unique().tolist() if len(train_data) > 0 else [],
            "train_categories_count": {
                cat: len(train_data[train_data['Category'] == cat])
                for cat in train_data['Category'].unique()
            } if len(train_data) > 0 else {}
        }

        return stats


def summarize_question_responses(df: pd.DataFrame, question: str) -> Dict:
    """
    Summarize responses for a specific question across all classes.

    Args:
        df: DataFrame with all data
        question: Question text to analyze

    Returns:
        Summary dictionary with statistics
    """
    q_data = df[df['Question'] == question].copy()

    if len(q_data) == 0:
        return {"error": "Question not found"}

    # Convert Value to numeric
    q_data['Value'] = pd.to_numeric(q_data['Value'], errors='coerce')
    q_data = q_data.dropna(subset=['Value'])

    summary = {
        "question": question,
        "total_responses": len(q_data),
        "classes_with_data": q_data['class_name'].nunique(),
        "mean_value": float(q_data['Value'].mean()) if len(q_data) > 0 else 0,
        "std_value": float(q_data['Value'].std()) if len(q_data) > 1 else 0,
        "min_value": float(q_data['Value'].min()) if len(q_data) > 0 else 0,
        "max_value": float(q_data['Value'].max()) if len(q_data) > 0 else 0,
        "variance": float(q_data['Value'].var()) if len(q_data) > 1 else 0
    }

    # Top answers
    if 'Answer' in q_data.columns:
        top_answers = q_data.groupby('Answer')['Value'].mean().nlargest(5)
        summary['top_answers'] = [
            {"answer": ans, "avg_value": float(val)}
            for ans, val in top_answers.items()
        ]

    return summary


if __name__ == "__main__":
    # Test the data loader
    loader = ACORNDataLoader(Path("demographic_runs_ACORN"))

    print("\n" + "="*70)
    print("ACORN Data Loader Test")
    print("="*70)

    # Print stats
    stats = loader.analyze_dataset_stats()
    print(f"\nDataset Statistics:")
    print(json.dumps(stats, indent=2))

    # Test loading
    print(f"\nAll classes: {loader.get_all_class_names()}")

    # Show sample data
    train_df = loader.load_all_classes(include_holdout=False)
    print(f"\nSample training data:")
    print(train_df.head(10))

    print("\n" + "="*70)
