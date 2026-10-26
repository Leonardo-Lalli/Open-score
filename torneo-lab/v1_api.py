"""Additive authenticated API. The legacy demo is kept behind a separate mode."""
import json
import os
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, Security
from fastapi.security import APIKeyCookie

import auth
from auth import fail, version
from db import database
import services as svc
import sports
import v1_domain as domain
import v1_resources as resources
import v1_results as results
import v1_schemas as schema
import v1_dto as dto

Cursor = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]


def create_router(path, secure_cookies=False, public_origin=None):
    router = APIRouter(prefix='/api/v1', tags=['Platform V1'], responses={
        code: {'model': dto.Error} for code in (400, 401, 403, 404, 409, 410, 422, 429)})
    cookie_auth = APIKeyCookie(name=auth.COOKIE, auto_error=False)

    def origin(request):
        return public_origin or str(request.base_url).rstrip('/')

    def context(request: Request, _cookie=Security(cookie_auth),
                _csrf: str | None = Header(None, alias='X-CSRF-Token')):
        with database(path, request.method not in ('GET', 'HEAD')) as db:
            record = auth.session(db, request)
            if request.method not in ('GET', 'HEAD'):
                auth.csrf(request, record)
            user = dict(db.execute('SELECT * FROM users WHERE id=?', (record['user_id'],)).fetchone())
            yield db, user

    @router.get('/auth/csrf', tags=['Auth'], response_model=dto.Csrf)
    def get_csrf(request: Request, response: Response):
        auth.rate_limit(path, request, 'csrf', 120)
        with database(path, True) as db:
            old = auth.session(db, request, False)
            if old:
                return {'csrf_token': old['csrf_token']}
            return {'csrf_token': auth.new_session(db, response, secure_cookies)}

    @router.post('/auth/register', status_code=201, tags=['Auth'], response_model=dto.Login)
    def register(request: Request, response: Response, data: schema.RegisterInput,
                 _csrf: str | None = Header(None, alias='X-CSRF-Token')):
        auth.rate_limit(path, request, 'register', 10)
        if os.environ.get('TORNEO_ALLOW_REGISTRATION', 'true').casefold() != 'true':
            fail(403, 'registration_disabled', 'Registrazione disabilitata')
        with database(path, True) as db:
            old = auth.session(db, request, False)
            auth.csrf(request, old)
            if db.execute('SELECT 1 FROM users WHERE email=?', (data.email,)).fetchone():
                fail(409, 'account_unavailable', 'Account non disponibile')
            uid = db.execute('INSERT INTO users(email,display_name,password_hash,role) VALUES (?,?,?,?)',
                 (data.email, data.display_name, auth.password_hash(data.password.get_secret_value()), 'student')).lastrowid
            token = auth.new_session(db, response, secure_cookies, uid, old)
            user = db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
            return dict(user=auth.public_user(user), csrf_token=token)

    @router.post('/auth/login', tags=['Auth'], response_model=dto.Login)
    def login(request: Request, response: Response, data: schema.Credentials,
              _csrf: str | None = Header(None, alias='X-CSRF-Token')):
        auth.rate_limit(path, request, 'login', 30)
        auth.rate_limit(path, request, 'login-account-'+auth.digest(data.email), 10)
        with database(path, True) as db:
            old = auth.session(db, request, False)
            auth.csrf(request, old)
            user = db.execute('SELECT * FROM users WHERE email=?', (data.email,)).fetchone()
            dummy = 'pbkdf2_sha256$600000$'+'00'*16+'$'+'00'*32
            valid = auth.verify_password(data.password.get_secret_value(), user['password_hash'] if user else dummy)
            if not user or not valid:
                fail(401, 'invalid_credentials', 'Credenziali non valide')
            token = auth.new_session(db, response, secure_cookies, user['id'], old)
            return dict(user=auth.public_user(user), csrf_token=token)

    @router.post('/auth/logout', status_code=204, tags=['Auth'])
    def logout_session(request: Request, ctx=Depends(context)):
        db, user = ctx
        db.execute('DELETE FROM sessions WHERE token_hash=?', (auth.digest(request.cookies.get(auth.COOKIE, '')),))
        response = Response(status_code=204)
        response.delete_cookie(auth.COOKIE, path='/', secure=secure_cookies, httponly=True, samesite='lax')
        return response

    @router.get('/users/me', tags=['Auth'], response_model=dto.User)
    def me(ctx=Depends(context)):
        return auth.public_user(ctx[1])

    @router.get('/organizations/current')
    def organization(ctx=Depends(context)):
        db, user = ctx
        if user['organization_id'] is None:
            return {'organization': None}
        return {'organization': dict(db.execute('SELECT * FROM organizations WHERE id=?', (user['organization_id'],)).fetchone())}

    @router.get('/sports', tags=['Sports'])
    def catalog(ctx=Depends(context)):
        items = [dict(id=vid, sport=value[0], name=value[1], score_type=value[2], preset='school', defaults=sports.configuration(vid))
                 for vid, value in sports.VARIANTS.items()]
        return dict(items=items, next_cursor=None)

    @router.get('/sports/variants/{vid}/rules-schema', tags=['Sports'], response_model=dto.RulesSchema)
    def rules_schema(vid: str, ctx=Depends(context)):
        domain.rules(vid, {})
        return sports.metadata(vid)

    @router.get('/tournaments', response_model=dto.Page[dto.Summary], response_model_exclude_unset=True)
    def tournaments(cursor: Cursor = 0, limit: Limit = 50, status: str | None = None, ctx=Depends(context)):
        db, user = ctx
        items = []
        for t in svc.rows(db, 'SELECT * FROM tournaments WHERE owner_id IS NOT NULL ORDER BY id'):
            try:
                state = domain.detail(db, user, t['id'])
            except HTTPException as exc:
                if exc.status_code == 404:
                    continue
                raise
            if status is None or state['status'] == status:
                items.append(dict(state['tournament'], status=state['status'], progress=state['progress'],
                                  team_count=len(state['teams']), champion_team_id=state['champion_team_id']))
        return domain.page(items, cursor, limit)

    @router.post('/tournaments', status_code=201, response_model=dto.Id)
    def create_tournament(data: schema.TournamentCreate, ctx=Depends(context)):
        return domain.create_tournament(*ctx, data)

    @router.get('/tournaments/{tid}', response_model=dto.Detail, response_model_exclude_unset=True)
    def tournament(tid: int, ctx=Depends(context)):
        return domain.detail(*ctx, tid)

    @router.patch('/tournaments/{tid}', response_model=dto.Tournament, response_model_exclude_unset=True)
    def edit_tournament(tid: int, data: schema.TournamentEdit, ctx=Depends(context)):
        db, user = ctx
        t = auth.access(db, user, tid, True)
        version(t, data.version)
        db.execute('UPDATE tournaments SET name=?,description=?,version=version+1 WHERE id=?',
                   (data.name if data.name is not None else t['name'],
                    data.description if data.description is not None else t['description'], tid))
        domain.audit(db, user, tid, 'tournament_updated', {})
        return domain.detail(db, user, tid)['tournament']

    @router.get('/tournaments/{tid}/rules', response_model=dto.Rules)
    def get_rules(tid: int, ctx=Depends(context)):
        db, user = ctx
        t = auth.access(db, user, tid)
        return dict(variant_id=t['variant_id'], config=json.loads(t['rules_json']) if t['rules_json'] else None, version=t['version'])

    @router.patch('/tournaments/{tid}/rules', response_model=dto.Rules)
    def change_rules(tid: int, data: schema.RulesInput, ctx=Depends(context)):
        db, user = ctx
        t = auth.access(db, user, tid, True)
        version(t, data.version)
        if svc.games(db, tid):
            fail(409, 'rules_locked', 'Le regole si cambiano soltanto prima della generazione')
        config = domain.rules(data.variant_id, data.config)
        db.execute('UPDATE tournaments SET variant_id=?,rules_json=?,sport=?,win_points=?,draw_points=?,loss_points=?,version=version+1 WHERE id=?',
                   (data.variant_id, json.dumps(config), sports.VARIANTS[data.variant_id][0], config.get('win_points', 3),
                    config.get('draw_points', 0), config.get('loss_points', 0), tid))
        domain.audit(db, user, tid, 'rules_updated', {'variant_id': data.variant_id})
        return dict(variant_id=data.variant_id, config=config, version=data.version+1)

    @router.get('/tournaments/{tid}/teams', response_model=dto.TeamsPage)
    def teams(tid: int, cursor: Cursor = 0, limit: Limit = 50, q: str = '', ctx=Depends(context)):
        db, user = ctx
        t = auth.access(db, user, tid)
        items = domain.ordered_teams(db, tid)
        if not auth.manages(db, user, t):
            items = [{k: item[k] for k in ('id', 'name', 'group_id', 'display_order', 'version')} for item in items]
        return domain.page([i for i in items if q.casefold() in i['name'].casefold()], cursor, limit, order_version=t['order_version'])

    @router.post('/tournaments/{tid}/teams', status_code=201, response_model=dto.Team)
    def add_team(tid: int, data: schema.TeamCreate, ctx=Depends(context)):
        return domain.add_team(*ctx, tid, data)

    @router.patch('/tournaments/{tid}/teams/order', response_model=dto.Order)
    def reorder(tid: int, data: schema.OrderInput, ctx=Depends(context)):
        return domain.reorder(*ctx, tid, data)

    @router.patch('/tournaments/{tid}/teams/{team_id}', response_model=dto.Team)
    def edit_team(tid: int, team_id: int, data: schema.TeamEdit, ctx=Depends(context)):
        return domain.edit_team(*ctx, tid, team_id, data)

    @router.delete('/tournaments/{tid}/teams/{team_id}', status_code=204)
    def delete_team(tid: int, team_id: int, data: schema.VersionInput, ctx=Depends(context)):
        domain.archive_team(*ctx, tid, team_id, data.version)
        return Response(status_code=204)

    @router.patch('/tournaments/{tid}/teams/{team_id}/penalty', response_model=dto.Penalty)
    def penalty(tid: int, team_id: int, data: schema.PenaltyInput, ctx=Depends(context)):
        db, user = ctx
        t = auth.access(db, user, tid, True)
        version(domain.get_team(db, tid, team_id), data.version)
        if t['format'] == 'knockout':
            fail(422, 'standings_required', 'Le penalità punti richiedono un girone')
        if t['format'] == 'groups' and any(m['kind'] == 'knockout' for m in svc.games(db, tid)):
            fail(409, 'qualification_locked', 'Penalità bloccate dopo la qualificazione; serve una revisione delle fasi')
        db.execute('INSERT INTO team_penalties VALUES (?,?,?) ON CONFLICT(team_id) DO UPDATE SET points=excluded.points,reason=excluded.reason',
                   (team_id, data.points, data.reason))
        db.execute('UPDATE teams SET version=version+1 WHERE id=?', (team_id,))
        domain.audit(db, user, tid, 'team_penalty_changed', {'team_id': team_id, 'points': data.points, 'reason': data.reason})
        return dict(team_id=team_id, points=data.points, version=data.version+1)

    @router.get('/tournaments/{tid}/students', response_model=dto.Page[dto.Student])
    def students(tid: int, cursor: Cursor = 0, limit: Limit = 50, q: str = '', team_id: int | None = None, ctx=Depends(context)):
        db, user = ctx
        auth.access(db, user, tid, True)
        items = svc.rows(db, 'SELECT * FROM students WHERE tournament_id=? ORDER BY id', (tid,))
        return domain.page([s for s in items if q.casefold() in s['display_name'].casefold()
                            and (team_id is None or team_id == s['team_id'])], cursor, limit)

    @router.post('/tournaments/{tid}/students', status_code=201, response_model=dto.Student)
    def add_student(tid: int, data: schema.StudentInput, ctx=Depends(context)):
        return domain.add_student(*ctx, tid, data)

    @router.patch('/tournaments/{tid}/students/{sid}/team', response_model=dto.Student)
    def move_student(tid: int, sid: int, data: schema.TeamAssignment, ctx=Depends(context)):
        return domain.assign_student(*ctx, tid, sid, data)

    @router.get('/tournaments/{tid}/my-participation', response_model=dto.Participation)
    def participation(tid: int, ctx=Depends(context)):
        db, user = ctx
        auth.access(db, user, tid)
        member = db.execute('SELECT * FROM students WHERE tournament_id=? AND user_id=?', (tid, user['id'])).fetchone()
        return {'student': dict(member) if member else None}

    @router.post('/tournaments/{tid}/enrollments', status_code=201, response_model=dto.Enrollment)
    def enroll(tid: int, data: schema.EnrollmentInput, ctx=Depends(context)):
        db, user = ctx
        return resources.enroll(db, user, tid, data.team_id, team_version=data.team_version)

    @router.get('/tournaments/{tid}/enrollments', response_model=dto.Page[dto.Enrollment])
    def enrollments(tid: int, cursor: Cursor = 0, limit: Limit = 50, status: str | None = None, ctx=Depends(context)):
        db, user = ctx
        t = svc.required(db, tid)
        items = svc.rows(db, 'SELECT * FROM enrollments WHERE tournament_id=? ORDER BY id', (tid,))
        if not auth.manages(db, user, t):
            items = [i for i in items if i['user_id'] == user['id']]
            if not items:
                fail(404, 'not_found', 'Richieste non trovate')
        return domain.page([i for i in items if status is None or i['status'] == status], cursor, limit)

    @router.post('/tournaments/{tid}/enrollments/{eid}/review', response_model=dto.Enrollment)
    def enrollment_review(tid: int, eid: int, data: schema.EnrollmentReview, ctx=Depends(context)):
        return resources.review_enrollment(*ctx, tid, eid, data)

    @router.post('/tournaments/{tid}/generate')
    def generate(tid: int, ctx=Depends(context)):
        db, user = ctx
        t = auth.access(db, user, tid, True)
        if not t['variant_id']:
            fail(409, 'rules_required', 'Configurare una variante prima della generazione')
        outcome = svc.generate(db, tid)
        domain.audit(db, user, tid, 'fixtures_generated', {})
        return outcome

    @router.get('/tournaments/{tid}/matches', response_model=dto.Page[dto.Match])
    def matches(tid: int, cursor: Cursor = 0, limit: Limit = 50, stage_id: int | None = None,
                group_id: int | None = None, team_id: int | None = None, status: str | None = None, ctx=Depends(context)):
        db, user = ctx
        items = domain.detail(db, user, tid)['matches']
        return domain.page([m for m in items if (stage_id is None or m['stage_id'] == stage_id)
                  and (group_id is None or m['group_id'] == group_id)
                  and (team_id is None or team_id in (m['home_team_id'], m['away_team_id']))
                  and (status is None or m['status'] == status)], cursor, limit)

    @router.get('/tournaments/{tid}/standings', response_model=dto.Standings, response_model_exclude_unset=True)
    def standings(tid: int, ctx=Depends(context)):
        db, user = ctx
        state = domain.detail(db, user, tid)
        variant = state['tournament']['variant_id']
        return dict(rows=state['standings'], groups=state['groups'],
                    criteria=sports.metadata(variant)['standings_criteria'] if variant else ['points', 'goal_difference', 'goals_for', 'name', 'team_id'])

    @router.get('/tournaments/{tid}/bracket', response_model=dto.Bracket, response_model_exclude_unset=True)
    def bracket(tid: int, ctx=Depends(context)):
        return domain.bracket(*ctx, tid)

    @router.get('/tournaments/{tid}/statistics', response_model=dto.Statistics, response_model_exclude_unset=True)
    def statistics(tid: int, ctx=Depends(context)):
        return domain.statistics(*ctx, tid)

    @router.post('/tournaments/{tid}/matches/{mid}/proposals', status_code=201, response_model=dto.Proposal)
    def proposal(tid: int, mid: int, data: schema.ProposalInput, ctx=Depends(context)):
        return results.propose(*ctx, tid, mid, data)

    @router.get('/tournaments/{tid}/matches/{mid}/proposals', response_model=dto.Page[dto.Proposal])
    def proposals(tid: int, mid: int, cursor: Cursor = 0, limit: Limit = 50, status: str | None = None, ctx=Depends(context)):
        db, user = ctx
        t = auth.access(db, user, tid)
        results.match(db, tid, mid)
        items = svc.rows(db, 'SELECT * FROM result_proposals WHERE tournament_id=? AND original_match_id=? ORDER BY id', (tid, mid))
        if not auth.manages(db, user, t):
            items = [i for i in items if i['submitted_by'] == user['id']]
        return domain.page([results.proposal_dto(db, i) for i in items if status is None or i['status'] == status], cursor, limit)

    @router.post('/tournaments/{tid}/matches/{mid}/proposals/{pid}/review', response_model=dto.ProposalReview, response_model_exclude_unset=True)
    def review(tid: int, mid: int, pid: int, data: schema.ProposalReview, ctx=Depends(context)):
        return results.review(*ctx, tid, mid, pid, data)

    @router.get('/tournaments/{tid}/matches/{mid}/result', response_model=dto.Result, response_model_exclude_unset=True)
    def official(tid: int, mid: int, ctx=Depends(context)):
        db, user = ctx
        auth.access(db, user, tid)
        return results.official(db, tid, mid)

    @router.patch('/tournaments/{tid}/matches/{mid}/result', response_model=dto.ResultMutation, response_model_exclude_unset=True)
    def result(tid: int, mid: int, data: schema.ResultInput, ctx=Depends(context)):
        return results.save(*ctx, tid, mid, data.match_version, data.score, data.invalidate, data.reason)

    @router.delete('/tournaments/{tid}/matches/{mid}/result', response_model=dto.ResultMutation, response_model_exclude_unset=True)
    def clear(tid: int, mid: int, data: schema.ResultClear, ctx=Depends(context)):
        return results.save(*ctx, tid, mid, data.match_version, None, data.invalidate, data.reason)

    @router.patch('/tournaments/{tid}/publication', response_model=dto.Publication)
    def publication(tid: int, data: schema.PublicationInput, request: Request, ctx=Depends(context)):
        db, user = ctx
        t = auth.access(db, user, tid, True)
        version(t, data.version)
        slug = t['public_slug'] or secrets.token_urlsafe(12)
        db.execute('UPDATE tournaments SET published=?,public_slug=?,version=version+1 WHERE id=?', (int(data.published), slug, tid))
        domain.audit(db, user, tid, 'publication_changed', {'published': data.published})
        return dict(published=data.published, public_slug=slug, public_url=origin(request)+'/api/v1/public/tournaments/'+slug, version=data.version+1)

    @router.get('/public/tournaments/{slug}', response_model=dto.Detail, response_model_exclude_unset=True)
    def public_detail(slug: str):
        with database(path) as db:
            t = db.execute('SELECT id FROM tournaments WHERE public_slug=? AND published=1', (slug,)).fetchone()
            if not t:
                fail(404, 'not_found', 'Torneo non pubblicato')
            return domain.detail(db, None, t['id'], True)

    @router.get('/public/tournaments/{slug}/statistics', response_model=dto.Statistics, response_model_exclude_unset=True)
    def public_statistics(slug: str):
        with database(path) as db:
            t = db.execute('SELECT id FROM tournaments WHERE public_slug=? AND published=1', (slug,)).fetchone()
            if not t:
                fail(404, 'not_found', 'Torneo non pubblicato')
            return domain.statistics(db, None, t['id'], True)

    @router.post('/tournaments/{tid}/invites', status_code=201, response_model=dto.CreatedInvite)
    def invite(tid: int, data: schema.InviteInput, request: Request, ctx=Depends(context)):
        return resources.create_invite(*ctx, tid, data, origin(request))

    @router.get('/tournaments/{tid}/invites', response_model=dto.Page[dto.Invite])
    def invites(tid: int, cursor: Cursor = 0, limit: Limit = 50, ctx=Depends(context)):
        db, user = ctx
        auth.access(db, user, tid, True)
        return domain.page([resources.invite_dto(i) for i in svc.rows(db, 'SELECT * FROM invites WHERE tournament_id=? ORDER BY id', (tid,))], cursor, limit)

    @router.delete('/tournaments/{tid}/invites/{iid}', status_code=204)
    def revoke(tid: int, iid: int, data: schema.VersionInput, ctx=Depends(context)):
        db, user = ctx
        auth.access(db, user, tid, True)
        item = db.execute('SELECT * FROM invites WHERE id=? AND tournament_id=?', (iid, tid)).fetchone()
        if not item:
            fail(404, 'not_found', 'Invito non trovato')
        version(item, data.version)
        db.execute('UPDATE invites SET revoked=1,version=version+1 WHERE id=?', (iid,))
        domain.audit(db, user, tid, 'invite_revoked', {'invite_id': iid})
        return Response(status_code=204)

    @router.post('/invites/validate', response_model=dto.InviteValidation)
    def validate_invite(data: schema.TokenInput, request: Request):
        auth.rate_limit(path, request, 'invite-validate', 60)
        with database(path) as db:
            item = resources.find_invite(db, data.token)
            tournament = svc.required(db, item['tournament_id'])
            team = resources.get_team(db, tournament['id'], item['team_id']) if item['team_id'] else None
            return dict(valid=True, tournament_name=tournament['name'], team_name=team['name'] if team else None,
                        expires_at=item['expires_at'], requires_login=True)

    @router.post('/invites/accept', status_code=201, response_model=dto.Enrollment)
    def accept(data: schema.TokenInput, ctx=Depends(context)):
        return resources.accept_invite(*ctx, data.token)

    @router.post('/venues', status_code=201, response_model=dto.Venue)
    def venue(data: schema.VenueInput, ctx=Depends(context)):
        db, user = ctx
        auth.teacher(user)
        ident = db.execute('INSERT INTO venues(owner_id,organization_id,name) VALUES (?,?,?)', (user['id'], user['organization_id'], data.name)).lastrowid
        db.execute("INSERT INTO administrative_audit(actor_id,action,resource_id) VALUES (?,'venue_created',?)", (user['id'], ident))
        return resources.owned(db, 'venues', user, ident)

    @router.get('/venues', response_model=dto.Page[dto.Venue])
    def venues(cursor: Cursor = 0, limit: Limit = 50, ctx=Depends(context)):
        db, user = ctx
        auth.teacher(user)
        return domain.page(svc.rows(db, 'SELECT * FROM venues WHERE owner_id=? ORDER BY id', (user['id'],)), cursor, limit)

    @router.post('/fields', status_code=201, response_model=dto.Field)
    def field(data: schema.FieldInput, ctx=Depends(context)):
        db, user = ctx
        item = resources.create_field(db, user, data)
        db.execute("INSERT INTO administrative_audit(actor_id,action,resource_id) VALUES (?,'field_created',?)", (user['id'], item['id']))
        return item

    @router.get('/fields', response_model=dto.Page[dto.Field])
    def fields(cursor: Cursor = 0, limit: Limit = 50, venue_id: int | None = None, sport_variant_id: str | None = None, ctx=Depends(context)):
        db, user = ctx
        auth.teacher(user)
        items = [resources.field_dto(i) for i in svc.rows(db, 'SELECT * FROM fields WHERE owner_id=? AND archived=0 ORDER BY id', (user['id'],))]
        return domain.page([i for i in items if (venue_id is None or i['venue_id'] == venue_id)
                  and (sport_variant_id is None or sport_variant_id in i['sport_variant_ids'])], cursor, limit)

    @router.patch('/fields/{fid}', response_model=dto.Field)
    def edit_field(fid: int, data: schema.FieldEdit, ctx=Depends(context)):
        db, user = ctx
        item = resources.edit_field(db, user, fid, data)
        db.execute("INSERT INTO administrative_audit(actor_id,action,resource_id) VALUES (?,'field_updated',?)", (user['id'], fid))
        return item

    @router.delete('/fields/{fid}', status_code=204)
    def archive_field(fid: int, data: schema.VersionInput, ctx=Depends(context)):
        db, user = ctx
        auth.teacher(user)
        version(resources.owned(db, 'fields', user, fid), data.version)
        db.execute('UPDATE fields SET archived=1,version=version+1 WHERE id=?', (fid,))
        db.execute("INSERT INTO administrative_audit(actor_id,action,resource_id) VALUES (?,'field_archived',?)", (user['id'], fid))
        return Response(status_code=204)

    @router.patch('/tournaments/{tid}/matches/{mid}/schedule', response_model=dto.Match, response_model_exclude_unset=True)
    def schedule(tid: int, mid: int, data: schema.ScheduleInput, ctx=Depends(context)):
        return resources.schedule(*ctx, tid, mid, data)

    @router.get('/tournaments/{tid}/calendar', response_model=dto.Page[dto.Match], response_model_exclude_unset=True)
    def calendar(tid: int, cursor: Cursor = 0, limit: Limit = 50, team_id: int | None = None,
                 field_id: int | None = None, from_at: str | None = Query(None, alias='from'),
                 to_at: str | None = Query(None, alias='to'), ctx=Depends(context)):
        from datetime import datetime
        db, user = ctx
        try:
            start = datetime.fromisoformat(from_at) if from_at else None
            end = datetime.fromisoformat(to_at) if to_at else None
            if any(stamp is not None and stamp.utcoffset() is None for stamp in (start, end)) or (start and end and start >= end):
                raise ValueError()
        except ValueError:
            fail(422, 'invalid_interval', 'Intervallo con timezone richiesto')
        items = domain.detail(db, user, tid)['matches']
        return domain.page([m for m in items if (team_id is None or team_id in (m['home_team_id'], m['away_team_id']))
            and (field_id is None or m['field_id'] == field_id)
            and (start is None or (m['scheduled_at'] and datetime.fromisoformat(m['scheduled_at']) >= start))
            and (end is None or (m['scheduled_at'] and datetime.fromisoformat(m['scheduled_at']) < end))], cursor, limit)

    return router
