"""Exercise the actual Team B adapters against both backend data lineages."""

import json
import sqlite3
from datetime import timedelta

from fastapi.testclient import TestClient

import platform_auth as auth
from db import BASE, database, initialize
from test_platform import assign, detail, ok, tournament
from test_platform import lab as platform_lab

lab = platform_lab


def request(actor, method, path, body=None, code=200):
    return ok(actor.client.request(method, "/api" + path, json=body), code)


def test_adapter_order_csv_roster_and_explicit_identity(lab):
    tid = tournament(lab.teacher, generate=False)
    state = detail(lab.teacher, tid)
    ids = [t["id"] for t in state["teams"]]
    route = f"/tournaments/{tid}"
    body = {"version": state["tournament"]["order_version"], "team_ids": ids[::-1]}
    request(lab.teacher, "PATCH", route + "/teams/order", body)
    assert (
        lab.teacher.client.patch("/api" + route + "/teams/order", json=body).status_code
        == 409
    )
    endpoint = route + f"/teams/{ids[0]}/players/import"
    assert (
        lab.teacher.client.post(
            "/api" + endpoint, json={"csv": "nome,numero\nAlias uno,7\nAlias due,no"}
        ).status_code
        == 422
    )
    assert request(lab.teacher, "GET", route + "/students")["students"] == []
    assert (
        request(
            lab.teacher,
            "POST",
            endpoint,
            {"csv": "nome,numero\nAlias uno,7\nAlias due,8"},
            201,
        )["created"]
        == 2
    )
    students = request(lab.teacher, "GET", route + "/students")["students"]
    student = request(
        lab.teacher,
        "PATCH",
        route + f"/students/{students[0]['id']}",
        {"version": students[0]["version"], "user_id": lab.student.uid},
    )
    moved = request(
        lab.teacher,
        "PATCH",
        route + f"/students/{student['id']}/team",
        {"version": student["version"], "team_id": ids[1]},
    )
    assert moved["team_id"] == ids[1]
    with database(lab.path) as db:
        assert (
            db.execute(
                "SELECT team_id FROM team_players WHERE student_id=?", (student["id"],)
            ).fetchone()[0]
            == ids[1]
        )
    request(
        lab.teacher,
        "PATCH",
        route + f"/students/{student['id']}/team",
        {"version": moved["version"], "team_id": None},
    )
    assert len(request(lab.teacher, "GET", route + "/students")["unassigned"]) == 1
    ok(lab.teacher.post(route + "/generate"))
    assert [t["id"] for t in detail(lab.teacher, tid)["teams"]] == ids[::-1]


def test_adapter_proposals_are_private_versioned_and_official_only_after_review(lab):
    tid = tournament(lab.teacher, n=2)
    assign(lab, tid)
    assign(lab, tid, lab.second, 1)
    game = detail(lab.teacher, tid)["matches"][0]
    base = f"/tournaments/{tid}"
    endpoint = base + f"/matches/{game['id']}/proposals"
    proposal = request(
        lab.student,
        "POST",
        endpoint,
        {"version": game["version"], "home_score": 3, "away_score": 1},
        201,
    )
    other = request(
        lab.second,
        "POST",
        endpoint,
        {"version": game["version"], "home_score": 2, "away_score": 1},
        201,
    )
    assert detail(lab.teacher, tid)["matches"][0]["home_score"] is None
    pending = request(lab.teacher, "GET", base + "/proposals")["proposals"]
    assert pending[0]["conflicts"] == [other["id"]]
    assert len(request(lab.student, "GET", base + "/proposals")["proposals"]) == 1
    assert lab.other.client.get("/api" + base + "/proposals").status_code == 404
    payload = {
        "action": "approve",
        "version": proposal["version"],
        "match_version": game["version"],
    }
    request(lab.teacher, "PATCH", f"/proposals/{proposal['id']}", payload)
    assert detail(lab.teacher, tid)["matches"][0]["home_score"] == 3
    assert (
        lab.teacher.client.patch(
            f"/api/proposals/{proposal['id']}", json=payload
        ).status_code
        == 409
    )
    invalid = {
        "action": "correct",
        "version": other["version"],
        "match_version": game["version"],
        "home_score": "wrong",
        "away_score": 2,
    }
    assert (
        lab.teacher.client.patch(
            f"/api/proposals/{other['id']}", json=invalid
        ).status_code
        == 422
    )


