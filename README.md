# RabiDon

Local-first, approval-gated production assistant (CLI + Telegram approvals) for original Hindi motion-graphics explainers and client production.

**Status:** implementation in progress (0A–0D foundations + local preview pipeline, offline tests passing). No public upload/publishing performed by this repo state.

## Source of truth
- `docs/BASELINE.md` — locked conflict resolutions / ADR summary (follow where older docs disagree)
- `PRD.md`, `TRD.md`, `Architecture.md`, `AGENTS.md`

## MVP shape
- Python 3.11+, CLI-first, SQLite (local disk, WAL), 1 worker, local files
- Piper/recorded narration (voice selection/licence pending — ADR-009), FFmpeg, sentence captions, QA
- Human approval before external side effects; private upload ≠ public release

## Quick checks (offline)
```bash
PYTHONPATH=. python3 -m pytest -v
# ruff check .  (if ruff installed)
```

## CLI (local)
```bash
PYTHONPATH=. python3 -m rabidon.cli.main --help
PYTHONPATH=. python3 -m rabidon.cli.main init
```

## Safety
No episode scraping, piracy/DRM bypass, auto-publish, bulk outreach, or paid LLM dependency required. External Telegram/YouTube actions require explicit exact-action approval and are not enabled by default tests.
