CREATE TABLE tournaments (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 2 AND 120),
 sport TEXT NOT NULL, format TEXT NOT NULL CHECK(format IN ('round_robin','knockout','groups')),
 description TEXT NOT NULL DEFAULT '', participant_kind TEXT NOT NULL DEFAULT 'team'
 CHECK(participant_kind IN ('team','individual')),
 win_points INTEGER NOT NULL DEFAULT 3 CHECK(win_points BETWEEN 0 AND 10),
 draw_points INTEGER NOT NULL DEFAULT 1 CHECK(draw_points BETWEEN 0 AND 10),
 loss_points INTEGER NOT NULL DEFAULT 0 CHECK(loss_points BETWEEN 0 AND 10),
 legs INTEGER NOT NULL DEFAULT 1 CHECK(legs IN (1,2)), group_count INTEGER NOT NULL DEFAULT 2,
 qualifiers INTEGER NOT NULL DEFAULT 2, random_seed INTEGER, demo_key TEXT UNIQUE,
 public_token TEXT NOT NULL UNIQUE,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE stages (
 id INTEGER PRIMARY KEY, tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
 ordinal INTEGER NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('round_robin','knockout')),
 source_id INTEGER, UNIQUE(tournament_id,ordinal)
);
CREATE TABLE groups (
 id INTEGER PRIMARY KEY, stage_id INTEGER NOT NULL REFERENCES stages(id) ON DELETE CASCADE,
 name TEXT NOT NULL, UNIQUE(stage_id,name)
);
CREATE TABLE teams (
 id INTEGER PRIMARY KEY, tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
 name TEXT NOT NULL COLLATE NOCASE CHECK(length(trim(name)) BETWEEN 1 AND 60),
 group_id INTEGER REFERENCES groups(id), source_id INTEGER,
 UNIQUE(tournament_id,name)
);
CREATE TABLE matches (
 id INTEGER PRIMARY KEY, tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
 stage_id INTEGER NOT NULL REFERENCES stages(id) ON DELETE CASCADE,
 group_id INTEGER REFERENCES groups(id), round_no INTEGER NOT NULL CHECK(round_no>0),
 position INTEGER NOT NULL DEFAULT 0,
 home_team_id INTEGER REFERENCES teams(id), away_team_id INTEGER REFERENCES teams(id),
 source_home INTEGER REFERENCES matches(id), source_away INTEGER REFERENCES matches(id),
 home_score INTEGER, away_score INTEGER, winner_team_id INTEGER REFERENCES teams(id),
 is_bye INTEGER NOT NULL DEFAULT 0 CHECK(is_bye IN (0,1)),
 version INTEGER NOT NULL DEFAULT 1, scheduled_at TEXT, location TEXT,
 duration INTEGER NOT NULL DEFAULT 20 CHECK(duration BETWEEN 1 AND 240), source_id INTEGER,
 CHECK(home_team_id IS NULL OR away_team_id IS NULL OR home_team_id!=away_team_id),
 CHECK((home_score IS NULL AND away_score IS NULL) OR
 (home_score IS NOT NULL AND away_score IS NOT NULL AND home_score BETWEEN 0 AND 999 AND away_score BETWEEN 0 AND 999)),
 UNIQUE(stage_id,round_no,position)
);
CREATE INDEX match_tournament ON matches(tournament_id,stage_id,round_no);
CREATE INDEX team_tournament ON teams(tournament_id);
CREATE TABLE audit_logs (
 id INTEGER PRIMARY KEY, tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
 action TEXT NOT NULL, payload TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
PRAGMA user_version=1;
