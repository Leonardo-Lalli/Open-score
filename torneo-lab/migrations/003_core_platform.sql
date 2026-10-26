-- Additive migration. Legacy tournaments remain unowned until an explicit claim.
CREATE TABLE organizations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL
);
CREATE TABLE users (
 id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE,
 display_name TEXT NOT NULL, password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('teacher','student')),
 organization_id INTEGER REFERENCES organizations(id),
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE sessions (
 token_hash TEXT PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
 csrf_token TEXT NOT NULL, expires_at TEXT NOT NULL
);
CREATE INDEX session_expiry ON sessions(expires_at);
CREATE TABLE auth_attempts (
 key TEXT PRIMARY KEY, attempts INTEGER NOT NULL, expires_at TEXT NOT NULL
);
CREATE TABLE administrative_audit (
 id INTEGER PRIMARY KEY AUTOINCREMENT, actor_id INTEGER NOT NULL REFERENCES users(id),
 action TEXT NOT NULL, resource_id INTEGER, payload TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
ALTER TABLE tournaments ADD COLUMN owner_id INTEGER REFERENCES users(id);
ALTER TABLE tournaments ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
ALTER TABLE tournaments ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE tournaments ADD COLUMN order_version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE tournaments ADD COLUMN variant_id TEXT;
ALTER TABLE tournaments ADD COLUMN rules_json TEXT;
ALTER TABLE tournaments ADD COLUMN published INTEGER NOT NULL DEFAULT 0 CHECK(published IN (0,1));
ALTER TABLE tournaments ADD COLUMN public_slug TEXT;
CREATE UNIQUE INDEX tournament_slug ON tournaments(public_slug) WHERE public_slug IS NOT NULL;
CREATE INDEX tournament_owner ON tournaments(owner_id);
CREATE TABLE tournament_collaborators (
 tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
 user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 PRIMARY KEY(tournament_id,user_id)
);
ALTER TABLE teams ADD COLUMN display_order INTEGER NOT NULL DEFAULT 0;
ALTER TABLE teams ADD COLUMN max_members INTEGER CHECK(max_members IS NULL OR max_members>0);
ALTER TABLE teams ADD COLUMN archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1));
ALTER TABLE teams ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
UPDATE teams SET display_order=id;
CREATE TABLE students (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
 user_id INTEGER REFERENCES users(id), display_name TEXT NOT NULL,
 team_id INTEGER REFERENCES teams(id), version INTEGER NOT NULL DEFAULT 1,
 UNIQUE(tournament_id,user_id)
);
CREATE INDEX student_team ON students(tournament_id,team_id);
CREATE TABLE invites (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
 team_id INTEGER REFERENCES teams(id), token_hash TEXT NOT NULL UNIQUE,
 expires_at TEXT NOT NULL, max_uses INTEGER NOT NULL CHECK(max_uses>0),
 used INTEGER NOT NULL DEFAULT 0 CHECK(used>=0),
 require_approval INTEGER NOT NULL CHECK(require_approval IN (0,1)),
 revoked INTEGER NOT NULL DEFAULT 0 CHECK(revoked IN (0,1)), version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE enrollments (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
 user_id INTEGER NOT NULL REFERENCES users(id), team_id INTEGER REFERENCES teams(id),
 invite_id INTEGER REFERENCES invites(id),
 status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected')),
 reason TEXT, version INTEGER NOT NULL DEFAULT 1,
 UNIQUE(tournament_id,user_id)
);
CREATE TABLE venues (
 id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL REFERENCES users(id),
 organization_id INTEGER NOT NULL REFERENCES organizations(id), name TEXT NOT NULL
);
CREATE TABLE fields (
 id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL REFERENCES users(id),
 organization_id INTEGER NOT NULL REFERENCES organizations(id),
 venue_id INTEGER REFERENCES venues(id), name TEXT NOT NULL,
 variants_json TEXT NOT NULL, availability_json TEXT NOT NULL,
 archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1)), version INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX field_owner ON fields(owner_id);
ALTER TABLE matches ADD COLUMN field_id INTEGER REFERENCES fields(id);
ALTER TABLE matches ADD COLUMN timezone TEXT;
ALTER TABLE matches ADD COLUMN score_json TEXT;
CREATE INDEX field_schedule ON matches(field_id,scheduled_at);
CREATE TABLE result_proposals (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
 match_id INTEGER REFERENCES matches(id) ON DELETE SET NULL,
 original_match_id INTEGER NOT NULL,
 submitted_by INTEGER NOT NULL REFERENCES users(id), score_json TEXT NOT NULL,
 match_version INTEGER NOT NULL, version INTEGER NOT NULL DEFAULT 1,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX proposal_match ON result_proposals(tournament_id,match_id,status);
-- Immutable history intentionally retains original match IDs after bracket rebuilds.
CREATE TABLE result_reviews (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
 match_id INTEGER NOT NULL, proposal_id INTEGER REFERENCES result_proposals(id),
 reviewed_by INTEGER NOT NULL REFERENCES users(id), decision TEXT NOT NULL,
 reason TEXT NOT NULL, score_json TEXT,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE official_results (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 match_id INTEGER NOT NULL UNIQUE REFERENCES matches(id) ON DELETE CASCADE,
 score_json TEXT NOT NULL, approved_by INTEGER NOT NULL REFERENCES users(id),
 approved_at TEXT NOT NULL, source_proposal_id INTEGER REFERENCES result_proposals(id)
);
ALTER TABLE audit_logs ADD COLUMN actor_id INTEGER REFERENCES users(id);
PRAGMA user_version=3;
