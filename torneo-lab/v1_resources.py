"""Enrollment, invite and shared field scheduling transactions."""
import json
import secrets
from datetime import datetime, timedelta, timezone

import platform_auth as auth
import platform_services as svc
import sports
from platform_auth import fail, version
from v1_domain import audit, capacity, get_team, student_user
from v1_results import match


def enroll(db, user, tid, team_id=None, invite=None, team_version=None):
    if user['role'] != 'student':
        fail(403, 'student_required', 'Iscrizione riservata agli studenti')
    t = svc.required(db, tid)
    if invite is None and not t['published']:
        fail(404, 'not_found', 'Torneo non disponibile per iscrizione diretta')
    auth.require_active(t)
    existing = db.execute('SELECT * FROM enrollments WHERE tournament_id=? AND user_id=?', (tid, user['id'])).fetchone()
    if existing:
        if invite is not None and existing['invite_id'] == invite['id'] and existing['status'] != 'rejected':
            return dict(existing)
        fail(409, 'already_enrolled', 'Iscrizione o richiesta già presente')
    if db.execute('SELECT 1 FROM students WHERE tournament_id=? AND user_id=?', (tid, user['id'])).fetchone():
        fail(409, 'already_enrolled', 'Studente già iscritto')
    if team_id is not None:
        team = capacity(db, tid, team_id)
        if invite is None:
            if team_version is None:
                fail(422, 'team_version_required', 'Inviare la versione della squadra')
            version(team, team_version)
    status = 'pending' if invite is None or invite['require_approval'] else 'approved'
    ident = db.execute('INSERT INTO enrollments(tournament_id,user_id,team_id,invite_id,status) VALUES (?,?,?,?,?)',
                       (tid, user['id'], team_id, invite['id'] if invite else None, status)).lastrowid
    if invite is not None:
        db.execute('UPDATE invites SET used=used+1,version=version+1 WHERE id=?', (invite['id'],))
    if status == 'approved':
        create_member(db, user, tid, team_id)
    audit(db, user, tid, 'enrollment_created', {'enrollment_id': ident, 'status': status})
    return dict(db.execute('SELECT * FROM enrollments WHERE id=?', (ident,)).fetchone())


def create_member(db, user, tid, team_id):
    if team_id is not None:
        capacity(db, tid, team_id)
    if any(s['display_name'].casefold() == user['display_name'].casefold()
           for s in svc.rows(db, 'SELECT display_name FROM students WHERE tournament_id=?', (tid,))):
        fail(409, 'duplicate_student', 'Alias già presente; il professore deve associare lo studente')
    sid=db.execute('INSERT INTO students(tournament_id,user_id,display_name,team_id) VALUES (?,?,?,?)',
               (tid, user['id'], user['display_name'], team_id)).lastrowid
    from roster_bridge import sync_student
    sync_student(db,sid)


def review_enrollment(db, user, tid, eid, data):
    auth.access(db, user, tid, True)
    item = db.execute('SELECT * FROM enrollments WHERE id=? AND tournament_id=?', (eid, tid)).fetchone()
    if not item:
        fail(404, 'not_found', 'Richiesta non trovata')
    version(item, data.version)
    if item['status'] != 'pending':
        fail(409, 'already_reviewed', 'Richiesta già revisionata')
    if data.decision == 'approve':
        if db.execute('SELECT 1 FROM students WHERE tournament_id=? AND user_id=?', (tid, item['user_id'])).fetchone():
            fail(409, 'already_enrolled', 'Studente già associato dal professore')
        create_member(db, student_user(db, item['user_id']), tid, item['team_id'])
    elif item['invite_id']:
        db.execute('UPDATE invites SET used=max(0,used-1),version=version+1 WHERE id=? AND revoked=0 AND expires_at>?',
                   (item['invite_id'], auth.now().isoformat()))
    db.execute('UPDATE enrollments SET status=?,reason=?,version=version+1 WHERE id=?',
               ('approved' if data.decision == 'approve' else 'rejected', data.reason, eid))
    audit(db, user, tid, 'enrollment_reviewed', {'enrollment_id': eid, 'decision': data.decision, 'reason': data.reason})
    return dict(db.execute('SELECT * FROM enrollments WHERE id=?', (eid,)).fetchone())


def invite_dto(item):
    result = dict(item)
    result.pop('token_hash', None)
    result['revoked'] = bool(result['revoked'])
    result['require_approval'] = bool(result['require_approval'])
    return result


