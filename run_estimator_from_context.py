#!/usr/bin/env python3
"""Run the estimator + critic agents using evidence parsed from context_summary.txt."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from agent_estimator.estimator_agent import EstimatorAgent
from agent_estimator.qa_agent import CriticAgent
from agent_estimator.common.config import LIKERT_ORDER, LIKERT_PRETTY, DEFAULT_RUNS, MAX_ITERATIONS


def parse_context_summary(path: Path) -> List[Dict[str, str]]:
    lines = [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines()]
    entries: List[Dict[str, str]] = []
    i = 0
    n = len(lines)
    current: Dict[str, str] = {}

    def collect_block(start_index: int) -> Tuple[str, int]:
        collected: List[str] = []
        j = start_index
        while j < n:
            line = lines[j]
            if not line.strip():
                break
            if line.startswith("### Concept:") or line.endswith("summary:") or line.startswith("Weight hints:"):
                break
            collected.append(line)
            j += 1
        return "\n".join(collected).strip(), j

    while i < n:
        line = lines[i]
        if line.startswith("### Concept:"):
            if current:
                entries.append(current)
            current = {"concept": line.split("### Concept:", 1)[1].strip()}
            i += 1
            continue
        if not current:
            i += 1
            continue
        if line.startswith("Selection notes:"):
            current["selection_notes"] = line.split(":", 1)[1].strip()
            i += 1
            continue
        if line.startswith("Types present:"):
            current["types_present"] = line.split(":", 1)[1].strip()
            i += 1
            continue
        if line.startswith("Quantitative summary:"):
            block, new_index = collect_block(i + 1)
            current["quant_summary"] = block
            i = new_index
            continue
        if line.startswith("Qualitative summary:"):
            block, new_index = collect_block(i + 1)
            current["textual_summary"] = block
            i = new_index
            continue
        if line.startswith("Weight hints:"):
            hints: List[str] = []
            j = i + 1
            while j < n and lines[j].strip():
                if lines[j].strip().startswith("- "):
                    hints.append(lines[j].strip()[2:].strip())
                else:
                    hints.append(lines[j].strip())
                j += 1
            current["weight_hints"] = "\n".join(hints)
            i = j
            continue
        i += 1

    if current:
        entries.append(current)
    return entries


def summarize_runs(runs: Iterable[Dict[str, any]]) -> str:
    lines: List[str] = []
    for run in runs:
        distr = run.get("distribution", {})
        dist_line = ", ".join(
            f"{LIKERT_PRETTY[label]}={distr.get(label, 0.0):.2f}%" for label in LIKERT_ORDER
        )
        lines.append(
            f"Run {run.get('run')}: {dist_line}\n  Conf={run.get('confidence', 0.0):.2f} "
            f"/ Rationale: {run.get('rationale', '')}"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run estimator and critic using evidence from context_summary.txt."
    )
    parser.add_argument(
        "--context",
        type=Path,
        default=Path("context_summary.txt"),
        help="Path to context summary produced by parser_main.py.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("estimator_results.txt"),
        help="Path to write the estimator results summary.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=DEFAULT_RUNS,
        help="Monte Carlo runs per concept for the estimator.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=MAX_ITERATIONS,
        help="Maximum estimator/critic iterations per concept.",
    )
    args = parser.parse_args()

    if not args.context.exists():
        raise FileNotFoundError(f"Context summary not found: {args.context}")

    evidence_entries = parse_context_summary(args.context)
    estimator = EstimatorAgent()
    critic = CriticAgent()

    output_lines: List[str] = []

    for entry in evidence_entries:
        concept = entry["concept"]
        quant_summary = entry.get("quant_summary", "")
        textual_summary = entry.get("textual_summary", "")
        weight_hints_raw = entry.get("weight_hints", "")
        weight_hints = [w.strip() for w in weight_hints_raw.splitlines() if w.strip()]
        selection_notes = entry.get("selection_notes", "")

        evidence_dict: Dict[str, any] = {
            "quant_summary": quant_summary,
            "textual_summary": textual_summary,
            "weight_hints": weight_hints,
            "selection_notes": selection_notes,
        }

        iteration = 0
        feedback = ""
        final_result = None
        final_runs: List[Dict[str, any]] = []
        final_critic = None

        while iteration < args.max_iterations:
            iteration += 1
            estimation = estimator.estimate(
                concept=concept,
                evidence=evidence_dict,
                runs=args.runs,
                iteration=iteration,
                feedback=feedback,
            )
            run_dicts = [
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
                evidence=evidence_dict,
                aggregated_distribution=estimation.aggregated_distribution,
                runs=run_dicts,
            )

            final_result = estimation
            final_runs = run_dicts
            final_critic = critic_assessment

            if not critic_assessment.needs_revision:
                break
            feedback = critic_assessment.feedback or ""

        if final_result is None or final_critic is None:
            continue

        output_lines.append(f"### Concept: {concept}")
        output_lines.append(f"Iterations: {iteration}")
        output_lines.append(f"Estimator average confidence: {final_result.avg_confidence:.2f}")
        output_lines.append(f"Critic confidence: {final_critic.confidence:.2f}")
        output_lines.append(f"Critic feedback: {final_critic.feedback or 'None'}")
        output_lines.append("Final distribution:")
        for label in LIKERT_ORDER:
            output_lines.append(
                f"  {LIKERT_PRETTY[label]}: {final_result.aggregated_distribution.get(label, 0.0):.2f}%"
            )
        output_lines.append("Runs:")
        output_lines.append(summarize_runs(final_runs) or "  (no runs)")
        output_lines.append("")

    args.output.write_text("\n".join(output_lines).strip() + "\n", encoding="utf-8")
    print(f"Estimator results written to {args.output}")


if __name__ == "__main__":
    main()