def test_fields_calendar_dashboard_and_booking_conflicts(lab):
    tid = tournament(lab.teacher, n=4)
    base = f"/tournaments/{tid}"
    field = request(
        lab.teacher,
        "POST",
        "/fields",
        {
            "name": "Palestra A",
            "sports": ["Calcio"],
            "venue": "Scuola",
            "availability": "Lunedì pomeriggio",
        },
        201,
    )
    assert (
        request(lab.teacher, "GET", "/fields")["fields"][0]["availability"]
        == "Lunedì pomeriggio"
    )
    assert request(lab.other, "GET", "/fields")["fields"] == []
    games = detail(lab.teacher, tid)["matches"]
    time = (auth.now() + timedelta(days=1)).replace(microsecond=0).isoformat()
    data = {
        "version": games[0]["version"],
        "scheduled_at": time,
        "field_id": field["id"],
        "location": "Palestra A",
        "duration": 20,
    }
    request(lab.teacher, "PATCH", base + f"/matches/{games[0]['id']}/schedule", data)
    data["version"] = games[1]["version"]
    assert (
        lab.teacher.client.patch(
            "/api" + base + f"/matches/{games[1]['id']}/schedule", json=data
        ).status_code
        == 409
    )
    events = request(lab.teacher, "GET", f"/calendar?tournament={tid}")["events"]
    assert (
        next(e for e in events if e["match_id"] == games[0]["id"])["field_id"]
        == field["id"]
    )
    assert len(request(lab.teacher, "GET", "/dashboard?mine=1")["upcoming"]) == len(
        games
    )
    assert lab.other.client.get("/api" + base + "/export.csv").status_code == 404
    request(
        lab.teacher,
        "DELETE",
        f"/fields/{field['id']}",
        {"version": field["version"]},
        204,
    )
    assert not request(lab.teacher, "GET", "/fields")["fields"][0]["active"]


def test_invite_preview_join_idempotency_and_real_student_session(lab):
    tid = tournament(lab.teacher, n=2)
    team = detail(lab.teacher, tid)["teams"][0]
    item = request(
        lab.teacher,
        "POST",
        f"/tournaments/{tid}/invites",
        {
            "team_id": team["id"],
            "expires_at": (auth.now() + timedelta(days=1)).isoformat(),
            "max_uses": 1,
            "require_approval": False,
        },
        201,
    )
    token = item["token"]
    endpoint = "/invites/" + token
    assert "/#/join/" in item["url"]
    with TestClient(lab.app) as anonymous:
        preview = ok(anonymous.get("/api" + endpoint))
        assert preview["kind"] == "team" and preview["status"] == "active"
        assert "email" not in json.dumps(preview)
        assert anonymous.post("/api" + endpoint + "/join").status_code == 401
    assert request(lab.student, "POST", endpoint + "/join")["status"] == "accepted"
    assert request(lab.student, "GET", endpoint)["status"] == "accepted"
    request(lab.student, "POST", endpoint + "/join")
    assert request(lab.second, "GET", endpoint)["status"] == "full"
    assert lab.second.client.post("/api" + endpoint + "/join").status_code == 409
    assert request(lab.student, "GET", "/auth/session")["role"] == "student"
    assert (
        request(lab.student, "GET", f"/tournaments/{tid}")["student_team_id"]
        == team["id"]
    )


