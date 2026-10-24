-- Extended sports configuration support
CREATE TABLE sport_configs (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK(length(trim(name)) BETWEEN 2 AND 60),
    description TEXT NOT NULL DEFAULT '',
    points_system TEXT NOT NULL DEFAULT 'standard',  -- standard, custom, etc.
    rules TEXT NOT NULL DEFAULT '',  -- JSON rules definition
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- Add sport_id to tournaments table
ALTER TABLE tournaments ADD COLUMN sport_id INTEGER REFERENCES sport_configs(id);

-- Create default sport configurations
INSERT INTO sport_configs (name, description, points_system, rules) VALUES 
('Calcio', 'Sport di squadra con regole classiche di calcio', 'standard', '{"max_team_size": 11, "min_team_size": 7, "field_type": "grass", "ball_type": "standard"}'),
('Calcio a 5', 'Calcio su campo ridotto con 5 giocatori per squadra', 'standard', '{"max_team_size": 5, "min_team_size": 5, "field_type": "grass", "ball_type": "small"}'),
('Basket', 'Sport di squadra con palla e canestro', 'standard', '{"max_team_size": 5, "min_team_size": 5, "court_type": "indoor", "ball_type": "basket"}'),
('Pallamano', 'Sport con palla e rete', 'standard', '{"max_team_size": 7, "min_team_size": 7, "court_type": "indoor", "ball_type": "handball"}'),
('Badminton', 'Sport con racchetta e volano', 'standard', '{"max_team_size": 2, "min_team_size": 1, "court_type": "indoor", "net_type": "standard"}'),
('Tennis', 'Sport con racchetta e palla', 'standard', '{"max_team_size": 2, "min_team_size": 1, "court_type": "outdoor", "surface": "clay"}'),
('Volley', 'Sport di squadra con rete', 'standard', '{"max_team_size": 6, "min_team_size": 6, "court_type": "indoor", "net_type": "standard"}'),
('Pallavolo', 'Sport con palla e rete', 'standard', '{"max_team_size": 6, "min_team_size": 6, "court_type": "indoor", "net_type": "standard"}'),
('Pallacanestro', 'Basket specifico (pallacanestro)', 'standard', '{"max_team_size": 5, "min_team_size": 5, "court_type": "indoor", "ball_type": "basket"}');

-- Update existing tournaments to use default sport configurations
UPDATE tournaments SET sport_id = (SELECT id FROM sport_configs WHERE name = sport);

-- Add tournament_type field to better manage different tournament formats
ALTER TABLE tournaments ADD COLUMN tournament_type TEXT NOT NULL DEFAULT 'general' CHECK(tournament_type IN ('general', 'championship', 'cup'));

-- Add scoring configuration fields to tournaments
ALTER TABLE tournaments ADD COLUMN scoring_system TEXT NOT NULL DEFAULT 'points' CHECK(scoring_system IN ('points', 'sets', 'time'));

-- Add optional custom points for win/draw/loss to support different scoring systems
ALTER TABLE tournaments ADD COLUMN win_points_custom INTEGER;
ALTER TABLE tournaments ADD COLUMN draw_points_custom INTEGER;
ALTER TABLE tournaments ADD COLUMN loss_points_custom INTEGER;

-- Set default values for existing tournaments
UPDATE tournaments SET 
    win_points_custom = win_points,
    draw_points_custom = draw_points,
    loss_points_custom = loss_points;

PRAGMA user_version=3;