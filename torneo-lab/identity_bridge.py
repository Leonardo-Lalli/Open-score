"""Explicit mapping between the two historical account IDs and variant namespaces."""

import json
import secrets

VARIANT_SLUGS = {
    "football-11": "calcio-a-11",
    "football-7": "calcio-a-7",
    "football-5": "calcio-a-5",
    "basketball": "basket-5v5",
    "volleyball-indoor": "pallavolo-6v6",
}


def ensure_platform_teacher(db, teacher):
    link = db.execute(
        "SELECT user_id FROM teacher_user_links WHERE teacher_id=?", (teacher["id"],)
    ).fetchone()
    if link:
        return dict(db.execute("SELECT * FROM users WHERE id=?", (link[0],)).fetchone())
    user = db.execute(
        "SELECT * FROM users WHERE email=?", (teacher["email"].casefold(),)
    ).fetchone()
    if user and user["role"] != "teacher":
        raise ValueError(
            "Email docente già usata da uno studente: serve riconciliazione amministrativa"
        )
    if user:
        uid = user["id"]
    else:
        oid = db.execute(
            "INSERT INTO organizations(name) VALUES (?)",
            ("Contesto " + teacher["display_name"],),
        ).lastrowid
        uid = db.execute(
            "INSERT INTO users(email,display_name,password_hash,role,organization_id) VALUES (?,?,?,'teacher',?)",
            (
                teacher["email"].casefold(),
                teacher["display_name"] or "Docente",
                teacher["password_hash"],
                oid,
            ),
        ).lastrowid
    db.execute("INSERT INTO teacher_user_links VALUES (?,?)", (teacher["id"], uid))
    return dict(db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone())


def ensure_legacy_teacher(db, user):
    link = db.execute(
        "SELECT teacher_id FROM teacher_user_links WHERE user_id=?", (user["id"],)
    ).fetchone()
    if link:
        return link[0]
    teacher = db.execute(
        "SELECT * FROM teachers WHERE email=? COLLATE NOCASE", (user["email"],)
    ).fetchone()
    if not teacher:
        tid = db.execute(
            "INSERT INTO teachers(email,password_hash,display_name) VALUES (?,?,?)",
            (user["email"], user["password_hash"], user["display_name"]),
        ).lastrowid
    else:
        tid = teacher["id"]
    db.execute("INSERT INTO teacher_user_links VALUES (?,?)", (tid, user["id"]))
    return tid


def attach_tournament(db, tid, teacher_id):
    teacher = db.execute("SELECT * FROM teachers WHERE id=?", (teacher_id,)).fetchone()
    user = ensure_platform_teacher(db, teacher)
    db.execute(
        "UPDATE tournaments SET owner_id=?,organization_id=?,public_slug=COALESCE(public_slug,?) WHERE id=?",
        (user["id"], user["organization_id"], secrets.token_urlsafe(12), tid),
    )
    db.execute("UPDATE teams SET display_order=id WHERE tournament_id=?", (tid,))
    return user


def sync_platform_tournament(db, tid):
    t = dict(db.execute("SELECT * FROM tournaments WHERE id=?", (tid,)).fetchone())
    if not t["owner_id"]:
        return
    user = dict(
        db.execute("SELECT * FROM users WHERE id=?", (t["owner_id"],)).fetchone()
    )
    teacher_id = ensure_legacy_teacher(db, user)
    slug = VARIANT_SLUGS.get(t["platform_variant_id"])
    variant = db.execute(
        "SELECT * FROM sport_variants WHERE slug=?", (slug,)
    ).fetchone()
    if not variant:
        db.execute("UPDATE tournaments SET teacher_id=? WHERE id=?", (teacher_id, tid))
        return
    sport = db.execute(
        "SELECT name FROM sport_configs WHERE id=?", (variant["sport_id"],)
    ).fetchone()[0]
    config = json.loads(t["rules_json"] or "{}")
    snapshot = json.loads(variant["rules"])
    if config:
        snapshot["match_duration"] = config["duration"]
        if "best_of" in config:
            snapshot.update(
                sets_to_win=config["best_of"] // 2 + 1,
                max_sets=config["best_of"],
                points_per_set=config["target"],
                tiebreak_points=config["deciding_target"],
            )
        else:
            snapshot["draw_allowed"] = config["allow_draw"]
    db.execute(
        "UPDATE tournaments SET teacher_id=?,sport=?,sport_id=?,variant_id=?,variant=?,rules_snapshot=?,regulation_snapshot=?,scoring_system=? WHERE id=?",
        (
            teacher_id,
            sport,
            variant["sport_id"],
            variant["id"],
            slug,
            json.dumps(snapshot),
            variant["regulation"],
            "sets" if snapshot["scoring_mode"] == "sets" else "points",
            tid,
        ),
    )


def migrate_identities(db):
    for teacher in db.execute("SELECT * FROM teachers").fetchall():
        ensure_platform_teacher(db, teacher)
    for user in db.execute("SELECT * FROM users WHERE role='teacher'").fetchall():
        ensure_legacy_teacher(db, user)
    for t in db.execute("SELECT * FROM tournaments").fetchall():
        if t["owner_id"]:
            sync_platform_tournament(db, t["id"])
        elif t["teacher_id"]:
            attach_tournament(db, t["id"], t["teacher_id"])
    # Preserve historical roster names even if two old teams used an alias alike.
    for player in db.execute(
        "SELECT p.*,t.tournament_id FROM team_players p JOIN teams t ON t.id=p.team_id WHERE p.student_id IS NULL"
    ).fetchall():
        sid = db.execute(
            "INSERT INTO students(tournament_id,display_name,team_id) VALUES (?,?,?)",
            (player["tournament_id"], player["name"], player["team_id"]),
        ).lastrowid
        db.execute(
            "UPDATE team_players SET student_id=? WHERE id=?", (sid, player["id"])
        )
