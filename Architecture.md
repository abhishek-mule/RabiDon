# CreatorOps AI — Architecture

**Version:** 1.0  
**Date:** 5 November 2026  
**Basis:** PRD v2.0 and proposed TRD baseline  
**Status:** Proposed design; no implementation or live API verification implied

## 1. Architectural goal

Support a part-time solo operator creating original Hindi motion-graphics explainers and delivering client videos. Automate repetitive work while preserving explicit human control over facts, rights, external sharing, publishing, outreach, and delivery.

No episode downloader, piracy distribution, automatic rights-clearance engine, paid-model dependency, or bulk unsolicited messaging is in scope.

## 2. Scope and deployment

### MVP

- One local machine and one operator.
- Python 3.11+ application with CLI and Telegram bot adapters.
- SQLite on local disk; WAL enabled per supported environment.
- One worker; one concurrent render.
- Local asset/artifact storage.
- Piper or recorded narration; FFmpeg/ffprobe.
- Optional free hosted text model, with manual fallback.
- YouTube private-first publishing after Phase 0.

Hardware performance, Hindi voice availability/licence, platform API access, OAuth requirements, and provider quotas must be validated during implementation. No specific render speed or API quota is assumed here.

### Deferred

Web API/dashboard, PostgreSQL, Redis, cloud storage, n8n, multi-tenancy, additional publisher adapters, generated cinematic video, and continuous character animation.

## 3. System view

```text
LOCAL TRUST BOUNDARY
┌───────────────────────────────────────────────────────────────────┐
│ CLI / Telegram command handler                                   │
│             ↓                                                     │
│ Application services + policy gates                              │
│ topic → sources → factual review → script → scene plan            │
│             ↓                                                     │
│ narration → caption timing → preview render → QA → review         │
│             ↓                                                     │
│ final render → immutable PublishPackage → approval                │
│             ↓                                                     │
│ SQLite repositories + job worker + local artifact store           │
└───────────────────────────────────────────────────────────────────┘
              │ explicit, logged adapter calls
              ↓
EXTERNAL BOUNDARY
Optional LLM │ Telegram previews │ YouTube private/public
Later: client delivery channel, outreach channel, Meta adapters
```

External preview sharing is a side effect, not a local-only operation. A private Telegram chat is still external storage/transmission.

## 4. Layers and dependencies

| Layer | Responsibilities | Must not do |
|---|---|---|
| Interfaces | CLI commands, bot callbacks, future HTTP | Directly bypass policy services |
| Application | Workflow orchestration, transactions, approval execution | Embed platform-specific SDK behaviour |
| Domain | Claim, asset, approval, package, delivery invariants | Depend on CLI, Telegram or SDK clients |
| Infrastructure | SQLite, files, FFmpeg, Piper, provider SDKs | Decide editorial/legal approval |

Ports/interfaces live alongside domain/application contracts. Infrastructure implements them; construction occurs in the application composition root.

## 5. Module contracts

| Module | Inputs | Outputs |
|---|---|---|
| Research | Topic, manually attached/approved source material | Dossier, source revisions, factual candidates |
| Factual review | Claim revision, evidence revisions, human decision | Accepted/narrowed/rejected assertion |
| Scripts | Dossier, format, user edits | Immutable script revision, assertion references |
| Scene planner | Approved script, brand, timing | Scene plan revision with required visuals |
| Assets | Files, provenance, permitted use evidence | Content-addressed asset and review records |
| TTS | Narration text, pronunciation map, voice config | Audio segments, final narration, timings |
| Captions | Segment timings and original text | Validated cues, SRT, ASS |
| Renderer | Scene plan, audio, fonts, assets | Preview/final artifact and manifest |
| QA | Artifact, manifest, target policy | Per-check pass/warn/fail/not_run results |
| Approvals | Exact action request, authorized human response | Single-action authorization decision |
| Publisher | Approved package, credentials | Remote ID, observed upload/processing state |
| CRM | Selected prospects and contact provenance | Qualification, demo, draft, follow-up records |
| Finance | Invoices, payments, costs, refunds, time | Cash and contribution reports |

## 6. Data model

All IDs are stable opaque identifiers or local surrogate keys; external IDs are stored separately. All timestamps are UTC. Money uses integer paise; timeline positions use integer milliseconds.

