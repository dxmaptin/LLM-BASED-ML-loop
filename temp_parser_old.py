"""Data parsing agent that ingests CSV/TXT evidence."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..common.config import FLATTENED_DIR, TEXTUAL_DIR, CONCEPTS_CSV
from ..common.openai_utils import call_response_api
from .prompts import PARSER_SYSTEM_PROMPT


def _require(condition: bool, msg: str) -> None:
    if not condition:
        raise RuntimeError(msg)


def _load_quant_inputs(path: Path) -> pd.DataFrame:
    _require(path.exists() and path.is_dir(), f"Missing folder: {path}")
    frames: List[pd.DataFrame] = []
    for csv_path in sorted(path.glob("*.csv")):
        try:
            df = pd.read_csv(csv_path)
        except Exception as exc:
            raise RuntimeError(f"Failed reading {csv_path}: {exc}") from exc
        df.columns = [str(c).strip().lower() for c in df.columns]
        rename_map: Dict[str, str] = {}
        for expected in ("question", "option", "value"):
            for col in df.columns:
                if col.startswith(expected):
                    rename_map[col] = expected
        df = df.rename(columns=rename_map)
        _require(
            {"question", "option", "value"}.issubset(set(df.columns)),
            f"{csv_path} must have headers starting with Question, Option, Value",
        )
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["question", "option", "value"]).copy()
        for col in ("question", "option"):
            df[col] = df[col].astype(str).str.strip()
        df["source_file"] = csv_path.name
        frames.append(df[["question", "option", "value", "source_file"]])
    _require(frames, f"No CSV files found in {path}")
    return pd.concat(frames, ignore_index=True)


def _summarise_quant(df: pd.DataFrame) -> str:
    lines: List[str] = []
    for question, sub in df.groupby("question", sort=False):
        ranked = sub.sort_values("value", ascending=False)
        parts = [f"{row.option}={row.value:.2f}" for row in ranked.itertuples(index=False)]
        lines.append(f"Q: {question} | Options: {', '.join(parts)}")
    return "\n".join(lines)


def _build_weight_hints(df: pd.DataFrame, top_n: int = 3) -> List[str]:
    hints: List[str] = []
    for question, sub in df.groupby("question", sort=False):
        ranked = sub.sort_values("value", ascending=False).head(top_n)
        parts = [f"{row.option} ({row.value:.2f})" for row in ranked.itertuples(index=False)]
        hints.append(f"{question}: top {len(parts)} -> {', '.join(parts)}")
    return hints


def _load_textual_inputs(path: Path) -> List[Dict[str, str]]:
    _require(path.exists() and path.is_dir(), f"Missing folder: {path}")
    chunks: List[Dict[str, str]] = []
    for txt_path in sorted(path.glob("*.txt")):
        try:
            text = txt_path.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception as exc:
            raise RuntimeError(f"Failed reading {txt_path}: {exc}") from exc
        if text:
            chunks.append({"file": txt_path.name, "text": text})
    _require(chunks, f"No TXT files found in {path}")
    return chunks


def _read_concepts(path: Path) -> List[str]:
    _require(path.exists(), f"Missing concepts file: {path}")
    df = pd.read_csv(path, header=None, names=["concept"], dtype=str)
    df["concept"] = df["concept"].fillna("").str.strip()
    concepts = [c for c in df["concept"].tolist() if c]
    _require(concepts, f"No concepts found in {path}")
    return concepts


@lru_cache(maxsize=4)
def _bundle_inputs(base_dir: Path) -> Dict[str, Any]:
    quant_df = _load_quant_inputs(base_dir / FLATTENED_DIR.name)
    textual_chunks = _load_textual_inputs(base_dir / TEXTUAL_DIR.name)
    textual_summary = "\n\n".join(chunk["text"] for chunk in textual_chunks)
    return {
        "quant_df": quant_df,
        "quant_summary": _summarise_quant(quant_df),
        "textual_summary": textual_summary,
        "weight_hints": _build_weight_hints(quant_df),
        "textual_chunks": textual_chunks,
    }


class DataParsingAgent:
    """IR agent responsible for loading and structuring evidence."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def load_evidence(self) -> Dict[str, Any]:
        bundle = _bundle_inputs(self.base_dir)
        quant_df = bundle["quant_df"]
        return {
            "quant_summary": bundle["quant_summary"],
            "textual_summary": bundle["textual_summary"],
            "weight_hints": bundle["weight_hints"],
            "quant_records": quant_df.to_dict("records"),
            "full_quant_summary": bundle["quant_summary"],
            "full_textual_summary": bundle["textual_summary"],
        }

    def list_concepts(self) -> List[str]:
        return _read_concepts(self.base_dir / CONCEPTS_CSV.name)

    def prepare_concept_bundle(self, concept: str) -> Dict[str, Any]:
        bundle = _bundle_inputs(self.base_dir)
        quant_df = bundle["quant_df"]
        quant_lines = [
            f"{idx+1}. file={row.source_file} | question={row.question} | option={row.option} | value={row.value:.4f}"
            for idx, row in enumerate(quant_df.itertuples(index=False))
        ]
        text_chunks = bundle["textual_chunks"]
        text_lines = [
            f"{idx+1}. file={chunk['file']} | excerpt={chunk['text'][:350].replace(chr(10), ' ')}"
            for idx, chunk in enumerate(text_chunks)
        ]
        weight_hints = bundle["weight_hints"]

        user_prompt = (
            f"Concept:\n{concept}\n\n"
            "Quantitative entries (each line shows question | option | value):\n"
            + "\n".join(quant_lines)
            + "\n\nQualitative snippets:\n"
            + ("\n".join(text_lines) if text_lines else "None provided.")
            + "\n\nExisting weight hints:\n"
            + ("\n".join(f"- {hint}" for hint in weight_hints) if weight_hints else "None.\n")
            + "\n\n"
            "Use the provided sources to select only the minimal evidence that directly "
            "supports evaluating agreement for this concept. Respond with JSON."
        )
        schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "parser_selection",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "question": {"type": "string"},
                        "top_sources": {
                            "type": "array",
                            "maxItems": 4,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "source_type": {"type": "string", "enum": ["quant", "qual"]},
                                    "file": {"type": "string"},
                                    "question": {"type": "string"},
                                    "option": {"type": "string"},
                                    "value": {"type": "number"},
                                    "excerpt": {"type": "string"},
                                    "relevance": {"type": "number", "minimum": 0, "maximum": 1},
                                    "weight_hint": {"type": "string"},
                                },
                                "required": ["source_type", "file", "relevance"],
                            },
                        },
                        "weight_hints": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 5,
                        },
                        "notes": {"type": "string"},
                    },
                    "required": ["question", "top_sources"],
                },
            },
        }

        try:
            selection = call_response_api(PARSER_SYSTEM_PROMPT, user_prompt, schema)
        except RuntimeError:
            selection = {}

        top_sources: List[Dict[str, Any]] = []
        if isinstance(selection, dict):
            raw_sources = selection.get("top_sources", [])
            if isinstance(raw_sources, list):
                for item in raw_sources[:4]:
                    if isinstance(item, dict):
                        source_type = item.get("source_type")
                        file_name = item.get("file")
                        relevance = item.get("relevance")
                        if source_type in {"quant", "qual"} and isinstance(file_name, str) and isinstance(relevance, (int, float)):
                            top_sources.append(
                                {
                                    "source_type": source_type,
                                    "file": file_name,
                                    "question": str(item.get("question", "")),
                                    "option": str(item.get("option", "")),
                                    "value": float(item["value"]) if "value" in item and item["value"] is not None else None,
                                    "excerpt": str(item.get("excerpt", "")),
                                    "relevance": float(relevance),
                                    "weight_hint": str(item.get("weight_hint", "")).strip(),
                                }
                            )

        selected_weight_hints = []
        if isinstance(selection, dict):
            raw_hints = selection.get("weight_hints", [])
            if isinstance(raw_hints, list):
                selected_weight_hints = [str(h).strip() for h in raw_hints if str(h).strip()]

        notes = ""
        if isinstance(selection, dict):
            notes = str(selection.get("notes", "")).strip()

        quant_entries = [
            src for src in top_sources if src["source_type"] == "quant" and src.get("question")
        ]
        qual_entries = [
            src for src in top_sources if src["source_type"] == "qual" and src.get("excerpt")
        ]

        quant_summary = (
            "\n".join(
                f"{entry['question']} | {entry.get('option','')} | value={entry['value']:.4f} "
                f"(file={entry['file']}, relevance={entry['relevance']:.2f})"
            )
            if quant_entries
            else ""
        )
        textual_summary = (
            "\n\n".join(
                f"{entry['excerpt']} (file={entry['file']}, relevance={entry['relevance']:.2f})"
                for entry in qual_entries
            )
            if qual_entries
            else ""
        )

        weight_hint_final = selected_weight_hints or [
            f"{entry['question']} {entry.get('option','')}".strip()
            for entry in quant_entries
            if entry.get("question")
        ]
        if not weight_hint_final:
            weight_hint_final = []

        return {
            "quant_summary": quant_summary,
            "textual_summary": textual_summary,
            "weight_hints": weight_hint_final,
            "selection_notes": notes or ("Targeted selection used." if top_sources else "No high-confidence evidence selected."),
            "full_quant_summary": bundle["quant_summary"],
            "full_textual_summary": bundle["textual_summary"],
            "top_sources": top_sources,
        }
