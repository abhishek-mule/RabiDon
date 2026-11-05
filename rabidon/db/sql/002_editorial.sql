-- 002_editorial.sql: topics/sources/claims/revisions/reviews/scripts (evidence gate)
-- ADR-008: timestamps UTC ISO-8601 text. Factual claims are distinct from platform observations.

CREATE TABLE IF NOT EXISTS topics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  angle TEXT NOT NULL,
  audience TEXT,
  format TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 5,
  status TEXT NOT NULL DEFAULT 'idea',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT,
  title TEXT NOT NULL,
  source_type TEXT NOT NULL,
  accessed_at TEXT NOT NULL,
  reliability TEXT NOT NULL DEFAULT 'unknown',
  notes TEXT,
  content_hash TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claims (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  topic_id INTEGER NOT NULL REFERENCES topics(id),
  current_revision_id INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claim_revisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  claim_id INTEGER NOT NULL REFERENCES claims(id),
  revision INTEGER NOT NULL,
  text TEXT NOT NULL,
  evidence_status TEXT NOT NULL CHECK (
    evidence_status IN ('supported','partial','conflicting','unsupported','unknown')
  ),
  evidence_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (claim_id, revision)
);

CREATE TABLE IF NOT EXISTS claim_revision_sources (
  claim_revision_id INTEGER NOT NULL REFERENCES claim_revisions(id),
  source_id INTEGER NOT NULL REFERENCES sources(id),
  supporting_note TEXT,
  excerpt TEXT,
  PRIMARY KEY (claim_revision_id, source_id)
);

CREATE TABLE IF NOT EXISTS claim_reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  claim_id INTEGER NOT NULL REFERENCES claims(id),
  claim_revision_id INTEGER NOT NULL REFERENCES claim_revisions(id),
  evidence_hash TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (
    decision IN ('accepted','narrowed','rejected','needs_evidence')
  ),
  accepted_wording TEXT,
  reviewer TEXT NOT NULL,
  notes TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_claim_reviews_claim ON claim_reviews(claim_id, created_at DESC);

CREATE TABLE IF NOT EXISTS scripts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  topic_id INTEGER NOT NULL REFERENCES topics(id),
  current_revision_id INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS script_revisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  script_id INTEGER NOT NULL REFERENCES scripts(id),
  revision INTEGER NOT NULL,
  language TEXT NOT NULL DEFAULT 'hi-IN',
  text TEXT NOT NULL,
  approval_status TEXT NOT NULL DEFAULT 'draft' CHECK (
    approval_status IN ('draft','approved','rejected','needs_changes','blocked')
  ),
  quality_score INTEGER,
  created_at TEXT NOT NULL,
  UNIQUE (script_id, revision)
);

CREATE TABLE IF NOT EXISTS script_revision_claims (
  script_revision_id INTEGER NOT NULL REFERENCES script_revisions(id),
  claim_id INTEGER NOT NULL REFERENCES claims(id),
  PRIMARY KEY (script_revision_id, claim_id)
);
