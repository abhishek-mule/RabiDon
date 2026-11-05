-- 005_business.sql: Phase 2 manual CRM/finance skeleton (local). No bulk outreach/auto-send.
-- ADR-008: money as integer paise (*_paise). UTC timestamps.

CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  handle TEXT,
  platform TEXT,
  source TEXT NOT NULL,
  contact_provenance TEXT,
  fit_score INTEGER,
  status TEXT NOT NULL DEFAULT 'new',
  opt_out INTEGER NOT NULL DEFAULT 0 CHECK (opt_out IN (0,1)),
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outreach_drafts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lead_id INTEGER NOT NULL REFERENCES leads(id),
  observation TEXT NOT NULL, -- genuine relevant observation required
  message_text TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (
    status IN ('draft','approved','sent','cancelled')
  ),
  approved_hash TEXT,
  sent_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lead_id INTEGER REFERENCES leads(id),
  name TEXT NOT NULL,
  package TEXT,
  rate_paise INTEGER,
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER NOT NULL REFERENCES clients(id),
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  confidentiality TEXT NOT NULL DEFAULT 'normal',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS deliveries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  deliverable TEXT NOT NULL,
  due_date TEXT,
  revisions_used INTEGER NOT NULL DEFAULT 0,
  revisions_allowed INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'pending',
  accepted_at TEXT,
  delivery_hours REAL,
  direct_cost_paise INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invoices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER NOT NULL REFERENCES clients(id),
  project_id INTEGER REFERENCES projects(id),
  amount_paise INTEGER NOT NULL CHECK (amount_paise >= 0),
  status TEXT NOT NULL DEFAULT 'due',
  issued_at TEXT NOT NULL,
  due_at TEXT
);

CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  amount_paise INTEGER NOT NULL CHECK (amount_paise > 0),
  paid_at TEXT NOT NULL,
  method TEXT,
  reference TEXT
);

CREATE TABLE IF NOT EXISTS payment_allocations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  payment_id INTEGER NOT NULL REFERENCES payments(id),
  invoice_id INTEGER NOT NULL REFERENCES invoices(id),
  amount_paise INTEGER NOT NULL CHECK (amount_paise > 0),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER REFERENCES projects(id),
  description TEXT NOT NULL,
  amount_paise INTEGER NOT NULL CHECK (amount_paise >= 0),
  incurred_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS time_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER REFERENCES projects(id),
  kind TEXT NOT NULL, -- delivery|revision|communication|sales|failure
  minutes INTEGER NOT NULL CHECK (minutes >= 0),
  occurred_at TEXT NOT NULL,
  notes TEXT
);