def test_manual_statistics_are_bounded_private_and_invalidated_by_score_correction(lab):
    tid = tournament(lab.teacher, n=2)
    assign(lab, tid)
    state = detail(lab.teacher, tid)
    game = state["matches"][0]
    base = f"/tournaments/{tid}"
    with database(lab.path) as db:
        player = db.execute(
            "SELECT p.id,p.team_id FROM team_players p JOIN students s ON s.id=p.student_id WHERE s.user_id=?",
            (lab.student.uid,),
        ).fetchone()
    assert request(lab.teacher, "GET", base + "/player-statistics")["players"] == []
    home = 3
    away = 2
    request(
        lab.teacher,
        "PATCH",
        base + f"/matches/{game['id']}",
        {"version": game["version"], "home_score": home, "away_score": away},
    )
    current = detail(lab.teacher, tid)["matches"][0]
    endpoint = base + f"/matches/{game['id']}/performances"
    excessive = {
        "version": current["version"],
        "players": [{"player_id": player["id"], "points": 99}],
    }
    assert lab.teacher.client.put("/api" + endpoint, json=excessive).status_code == 422
    saved = request(
        lab.teacher,
        "PUT",
        endpoint,
        {
            "version": current["version"],
            "players": [{"player_id": player["id"], "points": 1}],
        },
    )
    assert (
        request(lab.student, "GET", base + "/player-statistics")["players"][0]["points"]
        == 1
    )
    assert lab.other.client.get("/api" + base + "/player-statistics").status_code == 404
    request(
        lab.teacher,
        "PATCH",
        base + f"/matches/{game['id']}",
        {"version": saved["version"], "home_score": 4, "away_score": 1},
    )
    assert request(lab.teacher, "GET", base + "/player-statistics")["players"] == []


def test_deactivation_revokes_both_session_protocols(lab):
    with database(lab.path) as db:
        teacher_id = db.execute(
            "SELECT teacher_id FROM teacher_user_links WHERE user_id=?",
            (lab.teacher.uid,),
        ).fetchone()[0]
    request(lab.teacher, "POST", f"/teachers/{teacher_id}/deactivate")
    assert lab.teacher.get("/users/me").status_code == 401
    with TestClient(lab.app) as client:
        assert (
            client.post(
                "/api/auth/login",
                json={
                    "email": "teacher-a@example.test",
                    "password": "Synthetic-passphrase-123",
                },
            ).status_code
            == 401
        )
        csrf = ok(client.get("/api/v1/auth/csrf"))["csrf_token"]
        assert (
            client.post(
                "/api/v1/auth/login",
                headers={"X-CSRF-Token": csrf},
                json={
                    "email": "teacher-a@example.test",
                    "password": "Synthetic-passphrase-123",
                },
            ).status_code
            == 401
        )


def test_v1_logout_also_revokes_the_frontend_signed_cookie(lab):
    from auth import COOKIE_NAME

    with TestClient(lab.app) as client:
        ok(
            client.post(
                "/api/auth/login",
                json={
                    "email": "teacher-a@example.test",
                    "password": "Synthetic-passphrase-123",
                },
            )
        )
        signed = client.cookies.get(COOKIE_NAME)
        csrf = ok(client.get("/api/v1/auth/csrf"))["csrf_token"]
        ok(client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf}), 204)
        client.cookies.set(COOKIE_NAME, signed)
        assert not client.get("/api/auth/session").json()["authenticated"]
        assert (
            client.post("/api/tournaments", json={"name": "Forbidden"}).status_code
            == 401
        )


def test_catalog_rule_edits_and_penalties_share_the_v1_standings(lab):
    tid = tournament(lab.teacher, n=2, generate=False)
    base = f"/tournaments/{tid}"
    request(lab.teacher, "PATCH", base, {"name": "Nome aggiornato"})
    with database(lab.path) as db:
        assert (
            db.execute(
                "SELECT platform_variant_id FROM tournaments WHERE id=?", (tid,)
            ).fetchone()[0]
            == "football-5"
        )
    request(lab.teacher, "PATCH", base, {"win_points": 5})
    ok(lab.teacher.post(base + "/generate"))
    game = detail(lab.teacher, tid)["matches"][0]
    ok(
        lab.teacher.patch(
            base + f"/matches/{game['id']}/result",
            {
                "match_version": game["version"],
                "score": {"type": "points", "home": 2, "away": 1},
                "reason": "Verifica regolamento",
            },
        )
    )
    assert detail(lab.teacher, tid)["standings"][0]["points"] == 5
    team = next(
        t
        for t in ok(lab.teacher.get(base + "/teams"))["items"]
        if t["id"] == game["home_team_id"]
    )
    ok(
        lab.teacher.patch(
            base + f"/teams/{team['id']}/penalty",
            {"version": team["version"], "points": 2, "reason": "Penalità sintetica"},
        )
    )
    assert detail(lab.teacher, tid)["standings"][0]["points"] == 3
    assert request(lab.teacher, "GET", base)["standings"][0]["points"] == 3


