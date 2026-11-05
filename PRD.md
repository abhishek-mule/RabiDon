# CreatorOps AI — Product Requirements Document

## Document control

| Field | Value |
|---|---|
| Product | CreatorOps AI |
| Version | 2.0 |
| Status | Implementation-ready draft; configurable decisions remain |
| Owner | Founder / solo operator |
| Operating mode | Part-time validation; 90-day experiment |
| Revenue target | ₹3,00,000/year = ₹25,000 monthly average (target, not forecast) |
| Cost principle | Near-zero recurring spend; no paid LLM dependency |

## Executive summary

CreatorOps AI is a solo-operator system for producing original Hindi cartoon/anime nostalgia and explainer videos, building an audience, and selling short-form video production to creators and small businesses. It combines a quality-controlled Media Engine, rights-aware asset management, approval-based publishing, lightweight CRM, personalised demo generation, client delivery and revenue tracking.

It is not an episode downloader, copyright-evasion tool or autonomous spam bot. It will not scrape/repost copyrighted episodes from sites such as Toonix.bond. The monetizable output is original research, commentary, scripts, narration, visual storytelling and client-specific production.

Quality is an explicit requirement: factual claims need evidence, scenes need visual plans, and rendered videos need automated QA plus human review. Phase 1 targets professional motion-graphics explainers—not full cartoon animation or guaranteed cinematic AI footage.

## 1. Vision, problems and outcomes

### 1.1 Vision

Turn an approved idea into a fact-checked, visually coherent, publish-ready short video with a repeatable workflow—and use the same engine to deliver paid client videos.

### 1.2 Problems

- Research, scripting, voiceover, editing, captions, exporting and publishing consume hours per video.
- Generic AI scripts can invent facts, repeat clichés or sound unnatural in Hindi.
- Template-only output may look like a low-effort slideshow without scene design, pacing, motion and sound.
- Reposting third-party episodes creates rights, takedown, account and monetization risks.
- Ad revenue is uncertain and slow before audience scale and eligibility.
- Automation can waste time if built before a buyer and repeatable paid offer are validated.

### 1.3 Outcomes

| Outcome | Target |
|---|---|
| Efficiency | Routine human production effort trends toward 20–30 min/video; measure actual time, not just render time. |
| Quality | Reviewer approves without structural re-edit; rejection reasons captured. |
| Accuracy | Factual claims have sources or explicit uncertainty/opinion framing. |
| Safety | Unknown-rights assets cannot enter public packages. |
| Business | Paid pilot or credible buying signal before large platform automation. |
| Economics | Track collected revenue, direct costs, hours, revisions and contribution. |
| Reliability | Recover jobs/uploads without duplicate public publication. |

### 1.4 Non-goals

- Fully autonomous cartoon episodes with perfect character consistency.
- Downloading/reposting complete third-party episodes.
- Guaranteed virality, copyright safety, monetization approval or income.
- Five-platform publishing on day one.
- Unlimited free hosted AI or free video generation.
- Multi-tenant SaaS, Kubernetes, microservices or complex agents in MVP.

## 2. Users and value

| User | Need | Value |
|---|---|---|
| Founder | Produce quality videos with less repetitive work; control quality, rights and spend. | One workflow and measurable production/business operations. |
| Hindi nostalgia audience | Revisit/discuss cartoons through original content. | Interesting, accurate, entertaining Hindi commentary. |
| Small creator/client | Publish consistently without full-time editor. | Predictable package, turnaround and revisions. |
| Local/education business (later) | Turn offers/lessons/FAQs into shorts. | Affordable production with clear scope. |

## 3. Product principles

1. Original commentary first; clips are supporting material, never default product.
2. Unknown is not cleared; missing source/rights evidence remains unknown.
3. Human approval before public release, outreach sending, risky asset use or client delivery.
4. AI output is a draft; model confidence is not evidence.
5. Quality over volume; failed QA never auto-publishes.
6. Use the simplest architecture that proves workflow; migrate only when needed.
7. Free quotas are volatile dependencies; adapters and graceful fallback are mandatory.
8. Revenue validation precedes scale.

