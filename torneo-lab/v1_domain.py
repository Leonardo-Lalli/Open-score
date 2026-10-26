"""Authenticated tournament, team and student operations. Callers own transactions."""
import json
import secrets

from pydantic import ValidationError

import platform_auth as auth
import platform_services as svc
import sports
from platform_auth import fail, version
from platform_schemas import TournamentInput


def audit(db, user, tid, action, payload):
    db.execute('INSERT INTO audit_logs(tournament_id,action,payload,actor_id) VALUES (?,?,?,?)',
               (tid, action, json.dumps(payload, ensure_ascii=False), user['id']))


def page(items, cursor=0, limit=50, **extra):
    return dict(items=items[cursor:cursor+limit],
                next_cursor=cursor+limit if cursor+limit < len(items) else None, **extra)


def rules(variant_id, config):
    try:
        return sports.configuration(variant_id, config)
    except (ValueError, ValidationError) as exc:
        fail(422, 'invalid_rules', str(exc))


def create_tournament(db, user, data):
    auth.teacher(user)
    config = rules(data.variant_id, data.config)
    values = data.model_dump(exclude={'variant_id', 'config'})
    # Reuse the established generator/storage; sport-specific validation lives in V1.
    label = sports.VARIANTS[data.variant_id][0]
    values['sport'] = label if label != 'Pallavolo' else 'Calcio'
    values.update(win_points=config.get('win_points', 3), draw_points=config.get('draw_points', 0),
                  loss_points=config.get('loss_points', 0))
    try:
        payload = TournamentInput.model_validate(values)
    except ValidationError as exc:
        fail(422, 'invalid_tournament', str(exc))
    tid = svc.create(db, payload)
    db.execute('UPDATE tournaments SET owner_id=?,organization_id=?,platform_variant_id=?,rules_json=?,sport=?,public_slug=? WHERE id=?',
        (user['id'], user['organization_id'], data.variant_id, json.dumps(config), label, secrets.token_urlsafe(12), tid))
    db.execute('UPDATE teams SET display_order=id WHERE tournament_id=?', (tid,))
    from identity_bridge import sync_platform_tournament
    sync_platform_tournament(db, tid)
    audit(db, user, tid, 'tournament_owned', {})
    return {'id': tid}


def get_team(db, tid, team_id):
    item = db.execute('SELECT * FROM teams WHERE id=? AND tournament_id=? AND archived=0', (team_id, tid)).fetchone()
    if not item:
        fail(404, 'not_found', 'Squadra non trovata')
    return dict(item)


def ordered_teams(db, tid):
    return svc.rows(db, 'SELECT * FROM teams WHERE tournament_id=? AND archived=0 ORDER BY display_order,id', (tid,))


def unique_team(db, tid, name, excluding=None):
    if any(t['id'] != excluding and t['name'].casefold() == name.casefold() for t in ordered_teams(db, tid)):
        fail(409, 'duplicate_team', 'Nome squadra già presente')
    # SQL uniqueness also includes archived names, preserving historical identity.
    if db.execute('SELECT 1 FROM teams WHERE tournament_id=? AND name=? COLLATE NOCASE AND archived=1', (tid, name)).fetchone():
        fail(409, 'duplicate_team', 'Nome conservato da una squadra archiviata')


def add_team(db, user, tid, data):
    auth.access(db, user, tid, True)
    if svc.games(db, tid):
        fail(409, 'teams_locked', 'Struttura bloccata dopo la generazione')
    items = ordered_teams(db, tid)
    if len(items) >= 32:
        fail(422, 'team_limit', 'Massimo 32 squadre')
    unique_team(db, tid, data.name)
    ident = db.execute('INSERT INTO teams(tournament_id,name,max_members,display_order) VALUES (?,?,?,?)',
                       (tid, data.name, data.max_members, max((t['display_order'] for t in items), default=0)+1)).lastrowid
    db.execute('UPDATE tournaments SET order_version=order_version+1 WHERE id=?', (tid,))
    audit(db, user, tid, 'team_added', {'team_id': ident})
    return get_team(db, tid, ident)


def edit_team(db, user, tid, team_id, data):
    auth.access(db, user, tid, True)
    team = get_team(db, tid, team_id)
    version(team, data.version)
    unique_team(db, tid, data.name, team_id)
    count = db.execute('SELECT count(*) FROM students WHERE tournament_id=? AND team_id=?', (tid, team_id)).fetchone()[0]
    if data.max_members is not None and count > data.max_members:
        fail(409, 'team_full', 'Capienza inferiore ai membri già assegnati')
    db.execute('UPDATE teams SET name=?,max_members=?,version=version+1 WHERE id=?', (data.name, data.max_members, team_id))
    audit(db, user, tid, 'team_updated', {'team_id': team_id})
    return get_team(db, tid, team_id)


