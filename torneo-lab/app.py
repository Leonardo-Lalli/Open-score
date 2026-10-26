"""Tournament API with an explicit legacy demo / authenticated service boundary."""
import csv
import io
import os
import re
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from db import BASE, database, initialize
from demo import load_examples
from schemas import ClearInput, ResultInput, ScheduleInput, TeamInput, TournamentInput
import services as svc
from v1_api import create_router


def create_app(db_path: str | Path | None = None, seed: bool = True, mode: str | None = None) -> FastAPI:
    mode = mode or os.environ.get('TORNEO_MODE', 'demo')
    if mode not in ('demo', 'service'):
        raise ValueError('TORNEO_MODE deve essere demo oppure service')
    public_origin = os.environ.get('TORNEO_PUBLIC_ORIGIN') if mode == 'service' else None
    hosts = ['127.0.0.1', 'localhost', 'testserver']
    if mode == 'service':
        hosts = [s.strip() for s in os.environ.get('TORNEO_ALLOWED_HOSTS', '').split(',') if s.strip()]
        parsed = urlparse(public_origin or '')
        if (not hosts or any('*' in s for s in hosts) or parsed.scheme != 'https' or
                parsed.hostname not in hosts or parsed.path not in ('', '/') or parsed.query or parsed.fragment or parsed.username):
            raise ValueError('Service richiede TORNEO_ALLOWED_HOSTS espliciti e TORNEO_PUBLIC_ORIGIN HTTPS coerente')
        public_origin = public_origin.rstrip('/')
    path = Path(db_path or os.environ.get('TORNEO_DB_PATH', str(BASE/'data/open_score.sqlite3')))
    fresh = initialize(path)
    api = FastAPI(title='Open Score API',version='0.3.0',
                  description='API V1 autenticata e demo locale compatibile. Nessun collegamento alle API di Score7.')
    api.state.db_path = path
    api.state.mode = mode
    api.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
    api.mount('/static',StaticFiles(directory=BASE/'static'),name='static')
    api.include_router(create_router(path, secure_cookies=mode == 'service', public_origin=public_origin))

    @api.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        if request.url.path.startswith('/api/v1'):
            if isinstance(exc.detail, dict):
                detail = dict(exc.detail)
                message = detail.pop('message', 'Operazione non riuscita')
                return JSONResponse(dict(detail=message, **detail), status_code=exc.status_code, headers=exc.headers)
            return JSONResponse(dict(detail=exc.detail, code={404:'not_found',409:'conflict',422:'invalid_input'}.get(exc.status_code, 'request_failed')),
                                status_code=exc.status_code, headers=exc.headers)
        return JSONResponse({'detail': exc.detail}, status_code=exc.status_code, headers=exc.headers)

    @api.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Never reflect passwords, invite tokens or arbitrary input into errors.
        errors = [{k: item[k] for k in ('loc', 'msg', 'type')} for item in exc.errors()]
        body = {'detail': errors}
        if request.url.path.startswith('/api/v1'):
            body['code'] = 'validation_error'
        return JSONResponse(body, status_code=422)

    @api.middleware('http')
    async def local_mutations(request: Request, call_next):
        route = request.url.path
        legacy = route.startswith('/api/') and not route.startswith('/api/v1/') and route != '/api/health'
        if mode == 'service' and legacy:
            return JSONResponse({'detail':'API demo disabilitate in modalità servizio','code':'legacy_disabled'}, status_code=404)
        legacy_match = re.fullmatch(r'/api/tournaments/(\d+)(?:/.*)?', route)
        if legacy_match:
            with database(path) as db:
                owner = db.execute('SELECT owner_id FROM tournaments WHERE id=?', (int(legacy_match[1]),)).fetchone()
                if owner and owner['owner_id'] is not None:
                    return JSONResponse({'detail':'Torneo non trovato'}, status_code=404)
        # Block cross-origin browser writes to the unauthed loopback demo.
        origin = request.headers.get('origin')
        if request.method not in ('GET','HEAD','OPTIONS') and origin:
            expected_origin = public_origin or str(request.base_url).rstrip('/')
            if origin != expected_origin:
                if route.startswith('/api/v1/'):
                    return JSONResponse({'detail':'Origine non consentita','code':'origin_forbidden'}, status_code=403)
                return Response('Origine non consentita',status_code=403)
        response = await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        if route.startswith('/api/v1/'):
            response.headers['Cache-Control'] = 'no-store'
        if request.url.path not in ('/docs','/redoc','/docs/oauth2-redirect'):
            response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'"
        return response

    @api.get('/',include_in_schema=False)
    @api.get('/public/{token}',include_in_schema=False)
    def homepage(token: str = ''):
        return FileResponse(BASE/'static/index.html')

    @api.get('/api/health')
    def health():
        return {'status':'ok','version':'0.3.0','mode':'local-demo' if mode == 'demo' else 'service'}

    @api.get('/api/tournaments')
    def list_tournaments():
        with database(path) as db:
            return [dict(t, **{k:v for k,v in svc.detail(db,t['id']).items()
                    if k in ('status','progress','champion_team_id')},
                    team_count=db.execute('SELECT count(*) FROM teams WHERE tournament_id=?',(t['id'],)).fetchone()[0])
                    for t in svc.rows(db,'SELECT * FROM tournaments WHERE owner_id IS NULL ORDER BY id DESC')]

    @api.post('/api/tournaments',status_code=201)
    def create_tournament(data: TournamentInput):
        with database(path,True) as db:
            return {'id':svc.create(db,data)}

    @api.get('/api/tournaments/{tid}')
    def get_tournament(tid: int):
        with database(path) as db:
            return svc.detail(db,tid)

    @api.get('/api/public/{token}')
    def public_tournament(token: str):
        with database(path) as db:
            t = db.execute('SELECT id FROM tournaments WHERE public_token=? AND owner_id IS NULL',(token,)).fetchone()
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
            svc.required(db,tid)
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
            svc.required(db,tid)
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
            svc.required(db,tid)
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

    if seed and fresh and mode == 'demo':
        with database(path,True) as db:
            load_examples(db)
    return api


app = create_app()
