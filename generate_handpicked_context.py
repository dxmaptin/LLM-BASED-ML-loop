#!/usr/bin/env python3
"""Generate context summary for handpicked concepts within a demographic run."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from agent_estimator.ir_agent.parser import DataParsingAgent, _bundle_inputs
from agent_estimator.common.config import FLATTENED_DIR, TEXTUAL_DIR


def _normalise_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _slugify(name: str) -> str:
    slug = re.sub(r"[^\w]+", "_", name.strip().lower())
    return re.sub(r"_+", "_", slug).strip("_") or "segment"


def _extract_concepts(csv_path: Path, demographic: str) -> List[Dict[str, str]]:
    df = pd.read_csv(csv_path)
    if "Concept" not in df.columns:
        raise ValueError("Expected a 'Concept' column in the handpicked CSV.")
    demo_norm = df["Demographic"].astype(str).map(_normalise_whitespace)
    subset = df.loc[demo_norm == demographic].copy()

    if subset.empty:
        raise ValueError(f"No rows found for demographic '{demographic}'.")

    subset["Concept"] = subset["Concept"].astype(str).str.strip()
    subset["Question"] = subset["Question"].astype(str).str.strip()
    subset["Answer"] = subset["Answer"].astype(str).str.strip()

    seen: set[str] = set()
    records: List[Dict[str, str]] = []
    for _, row in subset.iterrows():
        concept = row["Concept"] or f"{row['Question']} - {row['Answer']}"
        if concept in seen:
            continue
        seen.add(concept)
        records.append(
            {
                "concept": concept,
                "question": row["Question"],
                "answer": row["Answer"],
            }
        )
    if not records:
        raise ValueError(f"No concepts found for demographic '{demographic}'.")
    return records


def _write_concepts_file(path: Path, records: List[Dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(f"{record['concept']}\n")


def _format_context_line(bundle: Dict[str, Any], label: str) -> List[str]:
    section = bundle.get(label, "")
    text = section if isinstance(section, str) else str(section)
    return text.splitlines() if text else ["(none)"]


def _write_context_summary(
    records: List[Dict[str, str]],
    bundles: Dict[str, Dict[str, Any]],
    output_path: Path,
) -> None:
    lines: List[str] = []
    for record in records:
        concept = record["concept"]
        bundle = bundles[concept]
        types_present = ", ".join(bundle.get("types_present", [])) or "(none)"
        lines.append(f"### Concept: {concept}")
        lines.append(f"Selection notes: {bundle.get('selection_notes', 'n/a')}")
        lines.append(f"Types present: {types_present}")
        lines.append("")
        lines.append("Top sources:")
        top_sources = bundle.get("top_sources", [])
        if top_sources:
            for src in top_sources:
                if src.get("source_type") == "quant":
                    value = src.get("value")
                    value_str = f"value={value:.4f}" if isinstance(value, (int, float)) else ""
                    lines.append(
                        f"- [quant] {src.get('file','?')} | {src.get('question','')} | "
                        f"{src.get('option','')} {value_str} | relevance={src.get('relevance',0):.2f}"
                    )
                else:
                    excerpt = src.get("excerpt", "")
                    lines.append(
                        f"- [qual] {src.get('file','?')} | relevance={src.get('relevance',0):.2f} | {excerpt}"
                    )
        else:
            lines.append("(none)")
        lines.append("")
        lines.append("Quantitative summary:")
        lines.extend(_format_context_line(bundle, "quant_summary"))
        lines.append("")
        lines.append("Qualitative summary:")
        lines.extend(_format_context_line(bundle, "textual_summary"))
        lines.append("")
        hints = bundle.get("weight_hints", [])
        if hints:
            lines.append("Weight hints:")
            for hint in hints:
                lines.append(f"- {hint}")
        else:
            lines.append("Weight hints: (none)")
        lines.append("")
    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def generate_context_summary(
    questions_csv: Path,
    demographic_label: str,
    run_dir: Path,
    output_filename: str,
) -> Path:
    records = _extract_concepts(questions_csv, demographic_label)
    run_dir.mkdir(parents=True, exist_ok=True)
    concept_path = run_dir / "handpicked_concepts.csv"
    _write_concepts_file(concept_path, records)

    flattened_dir = run_dir / FLATTENED_DIR.name
    if not flattened_dir.exists():
        raise FileNotFoundError(f"Missing flattened data directory: {flattened_dir}")
    csv_paths = sorted(flattened_dir.glob("*.csv"))
    if not csv_paths:
        raise FileNotFoundError(f"No CSV files found in {flattened_dir}")
    source_csv = csv_paths[0]
    original_df = pd.read_csv(source_csv)
    if not {"Question", "Option", "Value"}.issubset(original_df.columns):
        raise ValueError(f"{source_csv} must contain Question, Option, Value columns.")

    original_df["Question_norm"] = original_df["Question"].astype(str).map(_normalise_whitespace)
    original_df["Option_norm"] = original_df["Option"].astype(str).map(_normalise_whitespace)

    textual_dir = run_dir / TEXTUAL_DIR.name
    if not textual_dir.exists():
        raise FileNotFoundError(f"Missing textual data directory: {textual_dir}")

    workspace_dir = run_dir / "handpicked_context_workspace"
    workspace_flattened = workspace_dir / FLATTENED_DIR.name
    workspace_textual = workspace_dir / TEXTUAL_DIR.name
    workspace_flattened.mkdir(parents=True, exist_ok=True)
    shutil.copytree(textual_dir, workspace_textual, dirs_exist_ok=True)

    bundles: Dict[str, Dict[str, Any]] = {}
    for record in records:
        concept = record["concept"]
        question_norm = _normalise_whitespace(record["question"])
        answer_norm = _normalise_whitespace(record["answer"])

        filtered_df = original_df[
            ~(
                (original_df["Question_norm"] == question_norm)
                & (original_df["Option_norm"] == answer_norm)
            )
        ][["Question", "Option", "Value"]].copy()

        if filtered_df.empty:
            raise ValueError(
                f"Filtering removed all rows for concept '{concept}'. "
                "Check that the flattened CSV contains additional evidence."
            )

        filtered_csv = workspace_flattened / source_csv.name
        filtered_df.to_csv(filtered_csv, index=False)

        _bundle_inputs.cache_clear()
        parsing_agent = DataParsingAgent(workspace_dir)
        bundles[concept] = parsing_agent.prepare_concept_bundle(concept)

    output_path = run_dir / output_filename
    _write_context_summary(records, bundles, output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate context summary for handpicked concepts within a demographic run."
    )
    parser.add_argument(
        "--questions",
        type=Path,
        default=Path("Handpicked_experiments_10.csv"),
        help="CSV containing handpicked concepts with a 'Concept' column.",
    )
    parser.add_argument(
        "--demographic",
        type=str,
        default="Young Dependents",
        help="Demographic label to filter within the handpicked CSV.",
    )
    parser.add_argument(
        "--output-name",
        type=str,
        default="context_summary_handpicked.txt",
        help="Filename for the generated summary inside the demographic run folder.",
    )
    args = parser.parse_args()

    demographic_label = _normalise_whitespace(args.demographic)
    slug = _slugify(demographic_label)
    run_dir = Path("demographic_runs") / slug

    output_path = generate_context_summary(
        questions_csv=args.questions,
        demographic_label=demographic_label,
        run_dir=run_dir,
        output_filename=args.output_name,
    )
    print(f"[{demographic_label}] context summary -> {output_path}")


if __name__ == "__main__":
    main()
