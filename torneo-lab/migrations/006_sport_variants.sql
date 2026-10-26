-- Sport hierarchy: a parent sport plus selectable variants with their own rules.
-- Tournaments keep a snapshot so later catalog edits never rewrite history.

ALTER TABLE sport_configs ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0;

UPDATE sport_configs SET sort_order = 1 WHERE name = 'Calcio';
UPDATE sport_configs SET sort_order = 2 WHERE name = 'Basket';
UPDATE sport_configs SET sort_order = 3 WHERE name = 'Pallavolo';
UPDATE sport_configs SET sort_order = 4 WHERE name = 'Badminton';

INSERT INTO sport_configs (name, description, points_system, rules, sort_order)
SELECT 'Ping pong', 'Sport di racchetta con pallina e tavolo', 'standard', '{}', 5
WHERE NOT EXISTS (SELECT 1 FROM sport_configs WHERE name = 'Ping pong');

INSERT INTO sport_configs (name, description, points_system, rules, sort_order)
SELECT 'Biliardino', 'Calcio da tavolo con aste e giocatori', 'standard', '{}', 6
WHERE NOT EXISTS (SELECT 1 FROM sport_configs WHERE name = 'Biliardino');

CREATE TABLE sport_variants (
    id INTEGER PRIMARY KEY,
    sport_id INTEGER NOT NULL REFERENCES sport_configs(id) ON DELETE CASCADE,
    slug TEXT NOT NULL UNIQUE CHECK(length(trim(slug)) BETWEEN 2 AND 80),
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 2 AND 80),
    description TEXT NOT NULL DEFAULT '',
    participant_kind TEXT NOT NULL DEFAULT 'team'
        CHECK(participant_kind IN ('team', 'individual')),
    sort_order INTEGER NOT NULL DEFAULT 0,
    rules TEXT NOT NULL DEFAULT '{}',
    regulation TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE(sport_id, name)
);

CREATE INDEX sport_variants_sport ON sport_variants(sport_id, sort_order);

INSERT INTO sport_variants
    (sport_id, slug, name, description, participant_kind, sort_order, rules, regulation)
VALUES
((SELECT id FROM sport_configs WHERE name = 'Calcio'), 'calcio-a-11', 'Calcio a 11',
 'Undici giocatori per squadra su campo regolamentare.', 'team', 1,
 '{"players_on_field":11,"min_lineup":7,"max_roster":22,"match_duration":90,"periods":2,"period_minutes":45,"scoring_mode":"goals","score_label":"reti","draw_allowed":true,"sets_to_win":null,"max_sets":null,"points_per_set":null,"tiebreak_points":null,"win_by_two":null,"max_points":null,"target_goals":null,"standings":{"win":3,"draw":1,"loss":0,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"goal_difference","surface":"erba","notes":"Due tempi da 45 minuti; fino a 5 sostituzioni."}',
 'Calcio a 11: due tempi da 45 minuti. Ogni squadra schiera 11 giocatori, con un minimo di 7 per iniziare la partita. La rosa comprende al massimo 22 giocatori. Vittoria 3 punti, pareggio 1, sconfitta 0. A parita di punti decide la differenza reti.'),

((SELECT id FROM sport_configs WHERE name = 'Calcio'), 'calcio-a-7', 'Calcio a 7',
 'Sette giocatori per squadra su campo ridotto.', 'team', 2,
 '{"players_on_field":7,"min_lineup":5,"max_roster":14,"match_duration":50,"periods":2,"period_minutes":25,"scoring_mode":"goals","score_label":"reti","draw_allowed":true,"sets_to_win":null,"max_sets":null,"points_per_set":null,"tiebreak_points":null,"win_by_two":null,"max_points":null,"target_goals":null,"standings":{"win":3,"draw":1,"loss":0,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"goal_difference","surface":"erba","notes":"Due tempi da 25 minuti; fino a 5 sostituzioni."}',
 'Calcio a 7: due tempi da 25 minuti. Ogni squadra schiera 7 giocatori, con un minimo di 5 per iniziare. La rosa comprende al massimo 14 giocatori. Vittoria 3 punti, pareggio 1, sconfitta 0. A parita di punti decide la differenza reti.'),

