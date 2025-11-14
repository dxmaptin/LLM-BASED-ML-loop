#!/usr/bin/env python3
"""Run parser, estimator, and critic across all demographic columns."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from agent_estimator.common.config import (
    DEFAULT_RUNS,
    LIKERT_ORDER,
    LIKERT_PRETTY,
    MAX_ITERATIONS,
)
from agent_estimator.common.openai_utils import (
    TokenUsageLog,
    get_token_usage_log,
    reset_token_usage,
)
from agent_estimator.estimator_agent import EstimatorAgent
from agent_estimator.ir_agent.parser import DataParsingAgent, _bundle_inputs
from agent_estimator.qa_agent import CriticAgent


def slugify(name: str) -> str:
    slug = re.sub(r"[^\w]+", "_", name.strip().lower())
    return re.sub(r"_+", "_", slug).strip("_") or "segment"


def read_concepts(path: Path) -> List[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def parse_concept_pairs(concepts: List[str]) -> List[Tuple[str, Optional[str]]]:
    pairs: List[Tuple[str, Optional[str]]] = []
    for concept in concepts:
        if ":" in concept:
            question, answer = concept.split(":", 1)
            pairs.append((question.strip(), answer.strip()))
        else:
            pairs.append((concept.strip(), None))
    return pairs


def write_context_summary(
    concepts: List[str],
    bundles: Dict[str, Dict[str, any]],
    output_path: Path,
) -> None:
    lines: List[str] = []
    for concept in concepts:
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
                if src["source_type"] == "quant":
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
        quant_summary = bundle.get("quant_summary", "") or "(none)"
        lines.append(quant_summary)
        lines.append("")
        lines.append("Qualitative summary:")
        textual_summary = bundle.get("textual_summary", "") or "(none)"
        lines.append(textual_summary)
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


def summarize_runs(runs: Iterable[Dict[str, any]]) -> str:
    segments: List[str] = []
    for run in runs:
        distr = run.get("distribution", {})
        dist_line = ", ".join(
            f"{LIKERT_PRETTY[label]}={distr.get(label, 0.0):.2f}%"
            for label in LIKERT_ORDER
        )
        segments.append(
            f"Run {run.get('run')}: {dist_line}\n"
            f"  Conf={run.get('confidence', 0.0):.2f} | Rationale: {run.get('rationale', '')}"
        )
    return "\n".join(segments)


def write_estimator_results(
    concepts: List[str],
    bundles: Dict[str, Dict[str, any]],
    results: Dict[str, Dict[str, any]],
    output_path: Path,
    token_usage: Optional[TokenUsageLog] = None,
) -> None:
    lines: List[str] = []
    for concept in concepts:
        res = results[concept]
        estimation = res["estimation"]
        critic_assessment = res["critic"]
        iteration = res["iterations"]
        lines.append(f"### Concept: {concept}")
        lines.append(f"Iterations: {iteration}")
        lines.append(f"Estimator average confidence: {estimation.avg_confidence:.2f}")
        lines.append(f"Critic confidence: {critic_assessment.confidence:.2f}")
        lines.append(f"Critic feedback: {critic_assessment.feedback or 'None'}")
        lines.append("Final distribution:")
        for label in LIKERT_ORDER:
            lines.append(
                f"  {LIKERT_PRETTY[label]}: {estimation.aggregated_distribution.get(label, 0.0):.2f}%"
            )
        lines.append("Runs:")
        lines.append(summarize_runs(res["runs"]) or "  (no runs)")
        lines.append("")
    if token_usage and token_usage.requests:
        lines.append("### Token Usage Summary")
        lines.append(f"Total API calls: {token_usage.requests}")
        lines.append(f"Prompt tokens: {token_usage.prompt_tokens}")
        lines.append(f"Completion tokens: {token_usage.completion_tokens}")
        lines.append(f"Total tokens: {token_usage.total_tokens}")
        stage_totals = token_usage.stage_totals()
        if stage_totals:
            lines.append("")
            lines.append("Stage breakdown:")
            for stage, stats in sorted(stage_totals.items()):
                lines.append(
                    f"- {stage}: calls={stats['requests']}, prompt={stats['prompt_tokens']}, "
                    f"completion={stats['completion_tokens']}, total={stats['total_tokens']}"
                )
        if token_usage.details:
            lines.append("")
            lines.append("Call details:")
            for detail in token_usage.details:
                if detail.metadata:
                    meta_str = ", ".join(f"{k}={v}" for k, v in detail.metadata.items())
                else:
                    meta_str = "n/a"
                lines.append(
                    f"* {detail.label}: prompt={detail.prompt_tokens}, "
                    f"completion={detail.completion_tokens}, total={detail.total_tokens}, meta={meta_str}"
                )
        lines.append("")
    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def prepare_demographic_csv(
    df: pd.DataFrame,
    demographic: str,
    concept_pairs: List[Tuple[str, Optional[str]]],
    output_csv: Path,
) -> None:
    cols_needed = {"Question", "Answer", demographic}
    missing = cols_needed - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns {missing} in dataset.")

    question_norm = df["Question"].astype(str).str.strip()
    answer_norm = df["Answer"].astype(str).str.strip()

    mask = pd.Series(False, index=df.index)
    for question, answer in concept_pairs:
        if answer is None:
            mask |= question_norm == question
        else:
            mask |= (question_norm == question) & (answer_norm == answer)

    filtered = df[~mask][["Question", "Answer", demographic]].rename(
        columns={"Answer": "Option", demographic: "Value"}
    )
    filtered["Value"] = pd.to_numeric(filtered["Value"], errors="coerce")
    filtered = filtered.dropna(subset=["Question", "Option", "Value"]).reset_index(drop=True)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(output_csv, index=False)


def copy_textual_inputs(source_dir: Path, dest_dir: Path) -> None:
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(source_dir, dest_dir)


def run_experiment_for_demographic(
    demographic: str,
    dataset: pd.DataFrame,
    concepts: List[str],
    concept_pairs: List[Tuple[str, Optional[str]]],
    textual_dir: Path,
    output_root: Path,
    runs_per_concept: int,
    max_iterations: int,
) -> None:
    slug = slugify(demographic)
    run_dir = output_root / slug
    flattened_dir = run_dir / "Flattened Data Inputs"
    textual_dest = run_dir / "Textual Data Inputs"
    run_dir.mkdir(parents=True, exist_ok=True)

    prepare_demographic_csv(dataset, demographic, concept_pairs, flattened_dir / f"{slug}.csv")
    copy_textual_inputs(textual_dir, textual_dest)
    (run_dir / "concepts_to_test.csv").write_text(
        "\n".join(concepts) + "\n", encoding="utf-8"
    )
    _bundle_inputs.cache_clear()
    parsing_agent = DataParsingAgent(run_dir)

    reset_token_usage()

    bundles: Dict[str, Dict[str, any]] = {}
    for concept in concepts:
        bundles[concept] = parsing_agent.prepare_concept_bundle(concept)

    context_summary_path = run_dir / f"context_summary_{slug}.txt"
    write_context_summary(concepts, bundles, context_summary_path)

    estimator = EstimatorAgent()
    critic = CriticAgent()
    results: Dict[str, Dict[str, any]] = {}

    for concept in concepts:
        iteration = 0
        feedback = ""
        bundle = bundles[concept]
        final_estimation = None
        final_runs: List[Dict[str, any]] = []
        final_critic = None

        while iteration < max_iterations:
            iteration += 1
            estimation = estimator.estimate(
                concept=concept,
                evidence=bundle,
                runs=runs_per_concept,
                iteration=iteration,
                feedback=feedback,
            )
            run_records = [
                {
                    "run": run.run,
                    "distribution": run.distribution,
                    "confidence": run.confidence,
                    "rationale": run.rationale,
                }
                for run in estimation.runs
            ]
            critic_assessment = critic.assess(
                concept=concept,
                iteration=iteration,
                evidence=bundle,
                aggregated_distribution=estimation.aggregated_distribution,
                runs=run_records,
            )

            final_estimation = estimation
            final_runs = run_records
            final_critic = critic_assessment

            if not critic_assessment.needs_revision:
                break
            feedback = critic_assessment.feedback or ""

        if final_estimation is None or final_critic is None:
            continue

        results[concept] = {
            "estimation": final_estimation,
            "critic": final_critic,
            "runs": final_runs,
            "iterations": iteration,
        }

    usage_log = get_token_usage_log()

    estimator_output_path = run_dir / f"estimator_results_{slug}.txt"
    write_estimator_results(concepts, bundles, results, estimator_output_path, token_usage=usage_log)
    print(f"[{demographic}] context -> {context_summary_path}")
    print(f"[{demographic}] estimator -> {estimator_output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run demographic experiments.")
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Path to the wide demographic CSV (Category, Question, Answer, demo columns).",
    )
    parser.add_argument(
        "--sheet",
        type=str,
        default=0,
        help="Optional Excel sheet name (used when --dataset is an Excel file).",
    )
    parser.add_argument(
        "--textual-dir",
        type=Path,
        default=Path("Textual Data Inputs"),
        help="Folder containing qualitative summaries.",
    )
    parser.add_argument(
        "--concepts",
        type=Path,
        default=Path("concepts_to_test.csv"),
        help="Concepts list.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("demographic_runs"),
        help="Output directory for per-demographic artifacts.",
    )
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS, help="Estimator runs per concept.")
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=MAX_ITERATIONS,
        help="Max estimator/critic iterations per concept.",
    )
    args = parser.parse_args()

    if not args.dataset.exists():
        raise FileNotFoundError(f"Dataset not found: {args.dataset}")
    if not args.textual_dir.exists():
        raise FileNotFoundError(f"Textual directory not found: {args.textual_dir}")
    if not args.concepts.exists():
        raise FileNotFoundError(f"Concepts file not found: {args.concepts}")

    suffix = args.dataset.suffix.lower()
    if suffix in {".xlsx", ".xls", ".xlsm"}:
        df = pd.read_excel(args.dataset, sheet_name=args.sheet)
    else:
        df = pd.read_csv(args.dataset)
    expected_cols = {"Category", "Question", "Answer"}
    if not expected_cols.issubset(df.columns):
        raise ValueError(f"Dataset must include columns: {expected_cols}")
    demographic_columns = [col for col in df.columns if col not in ["Category", "Question", "Answer"]]
    if not demographic_columns:
        raise ValueError("No demographic columns found.")

    concepts = read_concepts(args.concepts)
    concept_pairs = parse_concept_pairs(concepts)
    args.output.mkdir(parents=True, exist_ok=True)

    for demographic in demographic_columns:
        print(f"=== Running demographic: {demographic} ===")
        run_experiment_for_demographic(
            demographic=demographic,
            dataset=df,
            concepts=concepts,
            concept_pairs=concept_pairs,
            textual_dir=args.textual_dir,
            output_root=args.output,
            runs_per_concept=args.runs,
            max_iterations=args.max_iterations,
        )


if __name__ == "__main__":
    main()






