"""Application rules; callers own the atomic database transaction."""

import json
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from engine import build_standings, knockout_plan, round_robin
from platform_schemas import TournamentInput


def rows(db, sql, params=()):
    return [dict(r) for r in db.execute(sql, params)]


def required(db, tid):
    result = db.execute("SELECT * FROM tournaments WHERE id=?", (tid,)).fetchone()
    if result is None:
        raise HTTPException(404, "Torneo non trovato")
    return dict(result)


def audit(db, tid, action, payload):
    db.execute(
        "INSERT INTO audit_logs(tournament_id,action,payload) VALUES (?,?,?)",
        (tid, action, json.dumps(payload, ensure_ascii=False)),
    )


def create(db, data: TournamentInput, demo_key=None):
    values = data.model_dump(exclude={"team_names"})
    values.update(public_token=secrets.token_urlsafe(18), demo_key=demo_key)
    cols = ",".join(values)
    tid = db.execute(
        f"INSERT INTO tournaments({cols}) VALUES ({','.join('?' for _ in values)})",
        list(values.values()),
    ).lastrowid
    db.executemany(
        "INSERT INTO teams(tournament_id,name) VALUES (?,?)",
        [(tid, n) for n in data.team_names],
    )
    audit(db, tid, "created", {"name": data.name})
    return tid


def teams(db, tid):
    return rows(
        db,
        "SELECT * FROM teams WHERE tournament_id=? AND archived=0 ORDER BY id",
        (tid,),
    )


def games(db, tid):
    return rows(
        db,
        "SELECT m.*,s.kind FROM matches m JOIN stages s ON s.id=m.stage_id "
        "WHERE m.tournament_id=? ORDER BY s.ordinal,m.round_no,m.position,m.id",
        (tid,),
    )


def table(db, t, group_id=None):
    roster = teams(db, t["id"])
    fixtures = [m for m in games(db, t["id"]) if m["kind"] == "round_robin"]
    if group_id is not None:
        roster = [p for p in roster if p["group_id"] == group_id]
        fixtures = [m for m in fixtures if m["group_id"] == group_id]
    if t.get("platform_variant_id"):
        from sports import standings

        penalties = {
            r["team_id"]: r["points"]
            for r in db.execute(
                "SELECT p.* FROM team_penalties p JOIN teams t ON t.id=p.team_id WHERE t.tournament_id=?",
                (t["id"],),
            )
        }
        return standings(
            roster,
            fixtures,
            t["platform_variant_id"],
            json.loads(t["rules_json"]),
            penalties,
        )
    if t.get("variant_id"):
        import services

        return services.table(db, t, group_id)
    return build_standings(
        roster, fixtures, t["win_points"], t["draw_points"], t["loss_points"]
    )


def detail(db, tid, public=False):
    t = required(db, tid)
    fixtures = games(db, tid)
    roster = teams(db, tid)
    groups = rows(
        db,
        "SELECT g.* FROM groups g JOIN stages s ON s.id=g.stage_id "
        "WHERE s.tournament_id=? ORDER BY g.id",
        (tid,),
    )
    for g in groups:
        g["standings"] = table(db, t, g["id"])
    for m in fixtures:
        m["status"] = (
            "bye"
            if m["is_bye"]
            else (
                "completed"
                if m["home_score"] is not None
                else ("ready" if m["home_team_id"] and m["away_team_id"] else "waiting")
            )
        )
    knockout = [m for m in fixtures if m["kind"] == "knockout"]
    champion = knockout[-1]["winner_team_id"] if knockout else None
    playable = [m for m in fixtures if not m["is_bye"]]
    completed = sum(m["home_score"] is not None for m in playable)
    status = (
        "draft"
        if not fixtures
        else (
            "completed"
            if (
                champion
                or (t["format"] == "round_robin" and completed == len(playable))
            )
            else "active"
        )
    )
    result = {
        "tournament": t,
        "teams": roster,
        "matches": fixtures,
        "groups": groups,
        "stages": rows(
            db, "SELECT * FROM stages WHERE tournament_id=? ORDER BY ordinal", (tid,)
        ),
        "standings": table(db, t) if t["format"] == "round_robin" else [],
        "champion_team_id": champion,
        "status": status,
        "progress": {"completed": completed, "total": len(playable)},
        "public": public,
    }
    if public:
        result["tournament"] = {
            k: v for k, v in t.items() if k not in ("public_token", "demo_key")
        }
    else:
        result["audit"] = rows(
            db,
            "SELECT id,action,created_at FROM audit_logs WHERE tournament_id=? ORDER BY id DESC LIMIT 30",
            (tid,),
        )
    return result


