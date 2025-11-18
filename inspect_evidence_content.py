"""
Inspect the actual content of evidence.
"""

from pathlib import Path
from agent_estimator.ir_agent.parser import DataParsingAgent
import json

def main():
    class_name = "exclusive_addresses"
    base_dir = Path(f"demographic_runs_ACORN/{class_name}")
    parser = DataParsingAgent(base_dir)

    test_question = "Healthy Eating"

    print("="*80)
    print(f"INSPECTING EVIDENCE FOR: {test_question}")
    print("="*80)

    evidence = parser.prepare_concept_bundle(test_question, exclude_exact_match=True)

    # Print all evidence fields
    for key, value in evidence.items():
        print(f"\n{key}:")
        print("-"*80)

        if isinstance(value, str):
            # Truncate long strings
            if len(value) > 500:
                print(value[:500] + "...")
            else:
                print(value)
        elif isinstance(value, (list, dict)):
            print(json.dumps(value, indent=2)[:1000])
        else:
            print(value)

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
