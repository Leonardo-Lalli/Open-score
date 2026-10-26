-- Extended sports configuration support.
-- Canonical catalog: one row per sport, no aliases or duplicates.

-- Normalise names used by the first schema before linking sport_id.
UPDATE tournaments SET sport = 'Pallavolo' WHERE sport = 'Volley';
UPDATE tournaments SET sport = 'Basket' WHERE sport = 'Pallacanestro';

CREATE TABLE sport_configs (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK(length(trim(name)) BETWEEN 2 AND 60),
    description TEXT NOT NULL DEFAULT '',
    points_system TEXT NOT NULL DEFAULT 'standard',
    rules TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

INSERT INTO sport_configs (name, description, points_system, rules) VALUES
('Calcio', 'Sport di squadra con regole classiche di calcio', 'standard',
 '{"max_team_size": 11, "min_team_size": 7, "field_type": "grass", "ball_type": "standard", "set_based_scoring": false, "time_based_scoring": false}'),
('Calcio a 5', 'Calcio su campo ridotto con 5 giocatori per squadra', 'standard',
 '{"max_team_size": 5, "min_team_size": 5, "field_type": "grass", "ball_type": "small", "set_based_scoring": false, "time_based_scoring": false}'),
('Basket', 'Sport di squadra con palla e canestro', 'standard',
 '{"max_team_size": 5, "min_team_size": 5, "court_type": "indoor", "ball_type": "basket", "set_based_scoring": false, "time_based_scoring": false}'),
('Pallamano', 'Sport con palla e rete', 'standard',
 '{"max_team_size": 7, "min_team_size": 7, "court_type": "indoor", "ball_type": "handball", "set_based_scoring": false, "time_based_scoring": false}'),
('Badminton', 'Sport con racchetta e volano', 'standard',
 '{"max_team_size": 2, "min_team_size": 1, "court_type": "indoor", "net_type": "standard", "set_based_scoring": true, "time_based_scoring": false}'),
('Tennis', 'Sport con racchetta e palla', 'standard',
 '{"max_team_size": 2, "min_team_size": 1, "court_type": "outdoor", "surface": "clay", "set_based_scoring": true, "time_based_scoring": false}'),
('Pallavolo', 'Sport di squadra con palla e rete', 'standard',
 '{"max_team_size": 6, "min_team_size": 6, "court_type": "indoor", "net_type": "standard", "set_based_scoring": true, "time_based_scoring": false}');

ALTER TABLE tournaments ADD COLUMN sport_id INTEGER REFERENCES sport_configs(id);
UPDATE tournaments SET sport_id = (SELECT id FROM sport_configs WHERE name = tournaments.sport);
CREATE INDEX tournament_sport ON tournaments(sport_id);

-- Format and scoring metadata used by the wizard and future sport rules.
ALTER TABLE tournaments ADD COLUMN tournament_type TEXT NOT NULL DEFAULT 'general' CHECK(tournament_type IN ('general', 'championship', 'cup'));
ALTER TABLE tournaments ADD COLUMN scoring_system TEXT NOT NULL DEFAULT 'points' CHECK(scoring_system IN ('points', 'sets', 'time'));
ALTER TABLE tournaments ADD COLUMN win_points_custom INTEGER;
ALTER TABLE tournaments ADD COLUMN draw_points_custom INTEGER;
ALTER TABLE tournaments ADD COLUMN loss_points_custom INTEGER;
UPDATE tournaments SET
    win_points_custom = win_points,
    draw_points_custom = draw_points,
    loss_points_custom = loss_points;

PRAGMA user_version=3;
