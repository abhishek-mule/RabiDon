# CreatorOps AI — Technical Requirements Document (TRD)

**Version:** 1.0  
**Date:** 5 November 2026  
**Status:** Implementation-ready technical baseline  
**Derived from:** `PRD.md` v2.0  
**Owner:** Founder / solo operator  

---

## 1. Purpose

This TRD translates the CreatorOps AI PRD into implementable technical requirements, architecture, data contracts, workflows, APIs, storage rules, QA gates, and acceptance criteria.

The MVP is a **local-first, single-operator system** that turns an approved topic and evidence-backed Hindi script into a reviewable motion-graphics explainer video. It must operate without a paid LLM dependency and must not publish unverified, rights-unclear, or unapproved content.

---

## 2. System Context

```text
Founder
  │
  ├── CLI
  ├── Telegram Bot
  └── Future Web Dashboard
          │
          ▼
    CreatorOps Core
          │
  ┌───────┼─────────┬─────────────┬─────────────┐
  │       │         │             │             │
Research  Claims  Scripting  Scene Planner  Asset Registry
  │       │         │             │             │
  └───────┴────┬────┴─────────────┴─────────────┘
               ▼
         Render Pipeline
   Piper TTS → Captions → FFmpeg → QA
               │
               ▼
       Approval Workflow
               │
       ┌───────┴────────┐
       │                │
 Local Archive     Publishing Adapters
                        │
              YouTube / Telegram / later Meta
```

### System boundaries

- CreatorOps does **not** scrape, download, mirror, or redistribute third-party episodes.
- CreatorOps does **not** automatically determine copyright clearance or monetization eligibility.
- CreatorOps does **not** send outreach without explicit human approval.
- CreatorOps does **not** publish content without explicit approval for the relevant release action.

---

## 3. Architectural Principles

| Principle | Technical consequence |
|---|---|
| Local-first MVP | SQLite, local filesystem, CLI-first workflow |
| Configurable dependencies | Voice, LLM, templates, destinations, and quotas are adapter/config driven |
| Reproducible renders | Every render has a content-addressable manifest |
| Safe failure | Failed QA, rights checks, or approvals block publication |
| Idempotent side effects | Publishing and job execution use idempotency keys and reconciliation |
| Human-controlled irreversible actions | Public release, outreach send, and client delivery require approval records |
| Minimal moving parts | No Redis, FastAPI, PostgreSQL, Docker, or n8n until justified |
| Auditability | State changes, approvals, rights decisions, and publishing events are logged |

---

## 4. MVP Technology Stack

| Layer | MVP choice | Rationale |
|---|---|---|
| Language | Python 3.11+ | FFmpeg, Piper, Telegram, and data tooling ecosystem |
| CLI | Typer or Click | Simple command interface |
| Database | SQLite with WAL mode | Single operator, local-first, transactional state |
| Job queue | SQLite-backed worker table | Avoid Redis until concurrency requires it |
| TTS | Piper | Local, offline, Hindi voice support |
| Audio processing | FFmpeg / ffprobe | Duration, loudness, concat, ducking |
| Rendering | FFmpeg | Deterministic template rendering |
| Captions | ASS/SRT generated from narration timing | No ASR dependency for initial captions |
| Approval | Telegram Bot API | Mobile-friendly approve/change/reject flow |
| Publishing | YouTube Data API v3 adapter | Private-first upload |
| Storage | Local filesystem | MVP simplicity |
| Configuration | `.env` + YAML/TOML | Secrets and non-secret settings separated |
| Testing | pytest | Unit, integration, and failure-injection tests |
| Logging | Structured JSON logs | Observable jobs and external calls |

### Deferred components

| Component | Trigger to introduce |
|---|---|
| FastAPI | Web dashboard, external integrations, or remote access |
| PostgreSQL | Concurrent workers, remote access, or complex reporting |
| Redis | Rate limiting, distributed locks, or high-throughput queues |
| Docker Compose | Repeatable deployment or multi-service setup |
| n8n | Stable workflow requiring visual orchestration |
| Object storage | Large asset library, backup needs, or remote collaboration |
| Next.js dashboard | Operational UI becomes more efficient than CLI/Telegram |

---

## 5. Repository Structure

