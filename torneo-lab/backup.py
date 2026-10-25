"""Consistent online backups of the SQLite database.

``VACUUM INTO`` asks SQLite for a transactionally consistent snapshot, so it is
safe to run while the server is writing. Copying the main file alone with WAL
enabled can lose recent commits; this script avoids that mistake.

Usage (from ``torneo-lab``)::

    python backup.py
    python backup.py --db data/open_score.sqlite3 --out backup --keep 14
"""

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DEFAULT_DB = BASE / 'data' / 'open_score.sqlite3'
DEFAULT_OUT = BASE / 'backup'


def backup_database(db_path: str | Path, out_dir: str | Path,
                    keep: int | None = None) -> Path:
    """Write a timestamped snapshot and optionally prune older ones."""
    source = Path(db_path)
    if not source.is_file():
        raise FileNotFoundError(f'Database non trovato: {source}')
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    target = destination / f'open_score-{stamp}.sqlite3'
    suffix = 2
    while target.exists():
        target = destination / f'open_score-{stamp}-{suffix}.sqlite3'
        suffix += 1

    with sqlite3.connect(source) as db:
        db.execute('PRAGMA busy_timeout=10000')
        db.execute('VACUUM INTO ?', (str(target),))

    if keep and keep > 0:
        snapshots = sorted(destination.glob('open_score-*.sqlite3'),
                           key=lambda item: (item.stat().st_mtime_ns, item.name),
                           reverse=True)
        for old in snapshots[keep:]:
            old.unlink(missing_ok=True)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Backup consistente del database Open Score')
    parser.add_argument('--db', default=str(DEFAULT_DB), help='database di partenza')
    parser.add_argument('--out', default=str(DEFAULT_OUT), help='cartella di destinazione')
    parser.add_argument('--keep', type=int, default=14,
                        help='quanti backup conservare (0 = tutti)')
    args = parser.parse_args(argv)
    target = backup_database(args.db, args.out, args.keep)
    print(target)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
