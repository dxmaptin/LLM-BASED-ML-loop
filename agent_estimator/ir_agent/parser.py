"""Data parsing agent that ingests CSV/TXT evidence and surfaces balanced signals."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
from jsonschema import Draft7Validator
from rapidfuzz import fuzz

from ..common.config import CONCEPTS_CSV, FLATTENED_DIR, TEXTUAL_DIR
from ..common.openai_utils import call_response_api
from .prompts import PARSER_SYSTEM_PROMPT

PROMPT_QUANT_LIMIT = 6
PROMPT_TEXT_LIMIT = 6
MIN_K = 3
TOP_K = 5
MAX_LLM_ATTEMPTS = 3
QUAL_MAX_CHARS = 1000  # Increased from 200 to allow full sentences/paragraphs


_SELECTION_SCHEMA: Dict[str, Any] = {
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
                    "value": {"type": ["number", "null"]},
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
    "required": ["top_sources"],
}

_SELECTION_VALIDATOR = Draft7Validator(_SELECTION_SCHEMA)

MATCH_WEIGHTS = {"exact": 1.0, "behavior": 0.7, "proxy": 0.4, "none": 0.0}
BASE_RELEVANCE = {"exact": 0.82, "behavior": 0.68, "proxy": 0.5, "none": 0.38}


def _require(condition: bool, msg: str) -> None:
    if not condition:
        raise RuntimeError(msg)


def _tokenise(text: str) -> List[str]:
    return [tok for tok in re.split(r"[^\w]+", text.lower()) if tok]


def _split_concept(concept: str) -> Tuple[str, str]:
    if ":" in concept:
        segment, construct = concept.split(":", 1)
        return segment.strip(), construct.strip()
    return "", concept.strip()


def _segment_lock(
    quant_df: pd.DataFrame,
    text_chunks: List[Dict[str, str]],
    segment_label: str,
) -> Tuple[pd.DataFrame, List[Dict[str, str]]]:
    if not segment_label:
        return quant_df, text_chunks

    seg_lower = segment_label.lower()

    quant_mask = quant_df["question"].str.lower().str.contains(seg_lower)
    if quant_mask.any():
        quant_df = quant_df[quant_mask].copy()

    filtered_chunks = [
        chunk for chunk in text_chunks if seg_lower in chunk["text"].lower()
    ]
    if filtered_chunks:
        text_chunks = filtered_chunks

    return quant_df, text_chunks


def _classify_match(construct_terms: List[str], text: str) -> str:
    if not text.strip():
        return "none"
    lower_text = text.lower()
    if construct_terms and all(term in lower_text for term in construct_terms):
        return "exact"
    if construct_terms and any(term in lower_text for term in construct_terms):
        return "behavior"
    if construct_terms and fuzz.partial_ratio(" ".join(construct_terms), lower_text) >= 60:
        return "proxy"
    return "none"


def _score_entry(construct_terms: List[str], text: str) -> Tuple[float, str]:
    match_class = _classify_match(construct_terms, text)
    fuzzy = fuzz.token_sort_ratio(" ".join(construct_terms), text.lower()) / 100 if construct_terms else 0
    length_bonus = min(len(text), QUAL_MAX_CHARS) / QUAL_MAX_CHARS
    base = MATCH_WEIGHTS[match_class]
    score = base * 0.7 + fuzzy * 0.2 + length_bonus * 0.1
    return score, match_class


def _compute_relevance(score: float, match_class: str) -> float:
    base = BASE_RELEVANCE.get(match_class, 0.4)
    relevance = base + 0.25 * max(0.0, min(1.0, score))
    return round(min(0.99, max(0.1, relevance)), 2)


def _make_entry_from_candidate(cand: Dict[str, Any], override_excerpt: Optional[str] = None) -> Dict[str, Any]:
    score = max(0.0, cand.get("score", 0.0))
    match_class = cand.get("match_class", "proxy")
    excerpt = override_excerpt if override_excerpt is not None else cand.get("excerpt", "")
    entry = {
        "source_type": cand["source_type"],
        "file": cand["file"],
        "question": cand.get("question", ""),
        "option": cand.get("option", ""),
        "value": cand.get("value") if cand["source_type"] == "quant" else None,
        "excerpt": "" if cand["source_type"] == "quant" else excerpt,
        "relevance": _compute_relevance(score, match_class),
        "weight_hint": "",
        "_score": score,
        "_match_class": match_class,
    }
    return entry


def _extract_best_sentence(text: str, construct_terms: List[str]) -> Tuple[str, str]:
    # Split by both sentence boundaries and newlines to handle structured text
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    best_sentence = ""
    best_score = -1.0
    best_class = "none"
    for sentence in sentences:
        sentence = sentence.strip()
        # Skip very short lines (likely headers, labels, or non-descriptive text)
        # Also skip lines that are all caps (headers), or end with colons (labels)
        if not sentence or len(sentence) < 30 or sentence.isupper() or sentence.endswith(':'):
            continue
        if construct_terms and not any(term in sentence.lower() for term in construct_terms):
            continue
        score, match_class = _score_entry(construct_terms, sentence)
        if score > best_score:
            best_sentence = sentence
            best_score = score
            best_class = match_class
    # Fallback: find first substantial sentence (>30 chars, not a header)
    if not best_sentence and sentences:
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= 30 and not sentence.isupper() and not sentence.endswith(':'):
                best_sentence = sentence[:QUAL_MAX_CHARS]
                best_class = "proxy" if construct_terms else "none"
                break
        if not best_sentence:
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 0:
                    best_sentence = sentence[:QUAL_MAX_CHARS]
                    best_class = "proxy" if construct_terms else "none"
                    break
    return best_sentence[:QUAL_MAX_CHARS], best_class


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
                if col.lower().startswith(expected):
                    rename_map[col] = expected
        # Handle "Answer" as alias for "Option" (for ACORN dataset)
        for col in df.columns:
            if col.lower().startswith("answer"):
                rename_map[col] = "option"
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
    return {
        "quant_df": _load_quant_inputs(base_dir / FLATTENED_DIR.name),
        "textual_chunks": _load_textual_inputs(base_dir / TEXTUAL_DIR.name),
    }


def _build_weight_hints(df: pd.DataFrame, top_n: int = 3) -> List[str]:
    hints: List[str] = []
    for question, sub in df.groupby("question", sort=False):
        ranked = sub.sort_values("value", ascending=False).head(top_n)
        parts = [f"{row.option} ({row.value:.2f})" for row in ranked.itertuples(index=False)]
        hints.append(f"{question}: top {len(parts)} -> {', '.join(parts)}")
    return hints


def _apply_ontology_whitelist(candidates: List[Dict[str, Any]], skip_exact: bool = False) -> List[Dict[str, Any]]:
    """
    Apply ontology whitelist to filter candidates by match tier.

    Args:
        candidates: List of candidate dictionaries with 'match_class' field
        skip_exact: If True, skip the 'exact' tier (used for LOO filtering)

    Returns:
        Filtered list of candidates from the highest available tier
    """
    tiers = ["behavior", "proxy"] if skip_exact else ["exact", "behavior", "proxy"]
    for tier in tiers:
        tier_matches = [cand for cand in candidates if cand["match_class"] == tier]
        if tier_matches:
            return tier_matches
    return []


def _prepare_candidates(
    construct_terms: List[str],
    quant_df: pd.DataFrame,
    text_chunks: List[Dict[str, str]],
    skip_exact: bool = False,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Prepare candidates for evidence selection.

    Args:
        construct_terms: Tokenized construct terms for matching
        quant_df: DataFrame with quantitative data
        text_chunks: List of textual data chunks
        skip_exact: If True, skip exact matches in ontology whitelist (for LOO filtering)

    Returns:
        Tuple of (quant_sorted, text_sorted, prompt_quant, prompt_text)
    """
    quant_candidates: List[Dict[str, Any]] = []
    for row in quant_df.itertuples(index=False):
        text_repr = f"{row.question} {row.option}"
        score, match_class = _score_entry(construct_terms, text_repr)
        quant_candidates.append(
            {
                "source_type": "quant",
                "file": row.source_file,
                "question": row.question,
                "option": row.option,
                "value": float(row.value),
                "excerpt": "",
                "score": score,
                "match_class": match_class,
            }
        )

    text_candidates: List[Dict[str, Any]] = []
    for chunk in text_chunks:
        sentence, match_class = _extract_best_sentence(chunk["text"], construct_terms)
        score, _ = _score_entry(construct_terms, sentence)
        text_candidates.append(
            {
                "source_type": "qual",
                "file": chunk["file"],
                "question": "",
                "option": "",
                "value": None,
                "excerpt": sentence,
                "score": score,
                "match_class": match_class,
            }
        )

    quant_filtered = [cand for cand in quant_candidates if cand["match_class"] != "none"]
    text_filtered = [cand for cand in text_candidates if cand["match_class"] != "none"]

    if quant_filtered:
        quant_filtered = _apply_ontology_whitelist(quant_filtered, skip_exact=skip_exact)
    if text_filtered:
        text_filtered = _apply_ontology_whitelist(text_filtered, skip_exact=skip_exact)

    quant_sorted = sorted(quant_filtered, key=lambda c: c["score"], reverse=True)
    text_sorted = sorted(text_filtered, key=lambda c: c["score"], reverse=True)

    prompt_quant = quant_sorted[:PROMPT_QUANT_LIMIT]
    prompt_text = text_sorted[:PROMPT_TEXT_LIMIT]

    return quant_sorted, text_sorted, prompt_quant, prompt_text


