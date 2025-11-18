"""
Inspect what evidence the IR agent is providing.
Check if the evidence already contains the answer.
"""

from agent_estimator.ir_agent.parser import DataParsingAgent
import json

HOLDOUT_QUESTIONS = [
    "I think brands should consider environmental sustainability when putting on events",
    "I don't like the idea of being in debt",
    "Healthy Eating"
]

def main():
    print("="*80)
    print("INSPECTING IR AGENT EVIDENCE")
    print("="*80)

    parser = DataParsingAgent(class_name="exclusive_addresses")

    for question in HOLDOUT_QUESTIONS:
        print(f"\n" + "="*80)
        print(f"Question: {question}")
        print("="*80)

        # Get evidence
        evidence = parser.prepare_concept_bundle(question, exclude_exact_match=True)

        print(f"\nEvidence keys: {evidence.keys()}")
        print(f"\nEvidence length: {len(str(evidence))} chars")

        # Check quantitative evidence
        if 'quantitative_evidence' in evidence:
            quant = evidence['quantitative_evidence']
            print(f"\nQuantitative evidence count: {len(quant) if isinstance(quant, list) else 'N/A'}")

            if isinstance(quant, list) and len(quant) > 0:
                print("\nTop 3 quantitative evidence items:")
                for i, item in enumerate(quant[:3]):
                    print(f"\n[{i+1}] Relevance: {item.get('relevance', 'N/A')}")
                    print(f"    Question: {item.get('question', 'N/A')[:100]}")
                    print(f"    Topline: {item.get('topline_percent', 'N/A')}")

                    # Check if this is the exact question
                    if 'distribution' in item:
                        dist = item['distribution']
                        print(f"    Distribution: SA={dist.get('strongly_agree')}%, A={dist.get('slightly_agree')}%")

        # Check qualitative evidence
        if 'qualitative_insights' in evidence:
            qual = evidence['qualitative_insights']
            print(f"\nQualitative evidence count: {len(qual) if isinstance(qual, list) else 'N/A'}")

            if isinstance(qual, list) and len(qual) > 0:
                print("\nTop qualitative insight:")
                print(f"  {qual[0][:200]}")

        print("\n" + "-"*80)


if __name__ == "__main__":
    main()
