-- 003_media_control.sql: assets/permissions, approvals, media artifacts, scene plans, QA.
-- ADR-003/004/005/008/010/011. No approval refs inside PublishPackage; approvals reference package hashes.

CREATE TABLE IF NOT EXISTS assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_type TEXT NOT NULL CHECK (asset_type IN ('graphic','video','audio','font','generated','other')),
  local_path TEXT NOT NULL,
  owner TEXT,
  provenance TEXT,
  content_hash TEXT NOT NULL,
  mime_type TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS asset_permissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id INTEGER NOT NULL REFERENCES assets(id),
  rights_basis TEXT NOT NULL CHECK (
    rights_basis IN ('owned','licensed','written_permission','reviewed_exception','unknown')
  ),
  rights_status TEXT NOT NULL CHECK (
    rights_status IN ('pending','approved','rejected','expired')
  ),
  permitted_uses_json TEXT NOT NULL DEFAULT '[]', -- e.g. ["local_preview","external_preview","final_render","private_upload","public_release","client_delivery"]
  evidence_ref TEXT,
  attribution TEXT,
  expires_at TEXT,
  reviewer TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_asset_permissions_asset ON asset_permissions(asset_id, id DESC);

CREATE TABLE IF NOT EXISTS approval_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  action TEXT NOT NULL, -- telegram_preview|final_render|private_upload|public_release|client_delivery|outreach_send
  object_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  object_version TEXT NOT NULL,
  object_hash TEXT NOT NULL,
  target_json TEXT NOT NULL DEFAULT '{}',
  token_hash TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (
    status IN ('pending','approved','rejected','changes_requested','expired','consumed')
  ),
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS approval_decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL REFERENCES approval_requests(id),
  approver TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (decision IN ('approved','rejected','changes_requested')),
  notes TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scene_plans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  script_revision_id INTEGER NOT NULL REFERENCES script_revisions(id),
  revision INTEGER NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('provisional','resolved')),
  timing_revision_id TEXT,
  plan_json TEXT NOT NULL,
  plan_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (script_revision_id, revision)
);

CREATE TABLE IF NOT EXISTS narration_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  script_revision_id INTEGER NOT NULL REFERENCES script_revisions(id),
  provider TEXT NOT NULL, -- piper|recorded
  voice_id TEXT,
  narration_path TEXT NOT NULL,
  segments_json TEXT NOT NULL,
  total_duration_ms INTEGER NOT NULL,
  segments_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS videos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  topic_id INTEGER NOT NULL REFERENCES topics(id),
  script_revision_id INTEGER NOT NULL REFERENCES script_revisions(id),
  scene_plan_id INTEGER REFERENCES scene_plans(id),
  narration_run_id INTEGER REFERENCES narration_runs(id),
  template_id TEXT,
  status TEXT NOT NULL DEFAULT 'created',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS render_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id INTEGER NOT NULL REFERENCES videos(id),
  kind TEXT NOT NULL CHECK (kind IN ('preview','final')),
  status TEXT NOT NULL DEFAULT 'running',
  manifest_path TEXT,
  manifest_hash TEXT,
  artifact_path TEXT,
  artifact_hash TEXT,
  qa_report_path TEXT,
  error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS qa_reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  render_run_id INTEGER NOT NULL REFERENCES render_runs(id),
  result TEXT NOT NULL CHECK (result IN ('pass','pass_with_warnings','fail')),
  report_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS publish_packages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id INTEGER NOT NULL REFERENCES videos(id),
  render_run_id INTEGER NOT NULL REFERENCES render_runs(id),
  destination TEXT NOT NULL,
  action TEXT NOT NULL,
  privacy TEXT NOT NULL,
  package_json TEXT NOT NULL,
  package_hash TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);
