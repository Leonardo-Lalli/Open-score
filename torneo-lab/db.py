"""SQLite unit of work. All mutations acquire the write lock before reading."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE = Path(__file__).resolve().parent


def initialize(path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        version = db.execute('PRAGMA user_version').fetchone()[0]
        if version > 2:
            raise RuntimeError('Database più recente del programma: aggiornare il codice')
        if version == 0:
            if db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
                raise RuntimeError('Database legacy: conservarlo e usare un nuovo TORNEO_DB_PATH. Vedi docs/DATABASE.md')
            db.executescript('BEGIN IMMEDIATE;\n' + (BASE/'migrations/001_initial.sql').read_text(encoding='utf-8') + '\nCOMMIT;')
        if version < 2:
            db.executescript('BEGIN IMMEDIATE;\n' + (BASE/'migrations/002_stable_match_ids.sql').read_text(encoding='utf-8') + '\nCOMMIT;')
        if db.execute('PRAGMA foreign_key_check').fetchone():
            raise RuntimeError('Integrità del database non valida: ripristinare un backup')
    return version == 0


@contextmanager
def database(path: Path, write: bool = False):
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        db.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
