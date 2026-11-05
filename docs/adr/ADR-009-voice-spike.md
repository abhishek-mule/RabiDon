# ADR-009 — TTS voice selection & licence spike (operator-gated)

**Status:** pending (human decision required)  
**Date:** 2026-11-05 (scaffold updated in Track C; no voice locked)  
**Related:** `docs/BASELINE.md` C-01 / ADR-006 / ADR-009

## Context
RabiDon must run without a paid LLM/key dependency. Narration supports Piper/local or recorded audio. `RABIDON_TTS_PROVIDER` remains `recorded`/`unresolved` until a voice is selected, licence-reviewed, and explicitly locked by the operator. **This repo must not auto-download binaries/models or lock config.**

## Guardrails (implemented)
- `rabidon.tts.piper.voice_readiness()` reports missing binary/model/licence/pronunciation config; Piper synthesis refuses unless operator-supplied local assets exist.
- `VoiceConfig.is_unresolved()` and recorded fallback remain valid.
- Pronunciation replacements load from operator-controlled TSV/CSV/JSON (`RABIDON_PRONUNCIATION_DICT`).
- `data/` and `output/` stay ignored; fixtures must be rights-documented/synthetic.

## Operator decision (manual)
Select and lock **one** Hindi voice configuration:
- **A — Piper voice:** record model identifier (e.g. candidate `hi_IN-*`, not auto-selected), model path, source/provenance, licence (redistribution/commercial/attribution terms), sample rate/speaker if applicable.
- **B — Alternative Piper voice:** same evidence.
- **C — Recorded narration:** operator/self/consented talent; document rights/consent for voice audio.

## Evaluation checklist
| Check | Evidence / notes |
|---|---|
| Sample script (30–60s Hindi, rights-documented) | path/ref: |
| Clarity & articulation | pass/warn/fail: |
| Natural pacing |  |
| Consonant/vowel accuracy |  |
| Proper nouns / pop-culture names (e.g. Doraemon, Nobita, Shinchan, cartoon titles) |  |
| Loanwords/technical terms |  |
| Pronunciation dictionary entries added | `data/tts/pronunciation.json` or `.tsv` ref: |
| Licence basis verified (model weights/voice) | MIT/CC-BY/other + URL/ref: |
| Redistribution/use in intended outputs permitted |  |
| Attribution required? |  |
| Binary/model provenance (local install path, no auto-download) |  |
| Human acceptance | name/date: |

## Lock procedure (only after explicit operator approval)
1. Place approved model/binary locally (operator action).
2. Set `RABIDON_TTS_PROVIDER=piper` (or keep `recorded`), `RABIDON_VOICE_ID`, `RABIDON_VOICE_MODEL_PATH`, `RABIDON_PIPER_BIN` (if needed), `RABIDON_VOICE_LICENCE_REF`, `RABIDON_PRONUNCIATION_DICT`.
3. Run local readiness/sample harness against operator-supplied assets; record result in this ADR.
4. Update status to `accepted` with evidence refs.

## Interim behavior
- `recorded` adapter imports operator-provided WAV segments with duration/silence QA.
- Placeholder synthesis is marked `silent` so QA blocks — never used for real output.
- Piper synthesis blocked until config/licence/local assets are ready.

## Environment note
Current environment: Piper binary/model not present; default remains `recorded`/unresolved.