```text
creatorops/
├── README.md
├── PRD.md
├── TRD.md
├── pyproject.toml
├── .env.example
├── Makefile
├── creatorops/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── db/
│   │   ├── connection.py
│   │   ├── migrations/
│   │   └── repositories/
│   ├── jobs/
│   │   ├── queue.py
│   │   ├── worker.py
│   │   └── recovery.py
│   ├── research/
│   │   ├── models.py
│   │   ├── sources.py
│   │   └── claims.py
│   ├── scripts/
│   │   ├── writer.py
│   │   ├── reviewer.py
│   │   └── quality.py
│   ├── scene_planner/
│   │   ├── planner.py
│   │   └── schemas.py
│   ├── ai/
│   │   ├── router.py
│   │   └── providers/
│   │       ├── rules.py
│   │       ├── gemini.py
│   │       └── local.py
│   ├── tts/
│   │   ├── base.py
│   │   ├── piper.py
│   │   └── recorded.py
│   ├── captions/
│   │   ├── builder.py
│   │   └── renderer.py
│   ├── render/
│   │   ├── ffmpeg.py
│   │   ├── audio.py
│   │   ├── manifest.py
│   │   └── templates/
│   │       ├── commentary.py
│   │       ├── listicle.py
│   │       └── comparison.py
│   ├── qa/
│   │   ├── media.py
│   │   ├── captions.py
│   │   ├── rights.py
│   │   └── report.py
│   ├── assets/
│   │   ├── registry.py
│   │   └── rights.py
│   ├── approvals/
│   │   ├── service.py
│   │   └── telegram.py
│   ├── publish/
│   │   ├── package.py
│   │   ├── youtube.py
│   │   ├── telegram.py
│   │   └── local_archive.py
│   ├── crm/
│   │   ├── leads.py
│   │   ├── outreach.py
│   │   └── clients.py
│   ├── finance/
│   │   ├── invoices.py
│   │   ├── payments.py
│   │   └── economics.py
│   └── analytics/
│       ├── metrics.py
│       └── reports.py
├── bot/
│   ├── main.py
│   ├── handlers.py
│   └── security.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── data/
│   ├── assets/
│   │   ├── graphics/
│   │   ├── audio/
│   │   ├── fonts/
│   │   └── generated/
│   ├── rights/
│   ├── projects/
│   └── backups/
└── output/
```

---

## 6. Configuration

### 6.1 Environment variables

```env
# Core
CREATOROPS_ENV=development
CREATOROPS_DB_URL=sqlite:///data/creatorops.db
CREATOROPS_DATA_DIR=./data
CREATOROPS_OUTPUT_DIR=./output

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_APPROVER_CHAT_ID=
TELEGRAM_ALLOWED_USER_IDS=

# YouTube
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_REFRESH_TOKEN=
YOUTUBE_DEFAULT_PRIVACY=private
YOUTUBE_UPLOAD_DAILY_OPERATIONAL_CAP=3

# AI providers
AI_PROVIDER_ORDER=rules,gemini,local
GEMINI_API_KEY=
GEMINI_MODEL=
GEMINI_TIMEOUT_SECONDS=30
GEMINI_MAX_RETRIES=2

# Piper
PIPER_BIN=piper
PIPER_MODEL_DIR=./data/models/piper
PIPER_DEFAULT_VOICE=hi_IN-default
```

### 6.2 Configuration rules

- Secrets must never be committed to version control.
- Non-secret defaults must live in a versioned config file.
- Provider order, model names, timeouts, retry limits, and quotas must be configurable.
- YouTube operational caps are application-level controls, not platform-limit assumptions.
- Configuration changes that affect a render must be recorded in the render manifest.

---

## 7. Database Design

### 7.1 SQLite pragmas

```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
```

### 7.2 Core schema

