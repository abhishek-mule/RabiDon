-- 004_jobs_publish.sql: job leases, publication attempts/observations (ADR-007, Phase 1 design).

CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_type TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  idempotency_key TEXT UNIQUE,
  status TEXT NOT NULL DEFAULT 'queued' CHECK (
    status IN ('queued','running','retry_scheduled','awaiting_approval','awaiting_manual_input','succeeded','failed','dead')
  ),
  attempts INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 3,
  run_after TEXT NOT NULL,
  locked_by TEXT,
  worker_token TEXT,
  locked_at TEXT,
  heartbeat_at TEXT,
  lease_expires_at TEXT,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_jobs_ready ON jobs(status, run_after);
CREATE INDEX IF NOT EXISTS idx_jobs_lease ON jobs(status, lease_expires_at);

CREATE TABLE IF NOT EXISTS publication_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  publish_package_id INTEGER REFERENCES publish_packages(id),
  destination TEXT NOT NULL,
  action TEXT NOT NULL, -- private_upload|public_release
  idempotency_key TEXT NOT NULL,
  upload_session_ref TEXT, -- stored securely/reference only; never log secrets
  local_state TEXT NOT NULL DEFAULT 'not_started' CHECK (
    local_state IN ('not_started','uploading','uploaded','failed','reconciliation_required')
  ),
  remote_id TEXT,
  remote_url TEXT,
  processing_state TEXT NOT NULL DEFAULT 'unknown',
  visibility_state TEXT NOT NULL DEFAULT 'unknown',
  last_observed_at TEXT,
  error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (destination, action, idempotency_key)
);

CREATE TABLE IF NOT EXISTS platform_observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  publication_attempt_id INTEGER NOT NULL REFERENCES publication_attempts(id),
  claim_status TEXT NOT NULL DEFAULT 'unknown' CHECK (
    claim_status IN ('unknown','no_claim_observed','active','released')
  ),
  restriction_status TEXT NOT NULL DEFAULT 'unknown',
  source TEXT NOT NULL, -- manual_studio|partner_api|email_notification
  observed_at TEXT NOT NULL,
  reviewer TEXT,
  notes TEXT
);
