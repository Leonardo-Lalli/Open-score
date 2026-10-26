-- Non-destructive lifecycle: tournaments are archived, never deleted.
ALTER TABLE tournaments ADD COLUMN archived_at TEXT;
ALTER TABLE tournaments ADD COLUMN updated_at TEXT;
UPDATE tournaments SET updated_at = created_at;
CREATE INDEX tournament_archive ON tournaments(archived_at);

PRAGMA user_version=4;