```sql
CREATE TABLE topics (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  angle TEXT NOT NULL,
  audience TEXT,
  format TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 5,
  status TEXT NOT NULL DEFAULT 'idea',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sources (
  id INTEGER PRIMARY KEY,
  url TEXT,
  title TEXT NOT NULL,
  source_type TEXT NOT NULL,
  accessed_at TEXT NOT NULL,
  reliability TEXT NOT NULL DEFAULT 'unknown',
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE claims (
  id INTEGER PRIMARY KEY,
  topic_id INTEGER NOT NULL REFERENCES topics(id),
  text TEXT NOT NULL,
  status TEXT NOT NULL CHECK (
    status IN ('supported','partial','conflicting','unsupported','unknown')
  ),
  reviewer TEXT,
  review_notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE claim_sources (
  claim_id INTEGER NOT NULL REFERENCES claims(id),
  source_id INTEGER NOT NULL REFERENCES sources(id),
  supporting_note TEXT,
  excerpt TEXT,
  PRIMARY KEY (claim_id, source_id)
);

CREATE TABLE scripts (
  id INTEGER PRIMARY KEY,
  topic_id INTEGER NOT NULL REFERENCES topics(id),
  version INTEGER NOT NULL,
  text TEXT NOT NULL,
  language TEXT NOT NULL DEFAULT 'hi-IN',
  quality_score INTEGER,
  approval_status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (topic_id, version)
);

CREATE TABLE script_claims (
  script_id INTEGER NOT NULL REFERENCES scripts(id),
  claim_id INTEGER NOT NULL REFERENCES claims(id),
  PRIMARY KEY (script_id, claim_id)
);

CREATE TABLE assets (
  id INTEGER PRIMARY KEY,
  asset_type TEXT NOT NULL CHECK (
    asset_type IN ('graphic','video','audio','font','generated','other')
  ),
  local_path TEXT NOT NULL,
  source_url TEXT,
  owner TEXT,
  provenance TEXT,
  rights_basis TEXT NOT NULL CHECK (
    rights_basis IN (
      'owned','licensed','written_permission',
      'reviewed_exception','unknown'
    )
  ),
  rights_status TEXT NOT NULL CHECK (
    rights_status IN ('pending','approved','rejected','expired')
  ),
  licence_ref TEXT,
  permitted_use TEXT,
  attribution TEXT,
  expires_at TEXT,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scene_plans (
  id INTEGER PRIMARY KEY,
  script_id INTEGER NOT NULL REFERENCES scripts(id),
  version INTEGER NOT NULL,
  plan_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE videos (
  id INTEGER PRIMARY KEY,
  topic_id INTEGER NOT NULL REFERENCES topics(id),
  script_id INTEGER NOT NULL REFERENCES scripts(id),
  scene_plan_id INTEGER NOT NULL REFERENCES scene_plans(id),
  template TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'created',
  preview_path TEXT,
  final_path TEXT,
  duration_seconds REAL,
  manifest_path TEXT,
  content_hash TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE jobs (
  id INTEGER PRIMARY KEY,
  job_type TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  idempotency_key TEXT UNIQUE,
  status TEXT NOT NULL DEFAULT 'queued',
  attempts INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 3,
  run_after TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  locked_by TEXT,
  locked_at TEXT,
  heartbeat_at TEXT,
  lease_expires_at TEXT,
  last_error TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_jobs_ready
ON jobs (status, run_after)
WHERE status = 'queued';

CREATE TABLE approvals (
  id INTEGER PRIMARY KEY,
  object_type TEXT NOT NULL,
  object_id INTEGER NOT NULL,
  object_version TEXT NOT NULL,
  object_hash TEXT NOT NULL,
  action TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (
    decision IN ('approved','changes_requested','rejected','expired')
  ),
  approver_id TEXT NOT NULL,
  decided_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TEXT,
  notes TEXT
);

CREATE TABLE publications (
  id INTEGER PRIMARY KEY,
  video_id INTEGER NOT NULL REFERENCES videos(id),
  destination TEXT NOT NULL,
  remote_id TEXT,
  remote_url TEXT,
  state TEXT NOT NULL DEFAULT 'draft',
  privacy TEXT,
  idempotency_key TEXT UNIQUE,
  publish_package_path TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (video_id, destination)
);

CREATE TABLE observations (
  id INTEGER PRIMARY KEY,
  publication_id INTEGER NOT NULL REFERENCES publications(id),
  claim_status TEXT NOT NULL CHECK (
    claim_status IN ('unknown','no_claim_observed','active','released')
  ),
  restriction_status TEXT NOT NULL DEFAULT 'unknown' CHECK (
    restriction_status IN ('unknown','none_observed','blocked','other')
  ),
  source TEXT NOT NULL CHECK (
    source IN ('manual_studio','email_notification','partner_api')
  ),
  observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewer TEXT,
  evidence_ref TEXT,
  notes TEXT
);

CREATE TABLE leads (
  id INTEGER PRIMARY KEY,
  handle TEXT,
  platform TEXT,
  source TEXT NOT NULL,
  contact_provenance TEXT,
  fit_score INTEGER,
  status TEXT NOT NULL DEFAULT 'new',
  opt_out INTEGER NOT NULL DEFAULT 0,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clients (
  id INTEGER PRIMARY KEY,
  lead_id INTEGER REFERENCES leads(id),
  name TEXT NOT NULL,
  package TEXT,
  rate_inr INTEGER,
  start_date TEXT,
  renewal_date TEXT,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE invoices (
  id INTEGER PRIMARY KEY,
  client_id INTEGER NOT NULL REFERENCES clients(id),
  period_start TEXT,
  period_end TEXT,
  amount_inr INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'due',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE payments (
  id INTEGER PRIMARY KEY,
  invoice_id INTEGER REFERENCES invoices(id),
  amount_inr INTEGER NOT NULL,
  paid_at TEXT NOT NULL,
  allocation_note TEXT
);

CREATE TABLE llm_calls (
  id INTEGER PRIMARY KEY,
  task TEXT NOT NULL,
  provider TEXT NOT NULL,
  model TEXT,
  prompt_version TEXT,
  input_hash TEXT,
  output_hash TEXT,
  latency_ms INTEGER,
  usage_json TEXT,
  success INTEGER NOT NULL,
  error TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_events (
  id INTEGER PRIMARY KEY,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  object_type TEXT NOT NULL,
  object_id INTEGER,
  before_json TEXT,
  after_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## 8. Domain Models and Contracts

### 8.1 Research dossier

```json
{
  "topic_id": 12,
  "question": "Doraemon gadgets real life mein possible hain?",
  "sources": [
    {
      "source_id": 31,
      "url": "https://example.com/source",
      "title": "Example source",
      "source_type": "secondary",
      "accessed_at": "2026-11-05T14:00:00+05:30",
      "reliability": "credible"
    }
  ],
  "claims": [
    {
      "claim_id": 88,
      "text": "Example factual claim.",
      "status": "supported",
      "source_ids": [31]
    }
  ]
}
```

### 8.2 Script contract

```json
{
  "script_id": 45,
  "topic_id": 12,
  "version": 3,
  "language": "hi-IN",
  "hook": "Bachpan ke Doraemon gadgets mein se ek aaj sach mein exist karta hai.",
  "body": [
    {
      "beat": "context",
      "text": "Example context sentence.",
      "claim_ids": [88]
    }
  ],
  "payoff": "Example payoff sentence.",
  "cta": null,
  "estimated_duration_seconds": 58
}
```

### 8.3 Scene plan contract

```json
{
  "scene_plan_id": 19,
  "script_id": 45,
  "version": 2,
  "canvas": {
    "width": 1080,
    "height": 1920,
    "fps": 30
  },
  "scenes": [
    {
      "scene_id": "s001",
      "narration_beat": "context",
      "start_seconds": 0.0,
      "end_seconds": 6.4,
      "on_screen_text": "Example on-screen text",
      "visual": {
        "asset_ids": [101],
        "motion": "slow_zoom",
        "transition_in": "fade",
        "transition_out": "cut"
      },
      "sfx": [],
      "asset_refs_required": true
    }
  ]
}
```

### 8.4 Render manifest

```json
{
  "manifest_version": 1,
  "video_id": 77,
  "script_id": 45,
  "script_hash": "sha256:...",
  "scene_plan_id": 19,
  "scene_plan_hash": "sha256:...",
  "template": "commentary_v1",
  "template_version": "1.2.0",
  "voice": {
    "provider": "piper",
    "model": "hi_IN-default",
    "voice_profile": "clear_explainer",
    "speed": 1.0
  },
  "assets": [
    {
      "asset_id": 101,
      "content_hash": "sha256:...",
      "rights_status": "approved",
      "rights_basis": "owned"
    }
  ],
  "render_settings": {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "video_codec": "libx264",
    "audio_codec": "aac",
    "loudness_target_lufs": -16
  },
  "qa_report_path": "output/video_77/qa_report.json",
  "created_at": "2026-11-05T14:30:00+05:30"
}
```

### 8.5 Publish package

```json
{
  "package_version": 1,
  "video_id": 77,
  "manifest_hash": "sha256:...",
  "destination": "youtube",
  "privacy": "private",
  "title": "Example Hindi title",
  "description": "Example description",
  "tags": [],
  "captions": {
    "srt_path": "output/video_77/captions.srt"
  },
  "asset_rights_snapshot": [
    {
      "asset_id": 101,
      "rights_status": "approved",
      "rights_basis": "owned"
    }
  ],
  "approval_refs": [
    {
      "approval_id": 501,
      "action": "final_render",
      "object_hash": "sha256:..."
    }
  ]
}
```

---

## 9. Workflow Requirements

### 9.1 Topic workflow

```text
idea → researching → evidence_review → scripting → script_review
     → approved → scene_planning → preview_render → qa
     → human_review → final_render → publish_package
     → private_upload → processing → manual_review
     → public_release_approval → published
