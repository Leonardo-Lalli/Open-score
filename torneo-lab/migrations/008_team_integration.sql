CREATE TABLE IF NOT EXISTS teacher_user_links (
 teacher_id INTEGER PRIMARY KEY REFERENCES teachers(id),
 user_id INTEGER NOT NULL UNIQUE REFERENCES users(id)
);
ALTER TABLE teachers ADD COLUMN active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1));
ALTER TABLE fields ADD COLUMN description TEXT NOT NULL DEFAULT '';
ALTER TABLE fields ADD COLUMN availability_note TEXT NOT NULL DEFAULT '';
ALTER TABLE team_players ADD COLUMN student_id INTEGER REFERENCES students(id);
CREATE UNIQUE INDEX team_player_student ON team_players(student_id) WHERE student_id IS NOT NULL;
CREATE TABLE player_performances (
 match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
 player_id INTEGER NOT NULL REFERENCES team_players(id) ON DELETE CASCADE,
 points INTEGER NOT NULL CHECK(points>=0 AND points<=999),
 PRIMARY KEY(match_id,player_id)
);
PRAGMA user_version=8;
