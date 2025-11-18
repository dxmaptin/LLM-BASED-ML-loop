"""
Deep Pattern Discovery Agent

Analyzes CSV data in detail to extract intricate patterns like:
- Digital adoption by age/income
- Life satisfaction patterns
- Environmental consciousness
- Financial behaviors
- Shopping patterns
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

from .data_prep import ACORNDataLoader


class DeepPatternAgent:
    """
    Discovers deep, intricate patterns from CSV data.

    This agent goes beyond high-level statistics to find specific
    behavioral patterns that affect predictions.
    """

    def __init__(self, data_loader: ACORNDataLoader):
        self.data_loader = data_loader
        self.train_data = None

    def discover_deep_patterns(self) -> Dict[str, Any]:
        """Main discovery function."""

        print("\n" + "="*80)
        print("DEEP PATTERN DISCOVERY")
        print("="*80)

        # Load data
        print("\n[1/7] Loading training data...")
        self.train_data = self.data_loader.load_all_classes(include_holdout=False)
        print(f"  Loaded {len(self.train_data)} rows from {self.train_data['class_name'].nunique()} classes")

        patterns = {}

        # Pattern 1: Digital Adoption
        print("\n[2/7] Analyzing digital adoption patterns by age...")
        patterns['digital_adoption'] = self._analyze_digital_by_age()

        # Pattern 2: Life Satisfaction
        print("\n[3/7] Analyzing life satisfaction patterns...")
        patterns['life_satisfaction'] = self._analyze_life_satisfaction()

        # Pattern 4: Environmental Consciousness
        print("\n[4/7] Analyzing environmental patterns...")
        patterns['environmental'] = self._analyze_environmental()

        # Pattern 5: Financial Behavior
        print("\n[5/7] Analyzing financial behavior patterns...")
        patterns['financial'] = self._analyze_financial()

        # Pattern 6: Shopping & Consumption
        print("\n[6/7] Analyzing shopping patterns...")
        patterns['shopping'] = self._analyze_shopping()

        # Pattern 7: Age-Income Interactions
        print("\n[7/7] Analyzing age-income interactions...")
        patterns['age_income'] = self._analyze_age_income_interactions()

        print("\n" + "="*80)
        print("DEEP PATTERN DISCOVERY COMPLETE")
        print("="*80)

        return patterns

    def _get_age_groups(self) -> Dict[str, List[str]]:
        """Categorize classes by dominant age group."""

        age_groups = {
            'young': ['up-and-coming_urbanites', 'flourishing_capital', 'aspiring_communities'],
            'middle': ['prosperous_professionals', 'upmarket_families', 'metropolitan_surroundings'],
            'elderly': ['stable_seniors', 'constrained_penisoners', 'semi-rural_maturity']
        }

        return age_groups

    def _get_income_groups(self) -> Dict[str, List[str]]:
        """Categorize classes by income level."""

        income_groups = {
            'high': ['exclusive_addresses', 'flourishing_capital', 'prosperous_professionals'],
            'middle': ['upmarket_families', 'commuter-belt_wealth', 'settled_suburbia'],
            'low': ['limited_budgets', 'challenging_circumstances', 'cash-strapped_families']
        }

        return income_groups

    def _analyze_digital_by_age(self) -> Dict[str, Any]:
        """Analyze digital behaviors split by age group."""

        digital_questions = [
            'Internet Access',
            'Online activity',
            'Manage current account',
            'Manage savings account',
            'Internet',
            'Digital'
        ]

        age_groups = self._get_age_groups()
        results = {}

        for age_label, classes in age_groups.items():
            age_data = self.train_data[self.train_data['class_name'].isin(classes)]

            # Find digital-related questions
            digital_rows = age_data[
                age_data['Question'].str.contains('|'.join(digital_questions), case=False, na=False) |
                age_data['Category'].isin(['Digital', 'Internet', 'Financial Channel'])
            ]

            if len(digital_rows) > 0:
                digital_rows['Value'] = pd.to_numeric(digital_rows['Value'], errors='coerce')
                digital_rows = digital_rows.dropna(subset=['Value'])

                if len(digital_rows) > 0:
                    mean_digital = digital_rows['Value'].mean()

                    results[age_label] = {
                        'mean_adoption': float(mean_digital),
                        'sample_size': len(digital_rows),
                        'interpretation': self._interpret_digital(age_label, mean_digital)
                    }

        return results

    def _interpret_digital(self, age_label: str, mean_val: float) -> str:
        """Interpret digital adoption level."""

        if mean_val > 0.6:
            return f"{age_label.capitalize()} segments show HIGH digital adoption ({mean_val:.1%}). Expect 70-90% agreement on digital banking, online tools, tech comfort."
        elif mean_val > 0.4:
            return f"{age_label.capitalize()} segments show MODERATE digital adoption ({mean_val:.1%}). Expect 50-70% agreement on digital services."
        else:
            return f"{age_label.capitalize()} segments show LOW digital adoption ({mean_val:.1%}). Expect 20-40% agreement on digital behaviors."

    def _analyze_life_satisfaction(self) -> Dict[str, Any]:
        """Analyze life satisfaction patterns."""

        satisfaction_keywords = ['satisfied', 'contentment', 'happy', 'life overall']

        results = {}

        # By income group
        income_groups = self._get_income_groups()

        for income_label, classes in income_groups.items():
            income_data = self.train_data[self.train_data['class_name'].isin(classes)]

            # Find satisfaction questions
            sat_rows = income_data[
                income_data['Question'].str.contains('|'.join(satisfaction_keywords), case=False, na=False) |
                income_data['Category'].str.contains('Contentment', case=False, na=False)
            ]

            if len(sat_rows) > 0:
                sat_rows['Value'] = pd.to_numeric(sat_rows['Value'], errors='coerce')
                sat_rows = sat_rows.dropna(subset=['Value'])

                if len(sat_rows) > 0:
                    mean_sat = sat_rows['Value'].mean()

                    results[income_label] = {
                        'mean_satisfaction': float(mean_sat),
                        'sample_size': len(sat_rows),
                        'interpretation': self._interpret_satisfaction(income_label, mean_sat)
                    }

        return results

    def _interpret_satisfaction(self, income_label: str, mean_val: float) -> str:
        """Interpret satisfaction level."""

        if mean_val > 0.5:
            return f"{income_label.capitalize()}-income segments show HIGH life satisfaction ({mean_val:.1%}). Expect 50-70% agreement on contentment/happiness."
        elif mean_val > 0.35:
            return f"{income_label.capitalize()}-income segments show MODERATE life satisfaction ({mean_val:.1%}). Expect 35-50% agreement."
        else:
            return f"{income_label.capitalize()}-income segments show LOWER life satisfaction ({mean_val:.1%}). Expect 20-35% agreement."

    def _analyze_environmental(self) -> Dict[str, Any]:
        """Analyze environmental consciousness patterns."""

        env_categories = ['Environment', 'Lifestyle']
        env_keywords = ['environment', 'climate', 'recycle', 'sustainability', 'green', 'eco']

        results = {}

        # By age
        age_groups = self._get_age_groups()

        for age_label, classes in age_groups.items():
            age_data = self.train_data[self.train_data['class_name'].isin(classes)]

            env_rows = age_data[
                age_data['Category'].isin(env_categories) |
                age_data['Question'].str.contains('|'.join(env_keywords), case=False, na=False)
            ]

            if len(env_rows) > 0:
                env_rows['Value'] = pd.to_numeric(env_rows['Value'], errors='coerce')
                env_rows = env_rows.dropna(subset=['Value'])

                if len(env_rows) > 0:
                    mean_env = env_rows['Value'].mean()

                    results[age_label] = {
                        'mean_environmental': float(mean_env),
                        'sample_size': len(env_rows),
                        'interpretation': self._interpret_environmental(age_label, mean_env)
                    }

        return results

    def _interpret_environmental(self, age_label: str, mean_val: float) -> str:
        """Interpret environmental consciousness."""

        if mean_val > 0.4:
            return f"{age_label.capitalize()} segments show HIGHER environmental consciousness ({mean_val:.1%}). Expect 40-60% for values, 25-45% for actions."
        elif mean_val > 0.25:
            return f"{age_label.capitalize()} segments show MODERATE environmental consciousness ({mean_val:.1%}). Expect 25-40% agreement."
        else:
            return f"{age_label.capitalize()} segments show LOWER environmental focus ({mean_val:.1%}). Expect 15-30% agreement."

    def _analyze_financial(self) -> Dict[str, Any]:
        """Analyze financial behavior patterns."""

        financial_categories = ['Finance', 'Financial Channel']

        results = {}

        # Saving vs Borrowing
        save_keywords = ['save', 'savings', 'accumulate']
        borrow_keywords = ['borrow', 'debt', 'loan', 'credit']

        age_groups = self._get_age_groups()

        for age_label, classes in age_groups.items():
            age_data = self.train_data[self.train_data['class_name'].isin(classes)]

            # Savings behavior
            save_rows = age_data[
                age_data['Question'].str.contains('|'.join(save_keywords), case=False, na=False)
            ]

            borrow_rows = age_data[
                age_data['Question'].str.contains('|'.join(borrow_keywords), case=False, na=False)
            ]

            save_mean = 0
            borrow_mean = 0

            if len(save_rows) > 0:
                save_rows['Value'] = pd.to_numeric(save_rows['Value'], errors='coerce')
                save_rows = save_rows.dropna(subset=['Value'])
                if len(save_rows) > 0:
                    save_mean = save_rows['Value'].mean()

            if len(borrow_rows) > 0:
                borrow_rows['Value'] = pd.to_numeric(borrow_rows['Value'], errors='coerce')
                borrow_rows = borrow_rows.dropna(subset=['Value'])
                if len(borrow_rows) > 0:
                    borrow_mean = borrow_rows['Value'].mean()

            results[age_label] = {
                'savings_propensity': float(save_mean),
                'borrowing_aversion': float(borrow_mean),
                'interpretation': self._interpret_financial(age_label, save_mean, borrow_mean)
            }

        return results

    def _interpret_financial(self, age_label: str, save_mean: float, borrow_mean: float) -> str:
        """Interpret financial behavior."""

        if save_mean > 0.5:
            save_text = f"HIGH savings orientation ({save_mean:.1%})"
        elif save_mean > 0.3:
            save_text = f"MODERATE savings ({save_mean:.1%})"
        else:
            save_text = f"LOWER savings focus ({save_mean:.1%})"

        if borrow_mean > 0.4:
            borrow_text = f"LOWER borrowing aversion ({borrow_mean:.1%})"
        else:
            borrow_text = f"HIGHER borrowing aversion ({borrow_mean:.1%})"

        return f"{age_label.capitalize()}: {save_text}, {borrow_text}"

    def _analyze_shopping(self) -> Dict[str, Any]:
        """Analyze shopping and consumption patterns."""

        shopping_category = 'Shopping'

        results = {}

        income_groups = self._get_income_groups()

        for income_label, classes in income_groups.items():
            income_data = self.train_data[self.train_data['class_name'].isin(classes)]

            shop_rows = income_data[income_data['Category'] == shopping_category]

            if len(shop_rows) > 0:
                shop_rows['Value'] = pd.to_numeric(shop_rows['Value'], errors='coerce')
                shop_rows = shop_rows.dropna(subset=['Value'])

                if len(shop_rows) > 0:
                    mean_shop = shop_rows['Value'].mean()

                    results[income_label] = {
                        'mean_value': float(mean_shop),
                        'sample_size': len(shop_rows),
                        'interpretation': f"{income_label.capitalize()}-income: {mean_shop:.1%} shopping engagement"
                    }

        return results

    def _analyze_age_income_interactions(self) -> Dict[str, Any]:
        """Analyze how age and income interact."""

        age_groups = self._get_age_groups()
        income_groups = self._get_income_groups()

        # Find overlap
        young_high = set(age_groups['young']) & set(income_groups['high'])
        young_low = set(age_groups['young']) & set(income_groups['low'])
        elderly_high = set(age_groups['elderly']) & set(income_groups['high'])
        elderly_low = set(age_groups['elderly']) & set(income_groups['low'])

        return {
            'young_affluent': list(young_high),
            'young_constrained': list(young_low),
            'elderly_affluent': list(elderly_high),
            'elderly_constrained': list(elderly_low),
            'interpretation': {
                'young_affluent': "Highest digital adoption, environmental values, financial confidence",
                'young_constrained': "High digital, moderate environmental, financial stress impacts satisfaction",
                'elderly_affluent': "Lower digital, moderate environmental, high satisfaction",
                'elderly_constrained': "Low digital, lower environmental, resilience despite constraints"
            }
        }

    def save_patterns(self, output_file: Path):
        """Save discovered patterns."""
        patterns = self.discover_deep_patterns()

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, indent=2)

        print(f"\n[OK] Deep patterns saved to: {output_file}")
        return patterns


if __name__ == "__main__":
    from .data_prep import ACORNDataLoader

    loader = ACORNDataLoader(Path("demographic_runs_ACORN"))
    agent = DeepPatternAgent(loader)

    patterns = agent.discover_deep_patterns()
    agent.save_patterns(Path("agent_estimator/prompt_agent/output/deep_patterns.json"))

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(json.dumps({
        k: f"{len(v)} patterns" if isinstance(v, dict) else str(v)
        for k, v in patterns.items()
    }, indent=2))