((SELECT id FROM sport_configs WHERE name = 'Calcio'), 'calcio-a-5', 'Calcio a 5',
 'Calcio a cinque su campo ridotto, con regole da futsal.', 'team', 3,
 '{"players_on_field":5,"min_lineup":5,"max_roster":12,"match_duration":40,"periods":2,"period_minutes":20,"scoring_mode":"goals","score_label":"reti","draw_allowed":true,"sets_to_win":null,"max_sets":null,"points_per_set":null,"tiebreak_points":null,"win_by_two":null,"max_points":null,"target_goals":null,"standings":{"win":3,"draw":1,"loss":0,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"goal_difference","surface":"parquet","notes":"Due tempi da 20 minuti effettivi; sostituzioni volanti."}',
 'Calcio a 5: due tempi da 20 minuti effettivi. Ogni squadra schiera 5 giocatori e la rosa comprende al massimo 12 giocatori. Sono ammesse sostituzioni volanti. Vittoria 3 punti, pareggio 1, sconfitta 0. A parita di punti decide la differenza reti.'),

((SELECT id FROM sport_configs WHERE name = 'Basket'), 'basket-5v5', 'Basket 5 contro 5',
 'Basket tradizionale su campo intero.', 'team', 1,
 '{"players_on_field":5,"min_lineup":5,"max_roster":12,"match_duration":40,"periods":4,"period_minutes":10,"scoring_mode":"points","score_label":"punti","draw_allowed":false,"sets_to_win":null,"max_sets":null,"points_per_set":null,"tiebreak_points":null,"win_by_two":null,"max_points":null,"target_goals":null,"standings":{"win":2,"draw":0,"loss":1,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"goal_difference","surface":"parquet","notes":"Quattro periodi da 10 minuti; nessun pareggio."}',
 'Basket 5 contro 5: quattro periodi da 10 minuti. Ogni squadra schiera 5 giocatori e la rosa comprende al massimo 12 giocatori. Non sono previsti pareggi: in caso di parita si giocano supplementari. Vittoria 2 punti, sconfitta 1, sconfitta a tavolino 0. A parita di punti decide la differenza canestri.'),

((SELECT id FROM sport_configs WHERE name = 'Basket'), 'basket-3x3', 'Basket 3x3',
 'Torneo di basket su mezzo campo, formula FIBA 3x3.', 'team', 2,
 '{"players_on_field":3,"min_lineup":3,"max_roster":4,"match_duration":10,"periods":1,"period_minutes":10,"scoring_mode":"points","score_label":"punti","draw_allowed":false,"sets_to_win":null,"max_sets":null,"points_per_set":null,"tiebreak_points":null,"win_by_two":null,"max_points":null,"target_goals":21,"standings":{"win":2,"draw":0,"loss":1,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"goal_difference","surface":"outdoor","notes":"Un periodo da 10 minuti o primo a 21 punti."}',
 'Basket 3x3: un solo periodo da 10 minuti, vince la squadra che arriva per prima a 21 punti. Ogni squadra schiera 3 giocatori e la rosa comprende al massimo 4 giocatori. Non sono previsti pareggi. Vittoria 2 punti, sconfitta 1. A parita di punti decide la differenza canestri.'),

((SELECT id FROM sport_configs WHERE name = 'Pallavolo'), 'pallavolo-6v6', 'Pallavolo 6 contro 6',
 'Pallavolo indoor con formula al meglio dei cinque set.', 'team', 1,
 '{"players_on_field":6,"min_lineup":6,"max_roster":14,"match_duration":105,"periods":null,"period_minutes":null,"scoring_mode":"sets","score_label":"set","draw_allowed":false,"sets_to_win":3,"max_sets":5,"points_per_set":25,"tiebreak_points":15,"win_by_two":true,"max_points":null,"target_goals":null,"standings":{"win":3,"draw":0,"loss":0,"win_tiebreak":2,"loss_tiebreak":1},"default_tie_breaker":"goal_difference","surface":"parquet","notes":"Al meglio dei 5 set; il quinto set si gioca a 15 punti."}',
 'Pallavolo 6 contro 6: partita al meglio dei cinque set. I primi quattro set si giocano a 25 punti, il quinto a 15; serve sempre uno scarto di almeno 2 punti. Ogni squadra schiera 6 giocatori con un massimo di 14 in rosa. Vittoria 3-0 o 3-1: 3 punti alla vincente e 0 alla perdente. Vittoria 3-2: 2 punti alla vincente e 1 alla perdente. A parita di punti decide la differenza set.'),