## 4. Scope and modules

### 4.1 Media Engine

Transforms topic + evidence + approved script + asset plan into preview, QA report and final publish package.

- Topic intake through CLI, Telegram command or later dashboard.
- Research dossier: sources, source type/date and claim candidates.
- Script generation with versioning, format structure and claim references.
- Script gate: unsupported claims flagged; uncertain claims qualified or removed.
- Scene plan: narration beat, on-screen text, visual, motion, duration, transition and asset refs.
- Piper/local or recorded narration; voice profile/licence metadata.
- Chunk audio, duration measurement, captions and SRT/VTT.
- FFmpeg rendering: motion graphics, transitions, captions, music ducking, SFX and branding.
- Preview render → automated QA → human approve/change/reject → final render.
- Reproducible manifest: script/template/assets hashes, voice and settings.

### 4.2 Research and factuality

- Research against source material; model memory alone is not evidence.
- Claim record: claim text, source URL/title/date, supporting note/excerpt, status and reviewer.
- Prefer official/primary sources for names, dates, broadcast/release facts; credible secondary sources for context.
- Flag unsupported claims, conflicting sources, uncertain chronology and invented episode details.
- Never invent URLs, quotes, episode numbers, dates or statistics.
- Use explicit uncertainty/opinion language when evidence is incomplete.
- Only accepted claims enter factual scripts.

| Claim state | Meaning | Action |
|---|---|---|
| supported | Evidence directly supports claim | Use subject to review |
| partial | Only part/context supported | Narrow or qualify |
| conflicting | Sources disagree | Explain conflict or omit |
| unsupported | No evidence found | Remove or mark opinion |
| unknown | Research incomplete | Block factual assertion |

### 4.3 Visual/audio quality engine

Phase 1 targets professional motion-graphics/explainer quality, not full animation or exact copyrighted character reproduction.

| Layer | Requirement |
|---|---|
| Identity | Consistent palette, typography, spacing, safe margins and brand. |
| Scene design | Every narration beat has visual purpose; avoid one static image throughout. |
| Motion | Kinetic typography, parallax, pans/zooms, animated cards, timelines, charts and transitions. |
| Asset consistency | Visuals match script; use original/licensed/permissioned assets. |
| Audio | Natural pacing, measured loudness, clean narration, ducked music, no clipping. |
| Captions | Correct Hindi, readable size, timing, line breaks and contrast. |
| Pacing | Scene duration follows spoken segment; avoid dead frames and gratuitous transitions. |
| AI imagery | Optional; relevance, consistency, artifacts and licence/terms reviewed. |
| Preview | Low-resolution review; final render only after approvals. |

### 4.4 Rights and asset register

- Asset fields: ID/type/source/provenance/owner/rights basis/status/licence evidence/permitted uses/attribution/expiry/reviewer/time.
- Rights basis: owned, licensed, written permission, reviewed exception, unknown; status: pending, approved, rejected, expired.
- Pending/unknown assets are preview-only; public package blocks them.
- Episode clips default to hold absent documented permission or case-specific legal review.
- AI art, stock, fonts, music and SFX each need applicable licence/use checks.
- Crop, zoom, blur, subtitles, watermark or speed change do not create rights.
- Store an asset manifest for every render/publication.

### 4.5 Publishing

| Destination | Phase | Rule |
|---|---|---|
| Local archive | MVP | Versioned outputs, metadata and manifest. |
| Telegram founder approval | MVP | Private preview; authenticated approve/change/reject. |
| YouTube | Phase 1 | Private-first; separate public approval; remote ID reconciliation. |
| Telegram audience | Later | Only approved original/rights-cleared content. |
| Instagram Reels | Later | After account/API requirements verified. |
| Facebook/others | Later | Adapter-by-adapter after demand/access checks. |

- Use platform-independent PublishPackage, not raw render path.
- Publication state separates upload, processing, scheduled, published, restricted, failed and deleted.
- Idempotency key; save remote ID; reconcile uncertain status before retry.
- Upload success is not rights clearance, monetization eligibility or processing completion.
- Verify API access, quotas, account eligibility and rules at implementation.

