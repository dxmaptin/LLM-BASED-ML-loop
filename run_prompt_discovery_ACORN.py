"""
Run Prompt Agent to discover patterns and generate prompts for ACORN dataset.

This script:
1. Analyzes all 22 ACORN classes
2. Discovers demographic and concept patterns
3. Generates baseline general prompt
4. Generates 22 class-specific prompts
"""

from pathlib import Path
from agent_estimator.prompt_agent.analyzer import run_prompt_discovery

# Configuration
DATASET_DIR = Path(__file__).parent / "demographic_runs_ACORN"
OUTPUT_DIR = Path(__file__).parent / "ACORN_prompt_analysis"
MODEL = "gpt-4o"  # Use GPT-4o (GPT-5 not yet available)

print("="*70)
print("PROMPT DISCOVERY FOR ACORN DATASET")
print("="*70)
print(f"\nDataset: {DATASET_DIR}")
print(f"Output: {OUTPUT_DIR}")
print(f"Model: {MODEL}")
print("\nThis will:")
print("  1. Analyze quantitative data (ACORN Flattened Data)")
print("  2. Analyze qualitative data (Pen portraits)")
print("  3. Discover demographic patterns (income, age, lifestyle)")
print("  4. Discover concept-type patterns (attitude, behavior, identity)")
print("  5. Generate baseline GENERAL prompt")
print("  6. Generate 22 class-specific prompts")
print("\nEstimated time: 5-10 minutes")
print("="*70)

print("\nStarting discovery...")

# Run discovery
results, class_prompts = run_prompt_discovery(
    dataset_dir=DATASET_DIR,
    output_dir=OUTPUT_DIR,
    model=MODEL
)

# Display summary
print("\n" + "="*70)
print("DISCOVERY COMPLETE - SUMMARY")
print("="*70)

print("\n1. DEMOGRAPHIC PATTERNS DISCOVERED:")
if "demographic_patterns" in results:
    patterns = results["demographic_patterns"]
    if "income_patterns" in patterns:
        print("\n   Income Patterns:")
        for key, val in patterns["income_patterns"].items():
            print(f"     - {key}: {str(val)[:80]}...")

    if "age_patterns" in patterns:
        print("\n   Age Patterns:")
        for key, val in patterns["age_patterns"].items():
            print(f"     - {key}: {str(val)[:80]}...")

print("\n2. CONCEPT PATTERNS DISCOVERED:")
if "concept_patterns" in results:
    patterns = results["concept_patterns"]
    for key in ["attitude_pattern", "behavior_low_friction", "behavior_high_friction", "identity_pattern"]:
        if key in patterns:
            print(f"   - {key}: Found")

print(f"\n3. BASELINE PROMPT GENERATED:")
prompt_length = len(results.get("generated_prompt", ""))
print(f"   Length: {prompt_length} characters")
print(f"   Preview: {results.get('generated_prompt', '')[:200]}...")

print(f"\n4. CLASS-SPECIFIC PROMPTS:")
print(f"   Generated: {len(class_prompts)} classes")
for class_name in list(class_prompts.keys())[:5]:
    print(f"     - {class_name}")
print(f"     ... and {len(class_prompts) - 5} more")

print("\n" + "="*70)
print("FILES CREATED:")
print("="*70)
print(f"  {OUTPUT_DIR}/analysis_results.json")
print(f"  {OUTPUT_DIR}/generated_baseline_prompt.txt")
print(f"  {OUTPUT_DIR}/class_specific_prompts.json")

print("\n" + "="*70)
print("NEXT STEPS:")
print("="*70)
print("1. Review generated_baseline_prompt.txt")
print("2. Integrate into agent_estimator/estimator_agent/prompts.py")
print("3. Review class_specific_prompts.json")
print("4. Add selected class prompts to DEMOGRAPHIC_PROMPTS dict")
print("5. Run predictions on ACORN classes")
print("6. Evaluate and iterate (RL loop)")

print("\n" + "="*70)
