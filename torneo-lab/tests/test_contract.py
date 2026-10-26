"""Keep the published machine-readable contract aligned with the running API."""
import json
import os
from pathlib import Path
import subprocess
import sys


SNAPSHOT = Path(__file__).resolve().parents[2] / 'docs/contracts/openapi.yaml'


def test_openapi_matches_published_contract(client):
    response = client.get('/openapi.json')
    assert response.status_code == 200
    # The .yaml artifact uses JSON syntax, valid in YAML 1.2 as well.
    assert response.json() == json.loads(SNAPSHOT.read_text(encoding='utf-8'))


def test_export_check_does_not_open_configured_database(tmp_path):
    protected = tmp_path / 'user-database.sqlite3'
    sentinel = b'User data: not a database for the exporter to initialize'
    protected.write_bytes(sentinel)
    before = SNAPSHOT.read_bytes()
    app_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(app_root / 'scripts/export_openapi.py'), '--check'],
        cwd=app_root,
        env={**os.environ, 'TORNEO_DB_PATH': str(protected)},
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert protected.read_bytes() == sentinel
    assert SNAPSHOT.read_bytes() == before
