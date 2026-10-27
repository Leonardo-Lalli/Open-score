"""Adapters requested by Team B; all state lives in the shared transaction/DB."""

import csv
import io
import json
from datetime import date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Request, Response
from pydantic import Field

import platform_auth as auth
import platform_services as core
import services
import sports
import v1_domain as domain
import v1_resources as resources
import v1_results as results
import v1_schemas as schema
from db import database
from schemas import Input, Name, PlayerInput, ResultInput, Score, SetPoints


class Order(Input):
    team_ids: list[schema.Identifier] = Field(max_length=32)
    version: schema.Version


class Review(Input):
    action: Literal["approve", "reject", "correct"]
    version: schema.Version
    match_version: schema.Version
    home_score: Score | None = None
    away_score: Score | None = None
    sets: list[SetPoints] | None = Field(default=None, min_length=1, max_length=7)
    reason: str = Field(default="", max_length=500)
    invalidate: bool = False


class FieldInput(Input):
    name: Name
    description: str = Field(default="", max_length=400)
    venue: str = Field(default="", max_length=120)
    sports: list[str] = Field(min_length=1, max_length=20)
    availability: str = Field(default="", max_length=160)
    availability_intervals: list[schema.Availability] = Field(
        default_factory=list, max_length=100
    )
    active: bool = True
    version: schema.Version | None = None


class Bulk(Input):
    rows: list[PlayerInput] | None = Field(default=None, max_length=1000)
    csv: str | None = Field(default=None, max_length=200_000)


class LinkStudent(schema.VersionInput):
    user_id: schema.Identifier


class Performance(Input):
    player_id: schema.Identifier
    points: int = Field(strict=True, ge=0, le=999)


class Performances(schema.VersionInput):
    players: list[Performance] = Field(max_length=64)


def score_input(data):
    from pydantic import TypeAdapter

    if data.sets is None and (data.home_score is None or data.away_score is None):
        auth.fail(422, "invalid_score", "Inserisci entrambi i punteggi")
    if data.sets is not None and (
        data.home_score is not None or data.away_score is not None
    ):
        auth.fail(422, "invalid_score", "Invia i set oppure i punti")
    payload = (
        {
            "type": "sets",
            "sets": [
                s.model_dump() if hasattr(s, "model_dump") else s for s in data.sets
            ],
        }
        if data.sets is not None
        else {"type": "points", "home": data.home_score, "away": data.away_score}
    )
    return TypeAdapter(sports.Score).validate_python(payload)


def visible(db, request, t):
    teacher = getattr(request.state, "teacher", None)
    user = getattr(request.state, "platform_user", None)
    return bool(
        t["published"]
        or (teacher and teacher["teacher_id"] == t["teacher_id"])
        or (
            user
            and db.execute(
                "SELECT 1 FROM students WHERE tournament_id=? AND user_id=?",
                (t["id"], user["id"]),
            ).fetchone()
        )
    )


def proposal_row(db, item):
    value = results.proposal_dto(db, item)
    game = (
        results.match(db, item["tournament_id"], item["match_id"])
        if item["match_id"]
        else None
    )
    names = {t["id"]: t["name"] for t in core.teams(db, item["tournament_id"])}
    score = value["score"]
    conflicts = core.rows(
        db,
        "SELECT id FROM result_proposals WHERE match_id=? AND status='pending' AND id!=? AND score_json!=?",
        (item["match_id"], item["id"], item["score_json"]),
    )
    author = db.execute(
        "SELECT display_name FROM users WHERE id=?", (item["submitted_by"],)
    ).fetchone()
    return dict(
        value,
        proposed_home_score=score.get("home"),
        proposed_away_score=score.get("away"),
        proposed_sets=score.get("sets"),
        author=author[0],
        conflicts=[i["id"] for i in conflicts],
        tournament_name=core.required(db, item["tournament_id"])["name"],
        home_name=names.get(game["home_team_id"]) if game else None,
        away_name=names.get(game["away_team_id"]) if game else None,
        match_version=game["version"] if game else item["match_version"],
    )