```

### 9.2 Required state transitions

| From | To | Condition |
|---|---|---|
| `idea` | `researching` | Topic accepted |
| `researching` | `evidence_review` | At least one source attached |
| `evidence_review` | `scripting` | Claims reviewed |
| `scripting` | `script_review` | Script draft created |
| `script_review` | `approved` | Human approval + quality threshold met |
| `approved` | `scene_planning` | Scene plan generated |
| `scene_planning` | `preview_render` | Asset plan resolvable |
| `preview_render` | `qa` | Preview file exists |
| `qa` | `human_review` | QA passed or warnings acknowledged |
| `human_review` | `final_render` | Approval recorded |
| `final_render` | `publish_package` | Final QA passed |
| `publish_package` | `private_upload` | Private-upload approval recorded |
| `private_upload` | `processing` | Remote ID stored |
| `processing` | `manual_review` | Platform processing observed |
| `manual_review` | `public_release_approval` | Manual claim/restriction review recorded |
| `public_release_approval` | `published` | Separate public approval recorded |

### 9.3 Exception states

| State | Trigger |
|---|---|
| `needs_changes` | Reviewer requests changes |
| `rejected` | Reviewer rejects content |
| `failed` | Render, QA, TTS, or job failure |
| `cancelled` | Operator cancels topic/video |
| `blocked_rights` | Rights gate fails |
| `expired_approval` | Approval expires before action |

---

## 10. Job Queue Requirements

### 10.1 Job lifecycle

```text
queued → running → succeeded
              ├──→ retry_scheduled → queued
              ├──→ failed → dead
              └──→ awaiting_approval
```

### 10.2 Queue rules

- Use SQLite transactions with `BEGIN IMMEDIATE` for job claiming.
- Use a worker lease with `lease_expires_at`.
- Workers must send heartbeats during long-running jobs.
- Expired leases must be recoverable.
- Jobs must have bounded retries and exponential backoff.
- Jobs must have a `dead` state after max attempts.
- Long renders and network uploads must not hold a database transaction open.
- Every job must support an idempotency key.
- Job payload and result artifacts must be versioned.

### 10.3 Job types

| Job type | Input | Output |
|---|---|---|
| `research_topic` | Topic ID | Research dossier |
| `draft_script` | Topic ID, format | Script draft |
| `review_script` | Script ID | QA/quality report |
| `generate_scene_plan` | Script ID | Scene plan |
| `generate_narration` | Script ID, voice profile | Narration and segment timings |
| `build_captions` | Script ID, narration timing | SRT/ASS files |
| `render_preview` | Video ID | Preview MP4 + QA report |
| `render_final` | Video ID, approval ID | Final MP4 + manifest |
| `create_publish_package` | Video ID, destination | Publish package |
| `upload_youtube_private` | Publication ID | Remote ID and upload state |
| `check_processing_status` | Publication ID | Updated publication state |
| `send_telegram_preview` | Video ID | Telegram message ID |
| `archive_local` | Video ID | Archived files and manifest |

---

## 11. AI Router Requirements

### 11.1 Provider interface

```python
class AIProvider(Protocol):
    name: str

    def generate(
        self,
        task: str,
        prompt: str,
        schema: dict | None = None,
        timeout_seconds: int = 30,
        max_tokens: int | None = None,
    ) -> AIResult:
        ...
