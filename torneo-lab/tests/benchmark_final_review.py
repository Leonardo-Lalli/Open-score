"""Local synthetic benchmark, not a load test. Run from torneo-lab with --out FILE."""

import argparse
import json
import os
import platform
import sqlite3
import statistics
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))


def run(output, runs=9):
    with tempfile.TemporaryDirectory(prefix="open-score-benchmark-") as folder:
        path = Path(folder) / "synthetic.sqlite3"
        os.environ["TORNEO_DB_PATH"] = str(Path(folder) / "import.sqlite3")
        os.environ["TORNEO_SECRET"] = "synthetic-benchmark-secret-only"
        from fastapi.testclient import TestClient

        import platform_auth as auth
        import platform_services as svc
        import v1_domain as domain
        import v1_schemas as schema
        from app import create_app
        from db import database
        from test_platform import PASSWORD, Actor

        app = create_app(path, mode="demo")
        with database(path, True) as db:
            user = auth.create_teacher(db, "teacher-a@example.test", PASSWORD, "Docente benchmark", "Benchmark sintetico")
            user = dict(db.execute("SELECT * FROM users WHERE id=?", (user,)).fetchone())
            field = db.execute("INSERT INTO fields(owner_id,organization_id,name,variants_json,availability_json) VALUES (?,?,?,'[\"football-5\"]','[]')", (user["id"], user["organization_id"], "Campo sintetico")).lastrowid
            for index in range(60):
                tid = domain.create_tournament(db, user, schema.TournamentCreate(
                    name=f"Coppa {index}", team_names=[f"Squadra {i}" for i in range(6)]))["id"]
                svc.generate(db, tid)
            games = [r[0] for r in db.execute("SELECT id FROM matches ORDER BY id")]
            start = datetime(2026, 11, 1, tzinfo=timezone.utc)
            db.executemany("UPDATE matches SET scheduled_at=?,duration=20,field_id=?,location='Campo sintetico' WHERE id=?", [((start + timedelta(hours=i)).isoformat(), field, mid) for i, mid in enumerate(games)])
        with TestClient(app) as client:
            Actor(client, "teacher-a@example.test", "Benchmark", False)
            result = {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
                      "dataset": {"tournaments": 60, "teams_per_tournament": 6, "scheduled_matches": len(games)},
                      "runs": runs, "warmups": 2, "routes": {}}
            original_connect = sqlite3.connect
            for route in ("/api/v1/tournaments?limit=50", "/api/calendar"):
                for _ in range(2):
                    response = client.get(route)
                    response.raise_for_status()
                samples = []
                for _ in range(runs):
                    start_time = time.perf_counter()
                    response = client.get(route)
                    response.raise_for_status()
                    samples.append((time.perf_counter() - start_time) * 1000)
                statements = []

                def traced(*args, **kwargs):
                    connection = original_connect(*args, **kwargs)
                    connection.set_trace_callback(statements.append)
                    return connection

                with patch("sqlite3.connect", traced):
                    response = client.get(route)
                    response.raise_for_status()
                ordered = sorted(samples)
                result["routes"][route] = {
                    "median_ms": round(statistics.median(samples), 3),
                    "p95_ms": round(ordered[min(len(ordered)-1, int(len(ordered)*0.95))], 3),
                    "selects": sum(s.lstrip().upper().startswith("SELECT") for s in statements),
                    "response_bytes": len(response.content),
                }
                # Local contract evidence, no credentials or session material.
                output.with_name(output.stem + ("-list.json" if "/v1/" in route else "-calendar.json")).write_text(response.text, encoding="utf-8")
            output.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Use a new output path")
    run(args.out)
