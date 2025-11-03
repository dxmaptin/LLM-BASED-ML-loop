"""Grounding and QA / critic agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from ..common.config import LIKERT_ORDER, LIKERT_PRETTY
from ..common.openai_utils import call_response_api


@dataclass
class CriticAssessment:
    needs_revision: bool
    confidence: float
    feedback: str


class CriticAgent:
    """Validates estimator outputs against evidence."""

    @staticmethod
    def _schema() -> Dict[str, Any]:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "critic_assessment",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "needs_revision": {"type": "boolean"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "feedback": {"type": "string"},
                    },
                    "required": ["needs_revision", "confidence", "feedback"],
                },
            },
        }

    def assess(
        self,
        concept: str,
        iteration: int,
        evidence: Dict[str, Any],
        aggregated_distribution: Dict[str, float],
        runs: Iterable[Dict[str, Any]],
    ) -> CriticAssessment:
        distribution_lines = "\n".join(
            f"{LIKERT_PRETTY[label]}: {aggregated_distribution.get(label, 0.0):.2f}%"
            for label in LIKERT_ORDER
        )
        run_lines = []
        for run in runs:
            distr = run.get("distribution", {})
            distr_line = ", ".join(
                f"{LIKERT_PRETTY[label]}={distr.get(label, 0.0):.2f}%"
                for label in LIKERT_ORDER
            )
            run_lines.append(
                f"Run {run.get('run')}: {distr_line}\nRationale: {run.get('rationale', '')}"
            )
        run_block = "\n\n".join(run_lines) if run_lines else "No run details."

        selection_notes = evidence.get("selection_notes", "")
        full_context_note = ""
        if selection_notes:
            full_context_note = f"\nEvidence selection rationale: {selection_notes}"

        system_prompt = (
            "You are a methodological critic ensuring simulated survey predictions "
            "are grounded in the provided evidence."
        )
        user_prompt = f"""Quantitative toplines:
{evidence.get("quant_summary", "")}

Qualitative notes:
{evidence.get("textual_summary", "")}

Latest estimate for concept "{concept}" (iteration {iteration}):
{distribution_lines}

Run-level detail:
{run_block}

{full_context_note}

Evaluate whether the estimate is sufficiently justified. If not, specify corrective feedback."""
        raw = call_response_api(
            system_prompt,
            user_prompt,
            self._schema(),
            usage_label="critic",
            usage_meta={"concept": concept, "iteration": iteration},
        )
        return CriticAssessment(
            needs_revision=bool(raw.get("needs_revision", False)),
            confidence=float(raw.get("confidence", 0.0)),
            feedback=str(raw.get("feedback", "")).strip(),
        )
