#!/usr/bin/env python3
"""
Simulate concept appeal for a target segment using OpenAI's gpt-5 model,
now with safe concurrency.

Key changes vs. the synchronous version:
- Uses asyncio + AsyncOpenAI to run many runs at once (across concepts and per concept).
- Global throttler (requests-per-second) + semaphore (max in-flight requests).
- Exponential backoff with jitter for 429/5xx/connection timeouts.
- Per-task scoping ensures outputs never mix between concepts/runs.

Folder structure (relative to this script):
- ./Flattened Data Inputs/  -> CSV files with columns: Question, Option, Value
- ./Textual Data Inputs/    -> TXT files with descriptive summaries of the segment
- ./concepts_to_test.csv    -> Column A only (no header); each row = one concept description

Outputs:
- ./predicted_appeal.csv          -> Mean % distribution per concept (sums exactly to 100.00)
- ./predicted_appeal_runs.csv     -> All individual runs per concept for auditability

Setup:
1) pip install -U openai pandas python-dotenv
2) Create a .env file (next to this script) with: OPENAI_API_KEY=sk-...
3) Run: python simulate_appeal_predictions_async.py

Notes:
- Uses the Responses API + Structured Outputs (JSON Schema) to force valid JSON where supported.
- Reasoning models like gpt-5 do not support temperature/top_p.
- Averages are computed in Python ONLY (the LLM never averages).
- Sends ALL quant options and ALL textual inputs to the LLM (no prompt compression).
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import random
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import pandas as pd
from dotenv import load_dotenv

# OpenAI async SDK
from openai import AsyncOpenAI
from openai import APIConnectionError, BadRequestError, AuthenticationError, PermissionDeniedError, RateLimitError


# -----------------------------
# Configuration
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
FLATTENED_DIR = BASE_DIR / "Flattened Data Inputs"
TEXTUAL_DIR = BASE_DIR / "Textual Data Inputs"
CONCEPTS_CSV = BASE_DIR / "concepts_to_test.csv"
OUTPUT_CSV = BASE_DIR / "predicted_appeal.csv"
RUNS_CSV = BASE_DIR / "predicted_appeal_runs.csv"

# Model + workload controls
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")  # Reasoning model name
RUNS_PER_CONCEPT = int(os.getenv("RUNS_PER_CONCEPT", "20"))

# Concurrency + rate limits (tune safely for your account/keys)
# MAX_CONCURRENCY caps the number of in-flight HTTP requests.
# MAX_RPS caps the cadence (requests per second) across the whole program.
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "96"))  # many in-flight to hide latency
MAX_RPS = float(os.getenv("MAX_RPS", "16.0"))              # ~960 RPM; TPM-safe for mid/large calls
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "6"))
INITIAL_BACKOFF = float(os.getenv("INITIAL_BACKOFF", "0.5"))
BACKOFF_MULTIPLIER = float(os.getenv("BACKOFF_MULTIPLIER", "1.8"))
MAX_BACKOFF = float(os.getenv("MAX_BACKOFF", "20.0"))

# Appeal scale (hard-coded)
LABELS_ORDERED: List[Tuple[str, str]] = [
    ("strongly_agree", "Strongly agree"),
    ("slightly_agree", "Slightly agree"),
    ("neither_agree_nor_disagree", "Neither agree nor disagree"),
    ("slightly_disagree", "Slightly disagree"),
    ("strongly_disagree", "Strongly disagree"),
]

QUESTION_STEM = (
    """
    Here is a statement: {concept}.
    To what extent do you agree or disagree with this statement?
    Choose one of: Strongly agree, Slightly agree, Neither agree nor disagree, Slightly disagree, Strongly disagree.
    """
).strip()


# -----------------------------
# Utilities
# -----------------------------
def _require(condition: bool, msg: str) -> None:
    if not condition:
        raise RuntimeError(msg)


def load_quant_inputs(path: Path) -> pd.DataFrame:
    _require(path.exists() and path.is_dir(), f"Missing folder: {path}")
    frames: List[pd.DataFrame] = []
    for csv_path in sorted(path.glob("*.csv")):
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            raise RuntimeError(f"Failed reading {csv_path}: {e}")
        # Normalise column names
        df.columns = [str(c).strip().lower() for c in df.columns]
        rename_map: Dict[str, str] = {}
        for expected in ["question", "option", "value"]:
            for col in df.columns:
                if col.startswith(expected):
                    rename_map[col] = expected
        df = df.rename(columns=rename_map)
        _require({"question", "option", "value"}.issubset(set(df.columns)),
                 f"{csv_path} must have columns: Question, Option, Value")
        # Coerce numeric
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["question", "option", "value"]).copy()
        frames.append(df[["question", "option", "value"]])
    _require(len(frames) > 0, f"No CSV files found in {path}")
    out = pd.concat(frames, ignore_index=True)
    for col in ["question", "option"]:
        out[col] = out[col].astype(str).str.strip()
    return out


def format_quant_full(df: pd.DataFrame) -> str:
    """Return a textual summary that includes ALL options per question (no capping).
    Sorted by Value descending within each question for readability.
    """
    lines: List[str] = []
    for q, sub in df.groupby("question", sort=False):
        sub = sub.sort_values("value", ascending=False)
        parts = [f"{row.option}={row.value:.2f}" for row in sub.itertuples(index=False)]
        lines.append(f"Q: {q} | Options: " + ", ".join(parts))
    return "\n".join(lines)


def load_textual_inputs(path: Path) -> str:
    _require(path.exists() and path.is_dir(), f"Missing folder: {path}")
    chunks: List[str] = []
    for txt_path in sorted(path.glob("*.txt")):
        try:
            txt = txt_path.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception as e:
            raise RuntimeError(f"Failed reading {txt_path}: {e}")
        if txt:
            chunks.append(txt)
    _require(len(chunks) > 0, f"No TXT files found in {path}")
    return "\n\n".join(chunks)


def read_concepts_csv(path: Path) -> List[str]:
    _require(path.exists(), f"Missing concepts file: {path}")
    df = pd.read_csv(path, header=None, names=["concept"], dtype=str)
    df["concept"] = df["concept"].fillna("").str.strip()
    concepts = [c for c in df["concept"].tolist() if c]
    _require(len(concepts) > 0, f"No concepts found in {path}")
    return concepts


def largest_remainder_round(values: Dict[str, float]) -> Dict[str, float]:
    """Round to 2dp while ensuring the sum equals exactly 100.00."""
    cleaned = {k: (0.0 if (v is None or not math.isfinite(float(v)) or v < 0) else float(v)) for k, v in values.items()}
    total = sum(cleaned.values())
    if total <= 0:
        equal = 100.0 / len(cleaned)
        cleaned = {k: equal for k in cleaned}
        total = 100.0

    scaled = {k: (v / total) * 100.0 for k, v in cleaned.items()}
    floors = {k: math.floor(v * 100.0) / 100.0 for k, v in scaled.items()}
    remainder = round(100.0 - sum(floors.values()), 2)

    if abs(remainder) < 1e-9:
        return {k: round(v, 2) for k, v in floors.items()}

    fracs = {k: (scaled[k] - floors[k]) for k in scaled}
    order = sorted(fracs.keys(), key=lambda k: fracs[k], reverse=(remainder > 0))
    steps = int(round(abs(remainder) * 100))

    out = floors.copy()
    i = 0
    while steps > 0 and len(order) > 0:
        k = order[i % len(order)]
        out[k] = round(out[k] + (0.01 if remainder > 0 else -0.01), 2)
        steps -= 1
        i += 1
    final_sum = round(sum(out.values()), 2)
    if final_sum != 100.0:
        diff = round(100.0 - final_sum, 2)
        max_key = max(out, key=out.get)
        out[max_key] = round(out[max_key] + diff, 2)
    return out


def normalise_distribution(d: Dict[str, float]) -> Dict[str, float]:
    # Accept proportions (0..1) or percents (0..100)
    s = sum(d.values())
    if s <= 0:
        equal = 100.0 / len(d)
        return {k: equal for k in d}
    if s <= 1.5:
        d = {k: v * 100.0 for k, v in d.items()}
    return largest_remainder_round(d)


def build_instructions(segment_quant_summary: str, segment_textual: str) -> str:
    lines = [
        "You are an expert quant researcher simulating survey responses for a named segment.",
        "Use the provided segment evidence (prior quant toplines and qualitative summaries) to predict how this segment would respond to the agreement question.",
        "Return a JSON object with percentages for each scale label; numbers must be non-negative and collectively sum to ~100 before any rounding.",
        "Do NOT compute any averages across runs. Each call represents a single Monte Carlo draw only.",
        "Never invent new labels; only use the five given.",
    ]
    context = (
        "\n\n=== SEGMENT QUANT (ALL options per question) ===\n{q}\n\n"
        "=== SEGMENT TEXTUAL SUMMARIES ===\n{t}\n"
    ).format(q=segment_quant_summary, t=segment_textual)
    return "\n".join(lines) + "\n" + context


# -----------------------------
# Throttling & Retry Helpers
# -----------------------------
class RateLimiter:
    """Simple global leaky-bucket limiter for requests-per-second (RPS)."""

    def __init__(self, max_rps: float):
        self.max_rps = max(0.1, max_rps)
        self._lock = asyncio.Lock()
        self._last_ts = 0.0

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            min_interval = 1.0 / self.max_rps
            wait_for = (self._last_ts + min_interval) - now
            if wait_for > 0:
                await asyncio.sleep(wait_for)
            self._last_ts = time.monotonic()


def _extract_usage(resp) -> Dict[str, int]:
    """Robustly extract usage counts from a Responses API result."""
    input_tokens = output_tokens = total_tokens = cached = reasoning = 0
    ud: Dict[str, int] = {}
    try:
        as_dict = resp.to_dict()
        ud = as_dict.get("usage") or {}
    except Exception:
        ud = {}

    if not ud and hasattr(resp, "usage"):
        try:
            maybe = resp.usage
            ud = maybe if isinstance(maybe, dict) else getattr(maybe, "__dict__", {})
        except Exception:
            ud = {}

    def get_nested(d: Dict[str, object], *path: str, default: int = 0) -> int:
        cur: object = d
        for p in path:
            if not isinstance(cur, dict) or p not in cur:
                return default
            cur = cur[p]
        return int(cur) if isinstance(cur, (int, float)) else default

    input_tokens = int(ud.get("input_tokens") or ud.get("prompt_tokens") or 0)
    output_tokens = int(ud.get("output_tokens") or ud.get("completion_tokens") or 0)
    total_tokens = int(ud.get("total_tokens") or (input_tokens + output_tokens))
    cached = int(
        get_nested(ud, "input_tokens_details", "cached_tokens", default=0)
        or get_nested(ud, "prompt_tokens_details", "cached_tokens", default=0)
    )
    reasoning = int(
        get_nested(ud, "output_tokens_details", "reasoning_tokens", default=0)
        or get_nested(ud, "completion_tokens_details", "reasoning_tokens", default=0)
    )

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_input_tokens": cached,
        "reasoning_tokens": reasoning,
    }


def _build_response_format():
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "agree_prediction",
            "strict": True,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "strongly_agree": {"type": "number", "minimum": 0},
                    "slightly_agree": {"type": "number", "minimum": 0},
                    "neither_agree_nor_disagree": {"type": "number", "minimum": 0},
                    "slightly_disagree": {"type": "number", "minimum": 0},
                    "strongly_disagree": {"type": "number", "minimum": 0},
                },
                "required": [
                    "strongly_agree",
                    "slightly_agree",
                    "neither_agree_nor_disagree",
                    "slightly_disagree",
                    "strongly_disagree",
                ],
            },
        },
    }


async def call_openai_predict_async(
    client: AsyncOpenAI,
    limiter: RateLimiter,
    semaphore: asyncio.Semaphore,
    concept: str,
    instructions: str,
    run_idx: int,
) -> Tuple[str, int, Dict[str, float], Dict[str, int]]:
    """
    One model call = one Monte Carlo run.
    Returns (concept, run_idx, distribution, usage).
    """
    nonce = os.urandom(4).hex()
    prompt = (
        f"{QUESTION_STEM.format(concept=concept)}\n\n"
        f"Calibration_tag: {nonce}\n"
        "Respond with JSON only using these exact keys:\n"
        "strongly_agree, slightly_agree, neither_agree_nor_disagree, slightly_disagree, strongly_disagree.\n"
        "Numbers must be non-negative and sum to ~100 before rounding."
    )

    response_format = _build_response_format()
    kwargs = dict(
        model=MODEL,
        instructions=instructions,
        input=prompt,
        reasoning={"effort": "high"}
    )

    backoff = INITIAL_BACKOFF
    last_exc: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        await limiter.wait()  # global RPS guard
        async with semaphore:  # max in-flight requests
            try:
                # Try structured outputs if SDK supports it
                try:
                    resp = await client.responses.create(response_format=response_format, **kwargs)
                except TypeError:
                    resp = await client.responses.create(**kwargs)

                usage = _extract_usage(resp)

                # Prefer parsed content if present (newer SDKs)
                parsed: Dict[str, float] = {}
                try:
                    out = getattr(resp, "output", None)
                    if out:
                        for item in out:
                            for c in getattr(item, "content", []) or []:
                                if hasattr(c, "parsed") and c.parsed:
                                    parsed = c.parsed  # type: ignore
                                    break
                            if parsed:
                                break
                except Exception:
                    parsed = {}

                if not parsed:
                    # Fallback parse
                    try:
                        parsed = json.loads(resp.output_text)
                    except Exception:
                        try:
                            as_dict = resp.to_dict()
                            content = as_dict.get("output", [])
                            text_blob = json.dumps(content)
                            start = text_blob.find("{")
                            end = text_blob.rfind("}")
                            parsed = json.loads(text_blob[start : end + 1])
                        except Exception as e:
                            raise RuntimeError(f"Failed to parse model output as JSON: {e}")

                # Keep expected keys and coerce to float
                dist = {k: float(parsed.get(k, 0.0)) for k, _ in LABELS_ORDERED}
                dist = normalise_distribution(dist)
                return concept, run_idx, dist, usage

            except (RateLimitError, APIConnectionError) as e:
                last_exc = e
                # Exponential backoff with jitter
                sleep_for = min(MAX_BACKOFF, backoff) * (1 + random.random() * 0.25)
                await asyncio.sleep(sleep_for)
                backoff *= BACKOFF_MULTIPLIER
                continue
            except (PermissionDeniedError, AuthenticationError, BadRequestError) as e:
                # Non-retryable
                raise
            except Exception as e:
                last_exc = e
                # Treat unknown as transient once or twice, then give up
                sleep_for = min(MAX_BACKOFF, backoff) * (1 + random.random() * 0.25)
                await asyncio.sleep(sleep_for)
                backoff *= BACKOFF_MULTIPLIER
                # Still retry up to MAX_RETRIES

    # All retries exhausted
    raise RuntimeError(f"Runs failed for concept '{concept}' run {run_idx}. Last error: {last_exc!r}")


# -----------------------------
# Orchestration
# -----------------------------
async def simulate_concepts_async(
    client: AsyncOpenAI,
    concepts: List[str],
    instructions: str,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, int], int]:
    """
    Fan out all runs across all concepts concurrently (bounded).
    Returns (means_df, runs_df, total_usage, total_requests).
    """
    limiter = RateLimiter(MAX_RPS)
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    # Submit all tasks (concepts x runs)
    tasks: List[asyncio.Task] = []
    for concept in concepts:
        for run_idx in range(1, RUNS_PER_CONCEPT + 1):
            tasks.append(
                asyncio.create_task(
                    call_openai_predict_async(
                        client=client,
                        limiter=limiter,
                        semaphore=semaphore,
                        concept=concept,
                        instructions=instructions,
                        run_idx=run_idx,
                    )
                )
            )

    # Collect as they finish; aggregate safely
    grand_usage = defaultdict(int)
    per_concept_runs: Dict[str, List[Dict[str, float]]] = defaultdict(list)
    run_rows: List[Dict[str, str]] = []

    total_requests = 0
    errors: List[str] = []

    for coro in asyncio.as_completed(tasks):
        try:
            concept, run_idx, dist, usage = await coro
            total_requests += 1
            for k, v in usage.items():
                grand_usage[k] += int(v)

            # Store: all individual runs (auditable)
            rr = {"Concept": concept, "Run": run_idx}
            for key, pretty in LABELS_ORDERED:
                rr[pretty] = f"{dist[key]:.2f}"
            run_rows.append(rr)

            per_concept_runs[concept].append(dist)

        except Exception as e:
            # Keep going; report at the end
            errors.append(repr(e))

    if errors:
        # If everything failed, bail out; else proceed with what we have
        if all(concept not in per_concept_runs for concept in concepts):
            raise RuntimeError("All runs failed. First error: " + errors[0])

    # Compute per-concept means (Python-side averaging, never by the model)
    mean_rows: List[Dict[str, str]] = []
    for concept in concepts:
        runs = per_concept_runs.get(concept, [])
        if not runs:
            # If a concept has no successful runs, fill equal shares to keep CSV shape consistent
            equal = 100.0 / len(LABELS_ORDERED)
            avg = {k: equal for k, _ in LABELS_ORDERED}
        else:
            avg = {}
            for k, _pretty in LABELS_ORDERED:
                vals = [r[k] for r in runs]
                avg[k] = sum(vals) / len(vals)
            avg = largest_remainder_round(avg)

        row = {"Concept": concept}
        for k, pretty in LABELS_ORDERED:
            row[pretty] = f"{avg[k]:.2f}"
        mean_rows.append(row)

    means_df = pd.DataFrame(mean_rows, columns=[
        "Concept",
        "Strongly agree",
        "Slightly agree",
        "Neither agree nor disagree",
        "Slightly agree",
        "Strongly agree",
    ])

    runs_df = pd.DataFrame(run_rows, columns=[
        "Concept",
        "Run",
        "Strongly agree",
        "Slightly agree",
        "Neither agree nor disagree",
        "Slightly agree",
        "Strongly agree",
    ]).sort_values(["Concept", "Run"], kind="stable")

    return means_df, runs_df, dict(grand_usage), total_requests


# -----------------------------
# Main
# -----------------------------
async def amain() -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    _require(bool(api_key), "OPENAI_API_KEY not set. Put it in a .env file or environment.")

    # Load inputs
    quant_df = load_quant_inputs(FLATTENED_DIR)
    quant_summary = format_quant_full(quant_df)
    textual_summary = load_textual_inputs(TEXTUAL_DIR)
    concepts = read_concepts_csv(CONCEPTS_CSV)
    print(f"Concepts: {len(concepts)} | Runs per concept: {RUNS_PER_CONCEPT}")
    print(f"Concurrency={MAX_CONCURRENCY}, Max RPS={MAX_RPS}, Max Retries={MAX_RETRIES}")

    # Prepare client and shared instructions
    client = AsyncOpenAI(api_key=api_key)
    instructions = build_instructions(quant_summary, textual_summary)

    means_df, runs_df, usage, total_requests = await simulate_concepts_async(
        client=client,
        concepts=concepts,
        instructions=instructions,
    )

    # Write CSVs
    means_df.to_csv(OUTPUT_CSV, index=False)
    runs_df.to_csv(RUNS_CSV, index=False)

    # Print usage summary
    print("\n=== OpenAI token usage (total across all requests) ===")
    print(f"Requests: {total_requests}")
    print(f"Input tokens:  {usage.get('input_tokens', 0)}")
    print(f"Output tokens: {usage.get('output_tokens', 0)} (reasoning: {usage.get('reasoning_tokens', 0)})")
    print(f"Cached input:  {usage.get('cached_input_tokens', 0)}")
    print(f"Total tokens:  {usage.get('total_tokens', 0)}")

    print(f"\nDone. Wrote {len(means_df)} row(s) to {OUTPUT_CSV} and {len(runs_df)} rows to {RUNS_CSV}")


def main() -> None:
    # Windows/old Python compatibility: make sure we have a clean loop
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        print("\nCancelled by user.")


if __name__ == "__main__":
    main()