def insert_bracket(db, tid, sid, ids, seed=None):
    mapping = {}
    for i, match in enumerate(knockout_plan(ids, seed)):
        m = dict(match)
        for key in ("source_home", "source_away"):
            if m[key] is not None:
                m[key] = mapping[m[key]]
        cols = ",".join(m)
        mapping[i] = db.execute(
            f"INSERT INTO matches(tournament_id,stage_id,{cols}) "
            f"VALUES (?,?,{','.join('?' for _ in m)})",
            [tid, sid, *m.values()],
        ).lastrowid
    tournament = required(db, tid)
    if tournament.get("rules_json"):
        db.execute(
            "UPDATE matches SET duration=? WHERE stage_id=?",
            (json.loads(tournament["rules_json"])["duration"], sid),
        )
    progress_bracket(db, tid)


def progress_bracket(db, tid):
    """Tree is topologically ordered by round; propagate winners exactly once."""
    known = {}
    for match in games(db, tid):
        if match["kind"] != "knockout":
            continue
        m = dict(match)
        for side in ("home", "away"):
            source = m["source_" + side]
            if source is not None:
                m[side + "_team_id"] = known[source]["winner_team_id"]
        if m["is_bye"]:
            m["winner_team_id"] = m["home_team_id"] or m["away_team_id"]
        if (m["home_team_id"], m["away_team_id"], m["winner_team_id"]) != (
            match["home_team_id"],
            match["away_team_id"],
            match["winner_team_id"],
        ):
            db.execute(
                "UPDATE matches SET home_team_id=?,away_team_id=?,winner_team_id=?,version=version+1 WHERE id=?",
                (m["home_team_id"], m["away_team_id"], m["winner_team_id"], m["id"]),
            )
        known[m["id"]] = m


def generate(db, tid):
    t = required(db, tid)
    if t.get("variant_id") and not t.get("platform_variant_id"):
        import services

        return services.generate(db, tid)
    if games(db, tid):
        raise HTTPException(409, "Incontri già generati: il comando non crea duplicati")
    ids = [p["id"] for p in teams(db, tid)]
    if not 2 <= len(ids) <= 32:
        raise HTTPException(422, "Servono da 2 a 32 partecipanti")
    if t["format"] == "groups":
        count = t["group_count"]
        if len(ids) % count or len(ids) // count < max(2, t["qualifiers"]):
            raise HTTPException(
                422,
                "Per questa demo servono gironi uguali con almeno 2 squadre e abbastanza qualificate",
            )
    kind = "knockout" if t["format"] == "knockout" else "round_robin"
    sid = db.execute(
        "INSERT INTO stages(tournament_id,ordinal,kind) VALUES (?,0,?)", (tid, kind)
    ).lastrowid
    if kind == "knockout":
        insert_bracket(db, tid, sid, ids, t["random_seed"])
    else:
        pools = [(None, ids)]
        if t["format"] == "groups":
            pools = []
            for i in range(t["group_count"]):
                gid = db.execute(
                    "INSERT INTO groups(stage_id,name) VALUES (?,?)",
                    (sid, "Girone " + chr(65 + i)),
                ).lastrowid
                members = ids[i :: t["group_count"]]
                db.executemany(
                    "UPDATE teams SET group_id=? WHERE id=?",
                    [(gid, p) for p in members],
                )
                pools.append((gid, members))
        position = 0
        for gid, members in pools:
            for turn, home, away in round_robin(members, t["legs"]):
                db.execute(
                    "INSERT INTO matches(tournament_id,stage_id,group_id,round_no,position,home_team_id,away_team_id) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (tid, sid, gid, turn, position, home, away),
                )
                position += 1
    if t.get("rules_json"):
        db.execute(
            "UPDATE matches SET duration=? WHERE tournament_id=?",
            (json.loads(t["rules_json"])["duration"], tid),
        )
    audit(db, tid, "generated", {"participants": len(ids)})
    return {"created": len(games(db, tid))}


