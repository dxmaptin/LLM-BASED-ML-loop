"""LangGraph orchestrator wiring the IR, estimator, and critic agents."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, TypedDict

import pandas as pd
from langgraph.graph import END, StateGraph

from ..common.config import (
    BASE_DIR,
    LIKERT_ORDER,
    LIKERT_PRETTY,
    OUTPUT_CSV,
    RUNS_CSV,
    DEFAULT_RUNS,
    MAX_ITERATIONS,
)
from ..common.math_utils import largest_remainder_round
from ..ir_agent import DataParsingAgent
from ..estimator_agent import EstimatorAgent
from ..qa_agent import CriticAgent


class AgentState(TypedDict, total=False):
    base_dir: str
    concept: str
    runs_requested: int
    max_iterations: int
    iteration: int
    evidence: Dict[str, Any]
    feedback_for_estimator: str
    latest_runs: List[Dict[str, Any]]
    aggregated: Dict[str, Any]
    estimator_rationale: str
    needs_revision: bool
    critic_feedback: str
    critic_confidence: float
    history: List[Dict[str, Any]]


class OrchestratorContext(TypedDict):
    parser: DataParsingAgent
    estimator: EstimatorAgent
    critic: CriticAgent


def parse_inputs_node(state: AgentState, context: OrchestratorContext) -> AgentState:
    bundle = context["parser"].prepare_concept_bundle(state["concept"])
    state["evidence"] = bundle
    state.setdefault("iteration", 0)
    state.setdefault("history", [])
    state["feedback_for_estimator"] = state.get("feedback_for_estimator", "")
    return state


def estimator_node(state: AgentState, context: OrchestratorContext) -> AgentState:
    iteration = state.get("iteration", 0) + 1
    runs_requested = state.get("runs_requested", DEFAULT_RUNS)
    feedback = state.pop("feedback_for_estimator", "")

    result = context["estimator"].estimate(
        concept=state["concept"],
        evidence=state.get("evidence", {}),
        runs=runs_requested,
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
        for run in result.runs
    ]

    state["iteration"] = iteration
    state["latest_runs"] = run_dicts
    state["aggregated"] = {
        "distribution": largest_remainder_round(result.aggregated_distribution),
        "runs": len(result.runs),
        "avg_confidence": result.avg_confidence,
        "iteration": iteration,
    }
    state["estimator_rationale"] = "\n---\n".join(
        [r["rationale"] for r in run_dicts if r.get("rationale")]
    ) or "No rationale provided."
    state.setdefault("history", []).append(
        {"iteration": iteration, "runs": run_dicts, "aggregated": state["aggregated"]}
    )
    return state


def critic_node(state: AgentState, context: OrchestratorContext) -> AgentState:
    aggregated = state.get("aggregated", {})
    assessment = context["critic"].assess(
        concept=state["concept"],
        iteration=state.get("iteration", 0),
        evidence=state.get("evidence", {}),
        aggregated_distribution=aggregated.get("distribution", {}),
        runs=state.get("latest_runs", []),
    )
    state["needs_revision"] = assessment.needs_revision
    state["critic_feedback"] = assessment.feedback
    state["critic_confidence"] = assessment.confidence
    state["feedback_for_estimator"] = assessment.feedback if assessment.needs_revision else ""
    return state


def critic_decision(state: AgentState) -> Literal["retry", "done"]:
    if state.get("needs_revision") and state.get("iteration", 0) < state.get("max_iterations", MAX_ITERATIONS):
        return "retry"
    return "done"


def build_graph(context: OrchestratorContext):
    graph = StateGraph(AgentState)
    graph.add_node("parse_inputs", lambda s: parse_inputs_node(s, context))
    graph.add_node("estimate", lambda s: estimator_node(s, context))
    graph.add_node("critic", lambda s: critic_node(s, context))

    graph.set_entry_point("parse_inputs")
    graph.add_edge("parse_inputs", "estimate")
    graph.add_edge("estimate", "critic")
    graph.add_conditional_edges("critic", critic_decision, {"retry": "estimate", "done": END})
    return graph.compile()


def _flatten_history(concept: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for iteration_record in history:
        iteration = iteration_record.get("iteration")
        for run in iteration_record.get("runs", []):
            distribution = run.get("distribution", {})
            row = {
                "Concept": concept,
                "Iteration": iteration,
                "Run": run.get("run"),
                "Confidence": run.get("confidence"),
                "Rationale": run.get("rationale", ""),
            }
            for label in LIKERT_ORDER:
                row[LIKERT_PRETTY[label]] = distribution.get(label, 0.0)
            rows.append(row)
    return rows


def run_agentic_pipeline(
    runs_per_iteration: int = DEFAULT_RUNS,
    max_iterations: int = MAX_ITERATIONS,
    output_csv: Path | str = OUTPUT_CSV,
    runs_csv: Path | str = RUNS_CSV,
) -> None:
    parser = DataParsingAgent(BASE_DIR)
    estimator = EstimatorAgent()
    critic = CriticAgent()
    context: OrchestratorContext = {"parser": parser, "estimator": estimator, "critic": critic}

    executor = build_graph(context)
    concepts = parser.list_concepts()

    summary_rows: List[Dict[str, Any]] = []
    run_rows: List[Dict[str, Any]] = []

    for concept in concepts:
        state: AgentState = {
            "base_dir": str(BASE_DIR),
            "concept": concept,
            "runs_requested": runs_per_iteration,
            "max_iterations": max_iterations,
            "feedback_for_estimator": "",
        }
        final_state = executor.invoke(state)
        aggregated = final_state.get("aggregated", {})
        distribution = aggregated.get("distribution", {})
        history = final_state.get("history", [])

        summary_row = {
            "Concept": concept,
            "Iterations": final_state.get("iteration", 0),
            "Runs per iteration": aggregated.get("runs", runs_per_iteration),
            "Estimator confidence": aggregated.get("avg_confidence", 0.0),
            "Critic confidence": final_state.get("critic_confidence", 0.0),
            "Rationale": final_state.get("estimator_rationale", ""),
            "Critic feedback": final_state.get("critic_feedback", ""),
        }
        for label in LIKERT_ORDER:
            summary_row[LIKERT_PRETTY[label]] = distribution.get(label, 0.0)
        summary_rows.append(summary_row)

        run_rows.extend(_flatten_history(concept, history))

    summary_df = pd.DataFrame(
        summary_rows,
        columns=[
            "Concept",
            "Strongly agree",
            "Slightly agree",
            "Neither agree nor disagree",
            "Slightly disagree",
            "Strongly disagree",
            "Iterations",
            "Runs per iteration",
            "Estimator confidence",
            "Critic confidence",
            "Rationale",
            "Critic feedback",
        ],
    )
    run_df = pd.DataFrame(
        run_rows,
        columns=[
            "Concept",
            "Iteration",
            "Run",
            "Strongly agree",
            "Slightly agree",
            "Neither agree nor disagree",
            "Slightly disagree",
            "Strongly disagree",
            "Confidence",
            "Rationale",
        ],
    ).sort_values(["Concept", "Iteration", "Run"], kind="stable")

    summary_df.to_csv(output_csv, index=False)
    run_df.to_csv(runs_csv, index=False)


def generate_context_summary(output_path: str = "context_summary.txt") -> None:
    """Run the parsing agent over all concepts and write out a context summary."""
    parser = DataParsingAgent(BASE_DIR)
    concepts = parser.list_concepts()

    records: List[str] = []
    for concept in concepts:
        bundle = parser.prepare_concept_bundle(concept)
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

    Path(output_path).write_text("\n".join(records), encoding="utf-8")
