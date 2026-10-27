"""Open Score API: read-only for students, teacher-scoped writes for the LAN."""
import csv
import io
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

import platform_auth
import services as svc
import sport_rules
from auth import COOKIE_NAME, authenticate, ensure_teacher
from auth import build as build_auth
from db import BASE, database, initialize
from frontend_api import create_router as create_frontend_router
from frontend_api import record_legacy_result, visible
from identity_bridge import attach_tournament, ensure_platform_teacher
from schemas import (
    ClearInput,
    LoginInput,
    PlayerInput,
    ResultInput,
    ScheduleInput,
    TeamInput,
    TournamentInput,
    TournamentUpdate,
)
from v1_api import create_router


def create_app(db_path: str | Path | None = None, seed: bool = False, *,
               admin_email: str | None = None,
               admin_password: str | None = None,
               session_secret: str | bytes | None = None,
               allowed_hosts: list[str] | None = None,
               cookie_secure: bool | None = None, mode: str | None = None) -> FastAPI:
    mode = mode or os.environ.get('TORNEO_MODE', 'demo')
    public_origin = os.environ.get('TORNEO_PUBLIC_ORIGIN') if mode == 'service' else None
    if mode not in ('demo', 'service'):
        raise ValueError('TORNEO_MODE deve essere demo oppure service')
    if mode == 'service':
        from urllib.parse import urlparse
        parsed = urlparse(public_origin or '')
        explicit = [h.strip() for h in os.environ.get('TORNEO_ALLOWED_HOSTS','').split(',') if h.strip()]
        if parsed.scheme != 'https' or parsed.hostname not in explicit or '*' in explicit:
            raise ValueError('Service richiede HTTPS e host espliciti coerenti')
        cookie_secure = True
    path = Path(db_path or os.environ.get('TORNEO_DB_PATH', str(BASE/'data/open_score.sqlite3')))
    initialize(path)
    auth = build_auth(BASE, secret=session_secret, cookie_secure=cookie_secure)

    bootstrap_email = (admin_email if admin_email is not None
                       else os.environ.get('TORNEO_ADMIN_EMAIL', '')).strip()
    bootstrap_password = (admin_password if admin_password is not None
                          else os.environ.get('TORNEO_ADMIN_PASSWORD', '')).strip()
    if bootstrap_password:
        with database(path, True) as db:
            ensure_teacher(db, bootstrap_email or 'admin@open-score.local',
                           bootstrap_password, 'Amministratore')

    default_hosts = ['127.0.0.1', 'localhost', 'testserver']
    configured = allowed_hosts
    if configured is None:
        configured = [host.strip() for host in
                      os.environ.get('TORNEO_ALLOWED_HOSTS', '').split(',') if host.strip()]
    hosts = list(dict.fromkeys(default_hosts + list(configured)))

    api = FastAPI(title='Open Score · API', version='0.9.1',
                  description='Applicazione originale per i tornei scolastici. Nessun collegamento alle API di Score7.')
    api.state.db_path = path
    api.state.mode = mode
    api.state.auth = auth
    api.state.allowed_hosts = hosts
    api.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
    api.mount('/static',StaticFiles(directory=BASE/'static'),name='static')
    api.include_router(create_router(path, secure_cookies=auth.cookie_secure, public_origin=public_origin))
    api.include_router(create_frontend_router(path))

    @api.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict):
            body = dict(exc.detail)
            body['detail'] = body.pop('message', 'Operazione non riuscita')
        else:
            body = {'detail': exc.detail}
            if request.url.path.startswith('/api/v1/'):
                body['code'] = {404:'not_found',409:'conflict',422:'invalid_input'}.get(exc.status_code,'request_failed')
        return JSONResponse(body,status_code=exc.status_code,headers=exc.headers)

    @api.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        body = {'detail':[{k:e[k] for k in ('loc','msg','type')} for e in exc.errors()]}
        if request.url.path.startswith('/api/v1/'):
            body['code']='validation_error'
        return JSONResponse(body,status_code=422)

    @api.middleware('http')
    async def local_security(request: Request, call_next):
        # Block cross-origin browser writes, then require a teacher session for
        # every mutation. Reads and public links stay open.
        origin = request.headers.get('origin')
        if (request.method not in ('GET','HEAD','OPTIONS') and origin
                and origin != (public_origin or str(request.base_url).rstrip('/'))):
            return Response('Origine non consentita',status_code=403)
        session = auth.session_from_request(request)
        platform_session = None
        platform_user = None
        with database(path) as db:
            if session:
                valid = db.execute('SELECT 1 FROM sessions s JOIN teacher_user_links l ON s.user_id=l.user_id JOIN teachers t ON t.id=l.teacher_id '
                    'WHERE s.token_hash=? AND s.expires_at>? AND t.id=? AND t.active=1',
                    (platform_auth.digest(request.cookies.get(COOKIE_NAME,'')),platform_auth.now().isoformat(),session['teacher_id'])).fetchone()
                if not valid:
                    session = None
            raw = request.cookies.get(platform_auth.COOKIE)
            if raw:
                platform_session = db.execute('SELECT * FROM sessions WHERE token_hash=? AND expires_at>?',
                    (platform_auth.digest(raw), platform_auth.now().isoformat())).fetchone()
                if platform_session and platform_session['user_id']:
                    platform_user = db.execute('SELECT * FROM users WHERE id=?',(platform_session['user_id'],)).fetchone()
                    if platform_user and platform_user['role']=='teacher':
                        linked = db.execute('SELECT t.* FROM teachers t JOIN teacher_user_links l ON l.teacher_id=t.id WHERE l.user_id=? AND t.active=1',
                                            (platform_user['id'],)).fetchone()
                        if linked and session is None:
                            session = {'teacher_id':linked['id'],'email':linked['email']}
                        elif not linked:
                            platform_user = None
        request.state.platform_user = dict(platform_user) if platform_user else None
        request.state.teacher = session
        route = request.url.path
        student_operation = ('/proposals' in route or (route.startswith('/api/invites/') and route.endswith('/join'))
                             or route.startswith('/api/auth/student/'))
        if (request.method not in ('GET','HEAD','OPTIONS')
                and request.url.path.startswith('/api')
                and request.url.path not in ('/api/auth/login','/api/auth/logout')
                and not route.startswith('/api/v1/') and not student_operation
                and session is None):
            return JSONResponse({'detail':'Accesso richiesto'},status_code=401)
        if (origin and request.method not in ('GET','HEAD','OPTIONS') and session and
                route not in ('/api/auth/login','/api/auth/logout') and not route.startswith('/api/v1/')):
            token = request.headers.get('X-CSRF-Token','')
            if not platform_session or not __import__('hmac').compare_digest(token,platform_session['csrf_token']):
                return JSONResponse({'detail':'Token CSRF mancante o scaduto','code':'csrf_invalid'},status_code=403)
        response = await call_next(request)
        if (request.url.path.startswith('/static/')
                and request.url.path.endswith(('.html', '.js', '.css'))):
            # Revalidate the shell and its assets so a stale mockup cannot survive.
            response.headers['Cache-Control'] = 'no-cache, must-revalidate'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        if auth.cookie_secure:
            response.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
        if request.url.path not in ('/docs','/redoc','/docs/oauth2-redirect'):
            response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'"
        return response

    def teacher(request: Request) -> dict:
        session = getattr(request.state, 'teacher', None)
        if session is None:
            raise HTTPException(401, 'Accesso richiesto')
        return session

    @api.get('/',include_in_schema=False)
    @api.get('/public/{token}',include_in_schema=False)
    def homepage(token: str = ''):
        # The shell must always reference the current versioned assets.
        return FileResponse(BASE/'static/index.html', headers={
            'Cache-Control': 'no-cache, must-revalidate', 'Pragma': 'no-cache'})

    legacy_pages = ('create.html', 'gestione_partecipanti.html',
                    'panoramica_torneo.html', 'tabellone_torneo.html',
                    'campione_sport_editorial.html')

    def legacy_page():
        return RedirectResponse('/', status_code=302)

    for page in legacy_pages:
        api.add_api_route(f'/{page}', legacy_page, include_in_schema=False)

    @api.get('/api/health')
    def health():
        return {'status':'ok','version':'0.9.1',
                'mode':'service' if mode=='service' else 'school-lan','auth':'teacher-login'}

    @api.get('/api/auth/session')
    def session_info(request: Request):
        session = getattr(request.state, 'teacher', None)
        teacher_info = None
        if session:
            with database(path) as db:
                row = db.execute('SELECT display_name FROM teachers WHERE id=?',
                                 (session['teacher_id'],)).fetchone()
            teacher_info = {'id': session['teacher_id'], 'email': session['email'],
                            'display_name': row[0] if row else ''}
        student = getattr(request.state,'platform_user',None)
        if not session and student:
            return {'authenticated':True,'role':'student','teacher':None,'student':platform_auth.public_user(student)}
        return {'authenticated': bool(session),
                'role': 'teacher' if session else 'student',
                'teacher': teacher_info}

    @api.post('/api/auth/login')
    def login(data: LoginInput, request: Request):
        key = request.client.host if request.client else 'unknown'
        if not auth.login_allowed(key):
            raise HTTPException(429,'Troppi tentativi. Riprova tra un minuto.')
        with database(path) as db:
            teacher_row = authenticate(db, data.email, data.password)
        if teacher_row is None:
            auth.record_failure(key)
            raise HTTPException(401,'Email o password non corretti')
        auth.record_success(key)
        response = JSONResponse({
            'authenticated': True, 'role': 'teacher',
            'teacher': {'id': teacher_row['id'], 'email': teacher_row['email'],
                        'display_name': teacher_row['display_name']},
        })
        signed = auth.issue(teacher_row['id'], teacher_row['email'])
        with database(path,True) as db:
            full = db.execute('SELECT * FROM teachers WHERE id=?',(teacher_row['id'],)).fetchone()
            user = ensure_platform_teacher(db,full)
            csrf = platform_auth.new_session(db,response,auth.cookie_secure,user['id'])
            from datetime import timedelta
            db.execute('INSERT INTO sessions VALUES (?,?,?,?)',(platform_auth.digest(signed),user['id'],csrf,
                       (platform_auth.now()+timedelta(seconds=auth.ttl)).isoformat()))
        response.set_cookie(COOKIE_NAME, signed,
                            max_age=auth.ttl, httponly=True,
                            samesite='lax', secure=auth.cookie_secure, path='/')
        return response

    @api.post('/api/auth/logout')
    def logout(request: Request):
        with database(path,True) as db:
            for name in (COOKIE_NAME,platform_auth.COOKIE):
                raw = request.cookies.get(name)
                if raw:
                    db.execute('DELETE FROM sessions WHERE token_hash=?',(platform_auth.digest(raw),))
        response = JSONResponse({'ok':True})
        response.delete_cookie(COOKIE_NAME, path='/')
        response.delete_cookie(platform_auth.COOKIE, path='/')
        return response

    @api.get('/api/tournaments')
    def list_tournaments(request: Request,
                         archived: Literal['exclude', 'include', 'only'] = 'exclude',
                         mine: bool = False):
        session = getattr(request.state, 'teacher', None)
        user = getattr(request.state,'platform_user',None)
        clauses, params = [], []
        if archived == 'exclude':
            clauses.append('archived_at IS NULL')
        elif archived == 'only':
            clauses.append('archived_at IS NOT NULL')
        if mine:
            if session is None and user is None:
                raise HTTPException(401, 'Accesso richiesto')
            if session:
                clauses.append('teacher_id=?')
                params.append(session['teacher_id'])
            else:
                clauses.append('id IN (SELECT tournament_id FROM students WHERE user_id=?)')
                params.append(user['id'])
        if user and user['role']=='student':
            clauses.append('(published=1 OR id IN (SELECT tournament_id FROM students WHERE user_id=?))')
            params.append(user['id'])
        elif session is None:
            clauses.append('published=1')
        else:
            clauses.append('(published=1 OR teacher_id=?)')
            params.append(session['teacher_id'])
        where = (' WHERE ' + ' AND '.join(clauses)) if clauses else ''
        with database(path) as db:
            states = svc.summary_states(db)
            counts = {row['tournament_id']: row['total'] for row in svc.rows(
                db, 'SELECT tournament_id,count(*) AS total FROM teams '
                    'GROUP BY tournament_id')}
            result = []
            for tournament in svc.rows(
                    db, f'SELECT * FROM tournaments{where} ORDER BY id DESC', tuple(params)):
                owner = bool(session and
                             tournament['teacher_id'] == session['teacher_id'])
                state = states.get(tournament['id'], {
                    'status': 'draft', 'progress': {'completed': 0, 'total': 0},
                    'champion_team_id': None})
                result.append(dict(
                    svc.visible_tournament(tournament, owner),
                    status=state['status'], progress=state['progress'],
                    champion_team_id=state['champion_team_id'],
                    archived=bool(tournament['archived_at']),
                    team_count=counts.get(tournament['id'], 0),
                    can_manage=owner,
                ))
            return result

    @api.post('/api/tournaments',status_code=201)
    def create_tournament(data: TournamentInput, request: Request):
        session = teacher(request)
        with database(path,True) as db:
            tid = svc.create(db, data, teacher_id=session['teacher_id'])
            attach_tournament(db,tid,session['teacher_id'])
            db.execute('UPDATE tournaments SET published=1 WHERE id=?',(tid,))
            return {'id':tid}

    @api.patch('/api/tournaments/{tid}')
    def update_tournament(tid: int, data: TournamentUpdate, request: Request):
        session = teacher(request)
        with database(path,True) as db:
            svc.require_owner(db, tid, session['teacher_id'])
            return svc.update_tournament(db,tid,data)

    @api.post('/api/tournaments/{tid}/archive')
    def archive_tournament(tid: int, request: Request):
        session = teacher(request)
        with database(path,True) as db:
            svc.require_owner(db, tid, session['teacher_id'])
            return svc.set_archived(db,tid,True)

    @api.post('/api/tournaments/{tid}/restore')
    def restore_tournament(tid: int, request: Request):
        session = teacher(request)
        with database(path,True) as db:
            svc.require_owner_any(db, tid, session['teacher_id'])
            return svc.set_archived(db,tid,False)

    @api.get('/api/tournaments/{tid}')
    def get_tournament(tid: int, request: Request):
        session = getattr(request.state, 'teacher', None)
        with database(path) as db:
            if not visible(db,request,svc.required(db,tid)):
                raise HTTPException(404,'Torneo non trovato')
            result=svc.detail(db, tid, viewer_id=(session or {}).get('teacher_id'))
            user=getattr(request.state,'platform_user',None)
            member=db.execute('SELECT team_id FROM students WHERE tournament_id=? AND user_id=?',(tid,user['id'])).fetchone() if user else None
            result['student_team_id']=member[0] if member else None
            return result

    @api.get('/api/tournaments/{tid}/teams/{team_id}')
    def get_team(tid: int, team_id: int, request: Request):
        session = getattr(request.state, 'teacher', None)
        with database(path) as db:
            if not visible(db,request,svc.required(db,tid)):
                raise HTTPException(404,'Torneo non trovato')
            result=svc.team_detail(db, tid, team_id,viewer_id=(session or {}).get('teacher_id'))
            user=getattr(request.state,'platform_user',None)
            member=db.execute('SELECT 1 FROM students WHERE tournament_id=? AND team_id=? AND user_id=?',(tid,team_id,user['id'])).fetchone() if user else None
            if not result['can_manage'] and not member:
                result['players']=[]
            return result

    @api.get('/api/public/{token}')
    def public_tournament(token: str):
        with database(path) as db:
            t = db.execute('SELECT id FROM tournaments WHERE public_token=? AND published=1',(token,)).fetchone()
            if not t:
                raise HTTPException(404,'Link del torneo non trovato')
            detail = svc.detail(db,t[0],public=True)
            detail['can_manage'] = False
            return detail

    @api.post('/api/tournaments/{tid}/teams',status_code=201)
    def add_team(tid: int,data: TeamInput, request: Request):
        session = teacher(request)
        with database(path,True) as db:
            svc.require_owner(db, tid, session['teacher_id'])
            if svc.games(db,tid):
                raise HTTPException(409,'Partecipanti bloccati dopo la generazione degli incontri')
            if len(svc.teams(db,tid)) >= 32:
                raise HTTPException(422,'Il torneo supporta al massimo 32 partecipanti')
            if any(t['name'].casefold()==data.name.casefold() for t in svc.teams(db,tid)):
                raise HTTPException(409,'Questo nome è già presente')
            cur = db.execute('INSERT INTO teams(tournament_id,name) VALUES (?,?)',(tid,data.name))
            svc.audit(db,tid,'team_added',{'name':data.name})
            return {'id':cur.lastrowid}

    @api.patch('/api/tournaments/{tid}/teams/{team_id}')
    def rename_team(tid: int,team_id: int,data: TeamInput, request: Request):
        session = teacher(request)
        with database(path,True) as db:
            svc.require_owner(db, tid, session['teacher_id'])
            if any(t['id']!=team_id and t['name'].casefold()==data.name.casefold() for t in svc.teams(db,tid)):
                raise HTTPException(409,'Questo nome è già presente')
            cur = db.execute('UPDATE teams SET name=? WHERE id=? AND tournament_id=?',(data.name,team_id,tid))
            if not cur.rowcount:
                raise HTTPException(404,'Partecipante non trovato')
            svc.audit(db,tid,'team_renamed',{'id':team_id,'name':data.name})
            return {'ok':True}

    @api.delete('/api/tournaments/{tid}/teams/{team_id}',status_code=204)
    def delete_team(tid: int,team_id: int, request: Request):
        session = teacher(request)
        with database(path,True) as db:
            svc.require_owner(db, tid, session['teacher_id'])
            if svc.games(db,tid):
                raise HTTPException(409,'Partecipanti bloccati dopo la generazione degli incontri')
            if not db.execute('DELETE FROM teams WHERE id=? AND tournament_id=?',(team_id,tid)).rowcount:
                raise HTTPException(404,'Partecipante non trovato')

    @api.get('/api/tournaments/{tid}/teams/{team_id}/players')
    def list_players(tid: int, team_id: int, request: Request):
        with database(path) as db:
            t=svc.required(db,tid)
            session=getattr(request.state,'teacher',None)
            user=getattr(request.state,'platform_user',None)
            member=db.execute('SELECT 1 FROM students WHERE tournament_id=? AND team_id=? AND user_id=?',(tid,team_id,user['id'])).fetchone() if user else None
            if not (session and session['teacher_id']==t['teacher_id']) and not member:
                raise HTTPException(403,'Rose riservate al docente e ai membri della squadra')
            return {'players': svc.players(db, tid, team_id)}

    @api.post('/api/tournaments/{tid}/teams/{team_id}/players', status_code=201)
    def add_player(tid: int, team_id: int, data: PlayerInput, request: Request):
        session = teacher(request)
        with database(path, True) as db:
            svc.require_owner(db, tid, session['teacher_id'])
            return svc.add_player(db, tid, team_id, data)

    @api.delete('/api/tournaments/{tid}/teams/{team_id}/players/{player_id}', status_code=204)
    def remove_player(tid: int, team_id: int, player_id: int, request: Request):
        session = teacher(request)
        with database(path, True) as db:
            svc.require_owner(db, tid, session['teacher_id'])
            svc.remove_player(db, tid, team_id, player_id)

    @api.post('/api/tournaments/{tid}/generate')
    def generate(tid: int, request: Request):
        session = teacher(request)
        with database(path,True) as db:
            svc.require_owner(db, tid, session['teacher_id'])
            return svc.generate(db,tid)

    @api.patch('/api/tournaments/{tid}/matches/{mid}')
    def result(tid: int,mid: int,data: ResultInput, request: Request):
        session = teacher(request)
        with database(path,True) as db:
            svc.require_owner(db, tid, session['teacher_id'])
            result=svc.save_result(db,tid,mid,data.version,data.home_score,data.away_score,
                                   data.invalidate, data.sets)
            record_legacy_result(db,session['teacher_id'],tid,mid,data.version)
            return result

    @api.delete('/api/tournaments/{tid}/matches/{mid}/result')
    def clear_result(tid: int,mid: int,data: ClearInput, request: Request):
        session = teacher(request)
        with database(path,True) as db:
            svc.require_owner(db, tid, session['teacher_id'])
            result=svc.save_result(db,tid,mid,data.version,invalidate=data.invalidate)
            record_legacy_result(db,session['teacher_id'],tid,mid,data.version)
            return result

    @api.patch('/api/tournaments/{tid}/matches/{mid}/schedule')
    def schedule(tid: int,mid: int,data: ScheduleInput, request: Request):
        session = teacher(request)
        with database(path,True) as db:
            svc.require_owner(db, tid, session['teacher_id'])
            return svc.schedule(db,tid,mid,data)

    @api.get('/api/tournaments/{tid}/export.csv')
    def export(tid: int, request: Request):
        with database(path) as db:
            if not visible(db,request,svc.required(db,tid)):
                raise HTTPException(404,'Torneo non trovato')
            state=svc.detail(db,tid)
        names={t['id']:t['name'] for t in state['teams']}
        out=io.StringIO(newline='')
        writer=csv.writer(out)
        writer.writerow(['Fase','Girone','Turno','Casa','Ospite','Punti casa','Punti ospite','Data UTC','Campo','Dettaglio set'])
        def safe(value):
            text=str(value or '')
            return "'"+text if text.startswith(('=','+','-','@','\t','\r')) else text
        for m in state['matches']:
            writer.writerow([m['kind'],m['group_id'] or '',m['round_no'],safe(names.get(m['home_team_id'],'')),
                             safe(names.get(m['away_team_id'],'')),
                             m['home_score'] if m['home_score'] is not None else '',
                             m['away_score'] if m['away_score'] is not None else '',
                             m['scheduled_at'] or '',safe(m['location']),
                             ' '.join(f"{s['home']}-{s['away']}" for s in m.get('sets', []))])
        return Response('\ufeff'+out.getvalue(),media_type='text/csv',
                        headers={'Content-Disposition':f'attachment; filename="torneo-{tid}.csv"'})

    @api.get('/api/sports')
    def list_sports():
        """Canonical catalog read from the database, so UI and validation agree."""
        with database(path) as db:
            return {'sports': [sport_rules.summary(config)
                               for config in sport_rules.list_sports(db)]}

    @api.get('/api/sports/{sport_name}')
    def get_sport_info(sport_name: str):
        with database(path) as db:
            config = sport_rules.get_sport(db, sport_name)
        if not config:
            raise HTTPException(404, 'Sport non trovato')
        return sport_rules.summary(config)

    @api.get('/api/sports/{sport_name}/variants/{variant_slug}')
    def get_variant_info(sport_name: str, variant_slug: str):
        with database(path) as db:
            variant = sport_rules.get_variant(db, sport_name, variant_slug)
        if not variant:
            raise HTTPException(404, 'Variante non trovata')
        return sport_rules.variant_detail(variant)

    @api.get('/api/variants/{variant_slug}')
    def get_variant_shortcut(variant_slug: str):
        with database(path) as db:
            variant = sport_rules.get_variant_by_slug(db, variant_slug)
        if not variant:
            raise HTTPException(404, 'Variante non trovata')
        return sport_rules.variant_detail(variant)

    return api


app = create_app()
