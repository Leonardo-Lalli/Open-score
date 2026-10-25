import sqlite3

from fastapi.testclient import TestClient

from app import create_app
from backup import backup_database


def seeded_database(tmp_path):
    path = tmp_path / 'live.sqlite3'
    with TestClient(create_app(path, seed=True, session_secret='backup-secret')):
        pass
    return path


def test_online_backup_is_readable_and_complete(tmp_path):
    source = seeded_database(tmp_path)
    target = backup_database(source, tmp_path / 'backups')

    assert target.exists()
    assert target.name.startswith('open_score-')
    with sqlite3.connect(target) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 6
        assert db.execute('SELECT count(*) FROM tournaments').fetchone()[0] == 4
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'


def test_retention_keeps_the_newest_snapshots(tmp_path):
    source = seeded_database(tmp_path)
    out = tmp_path / 'rotating'
    made = [backup_database(source, out) for _ in range(4)]
    assert len(list(out.glob('open_score-*.sqlite3'))) == 4

    backup_database(source, out, keep=2)
    remaining = sorted(out.glob('open_score-*.sqlite3'))
    assert len(remaining) == 2
    assert made[0] not in remaining
    assert made[1] not in remaining