### 4.6 Claim/restriction observations

| Field | Definition |
|---|---|
| Publication | Specific platform publication |
| Claim observation | unknown / no_claim_observed / active / released |
| Restriction | unknown / none_observed / blocked / other |
| Source | manual Studio / email ingestion / authorised API |
| Timestamp/reviewer | When and who checked |

Missing observation stays unknown. No-claim observed is a point-in-time platform observation—not proof of legal permission or future safety.

### 4.7 CRM and sales engine

Lead → source → qualification → relevant observation → idea → demo → human approval → outreach draft → human approval/send → follow-up → call → pilot → onboarding → production → invoice/payment → renewal

- Manual prospect selection in MVP; capture source/contact provenance.
- Score fit, activity, visible content bottleneck, commercial intent, budget fit and demo personalisation.
- Every message references a genuine relevant observation; no generic mass messaging or purchased lists.
- Human approval before send; respect opt-outs, platform terms and privacy/anti-spam rules.
- Follow-up reminders allowed; repeated automatic sends without review are not.
- Demo clearly labelled sample/speculative; rights-cleared assets only.
- Client scope: output count/duration/revisions/turnaround/posting/price/payment/cancellation.

### 4.8 Client production

- Brief: objective, audience, platform, brand, examples, CTA, assets, claims, restrictions and deadline.
- Client assets isolated by client/project; confidential assets never enter portfolio without permission.
- Script/preview approval recorded; revisions linked to version.
- Delivery includes final file, captions, title/caption suggestions and record.
- Track hours, costs, revisions, deadline, invoice/payment, renewal and feedback.
- Out-of-scope changes trigger change request or fee.

### 4.9 Analytics

| Category | Metrics |
|---|---|
| Content | Views, average view duration, retention, likes/comments/shares/saves, profile visits, clicks, joins, returning viewers. |
| Production | Human minutes/video, render time, failures/retries, QA, rejection reasons, rights coverage. |
| Sales | Qualified leads, demos, outreach/replies, positive replies, calls, pilots, conversion, follow-ups. |
| Finance | Invoices, collected revenue, outstanding, costs, refunds, contribution, hours, effective hourly earning. |
| Retention | Renewal, repeat purchase, churn reason, satisfaction, revision burden. |

Phase 0 may use JSON/CSV/manual metrics. Dashboard is not a prerequisite for validation.

## 5. Content strategy and editorial quality

| Format | Example | Rule |
|---|---|---|
| Nostalgia analysis | Why a childhood cartoon felt memorable | Original interpretation; opinion labelled. |
| Character analysis | Choices/friendship of a character | Fan theory not stated as canon. |
| Hindi TV/dub history | How shows reached Indian audiences | Research dates/broadcasters/dubbing facts. |
| Mystery/fact | Verified detail or misconception | Evidence required; no fake secrets. |
| Comparison/listicle | Themes, characters or eras | Transparent criteria. |
| Audience-led | Answer viewer question | Question/source logged. |

### Editorial score (0–5 each)

| Dimension | Pass guidance |
|---|---|
| Hook | Specific curiosity/emotional premise, no deceptive promise. |
| Originality | Adds perspective, synthesis, humour or explanation. |
| Evidence | Claims supported; uncertainty qualified. |
| Hindi | Speakable conversational Hindi; names checked. |
| Structure | Hook → context → payoff; no filler. |
| Visual potential | Every beat represented meaningfully. |
| Rights | No unapproved clips/music/art/logos. |
| Retention | Progression, pattern changes, satisfying ending. |

Initial threshold: ≥28/40 and no critical factual/rights failure. Calibrate with human reviews; score is not an objective quality guarantee.

## 6. AI strategy and free provider design

The system must work without a paid LLM key. Free hosted models are optional accelerators, not unlimited foundations.

