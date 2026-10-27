"""Regressions found by checking the real frontend/backend boundaries."""

import json
import shutil
import sqlite3
import subprocess
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

import pytest

import platform_auth as auth
from db import BASE as DB_BASE
from db import database, initialize
from test_platform import assign, detail, invite, ok, tournament
from test_platform import lab as platform_lab
from test_team_integration import request

lab = platform_lab
BASE = Path(__file__).resolve().parents[1]


def test_calendar_filter_vocabulary_matches_the_frontend(lab):
    tid = tournament(lab.teacher, n=4)
    base = f"/tournaments/{tid}"
    games = detail(lab.teacher, tid)["matches"]
    for index, game in enumerate(games[:2]):
        request(
            lab.teacher,
            "PATCH",
            base + f"/matches/{game['id']}/schedule",
            {
                "version": game["version"],
                "scheduled_at": (
                    auth.now() + timedelta(days=1, minutes=index * 60)
                ).isoformat(),
                "location": "Campo A",
                "duration": 20,
            },
        )
    game = detail(lab.teacher, tid)["matches"][0]
    request(
        lab.teacher,
        "PATCH",
        base + f"/matches/{game['id']}",
        {"version": game["version"], "home_score": 0, "away_score": 0},
    )
    played = request(lab.teacher, "GET", f"/calendar?tournament={tid}&status=played")
    assert [e["match_id"] for e in played["events"]] == [game["id"]]
    future = request(lab.teacher, "GET", f"/calendar?tournament={tid}&status=to-play")
    assert [e["match_id"] for e in future["events"]] == [games[1]["id"]]
    pending = request(
        lab.teacher, "GET", f"/calendar?tournament={tid}&status=unscheduled"
    )
    assert len(pending["events"]) == len(games) - 2
    assert any(t["id"] == tid for t in played["tournaments"])


@pytest.mark.parametrize("operation", ["proposal", "invite", "direct_enrollment"])
def test_archived_tournaments_reject_student_mutations_without_side_effects(
    lab, operation
):
    tid = tournament(lab.teacher, n=2)
    assign(lab, tid)
    game = detail(lab.teacher, tid)["matches"][0]
    link = invite(lab.teacher, tid, require_approval=False)
    state = detail(lab.teacher, tid)
    ok(
        lab.teacher.patch(
            f"/tournaments/{tid}/publication",
            {"version": state["tournament"]["version"], "published": True},
        )
    )
    request(lab.teacher, "POST", f"/tournaments/{tid}/archive")
    with database(lab.path) as db:
        before = {
            table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("students", "result_proposals", "enrollments")
        }
    if operation == "proposal":
        response = lab.student.client.post(
            f"/api/tournaments/{tid}/matches/{game['id']}/proposals",
            json={"version": game["version"], "home_score": 2, "away_score": 1},
        )
    elif operation == "invite":
        response = lab.second.client.post(f"/api/invites/{link['token']}/join")
    else:
        response = lab.second.post(f"/tournaments/{tid}/enrollments", {})
    assert response.status_code == 409, response.text
    with database(lab.path) as db:
        assert before == {
            table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in before
        }
        assert (
            db.execute("SELECT used FROM invites WHERE id=?", (link["id"],)).fetchone()[
                0
            ]
            == 0
        )


def test_v1_invitation_url_opens_the_actual_student_page(lab):
    tid = tournament(lab.teacher, n=2)
    link = invite(lab.teacher, tid)
    parts = urlsplit(link["url"])
    assert parts.fragment == "/join/" + link["token"]
    assert lab.student.client.get(parts.path).status_code == 200


def test_field_variant_identity_works_across_the_two_apis(lab):
    field = ok(
        lab.teacher.post(
            "/fields",
            {"name": "Campo solo calcio a 5", "sport_variant_ids": ["football-5"]},
        ),
        201,
    )
    row = request(lab.teacher, "GET", "/fields")["fields"][0]
    assert row["sports"] == ["Calcio"]
    tid = request(
        lab.teacher,
        "POST",
        "/tournaments",
        {
            "name": "Coppa catalogo",
            "sport": "Calcio",
            "variant": "calcio-a-5",
            "format": "round_robin",
            "team_names": ["Rossi", "Blu"],
        },
        201,
    )["id"]
    request(lab.teacher, "POST", f"/tournaments/{tid}/generate")
    game = request(lab.teacher, "GET", f"/tournaments/{tid}")["matches"][0]
    request(
        lab.teacher,
        "PATCH",
        f"/tournaments/{tid}/matches/{game['id']}/schedule",
        {
            "version": game["version"],
            "scheduled_at": (auth.now() + timedelta(days=1)).isoformat(),
            "field_id": field["id"],
            "location": field["name"],
        },
    )
    edited = request(
        lab.teacher,
        "PATCH",
        f"/fields/{field['id']}",
        {
            "version": field["version"],
            "name": field["name"],
            "sports": ["Calcio"],
            "description": "Solo descrizione",
        },
    )
    assert edited["sport_variant_ids"] == ["football-5"]


