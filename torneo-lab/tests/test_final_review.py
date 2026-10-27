"""Reproductions from FINAL_AUDIT; synthetic data and temporary files only."""

import importlib.util
import json
import logging
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from db import database
from test_platform import detail, ok, tournament
from test_platform import lab as platform_lab
from test_team_integration import request

lab = platform_lab
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("sport,variant", [
    ("Calcio", "calcio-a-5"), ("Basket", "basket-3x3"),
    ("Pallavolo", "pallavolo-6v6"), ("Ping pong", "ping-pong-singolare"),
])
def test_catalog_group_final_keeps_snapshot_duration_through_v1(lab, sport, variant):
    # Obtain real slugs from the catalog rather than assuming the UI's labels.
    catalog = lab.teacher.client.get("/api/sports").json()["sports"]
    chosen = next(s for s in catalog if s["name"] == sport)
    variants = chosen["variants"]
    selected = next(v for v in variants if v["slug"] == variant)
    tid = request(lab.teacher, "POST", "/tournaments", {
        "name": "Coppa durata sintetica", "sport": sport,
        "variant": selected["slug"], "format": "groups", "group_count": 2,
        "qualifiers": 1, "team_names": ["Nord", "Sud", "Est", "Ovest"],
    }, 201)["id"]
    request(lab.teacher, "POST", f"/tournaments/{tid}/generate")
    initial = detail(lab.teacher, tid)
    with database(lab.path) as db:
        rules = json.loads(db.execute("SELECT rules_snapshot FROM tournaments WHERE id=?", (tid,)).fetchone()[0])
    if rules["scoring_mode"] == "sets":
        target = rules["points_per_set"]
        score = {"type": "sets", "sets": [{"home": target, "away": 0}] * rules["sets_to_win"]}
    else:
        score = {"type": "points", "home": 2, "away": 1}
    for game in initial["matches"]:
        ok(lab.teacher.patch(f"/tournaments/{tid}/matches/{game['id']}/result", {
            "match_version": game["version"], "score": score, "reason": "Prova durata",
        }))
    finals = [g for g in detail(lab.teacher, tid)["matches"] if g["kind"] == "knockout"]
    assert finals
    assert {g["duration"] for g in finals} == {g["duration"] for g in initial["matches"]}


def test_legacy_correction_distinguishes_played_score_from_forfeit(lab):
    tid = tournament(lab.teacher, n=2)
    game = detail(lab.teacher, tid)["matches"][0]
    ok(lab.teacher.patch(f"/tournaments/{tid}/matches/{game['id']}/result", {
        "match_version": game["version"],
        "score": {"type": "forfeit", "winner": "home", "reason": "Decisione sintetica"},
        "reason": "Prova amministrativa",
    }))
    game = detail(lab.teacher, tid)["matches"][0]
    request(lab.teacher, "PATCH", f"/tournaments/{tid}/matches/{game['id']}", {
        "version": game["version"], "home_score": game["home_score"], "away_score": game["away_score"],
    })
    current = detail(lab.teacher, tid)["matches"][0]
    assert current["score"]["type"] == "points"
    assert current["version"] == game["version"] + 1
    official = ok(lab.teacher.get(f"/tournaments/{tid}/matches/{game['id']}/result"))
    assert official["official_result"]["score"] == current["score"]
    request(lab.teacher, "PATCH", f"/tournaments/{tid}/matches/{game['id']}", {
        "version": current["version"], "home_score": current["home_score"], "away_score": current["away_score"],
    })
    assert detail(lab.teacher, tid)["matches"][0]["version"] == current["version"]