### Editorial entities

- `topics`: angle, audience, format, priority, lifecycle.
- `sources`, `source_revisions`: URL/title/type, access date, source notes, content hash.
- `factual_claims`, `claim_revisions`: assertion, evidence status, source references.
- `claim_reviews`: reviewer, claim/evidence revisions, accepted wording, decision.
- `scripts`, `script_revisions`: structured beats, narration, referenced accepted assertions.
- `scene_plans`, `scene_plan_revisions`: narration segment references, visual actions, asset IDs.

Factual claims and platform copyright observations must use distinct names and services.

### Production entities

- `assets`: immutable file hash, provenance, owner, MIME/type.
- `asset_permissions`: basis, evidence, permitted uses/destinations, attribution, expiry, reviewer.
- `videos`, `render_runs`, `artifacts`: pipeline status, exact inputs, outputs, hashes.
- `qa_reports`: check result, severity, measurement, configured threshold, version.
- `jobs`: type, payload version, state, attempts, lease, worker token, error.
- `audit_events`: actor, action, object revision, timestamp, redacted details.

### Side-effect entities

- `approval_requests`: action, target account, object/package hash, expiry, token hash, state.
- `approval_decisions`: approver, decision, timestamp, exact request reference.
- `publish_packages`: immutable package metadata, media and manifest hashes.
- `publications`: destination account, remote ID, privacy, upload/processing/visibility observations.
- `publication_attempts`: request identity, secure session reference, outcome, reconciliation status.
- `platform_observations`: publication, claim/restriction observation, source, reviewer, timestamp.

### Business entities

- `leads`, `contact_permissions`, `outreach_drafts`, `outreach_attempts`, `followups`.
- `clients`, `projects`, `briefs`, `deliveries`, `revision_requests`, `acceptances`.
- `invoices`, `invoice_lines`, `payments`, `payment_allocations`, `refunds`, `expenses`, `time_entries`.
- `metric_samples`: publication, metric, period, provider/manual source, collection time.
- `llm_calls`: task/provider/version/hash/usage/error; confidential payload storage disabled by default.

Partial payments and refunds require separate records; an invoice status alone is not cash accounting. These are operational records, not a substitute for statutory tax/accounting advice.

## 7. Storage conventions

```text
data/
  creatorops.db
  assets/sha256/<prefix>/<hash>.<ext>
  rights/<permission_id>/evidence.*
  projects/<project_id>/
  secrets/                      # restrictive permissions, never git
  backups/<snapshot_id>/
output/
  <project_id>/<video_id>/<render_run_id>/
    narration.wav
    segments.json
    captions.srt
    captions.ass
    scene_plan.json
    preview.mp4
    final.mp4
    manifest.json
    qa_report.json
    render.log
```

Writes use a temporary file on the same filesystem followed by validation and atomic rename. Paths are resolved beneath permitted roots. Runtime files are ignored by version control.

## 8. Canonical contracts

### Scene plan

```json
{
  "schema_version": 1,
  "script_revision_id": "scr_r3",
  "timing_revision_id": "tim_r1",
  "canvas": {"width": 1080, "height": 1920, "fps": 30},
  "scenes": [{
    "id": "s1",
    "narration_segment_ids": ["n1"],
    "timeline_start_ms": 0,
    "timeline_end_ms": 4200,
    "layers": [{
      "asset_id": "asset_1",
      "source_start_ms": 0,
      "source_end_ms": 4200,
      "motion": "slow_zoom",
      "fit": "contain"
    }],
    "on_screen_text": "Example title",
    "transition_out": "cut"
  }]
}
```

Asset source trim and placement on the output timeline are distinct fields. Provisional scenes may be drafted before TTS; final scene timings are resolved against measured narration segments.

### Render manifest

```json
{
  "schema_version": 1,
  "render_run_id": "render_1",
  "script_hash": "sha256:...",
  "scene_plan_hash": "sha256:...",
  "narration_hash": "sha256:...",
  "template": {"id": "commentary", "version": "1.0.0"},
  "voice": {"provider": "recorded", "model_hash": null},
  "asset_hashes": ["sha256:..."],
  "font_hashes": ["sha256:..."],
  "tools": {"ffmpeg": "measured-at-runtime", "piper": null},
  "settings": {"width": 1080, "height": 1920, "fps": 30}
}
```