def qualify(db, tid):
    t = required(db, tid)
    if t.get("variant_id") and not t.get("platform_variant_id"):
        import services

        return services.qualify(db, tid)
    if t["format"] != "groups":
        return
    fixtures = games(db, tid)
    if any(m["kind"] == "knockout" for m in fixtures):
        return
    group_games = [m for m in fixtures if m["kind"] == "round_robin"]
    if not group_games or any(m["home_score"] is None for m in group_games):
        return
    gids = rows(
        db,
        "SELECT DISTINCT group_id FROM teams WHERE tournament_id=? ORDER BY group_id",
        (tid,),
    )
    tables = [table(db, t, g["group_id"]) for g in gids]
    # Ranked tiers, then group order. Standard bracket seeding distributes groups.
    ids = [
        standings[rank]["team_id"]
        for rank in range(t["qualifiers"])
        for standings in tables
    ]
    sid = db.execute(
        "INSERT INTO stages(tournament_id,ordinal,kind) VALUES (?,1,'knockout')", (tid,)
    ).lastrowid
    insert_bracket(db, tid, sid, ids)
    audit(db, tid, "qualified", {"team_ids": ids})


def required_match(db, tid, mid, version):
    tournament = required(db, tid)
    if tournament.get("archived_at"):
        raise HTTPException(409, "Torneo archiviato")
    m = next((m for m in games(db, tid) if m["id"] == mid), None)
    if m is None:
        raise HTTPException(404, "Partita non trovata")
    if m["version"] != version:
        raise HTTPException(409, "Dati cambiati: aggiorna la pagina prima di salvare")
    return m


def descendants(fixtures, mid):
    result, parents = [], {mid}
    for m in fixtures:
        if m["source_home"] in parents or m["source_away"] in parents:
            parents.add(m["id"])
            result.append(m)
    return result