```

### 11.2 AI result

```json
{
  "task": "script_draft",
  "provider": "gemini",
  "model": "configured-model",
  "text": "Example output",
  "structured": {},
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0
  },
  "latency_ms": 1200,
  "prompt_version": "script_draft_v3"
}
```

### 11.3 Routing rules

- Provider order must be configurable per task.
- Rules provider must be available for classification, caption cleanup, and fallback workflows.
- Free hosted providers are optional accelerators.
- A provider timeout, rate limit, quota error, or malformed response must trigger the next provider.
- Structured outputs must be schema-validated.
- Invalid output must not silently pass.
- Every call must be logged in `llm_calls`.
- Prompt templates must be versioned.
- Cached results must be keyed by task, prompt version, and input content hash.
- Cached factual research must have a freshness/revalidation policy.

### 11.4 Required AI guardrails

- AI cannot mark a claim as `supported`.
- AI cannot approve a script.
- AI cannot approve rights.
- AI cannot publish content.
- AI cannot send outreach.
- AI cannot invent source URLs, quotes, dates, episode numbers, or statistics.
- Unsupported factual assertions must be blocked from factual scripts.

---

## 12. Piper TTS Requirements

### 12.1 Functional requirements

- Accept Hindi UTF-8 text.
- Split text into configurable sentence or chunk units.
- Generate one WAV file per segment.
- Measure segment duration using `ffprobe`.
- Concatenate segments into a master narration WAV.
- Preserve segment start/end timings.
- Detect silent, zero-duration, or failed segments.
- Support pronunciation overrides for proper nouns.
- Store voice provider, model, voice profile, speed, and licence/reference metadata.

### 12.2 TTS output contract

```json
{
  "narration_path": "output/video_77/narration.wav",
  "total_duration_seconds": 58.2,
  "segments": [
    {
      "index": 0,
      "text": "Example Hindi sentence.",
      "audio_path": "output/video_77/segments/s000.wav",
      "start_seconds": 0.0,
      "end_seconds": 3.2,
      "duration_seconds": 3.2,
      "status": "ok"
    }
  ]
}
```

### 12.3 Failure handling

| Failure | Required behaviour |
|---|---|
| Piper binary missing | Fail job with actionable error |
| Model/voice missing | Fail job with configuration guidance |
| Silent output | Mark segment failed; do not concatenate blindly |
| Pronunciation error | Allow dictionary override and regeneration |
| Partial generation | Preserve completed segments; retry only failed segments |

---

## 13. Caption Requirements

### 13.1 MVP caption mode

- Sentence-level captions derived from TTS segment timing.
- Hindi UTF-8 rendering.
- Configurable font, size, colour, outline, safe margins, and maximum characters per line.
- SRT export.
- ASS rendering for final video.
- Caption timing must cover narration duration.
- Empty, malformed, or overlapping cues must fail QA.

### 13.2 Later caption mode

- Word-level highlighting through a separate alignment stage.
- Alignment output must be versioned and independently reviewable.
- Alignment failure must fall back to sentence captions, not block the entire render.

---

## 14. Render Engine Requirements

### 14.1 Render inputs

- Approved script version.
- Approved scene plan version.
- Narration audio and segment timings.
- Rights-approved assets.
- Template version.
- Brand configuration.
- Render settings.

### 14.2 Render outputs

- Preview MP4.
- Final MP4.
- SRT/ASS captions.
- Render manifest.
- QA report.
- Asset manifest.
- Thumbnail or cover asset, where applicable.

### 14.3 Template contract

Each template must define:

```json
{
  "template_id": "commentary_v1",
  "version": "1.2.0",
  "canvas": {"width": 1080, "height": 1920, "fps": 30},
  "required_assets": ["background", "accent_graphic"],
  "optional_assets": ["music_bed", "logo"],
  "supported_scene_motions": [
    "static", "slow_zoom", "pan", "ken_burns", "kinetic_text"
  ],
  "audio_rules": {
    "loudness_target_lufs": -16,
    "music_ducking": true,
    "max_true_peak_dbtp": -1.5
  },
  "caption_rules": {
    "mode": "sentence",
    "max_chars_per_line": 28,
    "safe_margin_px": 120
  }
}
```

### 14.4 FFmpeg implementation rules

- Build explicit input maps; do not rely on implicit index assumptions.
- Generate the filter graph programmatically from the scene plan.
- Separate source-trim timing from output-timeline placement.
- Use `setpts=PTS-STARTPTS+<timeline_start>/TB` or an equivalent explicit timing method.
- Validate that every referenced input stream exists.
- Validate that every filter label is defined exactly once and consumed correctly.
- Render preview at reduced resolution first.
- Render final only after human approval.
- Derive final duration from narration, not a hard-coded value.
- Preserve logs and return non-zero exit status on failure.
- Do not hold a DB transaction open during rendering.

### 14.5 Performance requirements

- Initial render concurrency: 1.
- Measure render wall time, CPU usage, peak memory, and output size.
- Do not increase concurrency without benchmark data.
- Preview render must be materially faster than final render.
- A failed render must not corrupt previous successful artifacts.

---

## 15. QA Requirements

### 15.1 Mandatory QA checks

| Check | Pass condition |
|---|---|
| File integrity | Output opens and has expected container/codec |
| Duration | Duration is within configured tolerance of narration duration |
| Resolution | Final render is 1080x1920; preview matches configured preview size |
| Audio stream | Audio stream exists and is non-silent |
| Loudness | Integrated loudness and true peak are within configured bounds |
| Clipping | No clipping detected |
| Captions | Cues exist, cover narration, and have valid timing |
| Hindi text | No missing glyph/tofu indicators in sampled frames |
| Assets | All referenced assets resolve |
| Rights | All public-package assets have approved rights status |
| Timeline | No unintended black frames or unexplained gaps |
| Manifest | Manifest hashes match actual inputs |
| Approval | Required approvals match exact content version/hash |

### 15.2 QA report

```json
{
  "video_id": 77,
  "qa_version": "1.0.0",
  "result": "pass_with_warnings",
  "checks": [
    {
      "check": "audio_loudness",
      "result": "pass",
      "value": -16.1,
      "threshold": "-16 LUFS ±1"
    },
    {
      "check": "rights_status",
      "result": "pass",
      "approved_assets": 4,
      "blocked_assets": 0
    }
  ],
  "warnings": [],
  " blockers": [],
  "created_at": "2026-11-05T14:45:00+05:30"
}
```

### 15.3 QA policy

- `fail` blocks final render and publication.
- `pass_with_warnings` may proceed only after reviewer acknowledgement.
- Automated QA cannot approve humour, storytelling, factual truth, or aesthetics.
- Human preview remains mandatory.

---

## 16. Rights and Asset Registry Requirements

### 16.1 Asset ingestion

- Compute SHA-256 content hash.
- Detect MIME/type where possible.
- Store local path, source URL, owner, provenance, and acquisition date.
- Require rights basis and rights status.
- Store licence evidence path or reference.
- Store permitted use, attribution requirement, and expiry.
- Reject duplicate asset ingestion unless explicitly versioned.

### 16.2 Rights gate

```text
public_package_request
        ↓
