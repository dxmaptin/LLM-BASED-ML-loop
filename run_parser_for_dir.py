import argparse
from pathlib import Path
from typing import Dict, List
from agent_estimator.orchestrator.runner import DataParsingAgent
from agent_estimator.ir_agent.parser import _bundle_inputs


def write_context_summary(
    concepts: List[str],
    bundles: Dict[str, Dict[str, any]],
    output_path: Path,
) -> None:
    """Write context summary in the same format as FRESCO demographic_runs."""
    records: List[str] = []
    for concept in concepts:
        bundle = bundles[concept]
        records.append(f"### Concept: {concept}")
        records.append(f"Selection notes: {bundle.get('selection_notes', 'n/a')}")
        types_present = bundle.get("types_present", [])
        records.append(
            "Types present: " + (", ".join(types_present) if types_present else "(none)")
        )
        records.append("")
        top_sources = bundle.get("top_sources", [])
        if top_sources:
            records.append("Top sources:")
            for src in top_sources:
                if src.get("source_type") == "quant":
                    value_str = f"value={src['value']:.4f}" if src.get("value") is not None else ""
                    records.append(
                        f"- [quant] {src.get('file','?')} | {src.get('question','')} | "
                        f"{src.get('option','')} {value_str} | relevance={src.get('relevance',0):.2f}"
                    )
                else:
                    excerpt = src.get("excerpt", "")
                    records.append(
                        f"- [qual] {src.get('file','?')} | relevance={src.get('relevance',0):.2f} | {excerpt}"
                    )
            records.append("")
        records.append("Quantitative summary:")
        records.append(bundle.get("quant_summary", "") or "(none)")
        records.append("")
        records.append("Qualitative summary:")
        records.append(bundle.get("textual_summary", "") or "(none)")
        records.append("")
        hints = bundle.get("weight_hints", [])
        if hints:
            records.append("Weight hints:")
            records.extend(f"- {hint}" for hint in hints)
        else:
            records.append("Weight hints: (none)")
        records.append("\n")

    output_path.write_text("\n".join(records), encoding="utf-8")

parser = argparse.ArgumentParser()
parser.add_argument('--base-dir', type=Path, required=True)
parser.add_argument('--output', type=Path, default=None)
args = parser.parse_args()

_bundle_inputs.cache_clear()
agent = DataParsingAgent(args.base_dir)
concepts = agent.list_concepts()

bundles = {}
for concept in concepts:
    bundles[concept] = agent.prepare_concept_bundle(concept)

if args.output is None:
    output_path = args.base_dir / 'context_summary_generated.txt'
else:
    output_path = args.output
write_context_summary(concepts, bundles, output_path)
print(f'Context summary written to {output_path}')