Output hash and QA report are stored alongside the manifest, not recursively included in the manifest hash. Runtime permission status is revalidated separately.

### PublishPackage

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

Canonical sorted JSON produces the package hash. Approval decisions reference that hash; approval records are not included inside the hashed package, preventing circular dependencies.

## 9. Evidence gate

1. Attach sources; store title/URL/access time and relevant notes.
2. Draft assertions and source links manually or through optional AI.
3. Human checks whether evidence supports the precise wording.
4. Unsupported factual statements block approval.
5. Partial/conflicting statements are narrowed, qualified, or omitted.
6. Approved script references accepted claim/evidence revisions.
7. A relevant revision invalidates acceptance and downstream approvals.

No automated completeness check proves that every unreferenced sentence is non-factual. Human editorial review remains responsible for assertions omitted from model-generated claim lists.

## 10. Rendering pipeline

```text
approved script
 → narration text normalization + pronunciation overrides
 → chunk synthesis / recorded-audio import
 → duration measurement + segment QA
 → final narration and timing map
 → resolve scene timings
 → generate SRT/ASS
 → build explicit FFmpeg graph
 → local preview render
 → technical QA + human review
 → final render
 → final QA and immutable artifact
```

### TTS

Voice is configurable and unresolved until tested. Validate binary/model presence, permitted use, pronunciation and sample quality. Sentence cues provide sentence boundaries, not word alignment. Recorded narration with manually supplied timing is a valid fallback; avoid adding automatic ASR as an MVP dependency.

### Visual design

One designed commentary template initially: palette, typography, safe zones, scene cards, kinetic titles, pans/zoom, purposeful transitions. Templates consume validated scene plans, not model-authored shell commands.

### QA

- File/stream readability, duration and resolution.
- Audio presence, loudness, clipping and unexpected silence.
- Caption ranges, overlaps, text/segment coverage and line layout.
- Missing inputs, timeline gaps and unintended black frames.
- Package rights and approval integrity.
- Sampled-frame review for Hindi glyphs, visual coherence, occlusion and artifacts.

Numeric thresholds are versioned template settings calibrated against sample videos. Glyph correctness, humour, truth, aesthetics and pacing are not guaranteed by media probes. Unsupported checks remain `manual_required`.

Preview rights failures may permit local inspection but prohibit Telegram transmission. Blocking failures cannot be bypassed with a warning acknowledgement.

## 11. Rights policy

Check permissions for each intended action: local inspection, external preview sharing, final rendering, private platform upload, public release, client delivery, portfolio use.

Before any external action verify:

- Correct asset/version and provenance.
- Approved non-expired permission.
- Commercial-use and destination scope where relevant.
- Required attribution included.
- Client confidentiality and reuse restrictions.
- Human review of exception-based use where applicable.

A public-release package must never rely on unknown or pending rights. Old permission snapshots, absence of a claim, and cosmetic edits are not clearance.

## 12. Approval architecture

### Requests and decisions

Create a request containing action, target, exact object/package hash, authorized approvers, expiry, and random token. Telegram carries only the opaque token/reference; full data remains server-side.

On callback:

1. Check user/chat allowlist.
2. Resolve and authenticate request token.
3. Check pending state and expiry.
4. Recompute current object/package hash.
5. Record decision and consume token transactionally.
6. Enqueue the exact approved action.
7. Recheck gates before executing.

The action authorization is consumed once; retries resume the same action attempt, not a new target or payload. If the result is ambiguous, reconcile. Material edits require a new request.

### Separate actions

Script acceptance, Telegram external preview, final-render approval, private upload, public release, client delivery and outreach send are distinct actions. Authorization must not leak across them.

## 13. Workflow states

### Production

`idea → researching → evidence_review → scripting → script_review → scene_planning → narration → preview_render → qa → human_review → final_render → final_qa → packaged`

Exceptions: `awaiting_manual_input`, `needs_changes`, `blocked_rights`, `failed`, `cancelled`.

### Publication

Track independent dimensions rather than one overloaded state:

