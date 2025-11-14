#!/usr/bin/env python3
"""
Regenerate Young Dependents context with LOO filtering enabled.
This will exclude exact matches from the IR agent extraction.
"""

import csv
from pathlib import Path
from agent_estimator.ir_agent.parser import DataParsingAgent

def write_context_summary(concepts: list, bundles: dict, output_path: Path) -> None:
    """Write formatted context summary to file."""
    with output_path.open("w", encoding="utf-8") as f:
        f.write("=" * 100 + "\n")
        f.write("CONTEXT SUMMARY WITH LOO FILTERING (Exact matches excluded)\n")
        f.write("=" * 100 + "\n\n")

        for idx, concept in enumerate(concepts, 1):
            bundle = bundles[concept]
            f.write(f"\n{'=' * 100}\n")
            f.write(f"CONCEPT {idx}/{len(concepts)}: {concept}\n")
            f.write(f"{'=' * 100}\n\n")

            # Quantitative summary
            f.write("QUANTITATIVE SUMMARY:\n")
            f.write("-" * 80 + "\n")
            quant_summary = bundle.get("quant_summary", "")
            if quant_summary:
                f.write(quant_summary + "\n")
            else:
                f.write("No quantitative data available.\n")
            f.write("\n")

            # Textual summary
            f.write("TEXTUAL SUMMARY:\n")
            f.write("-" * 80 + "\n")
            textual_summary = bundle.get("textual_summary", "")
            if textual_summary:
                f.write(textual_summary + "\n")
            else:
                f.write("No textual data available.\n")
            f.write("\n")

            # Metadata
            proximal = bundle.get("proximal_topline")
            concept_type = bundle.get("concept_type", "N/A")
            f.write("METADATA:\n")
            f.write("-" * 80 + "\n")
            f.write(f"Concept Type: {concept_type}\n")
            if proximal is not None:
                f.write(f"Proximal Topline: {proximal:.4f}\n")
            else:
                f.write("Proximal Topline: NOT FOUND (expected for LOO filtering)\n")
            f.write("\n")

def main():
    # Paths
    demographic_label = "Young Dependents"
    questions_path = Path("Handpicked_experiments_10.csv")
    base_dir = Path("demographic_runs/young_dependents/handpicked_context_workspace")
    output_path = Path("demographic_runs/young_dependents/context_summary_LOO_filtered.txt")

    print("=" * 100)
    print("REGENERATING YOUNG DEPENDENTS CONTEXT WITH LOO FILTERING")
    print("=" * 100)
    print(f"Base directory: {base_dir}")
    print(f"Output: {output_path}")
    print()
    print("LOO FILTERING ENABLED:")
    print("+ Exact keyword matches WILL BE EXCLUDED")
    print("+ Proximal toplines should NOT appear in context")
    print("+ This tests true prediction ability (not format conversion)")
    print("=" * 100)
    print()

    # Load concepts from CSV
    concepts = []
    with questions_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle line breaks in demographic names
            demo = row.get("Demographic", "").replace("\n", " ").strip()
            demo_normalized = " ".join(demo.split())  # Normalize whitespace
            if demo_normalized == demographic_label:
                # Use "Concept" column which has full question text
                concept = row.get("Concept", "").strip()
                if concept:
                    concepts.append(concept)

    print(f"Found {len(concepts)} concepts for {demographic_label}:")
    for i, concept in enumerate(concepts, 1):
        print(f"  {i}. {concept[:80]}...")
    print()

    # Clear cache to ensure we use updated QUAL_MAX_CHARS
    from agent_estimator.ir_agent.parser import _bundle_inputs
    _bundle_inputs.cache_clear()

    # Initialize IR agent
    print("Initializing IR agent...")
    agent = DataParsingAgent(base_dir)
    print("IR agent initialized.\n")

    # Generate bundles with LOO filtering
    print("Extracting evidence bundles with LOO filtering enabled...")
    bundles = {}
    for idx, concept in enumerate(concepts, 1):
        print(f"  [{idx}/{len(concepts)}] Extracting: {concept[:60]}...")
        # exclude_exact_match=True is the default, so LOO filtering is enabled
        bundle = agent.prepare_concept_bundle(concept, exclude_exact_match=True)
        bundles[concept] = bundle

        # Check if proximal topline was found (shouldn't be with LOO)
        proximal = bundle.get("proximal_topline")
        if proximal is not None:
            print(f"    WARNING: Proximal topline found ({proximal:.4f}) - LOO may not be working!")
        else:
            print(f"    OK: No proximal topline (expected with LOO)")

    print()

    # Write context summary
    print(f"Writing context summary to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_context_summary(concepts, bundles, output_path)
    print("Done!")
    print()

    print("=" * 100)
    print("VERIFICATION")
    print("=" * 100)
    print(f"Context file created: {output_path}")
    print()
    print("NEXT STEPS:")
    print("1. Review the context file to verify no exact matches appear")
    print("2. Check that proximal toplines are NOT found (expected with LOO)")
    print("3. Run estimation experiments with this new context")
    print("=" * 100)

if __name__ == "__main__":
    main()