| Task | Primary | Fallback | Forbidden |
|---|---|---|---|
| Classification | Rules | Rules | Invent facts |
| Research synthesis | Free hosted LLM | Manual source notes | Model memory as evidence |
| Script draft | Free hosted LLM | Prompt templates + human | Auto-approve |
| Script QA | Rules + second pass | Human checklist | Confidence = truth |
| Caption cleanup | Rules | Human edit | Change meaning |
| Lead scoring | Deterministic rubric | Manual | Infer sensitive data |
| Outreach | Template/optional LLM | Manual | Send unapproved |

- Provider adapter: `generate(task, prompt, schema, timeout, max_tokens)` → result/provider/model/usage/latency/error.
- Configurable provider/model; verify current free quota, data terms and privacy before use.
- Timeout/rate-limit/quota/malformed JSON triggers bounded retry or fallback.
- Log prompt/version, output hash, provider/model, latency/error/usage; avoid unnecessary personal data.
- Validate structured output; reject malformed results.
- Cache by content hash where appropriate; recheck stale facts.
- Local model optional and benchmarked on laptop; CPU speed not assumed.
- Piper and FFmpeg work without LLM.

## 7. Video quality specification

### 7.1 Quality tiers

| Tier | Definition | Phase |
|---|---|---|
| 0 Functional | Voice + captions + simple visual; internal test. | 0 |
| 1 Publishable motion graphics | Designed scenes, coherent visuals, typography, transitions, clean audio/captions, sourced script and QA. | 0–1 target |
| 2 AI cinematic montage | Optional generated scenes; reviewed for relevance, consistency, artifacts and rights/terms. | Later experiment |
| 3 Character animation | Continuous consistent acting/animation; not promised by MVP/free stack. | Out of scope |

### 7.2 Render specification

| Parameter | Requirement |
|---|---|
| Aspect | 9:16; 1080×1920 final; configurable lower preview. |
| FPS | Configurable template default; consistent source/output. |
| Audio | Loudness normalisation, ducking, clipping/silence checks. |
| Captions | Hindi UTF-8/font glyphs, safe margins, contrast, timing. |
| Visuals | Scene timeline, relevant assets, no blank/black frames or excessive repetition. |
| Brand | Palette/type/logo/handle and CTA where appropriate. |
| Export | MP4 with documented codec/container settings, manifest and QA. |
| Reproducibility | Template/script/assets/voice/settings logged. |

### 7.3 QA gates

- File opens; expected duration/resolution.
- Audio stream exists; silence/clipping/loudness checks pass.
- Captions exist, cover narration and contain no malformed/empty segments.
- Assets resolve and rights approved for public package.
- No unintended timeline gaps/black frames; scene durations within bounds.
- Script/asset approval matches exact render version.
- Optional sampled-frame QA flags duplicates, overflow, artifacts or mismatch for human review.
- Failure blocks final/publication; regeneration is bounded and surfaced.

Automated QA cannot fully judge humour, storytelling, factual truth or aesthetics. Human preview remains mandatory.

## 8. Journeys and state machines

### 8.1 Video journey

`idea → researching → evidence_review → scripting → script_review → approved → scene_planning → preview_render → QA → human_review → final_render → publish_package → private_upload → processing → manual_review → public_release_approval → published`

Exception states: rejected, needs_changes, failed, cancelled, blocked_rights, expired_approval. Material changes invalidate approval.

### 8.2 Lead journey

`new → sourced → qualified/disqualified → idea_ready → demo_ready → demo_approved → outreach_draft → outreach_approved → sent → replied/no_reply/opted_out → call → pilot → won/lost`

### 8.3 Approval rules

- Approval binds user, object, version/hash, action and timestamp.
- Telegram callback validates sender and permitted action.
- Expired approval is expired—not rejected—and requires fresh review.
- Material script/asset/destination/caption/privacy/scope changes require fresh approval.
- Public release is separate from preview and private-upload approval.

## 9. Functional requirements

