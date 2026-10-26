"""Conservative integration of Team A schema 4 and Team B schema 7."""

import re
import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
SCHEMA_VERSION = LATEST_SCHEMA = 8
MIGRATIONS = (
    (2, "002_stable_match_ids.sql"),
    (3, "003_sports_expansion.sql"),
    (4, "004_archive_and_updates.sql"),
    (5, "005_tie_breaker.sql"),
    (6, "006_sport_variants.sql"),
    (7, "007_teachers.sql"),
)


def statements(source):
    pending = ""
    for line in source.splitlines(keepends=True):
        pending += line
        if sqlite3.complete_statement(pending):
            yield pending.strip()
            pending = ""
    if pending.strip() and any(
        not line.lstrip().startswith("--") for line in pending.splitlines()
    ):
        raise RuntimeError("Migrazione SQL incompleta")


def run_script(db, name):
    for statement in statements(
        (BASE / "migrations" / name).read_text(encoding="utf-8")
    ):
        db.execute(statement)


def columns(db, table):
    return {row[1]: row[2] for row in db.execute(f"PRAGMA table_info({table})")}


def add_platform_schema(db):
    had_order = "display_order" in columns(db, "teams")
    source = (BASE / "migrations/003_core_platform.sql").read_text(encoding="utf-8")
    source = source.replace(
        "ADD COLUMN variant_id TEXT", "ADD COLUMN platform_variant_id TEXT"
    )
    for statement in statements(source):
        # Comments don't affect execution, but strip them for schema inspection.
        plain = "\n".join(
            line
            for line in statement.splitlines()
            if not line.lstrip().startswith("--")
        ).strip()
        if plain.startswith("PRAGMA user_version"):
            continue
        if had_order and plain.startswith("UPDATE teams SET display_order"):
            continue
        altered = re.match(r"ALTER TABLE (\w+) ADD COLUMN (\w+)", plain)
        if altered and altered[2] in columns(db, altered[1]):
            continue
        plain = re.sub(r"^CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ", plain)
        plain = re.sub(
            r"^CREATE (UNIQUE )?INDEX ",
            lambda m: "CREATE " + (m[1] or "") + "INDEX IF NOT EXISTS ",
            plain,
        )
        db.execute(plain)
    db.execute(
        "CREATE TABLE IF NOT EXISTS team_penalties (team_id INTEGER PRIMARY KEY REFERENCES teams(id) ON DELETE CASCADE, points INTEGER NOT NULL CHECK(points BETWEEN 0 AND 999), reason TEXT NOT NULL)"
    )
    run_script(db, "008_team_integration.sql")


def initialize(path: Path) -> bool:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=10)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        tables = {
            r[0]
            for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if version > LATEST_SCHEMA:
            raise RuntimeError(
                "Database più recente del programma: aggiornare il codice"
            )
        if version == 0 and tables:
            raise RuntimeError(
                "Database legacy: conservarlo e usare un nuovo TORNEO_DB_PATH. Vedi docs/DATABASE.md"
            )
        team_a = "users" in tables and "sport_configs" not in tables
        if version != LATEST_SCHEMA:
            if version:
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                with closing(
                    sqlite3.connect(
                        path.with_name(
                            path.stem + f".pre-v{LATEST_SCHEMA}-{stamp}.sqlite3"
                        )
                    )
                ) as backup:
                    db.backup(backup)
            # All migration steps commit together, including lineage translation.
            db.execute("PRAGMA foreign_keys=OFF")
            db.execute("BEGIN IMMEDIATE")
            try:
                if not version:
                    run_script(db, "001_initial.sql")
                if team_a:
                    if columns(db, "tournaments").get("variant_id") == "TEXT":
                        db.execute(
                            "ALTER TABLE tournaments RENAME COLUMN variant_id TO platform_variant_id"
                        )
                    start = 2
                else:
                    start = version
                for target, name in MIGRATIONS:
                    if start < target:
                        run_script(db, name)
                add_platform_schema(db)
                if not team_a:
                    db.execute(
                        "UPDATE tournaments SET published=1 WHERE owner_id IS NULL"
                    )
                from identity_bridge import migrate_identities

                migrate_identities(db)
                if db.execute("PRAGMA foreign_key_check").fetchone():
                    raise RuntimeError(
                        "Integrità del database non valida: ripristinare un backup"
                    )
                db.execute(f"PRAGMA user_version={LATEST_SCHEMA}")
                db.commit()
            except Exception:
                db.rollback()
                raise
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        if db.execute("PRAGMA foreign_key_check").fetchone():
            raise RuntimeError(
                "Integrità del database non valida: ripristinare un backup"
            )
    return version == 0


@contextmanager
def database(path: Path, write: bool = False):
    db = sqlite3.connect(path, timeout=10, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=10000")
    db.execute("PRAGMA foreign_keys=ON")
    try:
        db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