def create_invite(db, user, tid, data, origin):
    auth.access(db, user, tid, True)
    expiry = data.expires_at.astimezone(timezone.utc)
    if expiry <= auth.now() or expiry > auth.now()+timedelta(days=90):
        fail(422, 'invalid_expiry', 'Scadenza richiesta entro 90 giorni e nel futuro')
    if data.team_id is not None:
        get_team(db, tid, data.team_id)
    token = secrets.token_urlsafe(32)
    ident = db.execute('INSERT INTO invites(tournament_id,team_id,token_hash,expires_at,max_uses,require_approval) VALUES (?,?,?,?,?,?)',
            (tid, data.team_id, auth.digest(token), expiry.isoformat(), data.max_uses, int(data.require_approval))).lastrowid
    audit(db, user, tid, 'invite_created', {'invite_id': ident})
    return dict(invite_dto(db.execute('SELECT * FROM invites WHERE id=?', (ident,)).fetchone()),
                token=token, url=origin.rstrip('/')+'/#/join/'+token)


def find_invite(db, token, allow_exhausted=False):
    invite = db.execute('SELECT * FROM invites WHERE token_hash=?', (auth.digest(token),)).fetchone()
    if not invite:
        fail(404, 'not_found', 'Invito non trovato')
    if invite['revoked'] or datetime.fromisoformat(invite['expires_at']) <= auth.now() or (
            not allow_exhausted and invite['used'] >= invite['max_uses']):
        fail(410, 'invite_unavailable', 'Invito scaduto, revocato o esaurito')
    if invite['team_id'] is not None:
        get_team(db, invite['tournament_id'], invite['team_id'])
    return dict(invite)


def accept_invite(db, user, token):
    # Idempotent retry of an existing acceptance doesn't consume another use.
    invite = find_invite(db, token, allow_exhausted=True)
    existing = db.execute('SELECT * FROM enrollments WHERE tournament_id=? AND user_id=? AND invite_id=?',
                          (invite['tournament_id'], user['id'], invite['id'])).fetchone()
    if existing and existing['status'] != 'rejected':
        return dict(existing)
    if invite['used'] >= invite['max_uses']:
        fail(410, 'invite_unavailable', 'Invito esaurito')
    return enroll(db, user, invite['tournament_id'], invite['team_id'], invite)


def owned(db, table, user, ident):
    if table not in ('fields', 'venues'):
        raise ValueError('Invalid resource table')
    item = db.execute(f'SELECT * FROM {table} WHERE id=? AND owner_id=?', (ident, user['id'])).fetchone()
    if not item:
        fail(404, 'not_found', 'Risorsa non trovata')
    return dict(item)


def field_dto(item):
    item = dict(item)
    item['sport_variant_ids'] = json.loads(item.pop('variants_json'))
    item['availability'] = json.loads(item.pop('availability_json'))
    item['archived'] = bool(item['archived'])
    return item


def field_values(db, user, data):
    if data.venue_id is not None:
        owned(db, 'venues', user, data.venue_id)
    known=set(sports.VARIANTS) | {r[0] for r in db.execute('SELECT slug FROM sport_variants')}
    if len(set(data.sport_variant_ids)) != len(data.sport_variant_ids) or any(v not in known for v in data.sport_variant_ids):
        fail(422, 'invalid_variant', 'Varianti sconosciute o duplicate')
    slots = [{'starts_at': i.starts_at.astimezone(timezone.utc).isoformat(),
                  'ends_at': i.ends_at.astimezone(timezone.utc).isoformat()} for i in data.availability]
    return (data.name, data.venue_id, json.dumps(data.sport_variant_ids), json.dumps(slots))


def create_field(db, user, data):
    auth.teacher(user)
    values = field_values(db, user, data)
    ident = db.execute('INSERT INTO fields(owner_id,organization_id,name,venue_id,variants_json,availability_json) VALUES (?,?,?,?,?,?)',
                       (user['id'], user['organization_id'], *values)).lastrowid
    return field_dto(owned(db, 'fields', user, ident))