| ID | Requirement |
|---|---|
| FR-01 | Topic create/edit/archive; angle, audience, format, priority, status. |
| FR-02 | Research dossier and source reliability/freshness. |
| FR-03 | Claim ledger; unsupported factual statements blocked. |
| FR-04 | Versioned Hindi scripts; exact version preserved. |
| FR-05 | Quality scoring and factual/rights gates. |
| FR-06 | Scene planner maps narration to visuals, motion, duration and assets. |
| FR-07 | Piper/recorded audio; failed/silent segment detection. |
| FR-08 | Sentence captions, SRT/VTT, Hindi font/line breaks. |
| FR-09 | FFmpeg templates, preview/final, audio, branding, QA, manifest. |
| FR-10 | Rights register, licence evidence and expiry. |
| FR-11 | Telegram approval with identity/version/hash audit. |
| FR-12 | Private YouTube upload, idempotency and recovery. |
| FR-13 | Separate public release approval. |
| FR-14 | Manual Studio claim/restriction observations. |
| FR-15 | Lead source, score, demo, outreach and follow-up. |
| FR-16 | Personalised outreach draft, approval, opt-out. |
| FR-17 | Client brief, scope, assets, brand, deadline, rights. |
| FR-18 | Client production, revisions, delivery and acceptance. |
| FR-19 | Invoices, payments, costs, contribution and hourly earning. |
| FR-20 | Manual/API metrics with source and collection timestamp. |
| FR-21 | Backup and restore documentation/test. |
| FR-22 | Audit log for state changes, approvals, rights and publishing. |

## 10. Non-functional requirements

| Area | Requirement |
|---|---|
| Reliability | Bounded retries/backoff, max attempts, dead-letter, heartbeat and recovery. |
| Idempotency | Duplicate job/publication protection; reconcile before retry. |
| Security | Secrets in env/secret store; no secrets in logs; secure OAuth. |
| Authorization | Telegram allowlist; validate callback user/object/version/action. |
| Privacy | Minimise prospect/client data; provenance, retention and deletion policy. |
| Performance | Render concurrency 1; benchmark laptop; no DB transaction during render/upload. |
| Observability | Structured logs, state, attempts, lock, heartbeat, latency, error. |
| Maintainability | Configurable providers/templates/destinations; migrations/versioning. |
| Portability | Local-first and documented; no mandatory paid SaaS. |
| Recovery | Restart safely, reconcile upload, preserve partial artifacts, backup. |

## 11. Technical architecture

### 11.1 MVP

CLI / Telegram Bot → Python modules (research, claims, scripts, scene planner, TTS, captions, render, QA, approval, publish) → SQLite + local assets/output

Start single local operator and one worker. Add FastAPI after CLI stabilises. PostgreSQL is justified when concurrent workers, remote access or complexity require it.

### 11.2 Later

Telegram/Web → FastAPI → PostgreSQL job queue → worker(s) → AI/TTS/render/publish/CRM; local/object storage; Redis only for measured need.

### 11.3 Folder structure

```text
creatorops/
├── README.md, PRD.md, .env.example, pyproject.toml, Makefile
├── creatorops/
│   ├── cli.py, config.py
│   ├── db/, jobs/, research/, claims/, scripts/
│   ├── scene_planner/, ai/providers/
│   ├── tts/, captions/, render/templates/, qa/
│   ├── assets/, approvals/, publish/
│   ├── crm/, finance/, analytics/
├── bot/, tests/
├── data/assets/, data/rights/, data/projects/, data/backups/
└── output/
```

### 11.4 Core entities

| Entity | Purpose / key fields |
|---|---|
| topics | title, angle, audience, format, priority, status |
| sources | URL/title/type/access date/reliability/notes |
| claims | text, source refs, state, reviewer |
| scripts | topic, version, text, score, approval |
| scene_plans | script version, scenes, duration, assets, motion |
| assets | provenance, rights basis/status, licence, expiry, hash |
| videos | manifest, preview/final paths, QA, hash |
| jobs | type/state/attempts/heartbeat/lock/error/idempotency |
| approvals | object/version/hash/user/action/time/expiry |
| publications | video/destination/remote ID/state/privacy/key |
| observations | publication, claim/restriction, source/time/reviewer |
| metrics | publication, metric/value/period/source/time |
| leads | source/profile/score/status/contact provenance/opt-out |
| clients/deliveries | package/rate/scope/brief/revisions/deadline/acceptance |
| invoices/payments | amount/status/date/cost/allocation |
| llm_calls/audit | task/provider/prompt/version/result/error; actor/action/object/time |