def archive_team(db, user, tid, team_id, expected):
    auth.access(db, user, tid, True)
    version(get_team(db, tid, team_id), expected)
    if svc.games(db, tid) or db.execute('SELECT 1 FROM students WHERE team_id=?', (team_id,)).fetchone():
        fail(409, 'team_in_use', 'Sposta i membri e archivia prima della generazione')
    db.execute('UPDATE teams SET archived=1,version=version+1 WHERE id=?', (team_id,))
    db.execute('UPDATE tournaments SET order_version=order_version+1 WHERE id=?', (tid,))
    audit(db, user, tid, 'team_archived', {'team_id': team_id})


def reorder(db, user, tid, data):
    tournament = auth.access(db, user, tid, True)
    version(tournament, data.version, 'order_version')
    ids = data.ordered_team_ids
    if len(set(ids)) != len(ids) or set(ids) != {t['id'] for t in ordered_teams(db, tid)}:
        fail(422, 'invalid_team_order', 'Inviare ogni squadra attiva esattamente una volta')
    db.executemany('UPDATE teams SET display_order=? WHERE id=?', [(i, ident) for i, ident in enumerate(ids)])
    db.execute('UPDATE tournaments SET order_version=order_version+1 WHERE id=?', (tid,))
    audit(db, user, tid, 'teams_reordered', {'ordered_team_ids': ids})
    return {'ordered_team_ids': ids, 'version': data.version+1}


def student_user(db, uid):
    user = db.execute("SELECT * FROM users WHERE id=? AND role='student'", (uid,)).fetchone()
    if not user:
        fail(404, 'not_found', 'Account studente non trovato')
    return dict(user)


def add_student(db, user, tid, data):
    auth.access(db, user, tid, True)
    if data.user_id:
        student_user(db, data.user_id)
        if db.execute('SELECT 1 FROM students WHERE tournament_id=? AND user_id=?', (tid, data.user_id)).fetchone():
            fail(409, 'already_enrolled', 'Studente già iscritto')
    if any(s['display_name'].casefold() == data.display_name.casefold()
           for s in svc.rows(db, 'SELECT display_name FROM students WHERE tournament_id=?', (tid,))):
        fail(409, 'duplicate_student', 'Alias studente già presente')
    ident = db.execute('INSERT INTO students(tournament_id,user_id,display_name) VALUES (?,?,?)',
                       (tid, data.user_id, data.display_name)).lastrowid
    audit(db, user, tid, 'student_added', {'student_id': ident})
    return dict(db.execute('SELECT * FROM students WHERE id=?', (ident,)).fetchone())


def capacity(db, tid, team_id, excluding=None):
    team = get_team(db, tid, team_id)
    count = db.execute('SELECT count(*) FROM students WHERE tournament_id=? AND team_id=? AND id!=?',
                       (tid, team_id, excluding or -1)).fetchone()[0]
    if team['max_members'] is not None and count >= team['max_members']:
        fail(409, 'team_full', 'Squadra al completo')
    return team


def assign_student(db, user, tid, sid, data):
    auth.access(db, user, tid, True)
    student = db.execute('SELECT * FROM students WHERE id=? AND tournament_id=?', (sid, tid)).fetchone()
    if not student:
        fail(404, 'not_found', 'Studente non trovato')
    version(student, data.version)
    if data.team_id is not None:
        capacity(db, tid, data.team_id, sid)
    db.execute('UPDATE students SET team_id=?,version=version+1 WHERE id=?', (data.team_id, sid))
    from roster_bridge import sync_student
    sync_student(db,sid)
    audit(db, user, tid, 'student_moved', {'student_id': sid, 'from_team_id': student['team_id'], 'team_id': data.team_id})
    return dict(db.execute('SELECT * FROM students WHERE id=?', (sid,)).fetchone())