def test_frontend_adapters_consume_real_calendar_and_field_payloads(lab):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js non disponibile")
    tid = tournament(lab.teacher, n=2)
    game = detail(lab.teacher, tid)["matches"][0]
    request(
        lab.teacher,
        "PATCH",
        f"/tournaments/{tid}/matches/{game['id']}",
        {"version": game["version"], "home_score": 0, "away_score": 0},
    )
    start = auth.now() + timedelta(days=1)
    field = ok(
        lab.teacher.post(
            "/fields",
            {
                "name": "Campo limitato",
                "sport_variant_ids": ["football-5"],
                "availability": [
                    {
                        "starts_at": start.isoformat(),
                        "ends_at": (start + timedelta(hours=2)).isoformat(),
                    }
                ],
            },
        ),
        201,
    )
    payload = {
        "calendar": request(lab.teacher, "GET", "/calendar"),
        "field": request(lab.teacher, "GET", "/fields")["fields"][0],
    }
    result = subprocess.run(
        [node, str(BASE / "tests/frontend_contract_probe.js")],
        cwd=BASE,
        input=json.dumps(payload),
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    value = json.loads(result.stdout)
    assert value["score"] == "0–0"
    assert value["teamTournament"] == tid
    assert value["teamQuery"] == str(detail(lab.teacher, tid)["teams"][0]["id"])
    assert value["tournamentQuery"] == str(tid)
    assert value["availability"] == field["availability"]


def test_editing_field_metadata_preserves_schedule_constraints(lab):
    start = auth.now() + timedelta(days=1)
    slots = [
        {
            "starts_at": start.isoformat(),
            "ends_at": (start + timedelta(hours=2)).isoformat(),
        }
    ]
    field = ok(
        lab.teacher.post(
            "/fields",
            {
                "name": "Palestra vincolata",
                "sport_variant_ids": ["football-5"],
                "availability": slots,
            },
        ),
        201,
    )
    edited = request(
        lab.teacher,
        "PATCH",
        f"/fields/{field['id']}",
        {
            "version": field["version"],
            "name": field["name"],
            "sports": ["Calcio"],
            "description": "Nota aggiornata",
        },
    )
    assert edited["availability_intervals"] == field["availability"]
    assert edited["sport_variant_ids"] == ["football-5"]
    tid = tournament(lab.teacher, n=2)
    game = detail(lab.teacher, tid)["matches"][0]
    response = lab.teacher.client.patch(
        f"/api/tournaments/{tid}/matches/{game['id']}/schedule",
        json={
            "version": game["version"],
            "scheduled_at": (start + timedelta(hours=3)).isoformat(),
            "field_id": field["id"],
            "location": field["name"],
        },
    )
    assert response.status_code == 422
    cleared = request(
        lab.teacher,
        "PATCH",
        f"/fields/{field['id']}",
        {
            "version": edited["version"],
            "name": field["name"],
            "sports": ["Calcio"],
            "availability_intervals": [],
        },
    )
    assert cleared["availability_intervals"] == []


def test_team_b_v7_upgrade_preserves_accounts_rosters_and_results(tmp_path):
    import services
    from schemas import TournamentInput

    path = tmp_path / "team-b.sqlite3"
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        for name in [
            "001_initial.sql",
            "002_stable_match_ids.sql",
            "003_sports_expansion.sql",
            "004_archive_and_updates.sql",
            "005_tie_breaker.sql",
            "006_sport_variants.sql",
            "007_teachers.sql",
        ]:
            db.executescript(
                (DB_BASE / "migrations" / name).read_text(encoding="utf-8")
            )
        db.execute(
            "INSERT INTO teachers(id,email,password_hash,display_name) VALUES (7,'b@example.test','unused-synthetic-hash','Docente B')"
        )
        tid = services.create(
            db,
            TournamentInput(
                name="Storico B",
                sport="Calcio",
                variant="calcio-a-5",
                format="round_robin",
                team_names=["Rossi", "Blu"],
            ),
            teacher_id=7,
        )
        ids = [
            r[0]
            for r in db.execute(
                "SELECT id FROM teams WHERE tournament_id=? ORDER BY id", (tid,)
            )
        ]
        sid = db.execute(
            "INSERT INTO stages(tournament_id,ordinal,kind) VALUES (?,0,'round_robin')",
            (tid,),
        ).lastrowid
        db.execute(
            "INSERT INTO matches(tournament_id,stage_id,round_no,position,home_team_id,away_team_id,home_score,away_score,version) VALUES (?,?,1,0,?,?,4,2,5)",
            (tid, sid, *ids),
        )
        db.execute(
            "INSERT INTO team_players(team_id,name,shirt_number) VALUES (?,'Alias conservato',7)",
            (ids[0],),
        )
    initialize(path)
    initialize(path)
    with database(path) as db:
        row = dict(
            db.execute("SELECT * FROM tournaments WHERE id=?", (tid,)).fetchone()
        )
        assert (
            row["teacher_id"] == 7 and row["owner_id"] is not None and row["published"]
        )
        assert row["variant"] == "calcio-a-5" and row["platform_variant_id"] is None
        assert tuple(
            db.execute("SELECT home_score,away_score,version FROM matches").fetchone()
        ) == (4, 2, 5)
        player = db.execute("SELECT * FROM team_players").fetchone()
        student = db.execute(
            "SELECT * FROM students WHERE id=?", (player["student_id"],)
        ).fetchone()
        assert student["display_name"] == player["name"] == "Alias conservato"
        assert student["team_id"] == ids[0] and player["shirt_number"] == 7
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    assert len(list(tmp_path.glob("team-b.pre-v8-*.sqlite3"))) == 1