def site_builder():
    spec = importlib.util.spec_from_file_location("review_site_builder", ROOT / ".github/scripts/build_site.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pages_build_refuses_foreign_nonempty_output(tmp_path):
    module = site_builder()
    out = tmp_path / "other-work"
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("unrelated work", encoding="utf-8")
    with pytest.raises(SystemExit):
        module.render(out)
    assert sentinel.read_text(encoding="utf-8") == "unrelated work"


def test_pages_build_rejects_source_and_ancestors(tmp_path, monkeypatch):
    module = site_builder()
    root = tmp_path / "fake-repo"
    site = root / "website"
    site.mkdir(parents=True)
    sentinel = site / "keep.txt"
    sentinel.write_text("source", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module, "SITE", site)
    for out in (root, site, tmp_path, site / "nested-output"):
        with pytest.raises(SystemExit):
            module.render(out)
        assert sentinel.read_text(encoding="utf-8") == "source"


def test_pages_build_can_repeat_on_its_own_output(tmp_path):
    module = site_builder()
    out = tmp_path / "generated"
    module.render(out)
    (out / "stale.html").write_text("old generated content", encoding="utf-8")
    module.render(out)
    assert not (out / "stale.html").exists()
    assert (out / "index.html").exists()


@pytest.mark.parametrize("url,expected", [
    ("/api/invites/synthetic-token/join", "/api/invites/[redacted]/join"),
    ("/public/synthetic-token?invite=other-token", "/public/[redacted]"),
    ("/?invite=synthetic-token", "/"),
    ("/api/v1/invites/validate", "/api/v1/invites/validate"),
    ("/api/v1/tournaments?status=active", "/api/v1/tournaments"),
])
def test_access_logs_minimise_tokens_preserving_method_and_status(url, expected):
    from uvicorn.logging import AccessFormatter

    from access_logging import PrivateAccessFilter
    record = logging.LogRecord("uvicorn.access", logging.INFO, "", 0,
                               '%s - "%s %s HTTP/%s" %d',
                               ("127.0.0.1:1234", "POST", url, "1.1", 201), None)
    assert PrivateAccessFilter().filter(record)
    formatted = AccessFormatter(fmt='%(client_addr)s - "%(request_line)s" %(status_code)s', use_colors=False).format(record)
    assert expected in formatted
    assert "POST " in formatted and "201 Created" in formatted
    assert "synthetic-token" not in formatted and "other-token" not in formatted


def test_access_filter_installation_is_idempotent():
    from access_logging import PrivateAccessFilter, install_access_filter
    install_access_filter()
    install_access_filter()
    assert sum(isinstance(f, PrivateAccessFilter) for f in logging.getLogger("uvicorn.access").filters) == 1


def test_summary_equivalence_permissions_pagination_and_constant_queries(lab):
    import platform_auth as auth
    import platform_services as svc
    import v1_domain as domain
    from test_platform import assign

    ids = [tournament(lab.teacher, n=3, fmt="knockout"),
           tournament(lab.teacher, n=4, fmt="groups", qualifiers=1),
           tournament(lab.teacher, n=2, generate=False)]
    hidden = tournament(lab.other, n=2)
    assign(lab, ids[0])
    with database(lab.path, True) as db:
        # A published tournament belonging to someone else stays outside V1 lists.
        db.execute("UPDATE tournaments SET published=1 WHERE id=?", (hidden,))
        owner = db.execute("SELECT * FROM users WHERE id=?", (lab.teacher.uid,)).fetchone()
        db.execute("UPDATE users SET organization_id=? WHERE id=?", (owner["organization_id"], lab.other.uid))
        db.execute("INSERT INTO tournament_collaborators(tournament_id,user_id) VALUES (?,?)", (ids[1], lab.other.uid))
        db.execute("UPDATE tournaments SET archived_at='2026-10-27' WHERE id=?", (ids[2],))
    for actor in (lab.teacher, lab.other, lab.student, lab.second):
        with database(lab.path) as db:
            user = dict(db.execute("SELECT * FROM users WHERE id=?", (actor.uid,)).fetchone())
            expected = []
            for t in svc.rows(db, "SELECT * FROM tournaments WHERE owner_id IS NOT NULL ORDER BY id"):
                manager = auth.manages(db, user, t)
                enrolled = db.execute("SELECT 1 FROM students WHERE tournament_id=? AND user_id=?", (t["id"], actor.uid)).fetchone()
                if not manager and not enrolled:
                    continue
                state = domain.detail(db, user, t["id"])
                expected.append(dict(state["tournament"], status=state["status"], progress=state["progress"],
                                     team_count=len(state["teams"]), champion_team_id=state["champion_team_id"]))
            statements = []
            db.set_trace_callback(statements.append)
            assert domain.summaries(db, user) == expected
            assert sum(s.startswith("SELECT") for s in statements) <= 4
            db.set_trace_callback(None)
            for status in ("draft", "active", "completed", "unknown"):
                assert domain.summaries(db, user, status) == [i for i in expected if i["status"] == status]
        response = ok(actor.get("/tournaments?limit=1"))
        assert response["items"] == expected[:1]
        assert response["next_cursor"] == (1 if len(expected) > 1 else None)
        assert ok(actor.get("/tournaments?cursor=999"))["items"] == []


def test_calendar_window_matches_pairwise_reference_with_offsets(lab):
    from frontend_api import calendar_data

    tid = tournament(lab.teacher, n=8)
    rng = random.Random(1234)
    start = datetime(2026, 11, 3, 10, tzinfo=timezone.utc)
    with database(lab.path, True) as db:
        for mid, in db.execute("SELECT id FROM matches WHERE tournament_id=?", (tid,)).fetchall():
            stamp = (start + timedelta(minutes=rng.choice([0, 20, 40, 60, 1440]))).astimezone(
                timezone(timedelta(hours=rng.choice([-4, 0, 1, 5]))))
            db.execute("UPDATE matches SET scheduled_at=?,duration=?,location=? WHERE id=?",
                       (stamp.isoformat(), rng.choice([20, 40, 60]), rng.choice(["Campo A", "campo a", "", "Campo B"]), mid))
        teacher_id = db.execute("SELECT teacher_id FROM tournaments WHERE id=?", (tid,)).fetchone()[0]
    fake_request = SimpleNamespace(state=SimpleNamespace(teacher={"teacher_id": teacher_id}, platform_user=None))
    with database(lab.path) as db:
        result = calendar_data(db, fake_request)
    expected = []
    scheduled = [e for e in result["events"] if e["scheduled_at"]]
    messages = {"field": "Campo occupato due volte", "team": "Squadra in doppio impegno", "teacher": "Tornei dello stesso docente contemporanei"}
    for index, a in enumerate(scheduled):
        a_start = datetime.fromisoformat(a["scheduled_at"])
        for b in scheduled[index + 1:]:
            b_start = datetime.fromisoformat(b["scheduled_at"])
            if a_start >= b_start + timedelta(minutes=b["duration"]) or b_start >= a_start + timedelta(minutes=a["duration"]):
                continue
            shared = ({a["home_team_id"], a["away_team_id"]} - {None}) & {b["home_team_id"], b["away_team_id"]}
            kind = "field" if a["field"] and a["field"].casefold() == b["field"].casefold() else "team" if shared else "teacher"
            expected.append({"kind": kind, "match_id": a["match_id"], "other_match_id": b["match_id"], "message": messages[kind]})
    assert expected and result["conflicts"] == expected

