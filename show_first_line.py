#!/usr/bin/env python3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEXTUAL_DIR = BASE_DIR / "Textual Data Inputs"

if not TEXTUAL_DIR.exists():
    raise SystemExit(f"Missing folder: {TEXTUAL_DIR}")

txt_files = sorted(TEXTUAL_DIR.glob("*.txt"))
if not txt_files:
    raise SystemExit(f"No .txt files found in {TEXTUAL_DIR}")

for txt_path in txt_files:
    with txt_path.open(encoding="utf-8", errors="ignore") as handle:
        first_line = handle.readline().rstrip("\n\r")
    display = first_line if first_line else "(first line is empty)"
    print(f"{txt_path.name}: {display}")