## 12. Business model and unit economics

Early revenue priority: paid content-production pilots and retainers. Audience monetisation is a later, uncertain bonus.

| Offer | Test scope | Indicative test price |
|---|---|---|
| Pilot | 4 shorts, fixed duration, one revision each | ₹1,499–₹1,999 |
| Starter | 8/month, limited revisions | ₹2,999 |
| Growth | 12/month, fixed scope/schedule | ₹4,999 |

These are test prices—not validated market rates.

### Monthly illustration

| Amount |
|---|
| 3 clients × ₹5,000 = ₹15,000 |
| 2 clients × ₹4,000 = ₹8,000 |
| Affiliate/digital products = ₹2,000 |
| **Gross target = ₹25,000** |

- Contribution = collected revenue − direct production costs − transaction costs − refunds
- Effective hourly earning = (collected fee − direct costs) / total delivery hours
- Invoice raised ≠ cash collected.
- Track communication, revisions, failures and sales time—not only render time.
- Set minimum hourly earning threshold; revise price/scope if missed.
- Count affiliate/platform revenue only when collected.
- ₹3 lakh/year is a target, not forecast/guarantee.

## 13. Success metrics and experiments

| Phase | Exit criteria |
|---|---|
| 0 | One source-aware approved script renders a watchable preview; effort/errors measured; no public upload. |
| 1 | Private YouTube upload; remote ID/processing; manual review; simulated recovery without duplicate. |
| 2 | 10–15 original videos; paid pilot or credible buying signal; hours/contribution measured. |
| 3 | Repeat audience signal and/or client renewal; repeatable delivery. |
| 4 | Add destinations only where demand/access justify. |

### 13.1 Experiments

| Experiment | Hypothesis | Measure |
|---|---|---|
| Format | One format creates repeat engagement | Multiple posts; avoid viral outlier |
| Voice | Voice A more natural | Human ratings, pronunciation, retention if sample adequate |
| Offer | Creators pay for package | Qualified conversations and paid conversion |
| Pricing | Scope/price sustainable | Collected fee, hours, revisions |
| Lead channel | Channel gives qualified prospects | Qualified leads and paid conversion/hour |

## 14. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Hallucination | Misinformation | Claim sources, evidence gate, uncertainty, human review |
| Generic video | Low retention/no clients | Editorial identity, scene plan, motion, QA, preview |
| Free quota change | Pipeline stalls | Adapters, manual fallback, cache, quota monitoring |
| TTS errors | Unprofessional voice | Pronunciation dictionary, sample review, voice options |
| Visual artifacts | Distracting video | Scene review, approved assets, human QA |
| Rights issues | Takedown/account/legal exposure | Rights register; no episode repost; separate legal/platform/monetization checks |
| No demand | No revenue | Early outreach, narrow segment, paid pilot, pivot criteria |
| Scope creep | Loss-making client | Scope/revision cap/change requests |
| Burnout | Abandonment | Part-time cadence, batch production, client cap |
| Overengineering | Delayed validation | Local CLI MVP; defer dashboard/n8n/multiplatform |
| Duplicate publish | Quota/reputation harm | Idempotency, reconciliation, separate approval |
| Data loss | Lost work | Backups and restore test |

## 15. Compliance and ethics

- YouTube reused-content monetization review is distinct from copyright claims and legal permission.
- Permission does not guarantee monetization eligibility.
- No episode-site redistribution, DRM/access-control bypass or policy evasion.
- Never promise copyright-safe, claim-free or monetization-approved videos.
- Verify platform API access, quota, eligibility and terms at implementation.
- Respect terms, privacy, opt-outs and applicable anti-spam requirements.
- Use client assets only for agreed purpose; minimise retention/access.
- Review licences for libraries, fonts, music, stock and generated media.

## 16. Implementation roadmap

