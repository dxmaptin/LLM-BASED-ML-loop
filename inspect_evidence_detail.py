"""
Inspect the actual evidence being provided for one test question.
"""

from pathlib import Path
from agent_estimator.ir_agent.parser import DataParsingAgent

def main():
    class_name = "exclusive_addresses"
    base_dir = Path(f"demographic_runs_ACORN/{class_name}")
    parser = DataParsingAgent(base_dir)

    test_question = "I don't like the idea of being in debt"

    print("="*80)
    print(f"INSPECTING EVIDENCE FOR: {test_question}")
    print("="*80)

    evidence = parser.prepare_concept_bundle(test_question, exclude_exact_match=True)

    print("\nEvidence keys:", evidence.keys())

    # Check quantitative evidence
    if 'quantitative_evidence' in evidence:
        quant = evidence['quantitative_evidence']
        print(f"\nQuantitative evidence items: {len(quant)}")

        if len(quant) > 0:
            print("\nTop 5 quantitative evidence items:")
            for i, item in enumerate(quant[:5]):
                print(f"\n[{i+1}]")
                print(f"  Question: {item.get('question', 'N/A')}")
                print(f"  Relevance: {item.get('relevance', 'N/A')}")
                print(f"  Topline: {item.get('topline_percent', 'N/A')}%")

                if 'distribution' in item:
                    dist = item['distribution']
                    print(f"  Distribution: SA={dist.get('strongly_agree')}% A={dist.get('slightly_agree')}%")

    # Check qualitative evidence
    if 'qualitative_insights' in evidence:
        qual = evidence['qualitative_insights']
        print(f"\nQualitative evidence items: {len(qual)}")

        if len(qual) > 0:
            print("\nFirst qualitative insight:")
            print(f"  {qual[0][:300]}...")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
