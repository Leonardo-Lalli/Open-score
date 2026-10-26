-- Teacher accounts and tournament ownership.
-- Existing tournaments keep teacher_id NULL and stay read-only for teachers.

CREATE TABLE teachers (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE
        CHECK(length(trim(email)) BETWEEN 3 AND 200),
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX teachers_email ON teachers(email);

ALTER TABLE tournaments ADD COLUMN teacher_id INTEGER REFERENCES teachers(id);

CREATE INDEX tournaments_teacher ON tournaments(teacher_id, id);

PRAGMA user_version=7;