- Upload: not_started / uploading / uploaded / failed / reconciliation_required.
- Processing: unknown / processing / complete / failed.
- Visibility: private / scheduled / public / unlisted / unknown.
- Restriction observations: unknown / none_observed / blocked / other.

Local intended state and last observed remote state are separate. Remote observations include collection time.

### Copyright observations

`unknown / no_claim_observed / active / released` is point-in-time operational data, not legal permission. Phase 1 uses manual Studio review. Email ingestion is optional notification data; silence is never no-claim evidence.

## 14. Job execution and recovery

SQLite connections enable foreign keys and bounded busy handling. Each job claim uses a short `BEGIN IMMEDIATE` transaction, selects an eligible row, sets lease/owner token, increments attempts, and commits before external work.

- Heartbeat extends the lease only for its current owner token.
- Completion is conditional on matching owner token and state.
- Retry transient errors with bounded exponential backoff and jitter.
- Invalid input, rights failures, and missing approval do not retry endlessly.
- `awaiting_approval` and `awaiting_manual_input` are not worker failures.
- Preserve successful immutable artifacts; retry only invalid/missing stages.
- Never keep a database transaction open during FFmpeg or network requests.

### Upload ambiguity

Persist publication intent before upload; persist resumable session reference securely when supported. After interruption, query/resume the saved session and inspect remote state. If reconciliation cannot establish outcome, block for operator review rather than start a new upload.

An application idempotency key is not a guarantee supplied by YouTube or any other provider. No exactly-once external delivery guarantee is claimed.

## 15. AI adapter and privacy

```python
class TextProvider:
    def generate(self, task, prompt, schema, timeout_s, max_tokens):
        """Return validated result metadata or typed provider error."""
```

Use per-task configured providers; validate structured output and bound retries. Rules support classification/formatting, not factual invention. When generation is unavailable, pause for a human script rather than produce filler.

Hosted providers receive only approved non-confidential inputs. Client material requires provider/privacy review and client authorization. Retrieved text and model output cannot change system policy or trigger tools.

Cache by task, prompt/schema/provider versions and input hash; research caches have freshness review. Store minimum necessary call metadata and redact secrets/PII.

## 16. CRM, client delivery and finance

### MVP

Manual prospects and source provenance → qualification → speculative demo → approved outreach draft → explicit send approval → follow-up reminder → pilot → scoped project → production → approved delivery → invoice/payment → renewal.

No auto-sending follow-ups, purchased lists, sensitive profiling, or automated spam. Opt-out check is enforced both at draft and send time.

### Project isolation

Separate asset namespaces and authorization scopes per project. Client material is not automatically eligible for portfolio, demos, another client, or hosted AI processing.

### Economics

- Collected revenue and invoiced revenue are separate reports.
- Payment allocations support partial payments and refunds.
- Expenses record transaction/production costs without double counting.
- Time entries include delivery, revisions, communication, failures, and optional sales effort.
- Delivery hourly rate and fully loaded business hourly rate use separately labelled denominators.
- Prices in the PRD are test offers, not validated market rates.

## 17. Interfaces

Proposed CLI contracts, implemented incrementally:

```bash
creatorops init
creatorops topic create
creatorops source add
creatorops claim add
creatorops claim review
creatorops script import
creatorops script approve
creatorops asset register
creatorops asset review
creatorops video plan
creatorops video narrate
creatorops video preview
creatorops video qa
creatorops approval request
creatorops video render-final
creatorops publish prepare
creatorops publish youtube-private
creatorops publish reconcile
creatorops publication observe
creatorops publish release
creatorops worker run
creatorops backup create
creatorops backup verify
```

Commands validate policy server-side/application-side; a CLI flag cannot bypass rights or approvals. Dry-run commands do not contact external services or alter external state. Help text and command availability must match implementation.

No HTTP API is required for the MVP. Future FastAPI endpoints call the same application services and approval checks.

## 18. Security and operational controls