def test_team_b_only_set_variant_accepts_versioned_student_proposals(lab):
    tid = request(
        lab.teacher,
        "POST",
        "/tournaments",
        {
            "name": "Badminton sintetico",
            "sport": "Badminton",
            "variant": "badminton-singolare",
            "format": "round_robin",
            "team_names": ["Rosso", "Blu"],
        },
        201,
    )["id"]
    base = f"/tournaments/{tid}"
    ok(lab.teacher.post(base + "/generate"))
    assign(lab, tid)
    game = detail(lab.teacher, tid)["matches"][0]
    proposal = request(
        lab.student,
        "POST",
        base + f"/matches/{game['id']}/proposals",
        {
            "version": game["version"],
            "sets": [{"home": 21, "away": 12}, {"home": 21, "away": 16}],
        },
        201,
    )
    request(
        lab.teacher,
        "PATCH",
        f"/proposals/{proposal['id']}",
        {
            "action": "approve",
            "version": proposal["version"],
            "match_version": game["version"],
        },
    )
    match = request(lab.teacher, "GET", base)["matches"][0]
    assert match["home_score"] == 2 and len(match["sets"]) == 2
    assert (
        lab.student.client.post(
            "/api" + base + f"/matches/{game['id']}/proposals",
            json={"version": match["version"], "home_score": 2, "away_score": 0},
        ).status_code
        == 422
    )


def test_frontend_result_respects_the_platform_custom_set_rules(lab):
    tid = tournament(
        lab.teacher, n=2, variant="volleyball-indoor", config={"win_by": 3}
    )
    game = detail(lab.teacher, tid)["matches"][0]
    response = lab.teacher.client.patch(
        f"/api/tournaments/{tid}/matches/{game['id']}",
        json={"version": game["version"], "sets": [{"home": 25, "away": 23}] * 3},
    )
    assert response.status_code == 422
    assert detail(lab.teacher, tid)["matches"][0]["home_score"] is None


def test_team_a_v4_migration_preserves_manual_order_scores_and_ownership(tmp_path):
    path = tmp_path / "old-a.sqlite3"
    with sqlite3.connect(path) as db:
        for name in [
            "001_initial.sql",
            "002_stable_match_ids.sql",
            "003_core_platform.sql",
            "004_team_penalties.sql",
        ]:
            db.executescript((BASE / "migrations" / name).read_text(encoding="utf-8"))
        db.execute("INSERT INTO organizations(id,name) VALUES (1,'Scuola')")
        db.execute(
            "INSERT INTO users(id,email,display_name,password_hash,role,organization_id) VALUES (1,'old@example.test','Docente','unused-hash','teacher',1)"
        )
        import sports

        db.execute(
            "INSERT INTO tournaments(id,name,sport,format,public_token,owner_id,organization_id,variant_id,rules_json) VALUES (1,'Da preservare','Calcio','round_robin','token',1,1,'football-5',?)",
            (json.dumps(sports.configuration("football-5")),),
        )
        db.execute(
            "INSERT INTO teams(id,tournament_id,name,display_order) VALUES (1,1,'Prima',20),(2,1,'Seconda',10)"
        )
        db.execute(
            "INSERT INTO stages(id,tournament_id,ordinal,kind) VALUES (1,1,0,'round_robin')"
        )
        db.execute(
            "INSERT INTO matches(id,tournament_id,stage_id,round_no,position,home_team_id,away_team_id,home_score,away_score) VALUES (1,1,1,1,0,1,2,3,1)"
        )
    initialize(path)
    initialize(path)
    with database(path) as db:
        t = dict(db.execute("SELECT * FROM tournaments").fetchone())
        assert t["platform_variant_id"] == "football-5" and t["variant"] == "calcio-a-5"
        assert t["owner_id"] == 1 and t["teacher_id"] is not None and not t["published"]
        assert (
            db.execute("SELECT id FROM teams ORDER BY display_order").fetchall()[0][0]
            == 2
        )
        assert tuple(
            db.execute("SELECT home_score,away_score FROM matches").fetchone()
        ) == (3, 1)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    assert len(list(tmp_path.glob("old-a.pre-v8-*.sqlite3"))) == 1