((SELECT id FROM sport_configs WHERE name = 'Pallavolo'), 'pallavolo-4v4', 'Pallavolo 4 contro 4',
 'Minivolley scolastico con quattro giocatori per squadra.', 'team', 2,
 '{"players_on_field":4,"min_lineup":4,"max_roster":8,"match_duration":50,"periods":null,"period_minutes":null,"scoring_mode":"sets","score_label":"set","draw_allowed":false,"sets_to_win":2,"max_sets":3,"points_per_set":15,"tiebreak_points":15,"win_by_two":true,"max_points":null,"target_goals":null,"standings":{"win":2,"draw":0,"loss":1,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"goal_difference","surface":"parquet","notes":"Al meglio dei 3 set da 15 punti; scarto di 2."}',
 'Pallavolo 4 contro 4: formula scolastica al meglio dei tre set da 15 punti, con uno scarto di almeno 2 punti. Ogni squadra schiera 4 giocatori e la rosa comprende al massimo 8 giocatori. Vittoria 2 punti, sconfitta 1. A parita di punti decide la differenza set.'),

((SELECT id FROM sport_configs WHERE name = 'Pallavolo'), 'beach-volley-2v2', 'Beach volley 2 contro 2',
 'Pallavolo sulla sabbia con due giocatori per squadra.', 'team', 3,
 '{"players_on_field":2,"min_lineup":2,"max_roster":2,"match_duration":50,"periods":null,"period_minutes":null,"scoring_mode":"sets","score_label":"set","draw_allowed":false,"sets_to_win":2,"max_sets":3,"points_per_set":21,"tiebreak_points":15,"win_by_two":true,"max_points":null,"target_goals":null,"standings":{"win":2,"draw":0,"loss":1,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"goal_difference","surface":"sabbia","notes":"Al meglio dei 3 set; il terzo set si gioca a 15 punti."}',
 'Beach volley 2 contro 2: partita al meglio dei tre set. I primi due set si giocano a 21 punti, il terzo a 15; serve uno scarto di almeno 2 punti. Ogni squadra schiera 2 giocatori. Vittoria 2 punti, sconfitta 1. A parita di punti decide la differenza set.'),

((SELECT id FROM sport_configs WHERE name = 'Badminton'), 'badminton-singolare', 'Badminton singolare',
 'Singolo su campo regolamentare, al meglio dei tre set.', 'individual', 1,
 '{"players_on_field":1,"min_lineup":1,"max_roster":1,"match_duration":45,"periods":null,"period_minutes":null,"scoring_mode":"sets","score_label":"set","draw_allowed":false,"sets_to_win":2,"max_sets":3,"points_per_set":21,"tiebreak_points":21,"win_by_two":true,"max_points":30,"target_goals":null,"standings":{"win":1,"draw":0,"loss":0,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"wins","surface":"parquet","notes":"Al meglio dei 3 set da 21 punti; limite a 30."}',
 'Badminton singolare: partita al meglio dei tre set da 21 punti. Ogni set deve essere vinto con almeno 2 punti di scarto; sul 29-29 vince chi arriva per primo a 30. Un solo giocatore per parte. Vittoria 1 punto, sconfitta 0. A parita di punti decide il numero di vittorie.'),

((SELECT id FROM sport_configs WHERE name = 'Badminton'), 'badminton-doppio', 'Badminton doppio',
 'Due giocatori per squadra, al meglio dei tre set.', 'team', 2,
 '{"players_on_field":2,"min_lineup":2,"max_roster":2,"match_duration":45,"periods":null,"period_minutes":null,"scoring_mode":"sets","score_label":"set","draw_allowed":false,"sets_to_win":2,"max_sets":3,"points_per_set":21,"tiebreak_points":21,"win_by_two":true,"max_points":30,"target_goals":null,"standings":{"win":1,"draw":0,"loss":0,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"wins","surface":"parquet","notes":"Due giocatori per lato; al meglio dei 3 set da 21."}',
 'Badminton doppio: due giocatori per squadra, partita al meglio dei tre set da 21 punti con scarto di almeno 2 e limite a 30. Vittoria 1 punto, sconfitta 0. A parita di punti decide il numero di vittorie.'),

