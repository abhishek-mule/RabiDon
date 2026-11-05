from __future__ import annotations

import csv
import json
from pathlib import Path


def load_pronunciation_dict(path: Path | str | None) -> list[tuple[str, str]]:
    """Operator-controlled pronunciation replacements (ADR-009).

    Supported formats:
    - `.json`: object `{"source": "replacement"}` or list `[["source","replacement"]]`
    - `.tsv`/`.csv`/text: `source<TAB>replacement` or CSV rows; `#` comments ignored.
    Applied in order. Missing file returns empty rules (safe fallback).
    """
    if path is None:
        return []
    p = Path(path)
    if not p.exists():
        return []
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return [(str(k), str(v)) for k, v in data.items()]
        if isinstance(data, list):
            out: list[tuple[str, str]] = []
            for row in data:
                if isinstance(row, (list, tuple)) and len(row) >= 2:
                    out.append((str(row[0]), str(row[1])))
            return out
        return []
    rows: list[tuple[str, str]] = []
    text = p.read_text(encoding="utf-8").splitlines()
    for line in text:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line:
            a, b = line.split("\t", 1)
        else:
            parts = list(csv.reader([line]))[0]
            if len(parts) < 2:
                continue
            a, b = parts[0], parts[1]
        rows.append((a, b))
    return rows


def apply_pronunciation(text: str, rules: list[tuple[str, str]]) -> str:
    out = text
    for src, repl in rules:
        if src:
            out = out.replace(src, repl)
    return out


def normalize_for_tts(text: str, dict_path: Path | str | None = None) -> str:
    return apply_pronunciation(text, load_pronunciation_dict(dict_path))
