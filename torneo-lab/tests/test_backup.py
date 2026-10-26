import sqlite3

from fastapi.testclient import TestClient

from app import create_app
from backup import backup_database
from db import SCHEMA_VERSION


def populated_database(tmp_path):
    path = tmp_path / 'live.sqlite3'
    app = create_app(path, session_secret='backup-secret',
                     admin_email='prof@test.local', admin_password='password-lunga')
    with TestClient(app) as client:
        assert client.post('/api/auth/login', json={
            'email': 'prof@test.local', 'password': 'password-lunga'}).status_code == 200
        response = client.post('/api/tournaments', json={
            'name': 'Coppa di prova', 'sport': 'Calcio',
            'team_names': ['Alfa', 'Beta'],
        })
        assert response.status_code == 201, response.text
    return path


def test_online_backup_is_readable_and_complete(tmp_path):
    source = populated_database(tmp_path)
    target = backup_database(source, tmp_path / 'backups')

    assert target.exists()
    assert target.name.startswith('open_score-')
    with sqlite3.connect(target) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == SCHEMA_VERSION
        assert db.execute('SELECT count(*) FROM tournaments').fetchone()[0] == 1
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'


def test_retention_keeps_the_newest_snapshots(tmp_path):
    source = populated_database(tmp_path)
    out = tmp_path / 'rotating'
    made = [backup_database(source, out) for _ in range(4)]
    assert len(list(out.glob('open_score-*.sqlite3'))) == 4

    backup_database(source, out, keep=2)
    remaining = sorted(out.glob('open_score-*.sqlite3'))
    assert len(remaining) == 2
    assert made[0] not in remaining
    assert made[1] not in remaining