collect asset IDs
        ↓
all assets approved?
        ├── no → block package
        └── yes → create package
```

### 16.3 Rules

- `unknown` rights basis cannot enter a public package.
- `pending` rights status cannot enter a public package.
- Expired rights status blocks public use.
- Episode clips default to `hold` unless documented permission or reviewed exception exists.
- Cosmetic transformations do not alter rights status.
- Asset manifests must be immutable once a render/publication is created.

---

## 17. Approval Service Requirements

### 17.1 Approval object

```json
{
  "approval_id": 501,
  "object_type": "video",
  "object_id": 77,
  "object_version": "render:v3",
  "object_hash": "sha256:...",
  "action": "private_upload",
  "decision": "approved",
  "approver_id": "telegram:123456789",
  "decided_at": "2026-11-05T15:00:00+05:30",
  "expires_at": "2026-11-06T03:00:00+05:30"
}
```

### 17.2 Requirements

- Approval must bind actor, object, version/hash, action, and timestamp.
- Telegram callbacks must validate allowed user ID, chat ID, object, version, and action.
- Approval must expire after a configurable period.
- Expired approval state is `expired`, not `rejected`.
- Material changes to script, assets, destination, caption, privacy, or scope invalidate approval.
- Public release requires a distinct approval from preview and private-upload approvals.
- Every approval decision must create an audit event.

---

## 18. Publishing Requirements

### 18.1 YouTube adapter

#### MVP requirements

- Upload only after explicit private-upload approval.
- Default privacy: `private`.
- Store remote video ID and remote URL.
- Store upload state separately from processing state.
- Use an idempotency key per publication attempt.
- Persist API request/response metadata and errors.
- Reconcile uncertain upload status before retry.
- Never blindly re-upload after an interrupted request.
- Track processing status separately from copyright/claim status.
- Require separate approval for public release.
- Respect an application-level daily upload cap.

#### Upload states

```text
draft → approved_for_private_upload → uploading
      → uploaded → processing → processing_complete
      → manual_review → approved_for_public_release
      → published