def _format_prompt_candidates(candidates: Iterable[Dict[str, Any]]) -> str:
    lines = []
    for cand in candidates:
        if cand["source_type"] == "quant":
            lines.append(
                f"- [quant] file={cand['file']} | question={cand['question']} | option={cand['option']} "
                f"| value={cand['value']:.4f} | match={cand['match_class']} | score={cand['score']:.3f}"
            )
        else:
            lines.append(
                f"- [qual] file={cand['file']} | match={cand['match_class']} | score={cand['score']:.3f} | excerpt={cand['excerpt']}"
            )
    return "\n".join(lines) if lines else "None."


def _build_prompt(
    concept: str,
    prompt_quant: List[Dict[str, Any]],
    prompt_text: List[Dict[str, Any]],
) -> str:
    return (
        f"Concept:\n{concept}\n\n"
        "Quantitative candidates (pre-filtered, ontology-aligned):\n"
        f"{_format_prompt_candidates(prompt_quant)}\n\n"
        "Qualitative candidates (pre-filtered, ontology-aligned):\n"
        f"{_format_prompt_candidates(prompt_text)}\n\n"
        "Select up to 3 evidence items. Maintain balance: include at least one quantitative and one qualitative item when both candidate types exist. "
        "Prefer exact ontology matches over behavioral or proxy evidence."
    )