def detail(db, user, tid, public=False):
    tournament = svc.required(db, tid) if public else auth.access(db, user, tid)
    state = svc.detail(db, tid)
    # Explicit DTOs keep new private columns out of every visitor/student response.
    visible = ('id', 'name', 'sport', 'format', 'description', 'participant_kind',
               'win_points', 'draw_points', 'loss_points', 'legs', 'group_count',
               'qualifiers', 'created_at')
    state['tournament'] = {k: tournament[k] for k in visible}
    state['tournament']['variant_id'] = tournament['platform_variant_id']
    state['tournament']['rules'] = json.loads(tournament['rules_json']) if tournament['rules_json'] else None
    state['teams'] = [{k: t[k] for k in ('id', 'name', 'group_id', 'display_order')}
                      for t in ordered_teams(db, tid)]
    state.pop('audit', None)
    state['public'] = public
    for match in state['matches']:
        match.pop('source_id', None)
        raw = match.pop('score_json', None)
        match['score'] = json.loads(raw) if raw else None
        if public and match['score'] and match['score']['type'] == 'forfeit':
            match['score'] = {k: v for k, v in match['score'].items() if k != 'reason'}
        field = db.execute('SELECT id,name,venue_id FROM fields WHERE id=?', (match['field_id'],)).fetchone() if match['field_id'] else None
        match['field'] = dict(field) if field else None
    for stage in state['stages']:
        stage.pop('source_id', None)
    if not public and auth.manages(db, user, tournament):
        state['tournament'].update(version=tournament['version'], order_version=tournament['order_version'],
                                  published=bool(tournament['published']), public_slug=tournament['public_slug'])
        state['audit'] = svc.rows(db, 'SELECT id,action,created_at,actor_id FROM audit_logs WHERE tournament_id=? ORDER BY id DESC LIMIT 30', (tid,))
    return state


def bracket(db, user, tid, public=False):
    state = detail(db, user, tid, public)
    nodes = [m for m in state['matches'] if m['kind'] == 'knockout']
    next_slots = {}
    for match in nodes:
        for side in ('home', 'away'):
            if match['source_'+side] is not None:
                next_slots[match['source_'+side]] = {'match_id': match['id'], 'slot': side}
    stages = []
    for stage in state['stages']:
        if stage['kind'] != 'knockout':
            continue
        rounds = []
        for turn in sorted({m['round_no'] for m in nodes if m['stage_id'] == stage['id']}):
            matches = [dict(m, next=next_slots.get(m['id']),
                       official_result=({'score': m['score'], 'winner_team_id': m['winner_team_id']}
                                        if m['home_score'] is not None else None))
                       for m in nodes if m['stage_id'] == stage['id'] and m['round_no'] == turn]
            rounds.append({'round_no': turn, 'matches': matches})
        stages.append({'id': stage['id'], 'rounds': rounds})
    return {'stages': stages, 'champion_team_id': state['champion_team_id']}


def statistics(db, user, tid, public=False):
    state = detail(db, user, tid, public)
    total, completed = state['progress']['total'], state['progress']['completed']
    knockout = [m for m in state['matches'] if m['kind'] == 'knockout']
    qualified = sorted({ident for m in knockout if m['round_no'] == 1
                        for ident in (m['home_team_id'], m['away_team_id']) if ident is not None})
    result = {'team_count': len(state['teams']), 'matches_total': total, 'matches_completed': completed,
                  'matches_remaining': total-completed, 'completion_percentage': round(100*completed/total, 2) if total else 0,
                  'phases_pending_generation': state['tournament']['format'] == 'groups' and not knockout,
                  'champion_team_id': state['champion_team_id'], 'qualified_team_ids': qualified if state['tournament']['format'] == 'groups' else [],
                  'standings': state['standings'], 'groups': state['groups'], 'sport_statistics': {}}
    scored = [m for m in state['matches'] if m['home_score'] is not None and not m['is_bye']]
    variant = state['tournament']['variant_id']
    if variant and sports.VARIANTS[variant][2] == 'sets':
        result['sport_statistics']['sets_played'] = sum(m['home_score']+m['away_score'] for m in scored
                                                       if m['score'] and m['score']['type'] == 'sets')
    elif variant:
        result['sport_statistics']['points_scored'] = sum(m['home_score']+m['away_score'] for m in scored
                                                         if m['score'] and m['score']['type'] == 'points')
    if not public:
        tournament = auth.access(db, user, tid)
        result['student_count'] = db.execute('SELECT count(*) FROM students WHERE tournament_id=?', (tid,)).fetchone()[0]
        if auth.manages(db, user, tournament):
            result['pending_proposals'] = db.execute("SELECT count(*) FROM result_proposals WHERE tournament_id=? AND status='pending' AND match_id IS NOT NULL", (tid,)).fetchone()[0]
    return result
