import sqlite3

from fastapi.testclient import TestClient

from app import create_app
from db import BASE, initialize


def read_migration(name: str) -> str:
    return (BASE / 'migrations' / name).read_text(encoding='utf-8')


def test_fresh_database_is_version_four_with_canonical_catalog(tmp_path):
    path = tmp_path / 'fresh.sqlite3'
    assert initialize(path) is True

    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 4
        assert db.execute('PRAGMA journal_mode').fetchone()[0].lower() == 'wal'
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
        columns = {row[1] for row in db.execute('PRAGMA table_info(tournaments)')}
        assert {'sport_id', 'tournament_type', 'scoring_system', 'archived_at', 'updated_at'} <= columns
        names = [row[0] for row in db.execute('SELECT name FROM sport_configs ORDER BY id')]
        assert names == ['Calcio', 'Calcio a 5', 'Basket', 'Pallamano', 'Badminton', 'Tennis', 'Pallavolo']


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
        assert db.execute('PRAGMA user_version').fetchone()[0] == 4
        sport, sport_id = db.execute('SELECT sport,sport_id FROM tournaments WHERE id=1').fetchone()
        assert sport == 'Pallavolo'
        assert sport_id == 7
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
        assert db.execute('PRAGMA user_version').fetchone()[0] == 4
        archived_at, updated_at, created_at = db.execute(
            'SELECT archived_at,updated_at,created_at FROM tournaments WHERE id=1'
        ).fetchone()
        assert archived_at is None
        assert updated_at == created_at


def test_fresh_install_seeds_examples_with_sport_links(tmp_path):
    path = tmp_path / 'seed.sqlite3'
    with TestClient(create_app(path, seed=True)) as client:
        tournaments = client.get('/api/tournaments').json()
        assert len(tournaments) == 4
        assert all(tournament['sport_id'] for tournament in tournaments)


def test_create_tournament_resolves_sport_id_and_rejects_mismatch(tmp_path):
    path = tmp_path / 'create.sqlite3'
    with TestClient(create_app(path, seed=False)) as client:
        response = client.post('/api/tournaments', json={
            'name': 'Coppa di prova',
            'sport': 'Pallavolo',
            'team_names': ['Alfa', 'Beta'],
        })
        assert response.status_code == 201, response.text
        detail = client.get(f"/api/tournaments/{response.json()['id']}").json()
        assert detail['tournament']['sport_id'] == 7

        mismatch = client.post('/api/tournaments', json={
            'name': 'Coppa sbagliata',
            'sport': 'Calcio',
            'sport_id': 7,
        })
        assert mismatch.status_code == 422
