"""
Cross-Class Training Setup for Class-Specific Prompts

APPROACH:
1. Select TRAINING classes (e.g., 3 poor classes: cash-strapped_families,
   challenging_circumstances, limited_budgets)
2. Select TARGET class (e.g., hard-up_households) - HOLDOUT, never seen in training
3. Iteratively improve class-specific prompt on training classes until R² > 0.8
4. Test final prompt on target class

This ensures:
- No data leakage (target class unseen)
- Transfer learning (related demographics)
- Proper train/test split
- Same 10 questions used throughout (fair comparison)
"""

import pandas as pd
from pathlib import Path

# The 10 questions we'll use across all classes
QUESTIONS = [
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
]

# Experiment configurations
EXPERIMENTS = {
    "poor_classes": {
        "description": "Train on poor classes, test on different poor class",
        "training_classes": [
            "cash-strapped_families",
            "challenging_circumstances",
            "limited_budgets"
        ],
        "target_class": "hard-up_households",
        "demographic_profile": "poor/struggling"
    },
    "senior_classes": {
        "description": "Train on senior classes, test on different senior class",
        "training_classes": [
            "stable_seniors",
            "mature_success",
            "semi-rural_maturity"
        ],
        "target_class": "constrained_penisoners",
        "demographic_profile": "retired/senior"
    },
    "professional_classes": {
        "description": "Train on professional classes, test on different professional class",
        "training_classes": [
            "prosperous_professionals",
            "flourishing_capital",
            "commuter-belt_wealth"
        ],
        "target_class": "upmarket_families",
        "demographic_profile": "affluent professionals"
    }
}

def verify_classes_exist(classes):
    """Verify all classes have data"""
    base_dir = Path("demographic_runs_ACORN")

    for class_name in classes:
        class_dir = base_dir / class_name
        if not class_dir.exists():
            return False, f"Missing directory: {class_name}"

        # Check for required files
        flattened = class_dir / "Flattened Data Inputs" / f"ACORN_{class_name}.csv"
        if not flattened.exists():
            return False, f"Missing flattened data for: {class_name}"

    return True, "All classes verified"

def verify_ground_truth(classes):
    """Verify ground truth exists for all classes"""
    df = pd.read_csv("ACORN_ground_truth_named.csv")

    # Normalize class names in ground truth
    gt_classes = set()
    for _, row in df.iterrows():
        class_name = row['Class'].lower().replace(' ', '_')
        class_name_hyphen = row['Class'].lower().replace(' ', '-')
        gt_classes.add(class_name)
        gt_classes.add(class_name_hyphen)

    missing = []
    for class_name in classes:
        if class_name not in gt_classes:
            missing.append(class_name)

    if missing:
        return False, f"Missing ground truth for: {missing}"

    return True, "All ground truth verified"

def main():
    print("="*80)
    print("CROSS-CLASS TRAINING SETUP")
    print("="*80)
    print("\nVerifying experiment configurations...")
    print("="*80)

    for exp_name, exp_config in EXPERIMENTS.items():
        print(f"\n{exp_name.upper()}")
        print("-"*80)
        print(f"Description: {exp_config['description']}")
        print(f"Profile: {exp_config['demographic_profile']}")
        print(f"\nTraining classes:")
        for c in exp_config['training_classes']:
            print(f"  - {c}")
        print(f"\nTarget class (HOLDOUT):")
        print(f"  - {exp_config['target_class']}")

        # Verify all classes
        all_classes = exp_config['training_classes'] + [exp_config['target_class']]

        # Check directories
        exists, msg = verify_classes_exist(all_classes)
        if exists:
            print(f"\n✓ All class directories exist")
        else:
            print(f"\n✗ ERROR: {msg}")
            continue

        # Check ground truth
        has_gt, msg = verify_ground_truth(all_classes)
        if has_gt:
            print(f"✓ All ground truth data exists")
        else:
            print(f"✗ ERROR: {msg}")
            continue

        print(f"\n✓ Configuration valid!")

    print("\n" + "="*80)
    print("RECOMMENDED EXPERIMENT")
    print("="*80)
    print("""
Recommendation: Start with "poor_classes" experiment

Why:
1. Current general prompt performs worst on poor classes (R²=0.29-0.34)
2. Biggest opportunity for improvement
3. Will test if class-specific prompts can overcome general prompt limitations

Workflow:
1. Create class-specific prompt starting from general prompt v9_iter4
2. Test on training classes (cash-strapped_families, challenging_circumstances, limited_budgets)
3. Iterate until average R² > 0.8 on training classes
4. Test final prompt on target class (hard-up_households) - NEVER seen during training
5. Compare to general prompt baseline (R²=0.34 for hard-up_households)

Success criteria:
- Training classes: R² > 0.8 (shows prompt works for poor demographics)
- Target class: R² > 0.6 (shows generalization to unseen poor class)
- No data leakage (verify IR provides only demographics)

Would you like me to proceed with the "poor_classes" experiment?
    """)

if __name__ == "__main__":
    main()
