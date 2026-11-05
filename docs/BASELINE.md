# RabiDon — Engineering Baseline & Conflict Resolutions

**Version:** 1.0  
**Date:** 5 November 2026  
**Supersedes:** Conflicting clauses in earlier `TRD.md` / `Architecture.md` drafts  
**Status:** Locked baseline — implement against this document  

---

## 1. Purpose

This document resolves the known conflicts between the earlier TRD and Architecture drafts **before coding begins**. Where the two documents disagreed, the resolution recorded here is final. All future code, migrations, tests, and docs must follow this baseline.

Project name is **RabiDon** (formerly "CreatorOps"). All config keys, package names, CLI entry points, and docs use `RabiDon` / `rabidon_*` naming.

---

## 2. Resolved conflicts

| # | Conflict | Resolution | Rationale |
|---|---|---|---|
| C-01 | Voice/config placeholder vs unresolved | **Unresolved.** Add a voice-selection + licence spike before locking config. `rabidon_VOICE_ID` stays `null` until spike completes. | Piper Hindi voices vary in quality/licence; premature lock risks rework. |
| C-02 | Approval refs inside PublishPackage vs immutable hash without refs | **Follow Architecture / ADR-003.** PublishPackage hash excludes approval-decision references. Approvals reference the completed package hash, not vice versa. | Avoids circular dependency; package stays immutable before approval exists. |
| C-03 | Telegram preview as simple local step vs external transmission | **Follow Architecture.** Telegram preview is an external transmission requiring preview-sharing permission + rights/confidentiality check before send. | Private chat is still external storage/transmission. |
| C-04 | Scene timing pre-resolved vs provisional-then-resolved | **Follow Architecture.** Scene plan is provisional before TTS; final timings resolve from measured narration segments. | TTS duration is unknown until synthesis; avoids fake precision. |
| C-05 | "Reproducible render" ambiguity | **Honest framing:** traceable reruns, not cross-machine byte-identical media. Manifest records all inputs/versions; output may differ across FFmpeg/platform versions. | Byte-identity across environments is not achievable reliably. |

---

## 3. Locked design decisions (ADR summary)

| ADR | Decision | Status |
|---|---|---|
| ADR-001 | SQLite + local files + single worker for MVP | Accepted |
| ADR-002 | Facts, rights, QA, human approval = independent gates | Accepted |
| ADR-003 | PublishPackage hash excludes approval-decision refs | Accepted (resolves C-02) |
| ADR-004 | Private upload and public release separately authorized | Accepted |
| ADR-005 | External previews require sharing permission | Accepted (resolves C-03) |
| ADR-006 | No mandatory paid model or cloud generation | Accepted |
| ADR-007 | Pause on ambiguous uploads; no blind retries | Accepted |
| ADR-008 | Integer paise, UTC, integer timeline milliseconds | Accepted |
| ADR-009 | Voice unresolved until selection+licence spike | Accepted (resolves C-01) |
| ADR-010 | Provisional scene plan before TTS; final timing post-TTS | Accepted (resolves C-04) |
| ADR-011 | Reproducibility = traceable rerun, not byte identity | Accepted (resolves C-05) |

---

## 4. Updated contracts

### 4.1 Voice configuration (resolves C-01)

```env
# .env.example — voice unresolved until spike
RABIDON_TTS_PROVIDER=unresolved   # piper | recorded
RABIDON_VOICE_ID=                 # null until spike completes
RABIDON_VOICE_MODEL_PATH=
RABIDON_VOICE_LICENCE_REF=
```

**Spike task (before Sprint 1 media work):** download/test 2–3 Hindi Piper voices, check licence per voice, record sample, human-accept clarity/pronunciation, then lock `RABIDON_VOICE_ID` + licence ref. Until then, `recorded` narration is the default fallback.

### 4.2 PublishPackage (resolves C-02)

```json
{
  "schema_version": 1,
  "package_id": "pkg_1",
  "video_id": "video_1",
  "artifact_hash": "sha256:...",
  "manifest_hash": "sha256:...",
  "destination": {"platform": "youtube", "account_id": "resolved_account"},
  "action": "private_upload",
  "privacy": "private",
  "title": "Approved title",
  "description": "Approved description",
  "caption_hash": "sha256:...",
  "required_attributions": [],
  "qa_report_id": "qa_1",
  "asset_permission_refs": ["permission_1"]
}
```

**No `approval_refs` field.** Approval decisions live in a separate `approval_decisions` table referencing `package_hash`. Package is hashed and frozen before any approval exists.

### 4.3 Telegram preview (resolves C-03)

Preview send is gated:

```text
preview_request
  → check asset rights (all approved for "external_preview" use)
  → check client confidentiality (if client project)
  → require preview-sharing permission record
  → create approval request (action=telegram_preview)
  → human approves
  → send via Telegram adapter
```

Unknown/pending rights assets block Telegram preview, not just public publish.

### 4.4 Scene timing (resolves C-04)

```json
{
  "scene_plan_status": "provisional",
  "scenes": [
    {
      "id": "s1",
      "narration_segment_ids": [],
      "timeline_start_ms": null,
      "timeline_end_ms": null,
      "estimated_duration_ms": 4000,
      "layers": [...]
    }
  ]
}
```

After TTS:

```json
{
  "scene_plan_status": "resolved",
  "timing_revision_id": "tim_r1",
  "scenes": [
    {
      "id": "s1",
      "narration_segment_ids": ["n1"],
      "timeline_start_ms": 0,
      "timeline_end_ms": 4200
    }
  ]
}
```