((SELECT id FROM sport_configs WHERE name = 'Badminton'), 'badminton-doppio-misto', 'Badminton doppio misto',
 'Una giocatrice e un giocatore per squadra.', 'team', 3,
 '{"players_on_field":2,"min_lineup":2,"max_roster":2,"match_duration":45,"periods":null,"period_minutes":null,"scoring_mode":"sets","score_label":"set","draw_allowed":false,"sets_to_win":2,"max_sets":3,"points_per_set":21,"tiebreak_points":21,"win_by_two":true,"max_points":30,"target_goals":null,"standings":{"win":1,"draw":0,"loss":0,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"wins","surface":"parquet","notes":"Una donna e un uomo per lato."}',
 'Badminton doppio misto: ogni squadra schiera una giocatrice e un giocatore. Partita al meglio dei tre set da 21 punti con scarto di almeno 2 e limite a 30. Vittoria 1 punto, sconfitta 0. A parita di punti decide il numero di vittorie.'),

((SELECT id FROM sport_configs WHERE name = 'Ping pong'), 'ping-pong-singolare', 'Ping pong singolare',
 'Singolo al tavolo, al meglio dei cinque game.', 'individual', 1,
 '{"players_on_field":1,"min_lineup":1,"max_roster":1,"match_duration":30,"periods":null,"period_minutes":null,"scoring_mode":"sets","score_label":"game","draw_allowed":false,"sets_to_win":3,"max_sets":5,"points_per_set":11,"tiebreak_points":11,"win_by_two":true,"max_points":null,"target_goals":null,"standings":{"win":1,"draw":0,"loss":0,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"wins","surface":"tavolo","notes":"Al meglio dei 5 game da 11 punti; scarto di 2."}',
 'Ping pong singolare: partita al meglio dei cinque game da 11 punti, con almeno 2 punti di scarto. Un solo giocatore per parte. Vittoria 1 punto, sconfitta 0. A parita di punti decide il numero di vittorie.'),

((SELECT id FROM sport_configs WHERE name = 'Ping pong'), 'ping-pong-doppio', 'Ping pong doppio',
 'Due giocatori per squadra, al meglio dei cinque game.', 'team', 2,
 '{"players_on_field":2,"min_lineup":2,"max_roster":2,"match_duration":30,"periods":null,"period_minutes":null,"scoring_mode":"sets","score_label":"game","draw_allowed":false,"sets_to_win":3,"max_sets":5,"points_per_set":11,"tiebreak_points":11,"win_by_two":true,"max_points":null,"target_goals":null,"standings":{"win":1,"draw":0,"loss":0,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"wins","surface":"tavolo","notes":"Due giocatori per lato; al meglio dei 5 game da 11."}',
 'Ping pong doppio: due giocatori per squadra, partita al meglio dei cinque game da 11 punti con scarto di almeno 2. Vittoria 1 punto, sconfitta 0. A parita di punti decide il numero di vittorie.'),

((SELECT id FROM sport_configs WHERE name = 'Ping pong'), 'ping-pong-doppio-misto', 'Ping pong doppio misto',
 'Una giocatrice e un giocatore per squadra.', 'team', 3,
 '{"players_on_field":2,"min_lineup":2,"max_roster":2,"match_duration":30,"periods":null,"period_minutes":null,"scoring_mode":"sets","score_label":"game","draw_allowed":false,"sets_to_win":3,"max_sets":5,"points_per_set":11,"tiebreak_points":11,"win_by_two":true,"max_points":null,"target_goals":null,"standings":{"win":1,"draw":0,"loss":0,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"wins","surface":"tavolo","notes":"Una donna e un uomo per lato."}',
 'Ping pong doppio misto: ogni squadra schiera una giocatrice e un giocatore. Partita al meglio dei cinque game da 11 punti con scarto di almeno 2. Vittoria 1 punto, sconfitta 0. A parita di punti decide il numero di vittorie.'),

((SELECT id FROM sport_configs WHERE name = 'Biliardino'), 'biliardino-singolare', 'Biliardino singolare',
 'Un giocatore per parte, partita a tempo o a 5 gol.', 'individual', 1,
 '{"players_on_field":1,"min_lineup":1,"max_roster":1,"match_duration":15,"periods":1,"period_minutes":15,"scoring_mode":"goals","score_label":"gol","draw_allowed":false,"sets_to_win":null,"max_sets":null,"points_per_set":null,"tiebreak_points":null,"win_by_two":null,"max_points":null,"target_goals":5,"standings":{"win":2,"draw":0,"loss":1,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"goal_difference","surface":"tavolo","notes":"Primo a 5 gol oppure miglior punteggio allo scadere."}',
 'Biliardino singolare: un giocatore per parte. Vince chi arriva per primo a 5 gol oppure chi e in vantaggio allo scadere dei 15 minuti. Vittoria 2 punti, sconfitta 1. A parita di punti decide la differenza gol.'),

