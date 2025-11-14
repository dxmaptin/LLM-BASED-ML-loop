"""
Complete Prompt Discovery Pipeline

Orchestrates the two-agent system to generate prompts:
1. Agent 1: Discovers general patterns across all demographics
2. Agent 2: Discovers class-specific patterns for each demographic
3. Generates prompt files from discovered patterns
"""

import json
from pathlib import Path
from datetime import datetime

from agent_estimator.prompt_agent.data_prep import ACORNDataLoader
from agent_estimator.prompt_agent.general_agent import GeneralPatternAgent
from agent_estimator.prompt_agent.class_agent import ClassSpecificAgent
from agent_estimator.prompt_agent.prompt_generator import PromptGenerator


def run_full_pipeline(
    acorn_dir: Path,
    output_base_dir: Path,
    model: str = "gpt-5"
):
    """
    Run the complete prompt discovery pipeline.

    Args:
        acorn_dir: Path to demographic_runs_ACORN directory
        output_base_dir: Base directory for all outputs
        model: LLM model to use
    """
    print("\n" + "="*80)
    print("PROMPT DISCOVERY PIPELINE")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Model: {model}")
    print(f"ACORN data: {acorn_dir}")
    print(f"Output directory: {output_base_dir}")
    print("="*80)

    # Create output directories
    output_base_dir.mkdir(parents=True, exist_ok=True)
    patterns_dir = output_base_dir / "patterns"
    patterns_dir.mkdir(exist_ok=True)
    prompts_dir = output_base_dir / "prompts"
    prompts_dir.mkdir(exist_ok=True)

    # Initialize data loader
    print("\n" + "="*80)
    print("STEP 1: DATA PREPARATION")
    print("="*80)
    loader = ACORNDataLoader(acorn_dir)
    stats = loader.analyze_dataset_stats()
    print(f"\nDataset Statistics:")
    print(json.dumps(stats, indent=2))

    # Save stats
    with open(patterns_dir / "dataset_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)

    # Run Agent 1: General Pattern Discovery
    print("\n" + "="*80)
    print("STEP 2: AGENT 1 - GENERAL PATTERN DISCOVERY")
    print("="*80)
    agent1 = GeneralPatternAgent(loader, model=model)
    general_patterns = agent1.discover_patterns()

    # Save general patterns
    general_patterns_file = patterns_dir / "general_patterns.json"
    agent1.save_patterns(general_patterns_file)
    print(f"\n✓ General patterns saved to: {general_patterns_file}")

    # Run Agent 2: Class-Specific Pattern Discovery
    print("\n" + "="*80)
    print("STEP 3: AGENT 2 - CLASS-SPECIFIC PATTERN DISCOVERY")
    print("="*80)
    agent2 = ClassSpecificAgent(loader, model=model)
    class_patterns_dir = patterns_dir / "class_specific"
    all_class_patterns = agent2.discover_all_classes(output_dir=class_patterns_dir)

    # Save combined class patterns
    all_class_file = patterns_dir / "all_class_patterns.json"
    with open(all_class_file, 'w', encoding='utf-8') as f:
        json.dump(all_class_patterns, f, indent=2)
    print(f"\n✓ All class patterns saved to: {all_class_file}")

    # Generate Prompts
    print("\n" + "="*80)
    print("STEP 4: PROMPT GENERATION")
    print("="*80)
    generator = PromptGenerator(model=model)
    generator.generate_all_prompts(
        general_patterns=general_patterns,
        all_class_patterns=all_class_patterns,
        output_dir=prompts_dir
    )

    # Copy prompts to estimator agent directory
    print("\n" + "="*80)
    print("STEP 5: DEPLOYING PROMPTS TO ESTIMATOR")
    print("="*80)

    estimator_prompts_dir = Path("agent_estimator/estimator_agent/prompts")
    estimator_prompts_dir.mkdir(parents=True, exist_ok=True)

    # Copy general prompt
    general_src = prompts_dir / "general_system_prompt.txt"
    general_dst = estimator_prompts_dir / "general_system_prompt.txt"

    if general_src.exists():
        import shutil
        shutil.copy2(general_src, general_dst)
        print(f"✓ Deployed general prompt to: {general_dst}")

    # Copy class-specific prompts
    demographic_src_dir = prompts_dir / "demographic_guidance"
    demographic_dst_dir = estimator_prompts_dir / "demographic_guidance"
    demographic_dst_dir.mkdir(exist_ok=True)

    if demographic_src_dir.exists():
        import shutil
        for txt_file in demographic_src_dir.glob("*.txt"):
            dst_file = demographic_dst_dir / txt_file.name
            shutil.copy2(txt_file, dst_file)
        print(f"✓ Deployed {len(list(demographic_src_dir.glob('*.txt')))} class-specific prompts to: {demographic_dst_dir}")

    # Summary
    print("\n" + "="*80)
    print("PIPELINE COMPLETE")
    print("="*80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nGenerated Outputs:")
    print(f"  1. Dataset statistics: {patterns_dir / 'dataset_stats.json'}")
    print(f"  2. General patterns: {general_patterns_file}")
    print(f"  3. Class-specific patterns: {class_patterns_dir}/")
    print(f"  4. General prompt: {general_dst}")
    print(f"  5. Class-specific prompts: {demographic_dst_dir}/")
    print("\nNext Steps:")
    print("  1. Review generated prompts")
    print("  2. Run predictions on holdout test set")
    print("  3. Evaluate performance")
    print("="*80)

    return {
        "general_patterns": general_patterns,
        "class_patterns": all_class_patterns,
        "stats": stats
    }


if __name__ == "__main__":
    # Run the pipeline
    results = run_full_pipeline(
        acorn_dir=Path("demographic_runs_ACORN"),
        output_base_dir=Path("agent_estimator/prompt_agent/output"),
        model="gpt-5"
    )

    print("\n✓ Pipeline completed successfully!")