Renderer only accepts `resolved` plans for final render; `provisional` is preview-draft only.

### 4.5 Reproducibility statement (resolves C-05)

Docs and manifest must state:

> "Renders are traceable and re-runnable from recorded inputs/versions. Byte-identical output across machines or FFmpeg versions is not guaranteed."

Manifest records input hashes, tool versions (measured at runtime), template version, settings—enough to reproduce intent, not bytes.

---

## 5. Implementation strategy (gate-driven slices)

| Phase | Goal / exit gate | Build now | Defer |
|---|---|---|---|
| **0 — Foundation** | Repo, config, logging, migrations, CLI skeleton, test harness | `pyproject.toml`, `rabidon/{cli,config,db,jobs}/`, `.env.example`, SQLite WAL+FK+busy_timeout, Pydantic models, SHA-256/canonical JSON utils, UTC/paise/ms helpers | FastAPI, Postgres/Redis, n8n, dashboard |
| **0 — Editorial proof** | One approved evidence-backed script | topics/sources/claims/reviews/scripts repos+migrations, claim states, human acceptance bound to claim+evidence revision, script versioning, unsupported-factual block | Hosted LLM as dependency |
| **0 — Media proof** | One watchable local preview, no public upload | TTS (Piper+recorded fallback), segment timing QA, sentence captions, 1 `commentary_v1` template, manifest, QA report | Word alignment/ASR, cinematic AI, multi-template |
| **0 — Control proof** | Exact-action review before external side effects | Asset registry/permissions, rights gate, approval requests/decisions/tokens, Telegram preview (with sharing permission), local archive | Public posting, audience Telegram, outreach |
| **1 — Controlled publish** | Private YouTube + reconciliation | Immutable PublishPackage, private≠public approval, resumable wrapper, publication_attempts, reconciliation_required, manual observations | Auto-publish, claim automation |
| **2 — Business validation** | Paid pilot / buying signal | Manual leads+opt-out, demo via same pipeline, approved outreach, client isolation, delivery/acceptance, invoices/payments/allocations/expenses/time, contribution reports | Bulk CRM, auto follow-ups |
| **3–4** | Demand-justified scale | Metrics, renewals, optional 2nd publisher | Meta broad rollout, cloud migration |

**Per-slice rule:** inspect → plan+affected modules → migration+tests → implement → run existing `pytest`/`ruff` → report actual results/limitations. No external action without exact operator approval.

---

## 6. Repo reuse map

| Area | Reuse/adapt | Integration point | Must still build |
|---|---|---|---|
| YouTube upload | `wakamex/youtube-cli-uploader` | Wrap as `publish/youtube.py` behind `Publisher` port | Approval binding, idempotency, session persistence, reconciliation, private/public split, audit |
| TTS | Piper (`OHF-Voice/piper1-gpl`) | `tts/piper.py` + `tts/recorded.py` | Voice selection/licence spike, pronunciation dict, segment QA |
| Render/QA patterns | `reelforge`, `Kinocut`, `NovaClip` | Reference only → thin `Renderer`/`QA` interface + 1 deterministic template | Scene-plan contract, explicit FFmpeg maps, Hindi caption rules, rights QA, manifest hashing |
| Pipeline structure | `video-edit-agent`, `Chopify` | Reference for step decomposition | Deterministic testable Python pipeline |
| Orchestration | n8n (later), mcp-video (much later) | After CLI+SQLite+Telegram proven | SQLite leases/heartbeats/owner tokens, bounded retry |
| CRM/finance/evidence | — | — | Claim ledger, asset permissions, approval state machine, opt-out, paise accounting |

**Guardrails:** pin versions/licences; adapters replaceable; no third-party internals imported into domain; synthetic/rights-documented test fixtures; live tests only with explicit opt-in + approved test accounts.

---

## 7. Sprint 1 build order

1. Init Python package + `pyproject.toml` + `ruff`/`pytest` + `.env.example` (RabiDon naming) + structured JSON logging.
2. SQLite migrations/pragmas; repositories; `BEGIN IMMEDIATE` claim helper.
3. Core schemas: topic/source/claim+revision+review, script revision, asset+permission, job, approval request/decision, audit event.
4. CLI: `init`, `topic create`, `source add`, `claim add/review`, `script import/approve` (evidence gate).
5. Piper/recorded TTS adapter + segment timing + silence/failure detection.
6. Caption builder (sentence cues, Hindi UTF-8, SRT/ASS, overlap/empty validation).
7. `commentary_v1` template: provisional scene plan → TTS → resolved timing → explicit FFmpeg graph → preview → manifest → QA.
8. Telegram approval flow (allowlist, opaque token, expiry, hash recheck, duplicate-safe, preview-sharing/right checks).
9. Mandatory regression tests as features land.

---

## 8. Early risks

| Risk | Mitigation |
|---|---|
| Hindi font/glyph rendering | Fixture-first test with selected font; human glyph review |
| Piper voice quality/licence | Voice-selection spike before locking config |
| FFmpeg graph complexity | Fixture-first, explicit maps, temp→validate→promote |
| Upload ambiguity | Design reconciliation before first live upload |
| Scope creep (scraping/auto-publish/multi-platform) | Product boundaries + per-slice gates |

No external side effects occur as part of this baseline analysis.
