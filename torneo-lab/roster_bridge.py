"""One student membership shared by the V1 archive and the Team B roster."""

from fastapi import HTTPException


def link_player(db, player_id, tid):
    p = db.execute("SELECT * FROM team_players WHERE id=?", (player_id,)).fetchone()
    if p["student_id"] is not None:
        return p["student_id"]
    existing = [
        s
        for s in db.execute("SELECT * FROM students WHERE tournament_id=?", (tid,))
        if s["display_name"].casefold() == p["name"].casefold()
    ]
    if existing:
        s = existing[0]
        if s["team_id"] is not None and s["team_id"] != p["team_id"]:
            raise HTTPException(
                409, "Studente già assegnato: usare lo spostamento atomico"
            )
        sid = s["id"]
        db.execute(
            "UPDATE students SET team_id=?,version=version+1 WHERE id=?",
            (p["team_id"], sid),
        )
    else:
        sid = db.execute(
            "INSERT INTO students(tournament_id,display_name,team_id) VALUES (?,?,?)",
            (tid, p["name"], p["team_id"]),
        ).lastrowid
    db.execute("UPDATE team_players SET student_id=? WHERE id=?", (sid, player_id))
    return sid


def sync_student(db, sid):
    import services

    s = db.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
    player = db.execute(
        "SELECT * FROM team_players WHERE student_id=?", (sid,)
    ).fetchone()
    if s["team_id"] is None:
        if player:
            db.execute("DELETE FROM team_players WHERE id=?", (player["id"],))
        return
    t = services.required(db, s["tournament_id"])
    variant = services._variant_for_tournament(db, t)
    maximum = variant.max_roster if variant else 30
    count = db.execute(
        "SELECT count(*) FROM team_players WHERE team_id=? AND id!=?",
        (s["team_id"], player["id"] if player else -1),
    ).fetchone()[0]
    if count >= maximum:
        raise HTTPException(409, "Capienza rosa superata")
    if player:
        db.execute(
            "UPDATE team_players SET team_id=?,name=? WHERE id=?",
            (s["team_id"], s["display_name"], player["id"]),
        )
    else:
        db.execute(
            "INSERT INTO team_players(team_id,name,student_id) VALUES (?,?,?)",
            (s["team_id"], s["display_name"], sid),
        )