- `.env.example` contains placeholders only; `.env` and token files are ignored.
- Restrict filesystem access; store refresh tokens and session URIs outside logs/backups unless encrypted.
- Execute subprocess argument arrays with no shell interpolation.
- Validate asset paths and allowlisted external-fetch targets; no autonomous arbitrary URL fetching in MVP.
- Redact logs and apply configurable retention/deletion for contact/client data.
- Preserve audit records as append-only application events; do not claim tamper-proof storage on a local machine.
- Local desktop must be awake/network-connected for bot polling and publishing. No 24/7 reliability is assumed.

## 19. Backup and restore

Use SQLite backup APIs or a controlled quiescent snapshot; do not copy only the main DB file while WAL writes are active.

A backup manifest references DB snapshot, assets, rights evidence, manifests, and required project files. Verify hashes and restore to a temporary directory before declaring recovery successful. Keep encrypted/off-device backups when confidentiality and budget permit; keys stay separate.

Initial objective: daily backup while actively producing; acceptable data-loss and recovery-time targets are operator decisions, not untested guarantees.

## 20. Tests and observability

### Tests

- Unit: policy gates, hashes, time/money calculations, schema validation, claim revisions.
- Integration: SQLite leases, Piper sample, FFmpeg synthetic fixture, bot handlers, mocked publisher.
- Failure injection: timeout, disk full, lease loss, malformed JSON, duplicate callback, upload ambiguity.
- Security: wrong user, stale hash, path traversal, client isolation, opt-out.
- Recovery: restored backup can resolve assets and regenerate a preview.
- Human acceptance: Hindi pronunciation/glyphs, evidence accuracy, scene relevance, visual pacing.

Tests are offline by default. Live publishing/outreach tests require explicit exact-action approval and designated test accounts.

### Logs

UTC timestamp, correlation ID, job/video/publication ID, action/state, attempt, elapsed time, typed error and redacted context. Never emit credentials or full client-sensitive payloads.

## 21. Phases and release gates

| Phase | Build | Exit gate |
|---|---|---|
| 0 | CLI, SQLite, manual evidence/script, voice adapter, template, QA | Local reviewed preview; no public upload; measured manual effort |
| 1 | Approved external preview, private upload, processing observations, reconciliation | One private upload and simulated recovery without duplicate; separate public authorization |
| 2 | Portfolio, manual leads, scoped demos, approved outreach, delivery/payment records | Paid pilot or documented buying signal; measured economics |
| 3 | Metrics and renewal workflow; optional second publisher | Repeat engagement or renewal; sustainable workload |
| 4 | Selected automation/infrastructure expansion | Demand and measured bottlenecks justify change |

Dates are experiment planning targets; gates determine readiness. Client workflow completion is Phase 2, not a blocker for the first media release.

## 22. Architecture decisions

| ADR | Decision | Status |
|---|---|---|
| 001 | SQLite/local files/single worker initially | Accepted design |
| 002 | Facts, rights, QA and human approval are independent gates | Accepted design |
| 003 | Package hash excludes authorization decision references | Accepted design |
| 004 | Private upload and public release are separately authorized | Accepted design |
| 005 | External previews require sharing permission | Accepted design |
| 006 | No mandatory paid model or cloud generation | Accepted design |
| 007 | Pause on ambiguous uploads; no blind retries | Accepted design |
| 008 | Integer paise, UTC, integer timeline milliseconds | Accepted design |

## 23. TRD alignment notes

Before coding, reconcile these refinements with the earlier TRD:

- Placeholder voice identifiers are not verified downloadable models; select and review one explicitly.
- Add approval requests, permission reviews, claim revisions, costs, time entries and payment allocations to migrations.
- Remove circular PublishPackage approval references; approve the completed immutable package hash.
- Treat preview sharing as an external action with rights/confidentiality checks.
- Separate preliminary scene design from narration-resolved timeline.
- Use offline/manual fallbacks honestly; rules cannot replace research or creative judgement.
- Automated glyph and frame checks are diagnostic, not proof of visual quality.
- Local uniqueness constraints do not prevent external duplicates by themselves.
- Reproducibility is version/input traceability, not guaranteed cross-machine byte identity.

## 24. Definition of done

A completed feature has tests, configuration docs, observable typed failures, safe recovery, and updated contracts. A completed video has reviewed evidence, rights, exact-version approval, media QA and a manifest. A completed external action has authorization for the exact target/payload and a reconciled result. No file in this design implies that code has been implemented, tested live, or deployed.