def field_row(db, item):
    item = resources.field_dto(item)
    venue = (
        db.execute("SELECT name FROM venues WHERE id=?", (item["venue_id"],)).fetchone()
        if item["venue_id"]
        else None
    )
    from identity_bridge import VARIANT_SLUGS

    variants = {VARIANT_SLUGS.get(value, value) for value in item["sport_variant_ids"]}
    names = []
    for row in db.execute(
        "SELECT v.slug,s.name FROM sport_variants v JOIN sport_configs s ON s.id=v.sport_id"
    ):
        if row["slug"] in variants and row["name"] not in names:
            names.append(row["name"])
    return dict(
        item,
        venue=venue[0] if venue else "",
        sports=names,
        active=not item["archived"],
        availability=item["availability_note"],
        availability_intervals=item["availability"],
    )


def record_legacy_result(db, teacher_id, tid, mid, before):
    game = results.match(db, tid, mid)
    if game["version"] == before:
        return
    user = auth_user_for_teacher(db, teacher_id)
    if game["score_json"]:
        db.execute(
            "INSERT INTO official_results(match_id,score_json,approved_by,approved_at) VALUES (?,?,?,?) "
            "ON CONFLICT(match_id) DO UPDATE SET score_json=excluded.score_json,approved_by=excluded.approved_by,approved_at=excluded.approved_at,source_proposal_id=NULL",
            (mid, game["score_json"], user["id"], auth.now().isoformat()),
        )
    db.execute(
        "INSERT INTO result_reviews(tournament_id,match_id,reviewed_by,decision,reason,score_json) VALUES (?,?,?,?,?,?)",
        (
            tid,
            mid,
            user["id"],
            "official" if game["score_json"] else "clear",
            "Modifica del docente dalla interfaccia",
            game["score_json"],
        ),
    )
    domain.audit(
        db,
        user,
        tid,
        "official_result_saved" if game["score_json"] else "official_result_cleared",
        {"match_id": mid},
    )
    resources.validate_tournament_schedule(db, tid)


def auth_user_for_teacher(db, teacher_id):
    return dict(
        db.execute(
            "SELECT u.* FROM users u JOIN teacher_user_links l ON l.user_id=u.id WHERE l.teacher_id=?",
            (teacher_id,),
        ).fetchone()
    )


def calendar_data(db, request):
    tournaments = {
        t["id"]: t
        for t in core.rows(db, "SELECT * FROM tournaments WHERE archived_at IS NULL")
        if visible(db, request, t)
    }
    teams = {
        t["id"]: t
        for t in core.rows(db, "SELECT * FROM teams WHERE archived=0")
        if t["tournament_id"] in tournaments
    }
    stages = {s["id"]: s for s in core.rows(db, "SELECT * FROM stages")}
    groups = {g["id"]: g["name"] for g in core.rows(db, "SELECT * FROM groups")}
    events = []
    for game in core.rows(db, "SELECT * FROM matches ORDER BY scheduled_at,id"):
        if game["tournament_id"] not in tournaments or game["is_bye"]:
            continue
        t = tournaments[game["tournament_id"]]
        events.append(
            {
                "id": f"{t['id']}-{game['id']}",
                "tournament_id": t["id"],
                "tournament_name": t["name"],
                "match_id": game["id"],
                "home": teams.get(game["home_team_id"], {}).get("name", "Da definire"),
                "away": teams.get(game["away_team_id"], {}).get("name", "Da definire"),
                "home_team_id": game["home_team_id"],
                "away_team_id": game["away_team_id"],
                "round_no": game["round_no"],
                "kind": stages[game["stage_id"]]["kind"],
                "scheduled_at": game["scheduled_at"],
                "field": game["location"] or "",
                "location": game["location"],
                "field_id": game["field_id"],
                "duration": game["duration"],
                "status": services.match_status(game),
                "score": (
                    {"home": game["home_score"], "away": game["away_score"]}
                    if game["home_score"] is not None
                    else None
                ),
                "group": groups.get(game["group_id"]),
                "teacher_id": t["teacher_id"],
            }
        )
    conflicts = []
    # Parse once and sort actual instants, not ISO strings with different offsets.
    scheduled = sorted(
        ((datetime.fromisoformat(e["scheduled_at"]), index, e)
         for index, e in enumerate(events) if e["scheduled_at"]),
        key=lambda item: (item[0], item[1]),
    )
    for index, (start, original_index, a) in enumerate(scheduled):
        end = start + timedelta(minutes=a["duration"])
        for other_index in range(index + 1, len(scheduled)):
            other, original_other, b = scheduled[other_index]
            if other >= end:
                break
            same_field = (
                a["field_id"] is not None and a["field_id"] == b["field_id"]
            ) or (
                bool(a["field"])
                and a["field"].casefold() == b["field"].casefold()
                and a["teacher_id"] == b["teacher_id"]
            )
            shared = ({a["home_team_id"], a["away_team_id"]} - {None}) & {
                b["home_team_id"],
                b["away_team_id"],
            }
            kind = (
                "field"
                if same_field
                else (
                    "team"
                    if shared
                    else (
                        "teacher"
                        if a["teacher_id"] and a["teacher_id"] == b["teacher_id"]
                        else None
                    )
                )
            )
            if kind:
                # Preserve the existing pair orientation/order for API consumers.
                first, second = (a, b) if original_index < original_other else (b, a)
                conflicts.append(
                    {
                        "kind": kind,
                        "match_id": first["match_id"],
                        "other_match_id": second["match_id"],
                        "message": {
                            "field": "Campo occupato due volte",
                            "team": "Squadra in doppio impegno",
                            "teacher": "Tornei dello stesso docente contemporanei",
                        }[kind],
                    }
                )
    positions = {e["match_id"]: i for i, e in enumerate(events)}
    conflicts.sort(key=lambda c: (positions[c["match_id"]], positions[c["other_match_id"]]))
    for event in events:
        event.pop("teacher_id", None)
    return {
        "events": events,
        "tournaments": [
            {"id": t["id"], "name": t["name"]} for t in tournaments.values()
        ],
        "teams": [
            {"id": t["id"], "name": t["name"], "tournament_id": t["tournament_id"]}
            for t in teams.values()
        ],
        "fields": sorted({e["field"] for e in events if e["field"]}),
        "conflicts": conflicts,
    }


