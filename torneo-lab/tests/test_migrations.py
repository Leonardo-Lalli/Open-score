import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import create_app
from db import BASE, LATEST_SCHEMA, initialize


def read_migration(name: str) -> str:
    return (BASE / 'migrations' / name).read_text(encoding='utf-8')


def test_fresh_database_is_version_seven_with_canonical_catalog(tmp_path):
    path = tmp_path / 'fresh.sqlite3'
    assert initialize(path) is True

    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == LATEST_SCHEMA
        assert db.execute('PRAGMA journal_mode').fetchone()[0].lower() == 'wal'
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
        columns = {row[1] for row in db.execute('PRAGMA table_info(tournaments)')}
        assert {'sport_id', 'variant_id', 'variant', 'rules_snapshot',
                'regulation_snapshot', 'tournament_type', 'scoring_system',
                'archived_at', 'updated_at', 'tie_breaker', 'teacher_id'} <= columns
        names = [row[0] for row in db.execute(
            'SELECT name FROM sport_configs ORDER BY sort_order, id')]
        assert names == ['Calcio', 'Basket', 'Pallavolo', 'Badminton',
                         'Ping pong', 'Biliardino']
        assert db.execute('SELECT count(*) FROM sport_variants').fetchone()[0] == 16
        assert db.execute("SELECT count(*) FROM sport_variants "
                          "WHERE slug='badminton-singolare'").fetchone()[0] == 1
        tables = {row[0] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        assert {'sport_variants', 'team_players', 'match_sets', 'teachers'} <= tables


def test_version_two_database_migrates_and_maps_legacy_sport(tmp_path):
    path = tmp_path / 'v2.sqlite3'
    with sqlite3.connect(path) as db:
        db.executescript(read_migration('001_initial.sql'))
        db.executescript(read_migration('002_stable_match_ids.sql'))
        db.execute(
            "INSERT INTO tournaments(id,name,sport,format,public_token) "
            "VALUES (1,'Coppa esistente','Volley','knockout','old-token')"
        )

    assert initialize(path) is False

    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == LATEST_SCHEMA
        sport, sport_id, variant = db.execute(
            'SELECT sport,sport_id,variant FROM tournaments WHERE id=1').fetchone()
        assert sport == 'Pallavolo'
        assert sport_id == 7
        assert variant == 'pallavolo-6v6'
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []


def test_version_three_database_adds_archive_columns_and_backfills_update_time(tmp_path):
    path = tmp_path / 'v3.sqlite3'
    with sqlite3.connect(path) as db:
        for name in ('001_initial.sql', '002_stable_match_ids.sql', '003_sports_expansion.sql'):
            db.executescript(read_migration(name))
        db.execute(
            "INSERT INTO tournaments(id,name,sport,format,public_token) "
            "VALUES (1,'Coppa attiva','Calcio','round_robin','v3-token')"
        )

    assert initialize(path) is False

    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == LATEST_SCHEMA
        archived_at, updated_at, created_at, tie_breaker = db.execute(
            'SELECT archived_at,updated_at,created_at,tie_breaker FROM tournaments WHERE id=1'
        ).fetchone()
        assert archived_at is None
        assert updated_at == created_at
        assert tie_breaker == 'goal_difference'
        assert db.execute('SELECT variant FROM tournaments WHERE id=1').fetchone()[0] == 'calcio-a-11'


def test_version_four_database_adds_tie_breaker_with_default(tmp_path):
    path = tmp_path / 'v4.sqlite3'
    with sqlite3.connect(path) as db:
        for name in ('001_initial.sql', '002_stable_match_ids.sql',
                     '003_sports_expansion.sql', '004_archive_and_updates.sql'):
            db.executescript(read_migration(name))
        db.execute(
            "INSERT INTO tournaments(id,name,sport,format,public_token) "
            "VALUES (1,'Coppa v4','Calcio','round_robin','v4-token')"
        )

    assert initialize(path) is False

    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == LATEST_SCHEMA
        assert db.execute('SELECT tie_breaker FROM tournaments WHERE id=1').fetchone()[0] == 'goal_difference'
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("UPDATE tournaments SET tie_breaker='coin_toss' WHERE id=1")


def test_version_five_remaps_calcio_a_5_and_preserves_removed_sports(tmp_path):
    path = tmp_path / 'v5.sqlite3'
    with sqlite3.connect(path) as db:
        for name in ('001_initial.sql', '002_stable_match_ids.sql',
                     '003_sports_expansion.sql', '004_archive_and_updates.sql',
                     '005_tie_breaker.sql'):
            db.executescript(read_migration(name))
        db.execute(
            "INSERT INTO tournaments(id,name,sport,sport_id,participant_kind,format,public_token) "
            "VALUES (1,'Coppa a 5','Calcio a 5',2,'team','round_robin','five-token')"
        )
        db.execute(
            "INSERT INTO tournaments(id,name,sport,sport_id,format,public_token) "
            "VALUES (2,'Vecchia pallamano','Pallamano',4,'knockout','hand-token')"
        )

    assert initialize(path) is False

    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == LATEST_SCHEMA
        sport, sport_id, variant, snapshot = db.execute(
            "SELECT sport,sport_id,variant,rules_snapshot FROM tournaments WHERE id=1"
        ).fetchone()
        assert (sport, sport_id, variant) == ('Calcio', 1, 'calcio-a-5')
        assert '"players_on_field":5' in snapshot
        legacy_sport, legacy_id, legacy_variant = db.execute(
            "SELECT sport,sport_id,variant FROM tournaments WHERE id=2"
        ).fetchone()
        assert legacy_sport == 'Pallamano'
        assert legacy_id is None
        assert legacy_variant is None
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []


def test_fresh_install_starts_without_tournaments(tmp_path):
    path = tmp_path / 'empty.sqlite3'
    with TestClient(create_app(path)) as client:
        assert client.get('/api/tournaments').json() == []


def test_create_tournament_resolves_sport_id_and_rejects_mismatch(tmp_path):
    path = tmp_path / 'create.sqlite3'
    with TestClient(create_app(path, admin_email='prof@test.local',
                               admin_password='password-lunga')) as client:
        assert client.post('/api/auth/login', json={
            'email': 'prof@test.local', 'password': 'password-lunga'}).status_code == 200
        response = client.post('/api/tournaments', json={
            'name': 'Coppa di prova',
            'sport': 'Pallavolo',
            'variant': 'pallavolo-6v6',
            'team_names': ['Alfa', 'Beta'],
        })
        assert response.status_code == 201, response.text
        detail = client.get(f"/api/tournaments/{response.json()['id']}").json()
        assert detail['tournament']['sport_id'] == 7
        assert detail['tournament']['variant'] == 'pallavolo-6v6'

        mismatch = client.post('/api/tournaments', json={
            'name': 'Coppa sbagliata',
            'sport': 'Calcio',
            'sport_id': 7,
        })
        assert mismatch.status_code == 422

        wrong_variant = client.post('/api/tournaments', json={
            'name': 'Coppa sbagliata',
            'sport': 'Calcio',
            'variant': 'pallavolo-6v6',
        })
        assert wrong_variant.status_code == 422