def save_result(
    db, tid, mid, version, home=None, away=None, invalidate=False, score_payload=None
):
    m = required_match(db, tid, mid, version)
    if m["is_bye"] or not m["home_team_id"] or not m["away_team_id"]:
        raise HTTPException(
            409, "Incontro non giocabile: attendi gli avversari o il passaggio per BYE"
        )
    if m["kind"] == "knockout" and home is not None and home == away:
        raise HTTPException(
            422,
            "Serve un vincitore. Inserisci un punteggio decisivo; rigori e set non sono gestiti nella demo",
        )
    winner = (
        None
        if home is None or home == away
        else (m["home_team_id"] if home > away else m["away_team_id"])
    )
    fixtures = games(db, tid)
    affected = []
    if m["kind"] == "round_robin":
        affected = [g for g in fixtures if g["kind"] == "knockout"]
    elif winner != m["winner_team_id"]:
        affected = descendants(fixtures, mid)
    encoded = json.dumps(score_payload) if score_payload is not None else None
    changed = (home, away) != (m["home_score"], m["away_score"]) or (
        score_payload is not None and encoded != m.get("score_json")
    )
    if changed and affected:
        if (
            m["kind"] == "round_robin"
            or any(g["home_score"] is not None for g in affected)
        ) and not invalidate:
            raise HTTPException(
                409,
                "La correzione modifica le fasi successive. Conferma l’annullamento dei risultati dipendenti",
            )
        audit(db, tid, "invalidated", {"matches": affected})
        if m["kind"] == "round_robin":
            # Remove dependencies before nodes; retain snapshots in the audit log.
            for g in reversed(affected):
                db.execute("DELETE FROM matches WHERE id=?", (g["id"],))
            db.execute("DELETE FROM stages WHERE tournament_id=? AND ordinal=1", (tid,))
        else:
            for g in affected:
                db.execute(
                    "UPDATE matches SET home_score=NULL,away_score=NULL,winner_team_id=NULL,score_json=NULL,"
                    "scheduled_at=NULL,location=NULL,field_id=NULL,timezone=NULL,version=version+1 WHERE id=?",
                    (g["id"],),
                )
                db.execute("DELETE FROM official_results WHERE match_id=?", (g["id"],))
                db.execute("DELETE FROM match_sets WHERE match_id=?", (g["id"],))
                db.execute(
                    "DELETE FROM player_performances WHERE match_id=?", (g["id"],)
                )
    if changed:
        db.execute("DELETE FROM player_performances WHERE match_id=?", (mid,))
        db.execute(
            "UPDATE matches SET home_score=?,away_score=?,winner_team_id=?,score_json=?,version=version+1 WHERE id=?",
            (home, away, winner, encoded, mid),
        )
        db.execute("DELETE FROM match_sets WHERE match_id=?", (mid,))
        if score_payload and score_payload["type"] == "sets":
            db.executemany(
                "INSERT INTO match_sets(match_id,set_no,home_points,away_points) VALUES (?,?,?,?)",
                [
                    (mid, i, s["home"], s["away"])
                    for i, s in enumerate(score_payload["sets"], 1)
                ],
            )
        audit(
            db,
            tid,
            "result_cleared" if home is None else "result_saved",
            {
                "match_id": mid,
                "before": [m["home_score"], m["away_score"]],
                "after": [home, away],
            },
        )
    progress_bracket(db, tid)
    qualify(db, tid)
    state = detail(db, tid)
    return {
        "ok": True,
        "invalidated": len(affected) if changed else 0,
        "champion_team_id": state["champion_team_id"],
    }


def schedule(db, tid, mid, data):
    m = required_match(db, tid, mid, data.version)
    if m["is_bye"]:
        raise HTTPException(422, "Un BYE non occupa un campo")
    timestamp = (
        data.scheduled_at.astimezone(timezone.utc) if data.scheduled_at else None
    )
    location = data.location.strip()
    fixtures = games(db, tid)
    if timestamp:
        end = timestamp + timedelta(minutes=data.duration)
        ids = {m["home_team_id"], m["away_team_id"]} - {None}
        for other in fixtures:
            if other["id"] == mid or not other["scheduled_at"]:
                continue
            start = datetime.fromisoformat(other["scheduled_at"])
            finish = start + timedelta(minutes=other["duration"])
            field_clash = (
                location and location.casefold() == (other["location"] or "").casefold()
            )
            team_clash = ids & {other["home_team_id"], other["away_team_id"]}
            if timestamp < finish and start < end and (field_clash or team_clash):
                raise HTTPException(
                    409, "Orario in conflitto: campo o partecipante già impegnato"
                )
            if (
                other["id"] in (m["source_home"], m["source_away"])
                and finish > timestamp
            ):
                raise HTTPException(
                    409, "La partita deve iniziare dopo gli incontri da cui dipende"
                )
            if mid in (other["source_home"], other["source_away"]) and end > start:
                raise HTTPException(
                    409, "La partita deve finire prima del turno successivo pianificato"
                )
    db.execute(
        "UPDATE matches SET scheduled_at=?,location=?,duration=?,version=version+1 WHERE id=?",
        (
            timestamp.isoformat() if timestamp else None,
            location or None,
            data.duration,
            mid,
        ),
    )
    audit(
        db,
        tid,
        "scheduled",
        {
            "match_id": mid,
            "utc": timestamp.isoformat() if timestamp else None,
            "location": location,
        },
    )
    return {"ok": True}