def edit_field(db, user, fid, data):
    auth.teacher(user)
    item = owned(db, 'fields', user, fid)
    version(item, data.version)
    if item['archived']:
        fail(409, 'field_archived', 'Campo archiviato')
    values = field_values(db, user, data)
    candidate = dict(item, name=values[0], venue_id=values[1], variants_json=values[2], availability_json=values[3])
    for game in svc.rows(db, 'SELECT m.*,t.platform_variant_id,t.variant FROM matches m JOIN tournaments t ON t.id=m.tournament_id WHERE m.field_id=? AND m.scheduled_at IS NOT NULL', (fid,)):
        if game['home_score'] is None:
            check_field(candidate, game['platform_variant_id'] or game['variant'], datetime.fromisoformat(game['scheduled_at']), game['duration'])
    db.execute('UPDATE fields SET name=?,venue_id=?,variants_json=?,availability_json=?,version=version+1 WHERE id=?', (*values, fid))
    return field_dto(owned(db, 'fields', user, fid))


def check_field(field, variant_id, start, duration):
    from identity_bridge import VARIANT_SLUGS
    canonical=lambda value:VARIANT_SLUGS.get(value,value)
    if canonical(variant_id) not in {canonical(value) for value in json.loads(field['variants_json'])}:
        fail(422, 'sport_incompatible', 'Campo non compatibile con la variante')
    end = start+timedelta(minutes=duration)
    slots = json.loads(field['availability_json'])
    if slots and not any(datetime.fromisoformat(s['starts_at']) <= start and end <= datetime.fromisoformat(s['ends_at']) for s in slots):
        fail(422, 'outside_availability', 'Fuori dalla disponibilità del campo')


def check_booking(db, tournament, game, start, fid, duration):
    end = start+timedelta(minutes=duration)
    ids = {game['home_team_id'], game['away_team_id']} - {None}
    if fid is not None:
        field = db.execute('SELECT * FROM fields WHERE id=? AND owner_id=? AND organization_id=?',
                           (fid, tournament['owner_id'], tournament['organization_id'])).fetchone()
        if not field:
            fail(404, 'not_found', 'Campo non trovato nel contesto del torneo')
        check_field(field, tournament['platform_variant_id'] or tournament['variant'], start, duration)
    other_games = svc.rows(db, 'SELECT m.* FROM matches m JOIN tournaments t ON t.id=m.tournament_id '
                 'WHERE t.organization_id=? AND m.scheduled_at IS NOT NULL AND m.id!=?', (tournament['organization_id'], game['id']))
    for other in other_games:
        other_start = datetime.fromisoformat(other['scheduled_at'])
        other_end = other_start+timedelta(minutes=other['duration'])
        if start < other_end and other_start < end:
            if fid is not None and fid == other['field_id']:
                fail(409, 'field_busy', 'Campo già prenotato, anche in un altro torneo')
            if ids & {other['home_team_id'], other['away_team_id']}:
                fail(409, 'team_busy', 'Squadra già impegnata')
        if other['id'] in (game['source_home'], game['source_away']) and other_end > start:
            fail(409, 'dependency_conflict', 'La partita deve iniziare dopo i suoi incontri sorgente')
        if game['id'] in (other['source_home'], other['source_away']) and end > other_start:
            fail(409, 'dependency_conflict', 'La partita deve finire prima del turno successivo')


def validate_tournament_schedule(db, tid):
    t = svc.required(db, tid)
    for game in svc.games(db, tid):
        if game['scheduled_at']:
            check_booking(db, t, game, datetime.fromisoformat(game['scheduled_at']), game['field_id'], game['duration'])


def schedule(db, user, tid, mid, data):
    tournament = auth.access(db, user, tid, True)
    game = match(db, tid, mid, data.version)
    if game['is_bye']:
        fail(422, 'bye_not_schedulable', 'Un BYE non occupa un campo')
    stamp = data.scheduled_at.astimezone(timezone.utc) if data.scheduled_at else None
    field = None
    if data.field_id is not None:
        field = db.execute('SELECT * FROM fields WHERE id=? AND owner_id=? AND archived=0',
                           (data.field_id, tournament['owner_id'])).fetchone()
        if not field:
            fail(404, 'not_found', 'Campo non disponibile')
    if stamp:
        check_booking(db, tournament, game, stamp, data.field_id, data.duration)
    db.execute('UPDATE matches SET scheduled_at=?,timezone=?,field_id=?,location=?,duration=?,version=version+1 WHERE id=?',
               (stamp.isoformat() if stamp else None, data.timezone, data.field_id, field['name'] if field else None, data.duration, mid))
    audit(db, user, tid, 'match_scheduled', {'match_id': mid, 'field_id': data.field_id, 'scheduled_at': stamp.isoformat() if stamp else None})
    from v1_domain import detail
    return next(m for m in detail(db, user, tid)['matches'] if m['id'] == mid)
