"""Shared configuration values and constants."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

for env_file in (BASE_DIR / ".env.local", BASE_DIR / ".env"):
    if env_file.exists():
        load_dotenv(env_file)
        break
else:
    load_dotenv()

FLATTENED_DIR = BASE_DIR / "Flattened Data Inputs"
TEXTUAL_DIR = BASE_DIR / "Textual Data Inputs"
CONCEPTS_CSV = BASE_DIR / "concepts_to_test.csv"
OUTPUT_CSV = BASE_DIR / "agent_predicted_appeal.csv"
RUNS_CSV = BASE_DIR / "agent_predicted_appeal_runs.csv"

LIKERT_ORDER = [
    "strongly_agree",
    "slightly_agree",
    "neither_agree_nor_disagree",
    "slightly_disagree",
    "strongly_disagree",
]

LIKERT_PRETTY = {
    "strongly_agree": "Strongly agree",
    "slightly_agree": "Slightly agree",
    "neither_agree_nor_disagree": "Neither agree nor disagree",
    "slightly_disagree": "Slightly disagree",
    "strongly_disagree": "Strongly disagree",
}

DEFAULT_MODEL = (
    os.getenv("AGENT_ESTIMATOR_MODEL")
    or os.getenv("OPENAI_MODEL")
    or "gpt-4.1"
)

DEFAULT_RUNS = int(os.getenv("AGENT_RUNS", "5"))
MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "3"))
