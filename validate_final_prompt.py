"""
Final validation of the automated prompt generation system.
Runs a quick sanity check to ensure everything is working.
"""

import json
from pathlib import Path
from agent_estimator.estimator_agent.estimator import EstimatorAgent
from agent_estimator.ir_agent.parser import DataParsingAgent


def validate_prompt_system():
    """Run quick validation of the prompt system."""

    print("="*80)
    print("FINAL VALIDATION: Automated Prompt Generation System")
    print("="*80)

    # Check that prompt file exists
    prompt_file = Path("agent_estimator/estimator_agent/prompts/general_system_prompt.txt")
    if not prompt_file.exists():
        print("\nERROR: Prompt file not found!")
        return False

    print(f"\n[OK] Prompt file exists: {prompt_file}")
    prompt_text = prompt_file.read_text(encoding='utf-8')
    print(f"[OK] Prompt length: {len(prompt_text)} characters")

    # Check for key sections
    required_sections = [
        "DECISION WORKFLOW",
        "CONCEPT TYPE ALLOCATION",
        "LEARNED CONCEPT-SPECIFIC CORRECTIONS",
        "DEMOGRAPHIC CALIBRATIONS",
        "CRITICAL RULES",
        "EVIDENCE HIERARCHY"
    ]

    print("\n" + "-"*80)
    print("Checking prompt structure...")
    print("-"*80)

    missing = []
    for section in required_sections:
        if section in prompt_text:
            print(f"✓ {section}")
        else:
            print(f"✗ {section} - MISSING!")
            missing.append(section)

    if missing:
        print(f"\nERROR: Missing sections: {missing}")
        return False

    # Test that estimator can load and use the prompt
    print("\n" + "-"*80)
    print("Testing estimator initialization...")
    print("-"*80)

    try:
        estimator = EstimatorAgent(model="gpt-4o")
        print("✓ EstimatorAgent initialized successfully")
    except Exception as e:
        print(f"✗ ERROR initializing EstimatorAgent: {e}")
        return False

    # Test that parser can be initialized
    print("\n" + "-"*80)
    print("Testing parser initialization...")
    print("-"*80)

    try:
        parser = DataParsingAgent(class_name="exclusive_addresses")
        print("✓ DataParsingAgent initialized successfully")
    except Exception as e:
        print(f"✗ ERROR initializing ParserAgent: {e}")
        return False

    # Run a quick prediction test on one question
    print("\n" + "-"*80)
    print("Running sample prediction...")
    print("-"*80)

    test_concept = "I don't like the idea of being in debt"
    print(f"Concept: {test_concept}")

    try:
        # Get evidence using IR agent
        evidence = parser.prepare_concept_bundle(test_concept, exclude_exact_match=True)
        print(f"✓ Evidence retrieved: {len(str(evidence))} chars")

        # Run estimation
        result = estimator.estimate(
            concept=test_concept,
            evidence=evidence,
            runs=1,
            iteration=1,
            feedback=""
        )

        # Check result structure
        if 'distribution' not in result:
            print("✗ ERROR: No 'distribution' in result")
            return False

        dist = result['distribution']
        required_keys = ['strongly_agree', 'slightly_agree', 'neither_agree_nor_disagree',
                        'slightly_disagree', 'strongly_disagree']

        for key in required_keys:
            if key not in dist:
                print(f"✗ ERROR: Missing key '{key}' in distribution")
                return False

        # Calculate topline
        topline = dist['strongly_agree'] + dist['slightly_agree']

        print(f"✓ Prediction successful")
        print(f"  Distribution: SA={dist['strongly_agree']}%, A={dist['slightly_agree']}%, "
              f"N={dist['neither_agree_nor_disagree']}%, "
              f"D={dist['slightly_disagree']}%, SD={dist['strongly_disagree']}%")
        print(f"  Topline: {topline:.1f}%")
        print(f"  Confidence: {result.get('confidence', 'N/A')}")

        # Sanity check: topline should be reasonable (between 20% and 70% for this question)
        if 20 <= topline <= 70:
            print(f"✓ Topline is in reasonable range (20-70%)")
        else:
            print(f"⚠ WARNING: Topline seems unusual: {topline:.1f}%")
            print(f"  Expected range: 20-70% for debt aversion question")

    except Exception as e:
        print(f"✗ ERROR running prediction: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Check that key patterns are encoded
    print("\n" + "-"*80)
    print("Checking learned patterns...")
    print("-"*80)

    key_patterns = [
        "Healthy eating",
        "Environmental sustainability",
        "Fuel consumption",
        "Good at managing money",
        "Like to use cash",
        "Retirement",
        "debt",
        "Switching utilities",
        "Cut down gas",
        "Well insured"
    ]

    found_patterns = sum(1 for pattern in key_patterns if pattern.lower() in prompt_text.lower())
    print(f"✓ Found {found_patterns}/{len(key_patterns)} key patterns in prompt")

    if found_patterns < 8:
        print("⚠ WARNING: Some learned patterns may be missing")

    # Final summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print("✓ Prompt file exists and is properly structured")
    print("✓ All required sections present")
    print("✓ EstimatorAgent can load and use prompt")
    print("✓ ParserAgent can retrieve evidence")
    print("✓ Sample prediction runs successfully")
    print(f"✓ {found_patterns}/10 learned patterns encoded")
    print("\n" + "="*80)
    print("STATUS: ✓ SYSTEM VALIDATED - READY FOR USE")
    print("="*80)

    return True


if __name__ == "__main__":
    success = validate_prompt_system()
    exit(0 if success else 1)
