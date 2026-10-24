-- Rebuilt phases must never recycle IDs that an older browser still holds.
CREATE TABLE matches_new (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 tournament_id INTEGER NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
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
INSERT INTO matches_new SELECT * FROM matches;
DROP TABLE matches;
ALTER TABLE matches_new RENAME TO matches;
CREATE INDEX match_tournament ON matches(tournament_id,stage_id,round_no);
PRAGMA user_version=2;