```

Exception states:

```text
upload_failed, reconciliation_required,
restricted, deleted, blocked_rights, quota_or_limit_error
```

### 18.2 Telegram adapter

- Send preview video to an allowlisted approver chat.
- Include video title, script summary, duration, QA result, rights summary, and content hash.
- Provide Approve / Request Changes / Reject callbacks.
- Validate callback sender and object version.
- Store Telegram message ID for traceability.
- Audience Telegram publishing is a later adapter and requires separate approval.

### 18.3 Future Meta adapter

- Implement only after account, app, permission, and API eligibility are verified.
- Use a destination-specific publish package.
- Do not assume a YouTube package is directly reusable.
- Track platform-specific errors and state independently.

---

## 19. CRM and Outreach Requirements

### 19.1 Lead requirements

- Store source and contact provenance.
- Support manual lead creation in MVP.
- Store fit score, status, notes, and opt-out flag.
- Prevent outreach when `opt_out = 1`.
- Prevent outreach without a documented relevant observation.
- Prevent outreach without approval.

### 19.2 Outreach requirements

- Generate a draft, never send automatically.
- Draft must include prospect-specific observation, proposed content idea, and clear next step.
- Human must approve exact final message.
- Store approved message version and hash.
- Record sent state, message ID where available, and follow-up schedule.
- Repeated automatic follow-ups without review are prohibited.

### 19.3 Demo requirements

- Demo must be labelled as a sample/speculative concept.
- Demo must use rights-approved assets.
- Demo generation must use the same render/QA/approval pipeline.
- Demo must be linked to lead, outreach draft, and eventual client/project.

---

## 20. Client Delivery Requirements

### 20.1 Client project isolation

- Client assets must be isolated by client and project.
- Client confidential material must not enter public portfolio without permission.
- Client brand configuration must be versioned.
- Client deliverables must have a separate rights/approval trail.

### 20.2 Delivery record

```json
{
  "delivery_id": 301,
  "client_id": 12,
  "project_id": 8,
  "deliverable": "4_vertical_shorts",
  "due_date": "2026-11-20",
  "revisions_used": 1,
  "revisions_allowed": 1,
  "status": "delivered",
  "accepted_at": null,
  "invoice_id": 44,
  "delivery_hours": 7.5,
  "direct_cost_inr": 0,
  "notes": "Client approved final files."
}
```

### 20.3 Rules

- Scope, revision count, duration, deadline, posting responsibility, price, and cancellation terms must be recorded before production.
- Out-of-scope work must create a change request or revised quote.
- Delivery acceptance must be recorded.
- Invoice raised and payment collected must be tracked separately.

---

## 21. Analytics Requirements

### 21.1 Metric ingestion

- MVP supports manual CSV/JSON entry.
- Each metric must store publication, metric name, value, period, source, and collection timestamp.
- Platform API ingestion may be added later.
- Metrics must be attributable to a specific publication and date.
- Metric source must be recorded.

### 21.2 Required reports

| Report | Output |
|---|---|
| Format performance | Median and distribution by format |
| Topic performance | Views, engagement, retention, owned-destination clicks |
| Production efficiency | Human minutes/video, render minutes/video, failure rate |
| Sales funnel | Leads → qualified → demo → outreach → reply → pilot → client |
| Financial performance | Invoiced, collected, outstanding, costs, contribution |
| Rights coverage | Reviewed publications, unknown observations, active claims |
| Client profitability | Collected fee, direct cost, hours, effective hourly earning |

---

## 22. Security Requirements

- Store secrets in environment variables or a local secret store.
- Never log API keys, OAuth tokens, client secrets, or full prompts containing sensitive data.
- Restrict Telegram approval to configured user/chat IDs.
- Validate callback payload integrity and object version.
- Use least-privilege OAuth scopes.
- Store OAuth refresh tokens securely.
- Encrypt or restrict access to client-confidential assets.
- Maintain an audit trail for approvals, rights decisions, publishing, and client delivery.
- Provide a data-retention and deletion policy for prospect/client data.

---

## 23. Reliability and Recovery

### 23.1 Failure handling

| Failure | Required behaviour |
|---|---|
| Worker crash | Lease expires; job becomes recoverable |
| Render crash | Partial artifacts quarantined; job retryable |
| TTS failure | Segment-level retry; no silent concatenation |
| LLM timeout | Bounded retry, then fallback provider |
| Upload interruption | Reconcile remote state before retry |
| Duplicate callback | Idempotent handling |
| Disk full | Fail safely; preserve existing artifacts |
| Database lock | Retry with bounded backoff |

### 23.2 Backup requirements

- SQLite database backup command must exist.
- Asset/rights evidence and render manifests must be included in backup scope.
- Backup restore must be tested.
- Backups must be versioned or timestamped.
- A documented restore procedure must exist.

---

## 24. Observability Requirements

### 24.1 Structured log fields

```json
{
  "timestamp": "2026-11-05T15:10:00+05:30",
  "level": "info",
  "service": "worker",
  "job_id": 908,
  "job_type": "render_preview",
  "video_id": 77,
  "state": "running",
  "attempt": 1,
  "duration_ms": 184000,
  "message": "Preview render completed"
}
```

### 24.2 Required observability

- Job state, attempts, lock owner, heartbeat, and last error.
- External API provider, endpoint, status, latency, and error class.
- Render duration, output size, and QA result.
- Approval actor, object hash, action, and decision.
- Rights decisions and blocked assets.
- Publication state transitions and remote IDs.
- LLM task, provider, model, prompt version, latency, usage, and error.

---

## 25. Testing Requirements

### 25.1 Unit tests

- Claim state transitions.
- Script quality scoring.
- Sentence splitting and Hindi punctuation handling.
- Caption timing generation.
- Scene-plan validation.
- Asset rights gate.
- Manifest hash generation.
- Idempotency-key behaviour.
- Publish-package validation.

### 25.2 Integration tests

- Piper TTS with a small fixture script.
- FFmpeg render with synthetic image/audio assets.
- SQLite job claiming and recovery.
- Telegram approval callback handling.
- YouTube adapter with mocked API responses.
- Publication reconciliation after simulated interruption.

### 25.3 Failure-injection tests

- Piper timeout.
- Malformed LLM response.
- Missing asset.
- Expired approval.
- Worker crash during render.
- Worker crash during upload.
- Duplicate Telegram callback.
- Disk-full condition.
- Database lock contention.

### 25.4 Quality tests

- Hindi caption rendering and glyph coverage.
- Audio loudness and clipping.
- Scene timing alignment.
- Visual asset relevance sampled by human review.
- Manifest reproducibility.

---

## 26. Acceptance Criteria

### Phase 0 acceptance

1. Operator can create a topic and attach sources.
2. Operator can create claims and mark their evidence status.
3. Unsupported factual claims cannot enter an approved factual script.
4. Operator can create, edit, and approve a versioned Hindi script.
5. System generates a scene plan mapping narration beats to visuals and assets.
6. Piper generates narration and segment timings.
7. System detects silent or failed TTS segments.
8. System generates valid Hindi captions.
9. System renders a 480p or configurable preview.
10. QA report identifies missing assets, rights issues, audio problems, and caption problems.
11. Telegram preview supports approve/change/reject with identity and version checks.
12. Final render is reproducible from the manifest.
13. Unknown or pending-rights assets are blocked from public packages.
14. No public upload occurs in Phase 0.

### Phase 1 acceptance

1. Operator approves a final render for private YouTube upload.
2. System uploads privately and stores remote video ID.
3. Upload interruption is reconciled without duplicate upload.
4. Processing status is tracked separately from claim/restriction status.
5. Operator records a manual Studio observation.
6. Missing observation remains `unknown`.
7. Public release requires a separate approval.
8. Public package blocks unknown/pending/rejected/expired assets.
9. All approval and publication events are auditable.

### Phase 2 acceptance

1. Operator can create a client lead with source/provenance.
2. Operator can generate a demo concept or demo video.
3. Outreach draft requires explicit approval before sending.
4. Opted-out leads cannot receive outreach.
5. Client scope, revisions, deadline, and price are recorded.
6. Delivery hours, revisions, invoice, and payment are tracked.
7. At least one paid pilot or credible buying signal is recorded.

---

## 27. Build Order

### Sprint 1 — Local proof

1. Repository, config, logging, SQLite migrations.
2. Topic, source, claim, script, and asset models.
3. Claim ledger and evidence gate.
4. Piper adapter and narration timing.
5. Caption builder.
6. One FFmpeg motion-graphics template.
7. Preview QA report.
8. Telegram preview/approval.

### Sprint 2 — Controlled publishing

1. Approval service with version/hash binding.
2. YouTube private upload adapter.
3. Idempotency and reconciliation.
4. Processing-status tracking.
5. Manual Studio observation workflow.
6. Separate public-release approval.
7. Local archive and manifest validation.

### Sprint 3 — Business validation

1. Lead and client models.
2. Demo generator using existing render pipeline.
3. Outreach draft and approval workflow.
4. Client project/delivery tracker.
5. Invoice/payment/economics tracking.
6. Portfolio generation from approved original videos.

### Sprint 4 — Audience and optimisation

1. Metrics ingestion.
2. Format/topic reports.
3. Telegram audience digest.
4. Instagram adapter, if eligibility is verified.
5. Renewal tracking.
6. Additional templates only after demand evidence.

---

## 28. Definition of Done

### Feature

- Implemented according to this TRD.
- Covered by relevant tests.
- Configuration documented.
- Errors are observable and actionable.
- Failure path is safe.
- Audit events are recorded where applicable.

### Video

- Approved script version referenced.
- Claims and evidence recorded.
- Rights-approved assets only for public package.
- Narration and captions complete.
- QA report exists.
- Human approval recorded.
- Render manifest reproducible.

### Publication

- Destination-specific package created.
- Approval bound to exact package/version.
- Remote ID and state reconciled.
- Claim/restriction observation recorded where applicable.
- Audit trail complete.

### Client delivery

- Approved deliverables delivered.
- Scope, revisions, acceptance, invoice, payment, and hours updated.
- Client assets remain isolated.
- Confidential assets are not exposed without permission.

---

## 29. Open Technical Decisions

| Decision | Current default | To resolve |
|---|---|---|
| Piper Hindi voice | `hi_IN-default` | Test clarity, pacing, pronunciation, and licence |
| Pronunciation dictionary | Required for proper nouns | Build initial Hindi proper-noun map |
| First template | `commentary_v1` | Build and benchmark |
| Preview resolution | 480x854 or configurable | Benchmark speed/readability |
| LLM provider | Rules-first; hosted LLM optional | Verify current free quota and data terms |
| YouTube quota cap | 3 uploads/day operational cap | Verify actual project quota and channel limits |
| Asset sources | Original/local assets first | Identify licensed commercial-use sources |
| Client segment | Active small YouTube creators | Validate through outreach |
| Pilot price | ₹1,499–₹1,999 | Test conversion, delivery hours, and revisions |

---

## 30. Immediate Engineering Tasks

1. Initialise Python project, `pyproject.toml`, config loader, structured logging, and SQLite migrations.
2. Implement topic, source, claim, script, asset, video, job, approval, and publication schemas.
3. Build CLI commands:
   - `topic create`
   - `source add`
   - `claim add`
   - `claim review`
   - `script draft`
   - `script approve`
   - `video plan`
   - `video preview`
   - `video approve`
   - `video render-final`
   - `publish youtube-private`
4. Implement Piper adapter with segment timing and failure detection.
5. Implement caption builder and Hindi ASS/SRT renderer.
6. Implement one motion-graphics FFmpeg template with explicit timeline contract.
7. Implement QA gates for media, captions, rights, and manifest integrity.
8. Implement Telegram approval bot with allowlist and version-bound callbacks.
9. Implement YouTube private-upload adapter with idempotency and reconciliation.
10. Create three original portfolio videos using the complete local workflow.
11. Add client/lead/invoice tracking.
12. Run the first paid-pilot outreach experiment with human-approved messages.