((SELECT id FROM sport_configs WHERE name = 'Biliardino'), 'biliardino-doppio', 'Biliardino doppio',
 'Due giocatori per parte, partita a tempo o a 5 gol.', 'team', 2,
 '{"players_on_field":2,"min_lineup":2,"max_roster":2,"match_duration":15,"periods":1,"period_minutes":15,"scoring_mode":"goals","score_label":"gol","draw_allowed":false,"sets_to_win":null,"max_sets":null,"points_per_set":null,"tiebreak_points":null,"win_by_two":null,"max_points":null,"target_goals":5,"standings":{"win":2,"draw":0,"loss":1,"win_tiebreak":null,"loss_tiebreak":null},"default_tie_breaker":"goal_difference","surface":"tavolo","notes":"Due contro due; primo a 5 gol oppure miglior punteggio allo scadere."}',
 'Biliardino doppio: due giocatori per parte. Vince la squadra che arriva per prima a 5 gol oppure quella in vantaggio allo scadere dei 15 minuti. Vittoria 2 punti, sconfitta 1. A parita di punti decide la differenza gol.');

ALTER TABLE tournaments ADD COLUMN variant_id INTEGER REFERENCES sport_variants(id);
ALTER TABLE tournaments ADD COLUMN variant TEXT;
ALTER TABLE tournaments ADD COLUMN rules_snapshot TEXT NOT NULL DEFAULT '{}';
ALTER TABLE tournaments ADD COLUMN regulation_snapshot TEXT NOT NULL DEFAULT '';

-- The old standalone Calcio a 5 sport becomes a Calcio variant.
UPDATE tournaments
SET sport = 'Calcio',
    sport_id = (SELECT id FROM sport_configs WHERE name = 'Calcio'),
    variant = 'calcio-a-5',
    variant_id = (SELECT id FROM sport_variants WHERE slug = 'calcio-a-5')
WHERE sport = 'Calcio a 5';

-- Databases created before 003 may have a sport name but no foreign key.
UPDATE tournaments
SET sport_id = (SELECT id FROM sport_configs WHERE name = tournaments.sport)
WHERE sport_id IS NULL
  AND sport IN ('Calcio','Basket','Pallavolo','Badminton','Ping pong','Biliardino');

-- Sports outside the new catalog stay readable as historical records.
UPDATE tournaments
SET sport_id = NULL
WHERE sport_id IS NOT NULL
  AND sport_id NOT IN (SELECT id FROM sport_configs
                       WHERE name IN ('Calcio','Basket','Pallavolo','Badminton','Ping pong','Biliardino'));

-- Existing tournaments adopt the default variant for their participant kind.
UPDATE tournaments
SET variant_id = (
    SELECT v.id FROM sport_variants v
    WHERE v.sport_id = tournaments.sport_id
      AND v.participant_kind = tournaments.participant_kind
    ORDER BY v.sort_order, v.id LIMIT 1
)
WHERE sport_id IS NOT NULL AND variant_id IS NULL;

UPDATE tournaments
SET variant = (SELECT slug FROM sport_variants WHERE id = tournaments.variant_id)
WHERE variant_id IS NOT NULL;

UPDATE tournaments
SET rules_snapshot = COALESCE((SELECT rules FROM sport_variants WHERE id = tournaments.variant_id), '{}'),
    regulation_snapshot = COALESCE((SELECT regulation FROM sport_variants WHERE id = tournaments.variant_id), '')
WHERE variant_id IS NOT NULL;

DELETE FROM sport_configs
WHERE name NOT IN ('Calcio','Basket','Pallavolo','Badminton','Ping pong','Biliardino');

CREATE TABLE team_players (
    id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 60),
    shirt_number INTEGER CHECK(shirt_number BETWEEN 0 AND 99),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE(team_id, name)
);

CREATE INDEX team_players_team ON team_players(team_id);

CREATE TABLE match_sets (
    id INTEGER PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    set_no INTEGER NOT NULL CHECK(set_no BETWEEN 1 AND 7),
    home_points INTEGER NOT NULL CHECK(home_points BETWEEN 0 AND 999),
    away_points INTEGER NOT NULL CHECK(away_points BETWEEN 0 AND 999),
    UNIQUE(match_id, set_no)
);

CREATE INDEX match_sets_match ON match_sets(match_id);

PRAGMA user_version=6;
