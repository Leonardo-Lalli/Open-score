"""Open Score API: local demo by default, single-organiser auth for the LAN."""
import csv
import io
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from auth import COOKIE_NAME, build as build_auth
from db import BASE, database, initialize
from demo import load_examples
from schemas import (ClearInput, LoginInput, ResultInput, ScheduleInput, TeamInput,
                     TournamentInput, TournamentUpdate)
import services as svc
import sport_rules


def create_app(db_path: str | Path | None = None, seed: bool = True, *,
               admin_password: str | None = None, api_token: str | None = None,
               session_secret: str | bytes | None = None,
               allowed_hosts: list[str] | None = None,
               cookie_secure: bool | None = None) -> FastAPI:
    path = Path(db_path or os.environ.get('TORNEO_DB_PATH', str(BASE/'data/open_score.sqlite3')))
    fresh = initialize(path)
    auth = build_auth(BASE, password=admin_password, api_token=api_token,
                      secret=session_secret, cookie_secure=cookie_secure)

    default_hosts = ['127.0.0.1', 'localhost', 'testserver']
    configured = allowed_hosts
    if configured is None:
        configured = [host.strip() for host in
                      os.environ.get('TORNEO_ALLOWED_HOSTS', '').split(',') if host.strip()]
    hosts = list(dict.fromkeys(default_hosts + list(configured)))

    api = FastAPI(title='Open Score · API', version='0.3.0',
                  description='Applicazione originale per i tornei scolastici. Nessun collegamento alle API di Score7.')
    api.state.db_path = path
    api.state.auth = auth
    api.state.allowed_hosts = hosts
    api.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
    api.mount('/static',StaticFiles(directory=BASE/'static'),name='static')

    @api.middleware('http')
    async def local_security(request: Request, call_next):
        # Block cross-origin browser writes, then require an admin session for
        # every mutation when a password or API token is configured.
        origin = request.headers.get('origin')
        if request.method not in ('GET','HEAD','OPTIONS') and origin:
            if origin != str(request.base_url).rstrip('/'):
                return Response('Origine non consentita',status_code=403)
        if (auth.required and request.method not in ('GET','HEAD','OPTIONS')
                and request.url.path.startswith('/api')
                and request.url.path not in ('/api/auth/login','/api/auth/logout')
                and not auth.is_authenticated(request)):
            return JSONResponse({'detail':'Accesso richiesto'},status_code=401)
        response = await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        if auth.cookie_secure:
            response.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
        if request.url.path not in ('/docs','/redoc','/docs/oauth2-redirect'):
            response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'"
        return response

    @api.get('/',include_in_schema=False)
    @api.get('/public/{token}',include_in_schema=False)
    def homepage(token: str = ''):
        return FileResponse(BASE/'static/index.html')

    @api.get('/api/health')
    def health():
        return {'status':'ok','version':'0.3.0',
                'mode':'school-lan' if auth.required else 'local-demo',
                'auth':'required' if auth.required else 'disabled'}

    @api.get('/api/auth/session')
    def session_info(request: Request):
        authenticated = (not auth.required) or auth.is_authenticated(request)
        return {'authenticated':authenticated,'auth_required':auth.required,
                'role':'admin' if authenticated else 'viewer'}

    @api.post('/api/auth/login')
    def login(data: LoginInput, request: Request):
        if not auth.required:
            return {'authenticated':True,'auth_required':False,'role':'admin'}
        key = request.client.host if request.client else 'unknown'
        if not auth.login_allowed(key):
            raise HTTPException(429,'Troppi tentativi. Riprova tra un minuto.')
        if not auth.check_password(data.password):
            auth.record_failure(key)
            raise HTTPException(401,'Password non corretta')
        auth.record_success(key)
        response = JSONResponse({'authenticated':True,'auth_required':True,'role':'admin'})
        response.set_cookie(COOKIE_NAME, auth.issue(), max_age=auth.ttl, httponly=True,
                            samesite='lax', secure=auth.cookie_secure, path='/')
        return response

    @api.post('/api/auth/logout')
    def logout():
        response = JSONResponse({'ok':True})
        response.delete_cookie(COOKIE_NAME, path='/')
        return response

    @api.get('/api/tournaments')
    def list_tournaments(archived: Literal['exclude', 'include', 'only'] = 'exclude'):
        where = {'exclude': 'WHERE archived_at IS NULL',
                 'only': 'WHERE archived_at IS NOT NULL'}.get(archived, '')
        with database(path) as db:
            return [dict(t, **{k:v for k,v in svc.detail(db,t['id']).items()
                    if k in ('status','progress','champion_team_id')},
                    archived=bool(t['archived_at']),
                    team_count=db.execute('SELECT count(*) FROM teams WHERE tournament_id=?',(t['id'],)).fetchone()[0])
                    for t in svc.rows(db,f'SELECT * FROM tournaments {where} ORDER BY id DESC')]

    @api.post('/api/tournaments',status_code=201)
    def create_tournament(data: TournamentInput):
        with database(path,True) as db:
            return {'id':svc.create(db,data)}

    @api.patch('/api/tournaments/{tid}')
    def update_tournament(tid: int, data: TournamentUpdate):
        with database(path,True) as db:
            return svc.update_tournament(db,tid,data)

    @api.post('/api/tournaments/{tid}/archive')
    def archive_tournament(tid: int):
        with database(path,True) as db:
            return svc.set_archived(db,tid,True)

    @api.post('/api/tournaments/{tid}/restore')
    def restore_tournament(tid: int):
        with database(path,True) as db:
            return svc.set_archived(db,tid,False)

    @api.get('/api/tournaments/{tid}')
    def get_tournament(tid: int):
        with database(path) as db:
            return svc.detail(db,tid)

    @api.get('/api/tournaments/{tid}/teams/{team_id}')
    def get_team(tid: int, team_id: int):
        with database(path) as db:
            return svc.team_detail(db,tid,team_id)

    @api.get('/api/public/{token}')
    def public_tournament(token: str):
        with database(path) as db:
            t = db.execute('SELECT id FROM tournaments WHERE public_token=?',(token,)).fetchone()
            if not t:
                raise HTTPException(404,'Link del torneo non trovato')
            return svc.detail(db,t[0],public=True)

    @api.post('/api/demo')
    def examples():
        with database(path,True) as db:
            return load_examples(db)

    @api.post('/api/tournaments/{tid}/teams',status_code=201)
    def add_team(tid: int,data: TeamInput):
        with database(path,True) as db:
            svc.active(db,tid)
            if svc.games(db,tid):
                raise HTTPException(409,'Partecipanti bloccati dopo la generazione degli incontri')
            if len(svc.teams(db,tid)) >= 32:
                raise HTTPException(422,'La demo supporta al massimo 32 partecipanti')
            if any(t['name'].casefold()==data.name.casefold() for t in svc.teams(db,tid)):
                raise HTTPException(409,'Questo nome è già presente')
            cur = db.execute('INSERT INTO teams(tournament_id,name) VALUES (?,?)',(tid,data.name))
            svc.audit(db,tid,'team_added',{'name':data.name})
            return {'id':cur.lastrowid}

    @api.patch('/api/tournaments/{tid}/teams/{team_id}')
    def rename_team(tid: int,team_id: int,data: TeamInput):
        with database(path,True) as db:
            svc.active(db,tid)
            if any(t['id']!=team_id and t['name'].casefold()==data.name.casefold() for t in svc.teams(db,tid)):
                raise HTTPException(409,'Questo nome è già presente')
            cur = db.execute('UPDATE teams SET name=? WHERE id=? AND tournament_id=?',(data.name,team_id,tid))
            if not cur.rowcount:
                raise HTTPException(404,'Partecipante non trovato')
            svc.audit(db,tid,'team_renamed',{'id':team_id,'name':data.name})
            return {'ok':True}

    @api.delete('/api/tournaments/{tid}/teams/{team_id}',status_code=204)
    def delete_team(tid: int,team_id: int):
        with database(path,True) as db:
            svc.active(db,tid)
            if svc.games(db,tid):
                raise HTTPException(409,'Partecipanti bloccati dopo la generazione degli incontri')
            if not db.execute('DELETE FROM teams WHERE id=? AND tournament_id=?',(team_id,tid)).rowcount:
                raise HTTPException(404,'Partecipante non trovato')

    @api.post('/api/tournaments/{tid}/generate')
    def generate(tid: int):
        with database(path,True) as db:
            return svc.generate(db,tid)

    @api.patch('/api/tournaments/{tid}/matches/{mid}')
    def result(tid: int,mid: int,data: ResultInput):
        with database(path,True) as db:
            return svc.save_result(db,tid,mid,data.version,data.home_score,data.away_score,data.invalidate)

    @api.delete('/api/tournaments/{tid}/matches/{mid}/result')
    def clear_result(tid: int,mid: int,data: ClearInput):
        with database(path,True) as db:
            return svc.save_result(db,tid,mid,data.version,invalidate=data.invalidate)

    @api.patch('/api/tournaments/{tid}/matches/{mid}/schedule')
    def schedule(tid: int,mid: int,data: ScheduleInput):
        with database(path,True) as db:
            return svc.schedule(db,tid,mid,data)

    @api.get('/api/tournaments/{tid}/export.csv')
    def export(tid: int):
        with database(path) as db:
            state=svc.detail(db,tid)
        names={t['id']:t['name'] for t in state['teams']}
        out=io.StringIO(newline='')
        writer=csv.writer(out)
        writer.writerow(['Fase','Girone','Turno','Casa','Ospite','Punti casa','Punti ospite','Data UTC','Campo'])
        def safe(value):
            text=str(value or '')
            return "'"+text if text.startswith(('=','+','-','@','\t','\r')) else text
        for m in state['matches']:
            writer.writerow([m['kind'],m['group_id'] or '',m['round_no'],safe(names.get(m['home_team_id'],'')),
                             safe(names.get(m['away_team_id'],'')),
                             m['home_score'] if m['home_score'] is not None else '',
                             m['away_score'] if m['away_score'] is not None else '',
                             m['scheduled_at'] or '',safe(m['location'])])
        return Response('\ufeff'+out.getvalue(),media_type='text/csv',
                        headers={'Content-Disposition':f'attachment; filename="torneo-{tid}.csv"'})
    
    @api.get('/api/sports')
    def list_sports():
        """Canonical catalog read from the database, so UI and validation agree."""
        with database(path) as db:
            return {'sports': [sport_rules.summary(config)
                               for config in sport_rules.list_configs(db)]}

    @api.get('/api/sports/{sport_name}')
    def get_sport_info(sport_name: str):
        with database(path) as db:
            config = sport_rules.get_config(db, sport_name)
        if not config:
            raise HTTPException(404, 'Sport non trovato')
        return {**sport_rules.summary(config), 'rules': config.rules}

    if seed and fresh:
        with database(path,True) as db:
            load_examples(db)
    return api


app = create_app()