| Phase | Days | Build | Gate |
|---|---|---|---|
| 0 Local proof | 0–7 | CLI, SQLite, one format, evidence/claim gate, Piper, captions, FFmpeg, QA, Telegram preview | One approved watchable video; no public upload |
| 1 Controlled publishing | 8–21 | Approval, private YouTube, idempotency/recovery, processing, manual review | Private upload + simulated recovery; public separate |
| 2 Business validation | 22–45 | Portfolio, package, manual leads, demo, approval outreach, client/invoice tracker | Paid pilot/buying signal; workload measured |
| 3 Audience/retention | 46–75 | Metrics, format tests, renewals, optional Instagram adapter | Repeat engagement or renewal signal |
| 4 Scale | 76–90+ | More templates/destinations, lead research, dashboard, optional n8n | Scale proven workflows; continue/pivot |

## 17. Testing

| Test | Examples |
|---|---|
| Unit | Claim transitions, scoring, captions, durations, idempotency, package validation. |
| Integration | Piper, FFmpeg, SQLite, Telegram callbacks, mocked YouTube. |
| Failure injection | TTS timeout, malformed LLM, disk full, worker crash, interrupted upload, duplicate callback. |
| Quality | Hindi, facts, scene relevance, caption readability, audio, pacing, artifacts. |
| Security | Unauthorized callback, token leakage, client isolation, version mismatch. |
| Recovery | Worker restart, publication reconciliation, backup restore, manifest regeneration. |

## 18. First release acceptance criteria

1. Operator creates topic and attaches sources.
2. Script draft has claim references and unsupported claims flagged.
3. Script is editable/versioned and approved before release render.
4. Scene plan maps narration beats to visual, motion and asset.
5. Narration generated; failed/silent segments detected.
6. Hindi captions timed and rendered.
7. Preview has correct aspect, audio, captions and pacing.
8. QA reports missing assets, rights, audio/caption/render issues.
9. Telegram preview supports approve/change/reject with identity/version checks.
10. Final render reproducible from manifest.
11. Unknown/pending rights assets blocked from public package.
12. Private upload stores remote ID and reconciles uncertain retry.
13. Public release requires separate approval.
14. Manual platform observation recorded without claiming legal clearance.
15. Client workflow tracks scope, delivery, revisions, invoice, payment and hours.

## 19. Open decisions

1. Preferred Piper Hindi voice and pronunciation dictionary.
2. First two content formats/editorial identity.
3. First client segment (test hypothesis: active small YouTube creators).
4. Current free LLM providers, quotas, privacy terms and fallback order.
5. Actual YouTube project quota/channel limit and OAuth requirements.
6. Approved commercial visual/font/music/SFX sources.
7. Pilot package, price, revision policy and turnaround.
8. Minimum hourly earning and monthly contribution threshold.
9. Hosted storage/API vs local-first after validation.

## 20. Immediate next actions

1. Create repo, README, `.env.example` and PRD.
2. Build CLI topic/script/claim ledger with SQLite.
3. Implement source-aware Hindi script workflow and evidence review.
4. Integrate Piper; test voice and pronunciation.
5. Implement scene-plan JSON and one motion-graphics FFmpeg template.
6. Render preview, QA and Telegram approval.
7. Create 3 portfolio videos and test narrow paid pilot.
8. Add private YouTube publishing/recovery after proof.
9. Contact qualified prospects with personalised approved demos.
10. Review weekly; continue, revise or stop based on demand and economics.

## Appendix A — Definition of done

- **Feature:** tests, config docs, observable errors and safe failure.
- **Video:** script/claims, rights/assets, audio, captions, QA and human approval complete.
- **Publication:** destination state and remote ID reconciled.
- **Client delivery:** approved files delivered; revisions, acceptance and payment updated.
- **Experiment:** metric, sample, outcome and next decision recorded.

## Appendix B — Product promise

CreatorOps automates production steps; it does not automate truth, taste, legal clearance, customer trust or guaranteed revenue.

The goal is a reliable assistant-operated production business—not a black-box bot that publishes unverified content or sends indiscriminate messages.
