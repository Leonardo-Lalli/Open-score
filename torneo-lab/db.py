"""SQLite unit of work. All mutations acquire the write lock before reading."""
import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
SCHEMA_VERSION = 4


def initialize(path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as db:
        version = db.execute('PRAGMA user_version').fetchone()[0]
        if version > SCHEMA_VERSION:
            raise RuntimeError('Database più recente del programma: aggiornare il codice')
        if 0 < version < SCHEMA_VERSION:
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            backup = path.with_name(path.stem + f'.pre-v{SCHEMA_VERSION}-{stamp}.sqlite3')
            with closing(sqlite3.connect(backup)) as target:
                db.backup(target)
        if version == 0:
            if db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
                raise RuntimeError('Database legacy: conservarlo e usare un nuovo TORNEO_DB_PATH. Vedi docs/DATABASE.md')
            db.executescript('BEGIN IMMEDIATE;\n' + (BASE/'migrations/001_initial.sql').read_text(encoding='utf-8') + '\nCOMMIT;')
        if version < 2:
            db.executescript('BEGIN IMMEDIATE;\n' + (BASE/'migrations/002_stable_match_ids.sql').read_text(encoding='utf-8') + '\nCOMMIT;')
        db.execute('PRAGMA foreign_keys=ON')
        if version < 3:
            db.executescript('BEGIN IMMEDIATE;\n' + (BASE/'migrations/003_core_platform.sql').read_text(encoding='utf-8') + '\nCOMMIT;')
        if version < 4:
            db.executescript('BEGIN IMMEDIATE;\n' + (BASE/'migrations/004_team_penalties.sql').read_text(encoding='utf-8') + '\nCOMMIT;')
        if db.execute('PRAGMA foreign_key_check').fetchone():
            raise RuntimeError('Integrità del database non valida: ripristinare un backup')
    return version == 0


@contextmanager
def database(path: Path, write: bool = False):
    # A FastAPI yield dependency may enter/exit on different worker threads.
    # Each request still owns one connection and uses it sequentially.
    db = sqlite3.connect(path, timeout=10, check_same_thread=False)
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