def _invoke_model(concept: str, prompt: str) -> Dict[str, Any]:
    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "balanced_parser_selection",
            "strict": True,
            "schema": _SELECTION_SCHEMA,
        },
    }
    last_exc: Optional[Exception] = None
    for attempt in range(1, MAX_LLM_ATTEMPTS + 1):
        try:
            selection = call_response_api(
                PARSER_SYSTEM_PROMPT,
                prompt,
                schema,
                temperature=0.1,
                top_p=1.0,
                max_output_tokens=280,
                usage_label="parser",
                usage_meta={"concept": concept, "attempt": attempt},
            )
            _SELECTION_VALIDATOR.validate(selection)
            return selection
        except Exception as exc:  # pragma: no cover - retried
            last_exc = exc
            if attempt == MAX_LLM_ATTEMPTS:
                raise RuntimeError("Parser agent failed to return valid JSON.") from exc
    raise RuntimeError("Parser agent failed to return valid JSON.") from last_exc


def _dedupe_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    output: List[Dict[str, Any]] = []
    for src in sources:
        key = (
            src["source_type"],
            src.get("question", ""),
            src.get("option", ""),
            src.get("excerpt", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(src)
    return output


def _normalise_sources(raw_sources: Iterable[Dict[str, Any]], construct_terms: List[str]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for item in raw_sources:
        if not isinstance(item, dict):
            continue
        source_type = item.get("source_type")
        file_name = item.get("file")
        if source_type not in {"quant", "qual"} or not isinstance(file_name, str):
            continue
        if source_type == "quant":
            value = item.get("value")
            if not isinstance(value, (int, float)):
                continue
            text_repr = f"{item.get('question', '')} {item.get('option', '')}"
            excerpt = ""
        else:
            value = None
            excerpt = str(item.get("excerpt", ""))[:QUAL_MAX_CHARS]
            if not excerpt:
                continue
            text_repr = excerpt
        score, match_class = _score_entry(construct_terms, text_repr)
        entries.append(
            {
                "source_type": source_type,
                "file": file_name,
                "question": str(item.get("question", "")),
                "option": str(item.get("option", "")),
                "value": value,
                "excerpt": excerpt,
                "relevance": _compute_relevance(score, match_class),
                "weight_hint": str(item.get("weight_hint", "")).strip(),
                "_score": score,
                "_match_class": match_class,
            }
        )
    entries = _dedupe_sources(entries)
    entries.sort(key=lambda src: src["relevance"], reverse=True)
    return entries[: TOP_K + 1]


def _finalize_relevance(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not sources:
        return sources
    scores = [src.get("_score", 0.0) for src in sources]
    max_score = max(scores)
    min_score = min(scores)
    denom = max(1e-6, max_score - min_score)
    for idx, src in enumerate(sorted(sources, key=lambda s: s.get("_score", 0.0), reverse=True)):
        score = src.get("_score", 0.0)
        match_class = src.get("_match_class", "proxy")
        norm = (score - min_score) / denom if denom > 1e-6 else 0.5
        rank_bonus = 0.05 * (1 - idx / max(len(sources) - 1, 1))
        base = BASE_RELEVANCE.get(match_class, 0.4)
        relevance = round(min(0.99, max(0.1, base + 0.25 * norm + rank_bonus)), 2)
        src["relevance"] = relevance
    for src in sources:
        src.pop("_score", None)
        # Keep _match_class for later use in identifying proximal toplines
    sources.sort(key=lambda s: s["relevance"], reverse=True)
    return sources


def _enforce_parity(
    selected: List[Dict[str, Any]],
    quant_sorted: List[Dict[str, Any]],
    text_sorted: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], str]:
    selected = selected[:TOP_K]
    available_quant = any(c["score"] > 0 for c in quant_sorted)
    available_qual = any(c["score"] > 0 for c in text_sorted)

    def _best_candidate(pool: List[Dict[str, Any]], existing: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        existing_keys = {
            (
                item["source_type"],
                item.get("question", ""),
                item.get("option", ""),
                item.get("excerpt", ""),
            )
            for item in existing
        }
        for cand in pool:
            if cand["score"] <= 0:
                continue
            key = (
                cand["source_type"],
                cand.get("question", ""),
                cand.get("option", ""),
                cand.get("excerpt", ""),
            )
            if key in existing_keys:
                continue
            entry = _make_entry_from_candidate(cand)
            return entry
        return None

    notes_parts: List[str] = []

    has_quant = any(src["source_type"] == "quant" for src in selected)
    has_qual = any(src["source_type"] == "qual" for src in selected)

    if available_quant and available_qual:
        if not has_quant:
            replacement = _best_candidate(quant_sorted, selected)
            if replacement:
                if len(selected) >= TOP_K:
                    selected.pop()
                selected.append(replacement)
                notes_parts.append("Balanced selection by adding quantitative evidence.")
        if not has_qual:
            replacement = _best_candidate(text_sorted, selected)
            if replacement:
                if len(selected) >= TOP_K:
                    selected.pop()
                selected.append(replacement)
                notes_parts.append("Balanced selection by adding qualitative evidence.")

    if len(selected) < MIN_K:
        combined_sorted = sorted(
            quant_sorted + text_sorted, key=lambda c: c["score"], reverse=True
        )
        for cand in combined_sorted:
            if cand["score"] <= 0:
                continue
            duplicate = False
            key = (
                cand["source_type"],
                cand.get("question", ""),
                cand.get("option", ""),
                cand.get("excerpt", ""),
            )
            for existing in selected:
                existing_key = (
                    existing["source_type"],
                    existing.get("question", ""),
                    existing.get("option", ""),
                    existing.get("excerpt", ""),
                )
                if existing_key == key:
                    duplicate = True
                    break
            if duplicate:
                continue
            entry = _make_entry_from_candidate(cand)
            selected.append(entry)
            notes_parts.append("Top-up evidence added to satisfy minimum context.")
            if len(selected) >= max(MIN_K, TOP_K):
                break

    selected.sort(key=lambda src: src["relevance"], reverse=True)
    return selected[:TOP_K], " ".join(notes_parts).strip()


def _format_quant_summary(top_sources: List[Dict[str, Any]]) -> str:
    lines = []
    for entry in top_sources:
        if entry["source_type"] != "quant":
            continue
        value = entry.get("value")
        value_str = f"value={value:.4f}" if isinstance(value, (int, float)) else "value=n/a"
        match_type = entry.get("_match_class", "")
        proximity_marker = " [PROXIMAL]" if match_type == "exact" else ""
        lines.append(
            f"{entry['question']} | {entry.get('option','')} | {value_str}{proximity_marker} "
            f"(file={entry['file']}, relevance={entry['relevance']:.2f})"
        )
    return "\n".join(lines)


def _format_textual_summary(top_sources: List[Dict[str, Any]]) -> str:
    lines = []
    for entry in top_sources:
        if entry["source_type"] != "qual" or not entry.get("excerpt"):
            continue
        lines.append(
            f"{entry['excerpt']} (file={entry['file']}, relevance={entry['relevance']:.2f})"
        )
    return "\n\n".join(lines)


def _build_weight_hints_from_selection(top_sources: List[Dict[str, Any]]) -> List[str]:
    hints: List[str] = []
    for entry in top_sources:
        if entry["source_type"] == "quant":
            value = entry.get("value")
            if isinstance(value, (int, float)):
                hints.append(f"{entry['question']} -> {entry.get('option','')} (value={value:.2f})")
            else:
                hints.append(entry['question'])
        elif entry["source_type"] == "qual" and entry.get("excerpt"):
            hints.append(f"Quote: \"{entry['excerpt']}\"")
    return hints[:5]


def _extract_proximal_topline(top_sources: List[Dict[str, Any]]) -> Optional[float]:
    """Extract the value from the first 'exact' match quantitative source."""
    for entry in top_sources:
        if entry["source_type"] == "quant" and entry.get("_match_class") == "exact":
            value = entry.get("value")
            if isinstance(value, (int, float)):
                return float(value)
    return None


def _infer_concept_type(concept: str) -> str:
    """
    Infer concept type from concept string.
    Returns one of: attitude | behavior_low_friction | behavior_high_friction | identity
    """
    concept_lower = concept.lower()

    # Check for behavior keywords
    behavior_keywords = ["buy", "purchase", "use", "visit", "go to", "travel", "spend", "save", "invest"]
    high_friction_keywords = ["invest", "purchase", "buy a home", "switch", "change provider", "pension", "mortgage"]
    low_friction_keywords = ["use", "prefer", "choose", "consider", "look at", "browse"]
    identity_keywords = ["i am", "i'm", "myself", "identity", "who i am", "type of person"]

    # Check identity first (highest priority)
    if any(kw in concept_lower for kw in identity_keywords):
        return "identity"

    # Check high-friction behaviors
    if any(kw in concept_lower for kw in high_friction_keywords):
        return "behavior_high_friction"

    # Check low-friction behaviors
    if any(kw in concept_lower for kw in low_friction_keywords):
        return "behavior_low_friction"

    # Check general behaviors
    if any(kw in concept_lower for kw in behavior_keywords):
        return "behavior_low_friction"  # Default to low friction if unclear

    # Default to attitude for opinion/preference statements
    return "attitude"


def _is_exact_match_to_exclude(concept: str, candidate: Dict[str, Any]) -> bool:
    """
    Check if a quantitative candidate is an exact match to the target concept and should be excluded (LOO).

    Args:
        concept: Target concept string (e.g., "Attitudes - I like to look out for where my products are made or grown")
        candidate: Candidate dict with 'question', 'option', 'source_type'

    Returns:
        True if this is the exact target question/answer and should be excluded
    """
    if candidate.get("source_type") != "quant":
        return False  # Don't exclude qualitative data

    # Extract the construct from concept (part after " - ")
    if " - " in concept:
        construct = concept.split(" - ", 1)[1].strip().lower()
    else:
        construct = concept.strip().lower()

    # Get the candidate's option text
    option = candidate.get("option", "").strip().lower()

    # Check for exact match - the option text matches the construct
    # We consider it exact if they're nearly identical (accounting for minor punctuation differences)
    construct_normalized = construct.replace("'", "").replace('"', '').replace(".", "").replace(",", "")
    option_normalized = option.replace("'", "").replace('"', '').replace(".", "").replace(",", "")

    return construct_normalized == option_normalized


def _fallback_on_empty(
    construct_terms: List[str],
    quant_sorted: List[Dict[str, Any]],
    text_sorted: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], str]:
    combined: List[Dict[str, Any]] = []

    for cand in quant_sorted[:TOP_K]:
        entry = _make_entry_from_candidate(cand)
        entry["weight_hint"] = f"Auto proxy (score={cand['score']:.2f})"
        combined.append(entry)

    if len(combined) < TOP_K:
        needed = TOP_K - len(combined)
        for cand in text_sorted[:needed]:
            sentence = cand.get("excerpt", "")[:QUAL_MAX_CHARS]
            if not sentence:
                continue
            entry = _make_entry_from_candidate(cand, override_excerpt=sentence)
            entry["weight_hint"] = "Auto-selected qualitative proxy."
            combined.append(entry)

    combined = _dedupe_sources(combined)
    combined.sort(key=lambda src: src["relevance"], reverse=True)
    combined = combined[:TOP_K]

    if not combined:
        return [], "No related evidence surfaced; parser returned empty."

    types = {src["source_type"] for src in combined}
    if types == {"quant"}:
        note = "Auto-selected quantitative proxies."
    elif types == {"qual"}:
        note = "Auto-selected qualitative proxies."
    else:
        note = "Auto-selected proxies from both quant and qual."
    return combined, note


class DataParsingAgent:
    """IR agent responsible for loading and structuring evidence."""

    def __init__(self, base_dir: Path, demographic_name: str = ""):
        self.base_dir = base_dir
        self.demographic_name = demographic_name

    def load_evidence(self) -> Dict[str, Any]:
        bundle = _bundle_inputs(self.base_dir)
        quant_df = bundle["quant_df"]
        return {"quant_records": quant_df.to_dict("records")}

    def list_concepts(self) -> List[str]:
        return _read_concepts(self.base_dir / CONCEPTS_CSV.name)

    def prepare_concept_bundle(self, concept: str, exclude_exact_match: bool = True) -> Dict[str, Any]:
        """
        Prepare evidence bundle for a concept.

        Args:
            concept: Target concept to estimate
            exclude_exact_match: If True, excludes exact matches (LOO filtering at data extraction stage)
        """
        bundle = _bundle_inputs(self.base_dir)
        segment_label, construct_label = _split_concept(concept)
        construct_terms = _tokenise(construct_label)

        quant_df = bundle["quant_df"]
        text_chunks = bundle["textual_chunks"]
        quant_df, text_chunks = _segment_lock(quant_df, text_chunks, segment_label)

        # When LOO filtering is enabled, skip exact matches in the ontology whitelist
        # This allows proxy/behavior questions to be selected instead
        quant_sorted, text_sorted, prompt_quant, prompt_text = _prepare_candidates(
            construct_terms, quant_df, text_chunks, skip_exact=exclude_exact_match
        )

        # LEAVE-ONE-OUT FILTERING: Additional exact match removal as backup
        # (ontology whitelist should have already excluded them when skip_exact=True)
        if exclude_exact_match:
            quant_sorted_filtered = []
            for cand in quant_sorted:
                if not _is_exact_match_to_exclude(concept, cand):
                    quant_sorted_filtered.append(cand)
            quant_sorted = quant_sorted_filtered

            prompt_quant_filtered = []
            for cand in prompt_quant:
                if not _is_exact_match_to_exclude(concept, cand):
                    prompt_quant_filtered.append(cand)
            prompt_quant = prompt_quant_filtered

        prompt = _build_prompt(concept, prompt_quant, prompt_text)
        try:
            selection = _invoke_model(concept, prompt)
        except RuntimeError:
            selection = {}

        raw_sources = selection.get("top_sources", []) if isinstance(selection, dict) else []
        top_sources = _normalise_sources(raw_sources, construct_terms)
        parity_note = ""
        top_sources, parity_note = _enforce_parity(top_sources, quant_sorted, text_sorted)

        notes = str(selection.get("notes", "")).strip() if isinstance(selection, dict) else ""
        if parity_note:
            notes = f"{notes} {parity_note}".strip()

        if not top_sources:
            top_sources, fallback_note = _fallback_on_empty(construct_terms, quant_sorted, text_sorted)
            notes = fallback_note
        top_sources = _finalize_relevance(top_sources)

        types_present = sorted({src["source_type"] for src in top_sources})
        weight_hints = _build_weight_hints_from_selection(top_sources)
        quant_summary = _format_quant_summary(top_sources)
        textual_summary = _format_textual_summary(top_sources)
        proximal_topline = _extract_proximal_topline(top_sources)

        # Infer concept_type from concept string or default to "attitude"
        concept_type = _infer_concept_type(concept)

        return {
            "quant_summary": quant_summary,
            "textual_summary": textual_summary,
            "weight_hints": weight_hints,
            "selection_notes": notes or "Balanced selection used.",
            "top_sources": top_sources,
            "types_present": types_present,
            "proximal_topline": proximal_topline,
            "concept_type": concept_type,
            "demographic_name": self.demographic_name,
        }