def create_router(path):
    router = APIRouter(prefix="/api", tags=["Team B integration"])

    def context(request: Request):
        user = getattr(request.state, "platform_user", None)
        if not user:
            auth.fail(401, "authentication_required", "Accesso richiesto")
        with database(path, request.method not in ("GET", "HEAD")) as db:
            if request.method not in ("GET", "HEAD"):
                auth.csrf(request, auth.session(db, request))
            yield db, user

    @router.patch("/tournaments/{tid}/teams/order")
    def order(tid: int, data: Order, ctx=Depends(context)):
        value = domain.reorder(
            *ctx,
            tid,
            schema.OrderInput(ordered_team_ids=data.team_ids, version=data.version),
        )
        return {
            "ok": True,
            "team_ids": value["ordered_team_ids"],
            "version": value["version"],
        }

    @router.get("/tournaments/{tid}/proposals")
    def proposals(tid: int, status: str = "pending", ctx=Depends(context)):
        db, user = ctx
        t = auth.access(db, user, tid)
        items = core.rows(
            db,
            "SELECT * FROM result_proposals WHERE tournament_id=? AND status=? ORDER BY id",
            (tid, status),
        )
        if not auth.manages(db, user, t):
            items = [p for p in items if p["submitted_by"] == user["id"]]
        return {"proposals": [proposal_row(db, p) for p in items]}

    @router.post("/tournaments/{tid}/matches/{mid}/proposals", status_code=201)
    def propose(tid: int, mid: int, data: ResultInput, ctx=Depends(context)):
        return results.propose(
            *ctx,
            tid,
            mid,
            schema.ProposalInput(match_version=data.version, score=score_input(data)),
        )

    @router.patch("/proposals/{pid}")
    def review(pid: int, data: Review, ctx=Depends(context)):
        db, user = ctx
        p = db.execute("SELECT * FROM result_proposals WHERE id=?", (pid,)).fetchone()
        if not p or p["match_id"] is None:
            auth.fail(404, "not_found", "Proposta non trovata")
        value = schema.ProposalReview(
            decision=data.action,
            proposal_version=data.version,
            match_version=data.match_version,
            invalidate=data.invalidate,
            score=score_input(data) if data.action == "correct" else None,
            reason=data.reason
            or (
                "Respinta dal professore"
                if data.action == "reject"
                else "Revisione del professore"
            ),
        )
        return results.review(db, user, p["tournament_id"], p["match_id"], pid, value)

    @router.get("/invites/{token}")
    def invitation(token: str, request: Request):
        auth.rate_limit(path, request, "invite-preview", 60)
        with database(path) as db:
            item = resources.find_invite(db, token, allow_exhausted=True)
            t = core.required(db, item["tournament_id"])
            team = (
                domain.get_team(db, t["id"], item["team_id"])
                if item["team_id"]
                else None
            )
            user = getattr(request.state, "platform_user", None)
            membership = (
                db.execute(
                    "SELECT status FROM enrollments WHERE tournament_id=? AND user_id=?",
                    (t["id"], user["id"]),
                ).fetchone()
                if user
                else None
            )
            count = (
                db.execute(
                    "SELECT count(*) FROM students WHERE team_id=?", (team["id"],)
                ).fetchone()[0]
                if team
                else 0
            )
            variant = services._variant_for_tournament(db, t)
            caps = [
                n
                for n in (
                    (team["max_members"] if team else None),
                    (variant.max_roster if variant and team else None),
                )
                if n is not None
            ]
            slots = max(0, min(caps) - count) if caps else None
            state = (
                (
                    "accepted"
                    if membership and membership["status"] == "approved"
                    else membership["status"]
                )
                if membership
                else (
                    "full"
                    if slots == 0 or item["used"] >= item["max_uses"]
                    else "active"
                )
            )
            return {
                "status": state,
                "kind": "team" if team else "tournament",
                "tournament": {
                    k: t[k]
                    for k in (
                        "id",
                        "name",
                        "sport",
                        "variant",
                        "format",
                        "participant_kind",
                    )
                },
                "team": {"name": team["name"]} if team else None,
                "available_slots": slots,
                "requires_approval": bool(item["require_approval"]),
            }

    @router.post("/invites/{token}/join")
    def join(token: str, ctx=Depends(context)):
        db, user = ctx
        item = resources.find_invite(db, token, allow_exhausted=True)
        enrolled = db.execute(
            "SELECT 1 FROM enrollments WHERE tournament_id=? AND user_id=?",
            (item["tournament_id"], user["id"]),
        ).fetchone()
        if not enrolled and item["used"] >= item["max_uses"]:
            auth.fail(409, "invite_full", "Invito esaurito")
        value = resources.accept_invite(*ctx, token)
        return {
            "status": "accepted" if value["status"] == "approved" else value["status"],
            "message": "Adesione registrata",
        }

    @router.post("/tournaments/{tid}/invites", status_code=201)
    def invite(
        tid: int, data: schema.InviteInput, request: Request, ctx=Depends(context)
    ):
        result = resources.create_invite(
            *ctx, tid, data, str(request.base_url).rstrip("/")
        )
        result["url"] = str(request.base_url).rstrip("/") + "/#/join/" + result["token"]
        return result

    @router.get("/fields")
    def fields(ctx=Depends(context)):
        db, user = ctx
        auth.teacher(user)
        return {
            "fields": [
                field_row(db, f)
                for f in core.rows(
                    db,
                    "SELECT * FROM fields WHERE owner_id=? ORDER BY id",
                    (user["id"],),
                )
            ]
        }

    def save_field(db, user, data, fid=None):
        auth.teacher(user)
        if fid is not None:
            current = resources.owned(db, "fields", user, fid)
            if data.version is None:
                auth.fail(422, "version_required", "Inviare la versione del campo")
            auth.version(current, data.version)
        if any(
            r["id"] != fid and r["name"].casefold() == data.name.casefold()
            for r in core.rows(
                db, "SELECT id,name FROM fields WHERE owner_id=?", (user["id"],)
            )
        ):
            auth.fail(409, "duplicate_field", "Nome campo già presente")
        known = {r["name"] for r in db.execute("SELECT name FROM sport_configs")}
        if not set(data.sports) <= known:
            auth.fail(422, "invalid_sports", "Sport non supportato")
        variants = [
            r["slug"]
            for r in db.execute(
                "SELECT v.slug,s.name FROM sport_variants v JOIN sport_configs s ON s.id=v.sport_id"
            )
            if r["name"] in data.sports
        ]
        from identity_bridge import VARIANT_SLUGS

        variants += [key for key, value in VARIANT_SLUGS.items() if value in variants]
        venue = None
        if data.venue.strip():
            row = db.execute(
                "SELECT id FROM venues WHERE owner_id=? AND name=?",
                (user["id"], data.venue.strip()),
            ).fetchone()
            venue = (
                row[0]
                if row
                else db.execute(
                    "INSERT INTO venues(owner_id,organization_id,name) VALUES (?,?,?)",
                    (user["id"], user["organization_id"], data.venue.strip()),
                ).lastrowid
            )
        if fid is not None and set(data.sports) == set(
            field_row(db, current)["sports"]
        ):
            variants = json.loads(current["variants_json"])
        availability = data.availability_intervals
        if fid is not None and "availability_intervals" not in data.model_fields_set:
            availability = json.loads(current["availability_json"])
        value = schema.FieldInput(
            name=data.name,
            venue_id=venue,
            sport_variant_ids=variants,
            availability=availability,
        )
        if fid is None:
            fid = resources.create_field(db, user, value)["id"]
        else:
            if current["archived"]:
                db.execute("UPDATE fields SET archived=0 WHERE id=?", (fid,))
            resources.edit_field(
                db,
                user,
                fid,
                schema.FieldEdit(**value.model_dump(), version=data.version),
            )
        db.execute(
            "UPDATE fields SET description=?,availability_note=?,archived=? WHERE id=?",
            (data.description, data.availability, int(not data.active), fid),
        )
        db.execute(
            "INSERT INTO administrative_audit(actor_id,action,resource_id) VALUES (?,?,?)",
            (user["id"], "field_saved", fid),
        )
        return field_row(db, resources.owned(db, "fields", user, fid))

    @router.post("/fields", status_code=201)
    def add_field(data: FieldInput, ctx=Depends(context)):
        return save_field(*ctx, data)

    @router.patch("/fields/{fid}")
    def edit_field(fid: int, data: FieldInput, ctx=Depends(context)):
        return save_field(*ctx, data, fid)

    @router.delete("/fields/{fid}", status_code=204)
    def deactivate_field(fid: int, data: schema.VersionInput, ctx=Depends(context)):
        db, user = ctx
        auth.teacher(user)
        auth.version(resources.owned(db, "fields", user, fid), data.version)
        db.execute("UPDATE fields SET archived=1,version=version+1 WHERE id=?", (fid,))
        db.execute(
            "INSERT INTO administrative_audit(actor_id,action,resource_id) VALUES (?,'field_archived',?)",
            (user["id"], fid),
        )
        return Response(status_code=204)

    @router.get("/calendar")
    def calendar(
        request: Request,
        tournament: int | None = None,
        team: int | None = None,
        day: str | None = None,
        field: str | None = None,
        status: str | None = None,
    ):
        with database(path) as db:
            value = calendar_data(db, request)
        if day:
            try:
                date.fromisoformat(day)
            except ValueError:
                auth.fail(422, "invalid_day", "Giorno non valido")
        from zoneinfo import ZoneInfo

        value["events"] = [
            e
            for e in value["events"]
            if (tournament is None or e["tournament_id"] == tournament)
            and (team is None or team in (e["home_team_id"], e["away_team_id"]))
            and (not field or field == e["field"] or field == str(e["field_id"]))
            and (
                not day
                or (
                    e["scheduled_at"]
                    and datetime.fromisoformat(e["scheduled_at"])
                    .astimezone(ZoneInfo("Europe/Rome"))
                    .date()
                    .isoformat()
                    == day
                )
            )
            and (
                not status
                or status == "all"
                or e["status"] == status
                or (status == "played" and e["status"] == "completed")
                or (
                    status == "to-play"
                    and e["scheduled_at"]
                    and e["status"] != "completed"
                )
                or (status == "pending" and e["status"] != "completed")
                or (
                    status == "unscheduled"
                    and not e["scheduled_at"]
                    and e["status"] != "completed"
                )
            )
        ]
        ids = {e["match_id"] for e in value["events"]}
        value["conflicts"] = [
            c
            for c in value["conflicts"]
            if c["match_id"] in ids or c["other_match_id"] in ids
        ]
        return value

    @router.get("/dashboard")
    def dashboard(request: Request, mine: bool = True, ctx=Depends(context)):
        db, user = ctx
        value = calendar_data(db, request)
        ids = {
            t["id"]
            for t in core.rows(db, "SELECT * FROM tournaments")
            if auth.manages(db, user, t)
        }
        if user["role"] == "student":
            ids = {
                s[0]
                for s in db.execute(
                    "SELECT tournament_id FROM students WHERE user_id=?", (user["id"],)
                )
            }
        events = [
            e
            for e in value["events"]
            if e["tournament_id"] in ids
            and e["status"] == "ready"
            and (
                not e["scheduled_at"]
                or datetime.fromisoformat(e["scheduled_at"]) >= auth.now()
            )
        ]
        events.sort(key=lambda e: e["scheduled_at"] or "9999")
        return {
            "upcoming": events,
            "pending_proposals": sum(
                1
                for p in core.rows(
                    db,
                    "SELECT tournament_id FROM result_proposals WHERE status='pending' AND match_id IS NOT NULL",
                )
                if p["tournament_id"] in ids
            ),
            "student_count": sum(
                1
                for s in core.rows(db, "SELECT tournament_id FROM students")
                if s["tournament_id"] in ids
            ),
            "conflicts": [
                c
                for c in value["conflicts"]
                if any(
                    e["match_id"] == c["match_id"] and e["tournament_id"] in ids
                    for e in events
                )
            ],
        }

    @router.get("/tournaments/{tid}/students")
    def students(tid: int, ctx=Depends(context)):
        db, user = ctx
        auth.access(db, user, tid, True)
        items = core.rows(
            db, "SELECT * FROM students WHERE tournament_id=? ORDER BY id", (tid,)
        )
        return {
            "students": items,
            "unassigned": [s for s in items if s["team_id"] is None],
        }

    @router.patch("/tournaments/{tid}/students/{sid}/team")
    def assign(tid: int, sid: int, data: schema.TeamAssignment, ctx=Depends(context)):
        return domain.assign_student(*ctx, tid, sid, data)

    @router.patch("/tournaments/{tid}/students/{sid}")
    def link_student(tid: int, sid: int, data: LinkStudent, ctx=Depends(context)):
        db, user = ctx
        auth.access(db, user, tid, True)
        student = db.execute(
            "SELECT * FROM students WHERE id=? AND tournament_id=?", (sid, tid)
        ).fetchone()
        if not student:
            auth.fail(404, "not_found", "Studente non trovato")
        auth.version(student, data.version)
        domain.student_user(db, data.user_id)
        if student["user_id"] not in (None, data.user_id):
            auth.fail(
                409,
                "student_already_linked",
                "Profilo già associato: serve amministrazione locale",
            )
        if db.execute(
            "SELECT 1 FROM students WHERE tournament_id=? AND user_id=? AND id!=?",
            (tid, data.user_id, sid),
        ).fetchone():
            auth.fail(409, "already_enrolled", "Account già associato")
        db.execute(
            "UPDATE students SET user_id=?,version=version+1 WHERE id=?",
            (data.user_id, sid),
        )
        domain.audit(
            db,
            user,
            tid,
            "student_account_linked",
            {"student_id": sid, "user_id": data.user_id},
        )
        return dict(db.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone())

    @router.put("/tournaments/{tid}/matches/{mid}/performances")
    def performances(tid: int, mid: int, data: Performances, ctx=Depends(context)):
        db, user = ctx
        t = auth.access(db, user, tid, True)
        game = results.match(db, tid, mid, data.version)
        if (
            game["home_score"] is None
            or services._rules(t).get("scoring_mode") == "sets"
        ):
            auth.fail(
                409,
                "official_points_required",
                "Servono punti ufficiali di una partita giocata a punteggio numerico",
            )
        if game["score_json"] and json.loads(game["score_json"])["type"] == "forfeit":
            auth.fail(409, "unplayed_match", "Un tavolino non ha marcatori")
        if len({p.player_id for p in data.players}) != len(data.players):
            auth.fail(422, "duplicate_player", "Giocatore duplicato")
        sums = {game["home_team_id"]: 0, game["away_team_id"]: 0}
        for p in data.players:
            player = db.execute(
                "SELECT * FROM team_players WHERE id=?", (p.player_id,)
            ).fetchone()
            if not player or player["team_id"] not in sums:
                auth.fail(404, "not_found", "Giocatore non appartenente alla partita")
            sums[player["team_id"]] += p.points
        if (
            sums[game["home_team_id"]] > game["home_score"]
            or sums[game["away_team_id"]] > game["away_score"]
        ):
            auth.fail(
                422,
                "points_exceed_result",
                "Punti individuali superiori al risultato ufficiale",
            )
        db.execute("DELETE FROM player_performances WHERE match_id=?", (mid,))
        db.executemany(
            "INSERT INTO player_performances VALUES (?,?,?)",
            [(mid, p.player_id, p.points) for p in data.players],
        )
        db.execute("UPDATE matches SET version=version+1 WHERE id=?", (mid,))
        domain.audit(
            db,
            user,
            tid,
            "player_performances_saved",
            {"match_id": mid, "players": [p.model_dump() for p in data.players]},
        )
        return {"ok": True, "version": data.version + 1}

    @router.get("/tournaments/{tid}/player-statistics")
    def player_statistics(tid: int, ctx=Depends(context)):
        db, user = ctx
        t = auth.access(db, user, tid)
        items = core.rows(
            db,
            "SELECT p.id AS player_id,p.name,p.team_id,sum(x.points) AS points,count(*) AS matches "
            "FROM player_performances x JOIN team_players p ON p.id=x.player_id JOIN matches m ON m.id=x.match_id "
            "JOIN teams team ON team.id=p.team_id LEFT JOIN students s ON s.id=p.student_id "
            "WHERE m.tournament_id=? AND team.tournament_id=? AND m.home_score IS NOT NULL AND (? OR s.user_id=?) "
            "GROUP BY p.id ORDER BY points DESC,p.id",
            (tid, tid, int(bool(auth.manages(db, user, t))), user["id"]),
        )
        return {"players": items, "source": "teacher-recorded-official-matches"}

    @router.post("/tournaments/{tid}/teams/{team_id}/players/import", status_code=201)
    def import_players(tid: int, team_id: int, data: Bulk, ctx=Depends(context)):
        db, user = ctx
        auth.access(db, user, tid, True)
        domain.get_team(db, tid, team_id)
        rows = data.rows
        if (rows is None) == (data.csv is None):
            auth.fail(422, "invalid_import", "Inviare rows oppure csv")
        errors = []
        parsed = []
        if data.csv is not None:
            reader = csv.DictReader(io.StringIO(data.csv.lstrip("\ufeff")))
            if not reader.fieldnames or not ({"nome", "name"} & set(reader.fieldnames)):
                auth.fail(
                    422,
                    "invalid_import",
                    "CSV con intestazione nome oppure name richiesta",
                )
            raw = list(reader)
            if len(raw) > 1000:
                auth.fail(422, "import_limit", "Massimo 1000 righe")
            from pydantic import ValidationError

            for index, row in enumerate(raw, 2):
                try:
                    number = row.get("numero", row.get("shirt_number"))
                    parsed.append(
                        PlayerInput(
                            name=row.get("nome", row.get("name", "")),
                            shirt_number=int(number)
                            if number and number.strip()
                            else None,
                        )
                    )
                except (ValueError, ValidationError):
                    errors.append({"row": index, "message": "Nome o numero non valido"})
        else:
            parsed = rows
        seen = {
            p["display_name"].casefold()
            for p in core.rows(
                db, "SELECT display_name FROM students WHERE tournament_id=?", (tid,)
            )
        }
        for index, row in enumerate(parsed, 1):
            if row.name.casefold() in seen:
                errors.append({"row": index, "message": "Nome duplicato"})
            seen.add(row.name.casefold())
        variant = services._variant_for_tournament(db, core.required(db, tid))
        if not variant:
            auth.fail(409, "rules_required", "Assegnare una variante sportiva")
        maximum = variant.max_roster
        count = db.execute(
            "SELECT count(*) FROM team_players WHERE team_id=?", (team_id,)
        ).fetchone()[0]
        if count + len(parsed) > maximum:
            errors.append({"row": None, "message": "Capienza rosa superata"})
        if errors:
            auth.fail(
                422,
                "invalid_import",
                "Import annullato: nessuna riga salvata",
                errors=errors,
            )
        created = [services.add_player(db, tid, team_id, row) for row in parsed]
        return {"created": len(created), "players": created, "errors": []}

    @router.post("/teachers/{teacher_id}/deactivate")
    def deactivate(teacher_id: int, ctx=Depends(context)):
        db, user = ctx
        auth.teacher(user)
        linked = db.execute(
            "SELECT teacher_id FROM teacher_user_links WHERE user_id=?", (user["id"],)
        ).fetchone()[0]
        if teacher_id != linked:
            auth.fail(
                403,
                "self_only",
                "Puoi disattivare solo il tuo account; per altri serve amministrazione locale",
            )
        db.execute("UPDATE teachers SET active=0 WHERE id=?", (teacher_id,))
        db.execute("DELETE FROM sessions WHERE user_id=?", (user["id"],))
        db.execute(
            "INSERT INTO administrative_audit(actor_id,action,resource_id) VALUES (?,'teacher_deactivated',?)",
            (user["id"], teacher_id),
        )
        return {"active": False}

    return router
