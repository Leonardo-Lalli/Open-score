import csv
import io
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from app import create_app
from conftest import make,score,state


def test_round_robin_flow(client):
    tid=make(client)
    data=state(client,tid)
    assert len(data['matches'])==6
    assert score(client,tid,data['matches'][0]).status_code==200
    assert state(client,tid)['standings'][0]['points']==3
    assert client.post(f'/api/tournaments/{tid}/generate').status_code==409
    assert client.post(f'/api/tournaments/{tid}/teams',json={'name':'Extra'}).status_code==409
    assert client.delete(f'/api/tournaments/{tid}/teams/{data["teams"][0]["id"]}').status_code==409


@pytest.mark.parametrize('n',[2,3,4,5,8,16,32])
def test_complete_knockout_with_byes(client,n):
    tid=make(client,'knockout',n)
    count=0
    while not state(client,tid)['champion_team_id']:
        playable=[m for m in state(client,tid)['matches'] if m['status']=='ready']
        assert playable
        for m in playable:
            assert score(client,tid,m).status_code==200
            count+=1
    data=state(client,tid)
    assert count==n-1
    assert data['status']=='completed'
    assert data['champion_team_id'] in [t['id'] for t in data['teams']]


def test_safe_knockout_correction_and_audit(client):
    tid=make(client,'knockout')
    for m in state(client,tid)['matches'][:2]:assert score(client,tid,m).status_code==200
    final=state(client,tid)['matches'][-1]
    assert score(client,tid,final).status_code==200
    semifinal=state(client,tid)['matches'][0]
    assert score(client,tid,semifinal,0,4).status_code==409
    assert state(client,tid)['champion_team_id'] is not None
    assert score(client,tid,semifinal,0,4,invalidate=True).status_code==200
    data=state(client,tid)
    assert data['champion_team_id'] is None
    assert data['matches'][-1]['home_score'] is None
    assert data['matches'][-1]['home_team_id']==semifinal['away_team_id']
    assert any(a['action']=='invalidated' for a in data['audit'])


def test_same_winner_correction_preserves_final(client):
    tid=make(client,'knockout')
    for m in state(client,tid)['matches'][:2]:score(client,tid,m)
    final=state(client,tid)['matches'][-1];score(client,tid,final)
    semi=state(client,tid)['matches'][0]
    assert score(client,tid,semi,5,1).status_code==200
    assert state(client,tid)['matches'][-1]['home_score']==2


def test_multiphase_16_teams_and_requalification(client):
    tid=make(client,'groups',16,group_count=4)
    initial=state(client,tid)
    assert len(initial['groups'])==4 and len(initial['matches'])==24
    for index,m in enumerate(initial['matches']):
        assert score(client,tid,m).status_code==200
        if index<23:assert len(state(client,tid)['stages'])==1
    data=state(client,tid)
    finals=[m for m in data['matches'] if m['kind']=='knockout']
    assert len(finals)==7
    assert len([m for m in finals if m['round_no']==1])==4
    qualified=[row['team_id'] for g in data['groups'] for row in g['standings'][:2]]
    assert sorted(qualified)==sorted(p for m in finals if m['round_no']==1 for p in (m['home_team_id'],m['away_team_id']))
    membership={t['id']:t['group_id'] for t in data['teams']}
    assert all(membership[m['home_team_id']]!=membership[m['away_team_id']] for m in finals if m['round_no']==1)
    while not state(client,tid)['champion_team_id']:
        for m in state(client,tid)['matches']:
            if m['kind']=='knockout' and m['status']=='ready':score(client,tid,m)
    old=state(client,tid)['matches'][0]
    assert score(client,tid,old,0,7).status_code==409
    assert score(client,tid,old,0,7,invalidate=True).status_code==200
    data=state(client,tid)
    assert data['champion_team_id'] is None
    assert len(data['stages'])==2
    assert all(m['home_score'] is None for m in data['matches'] if m['kind']=='knockout')
    assert not {m['id'] for m in finals} & {m['id'] for m in data['matches'] if m['kind']=='knockout'}
    assert score(client,tid,finals[0]).status_code==404


@pytest.mark.parametrize('payload',[{'name':'  '},{'name':'A'},{'name':'OK','team_names':['Alfa','alfa']},{'name':'OK','team_names':['  ']},{'name':'OK','sport':'Curling'},{'name':'OK','format':'swiss'}])
def test_tournament_validation(client,payload):
    assert client.post('/api/tournaments',json=payload).status_code==422
    assert client.get('/api/tournaments').json()==[]


@pytest.mark.parametrize('home,away',[(True,1),(1.2,1),('2',1),(-1,1),(1000,1),(None,1)])
def test_scores_strict_and_atomic(client,home,away):
    tid=make(client,'knockout');m=state(client,tid)['matches'][0]
    assert score(client,tid,m,home,away).status_code==422
    assert state(client,tid)['progress']['completed']==0


def test_tie_and_unready_bye_rejected(client):
    tid=make(client,'knockout',3)
    data=state(client,tid)
    bye=next(m for m in data['matches'] if m['is_bye'])
    assert score(client,tid,bye).status_code==409
    ready=next(m for m in data['matches'] if m['status']=='ready')
    assert score(client,tid,ready,1,1).status_code==422
    future=data['matches'][-1]
    assert score(client,tid,future).status_code==409


def test_result_clear_and_optimistic_version(client):
    tid=make(client);m=state(client,tid)['matches'][0]
    assert score(client,tid,m).status_code==200
    assert score(client,tid,m,4,1).status_code==409
    current=state(client,tid)['matches'][0]
    assert client.request('DELETE',f'/api/tournaments/{tid}/matches/{m["id"]}/result',json={'version':current['version']}).status_code==200
    assert state(client,tid)['progress']['completed']==0


def test_concurrent_results_only_one_wins(client):
    tid=make(client);m=state(client,tid)['matches'][0]
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses=list(pool.map(lambda x:score(client,tid,m,x,0).status_code,[1,2]))
    assert sorted(statuses)==[200,409]


def test_schedule_overlap_and_timezone(client):
    tid=make(client);matches=state(client,tid)['matches']
    first=matches[0];other=matches[1]
    body={'version':first['version'],'scheduled_at':'2026-11-03T10:00:00+01:00','location':'Campo A','duration':20}
    assert client.patch(f'/api/tournaments/{tid}/matches/{first["id"]}/schedule',json=body).status_code==200
    assert state(client,tid)['matches'][0]['scheduled_at']=='2026-11-03T09:00:00+00:00'
    body['version']=other['version']
    assert client.patch(f'/api/tournaments/{tid}/matches/{other["id"]}/schedule',json=body).status_code==409
    body['scheduled_at']='2026-11-03T10:20:00+01:00'
    assert client.patch(f'/api/tournaments/{tid}/matches/{other["id"]}/schedule',json=body).status_code==200
    body['scheduled_at']='2026-11-03T10:20:00'
    body['version']+=1
    assert client.patch(f'/api/tournaments/{tid}/matches/{other["id"]}/schedule',json=body).status_code==422


def test_demo_idempotent_and_reference_fidelity(client):
    first=client.post('/api/demo').json()['ids']
    assert client.post('/api/demo').json()['ids']==first
    data=state(client,first[0]);m=data['matches'][0]
    assert m['source_id']==117234055 and m['home_score'] is None and m['scheduled_at'] is None
    assert [p['source_id'] for p in data['teams']]==[23045803,23045804]
    assert data['stages'][0]['source_id']==53882484
    assert score(client,first[0],m).status_code==200
    assert client.post('/api/demo').json()['ids']==first
    assert state(client,first[0])['progress']['completed']==1


def test_public_read_only_and_no_private_fields(client):
    tid=make(client);token=state(client,tid)['tournament']['public_token']
    public=client.get('/api/public/'+token).json()
    assert public['public'] and 'audit' not in public
    assert 'public_token' not in public['tournament']
    assert client.patch('/api/public/'+token,json={}).status_code==405
    assert client.get('/api/public/invalido').status_code==404
    assert client.get('/public/'+token).status_code==200


def test_persistence_and_migration(tmp_path):
    path=tmp_path/'persist.sqlite3'
    with TestClient(create_app(path,False)) as c:
        tid=make(c);m=state(c,tid)['matches'][0];score(c,tid,m)
    with TestClient(create_app(path,False)) as c:
        assert state(c,tid)['progress']['completed']==1
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0]==5
        assert db.execute('PRAGMA foreign_key_check').fetchall()==[]


def test_cross_tournament_access_and_origin(client):
    a=make(client);b=make(client);m=state(client,b)['matches'][0]
    assert score(client,a,m).status_code==404
    assert client.post('/api/demo',headers={'Origin':'https://other.example'}).status_code==403
    assert client.get('/',headers={'Host':'other.example'}).status_code==400


def test_csv_zero_scores_and_formula_names(client):
    r=client.post('/api/tournaments',json={'name':'CSV test','team_names':['=1+1','Beta']})
    tid=r.json()['id'];client.post(f'/api/tournaments/{tid}/generate')
    m=state(client,tid)['matches'][0];score(client,tid,m,0,0)
    response=client.get(f'/api/tournaments/{tid}/export.csv')
    records=list(csv.reader(io.StringIO(response.text.lstrip('\ufeff'))))
    assert records[1][5:7]==['0','0']
    assert "'=1+1" in records[1]


def test_participant_editing_and_case_insensitive_duplicate(client):
    r=client.post('/api/tournaments',json={'name':'Bozza'});tid=r.json()['id']
    r=client.post(f'/api/tournaments/{tid}/teams',json={'name':'Alfa'});pid=r.json()['id']
    assert client.post(f'/api/tournaments/{tid}/teams',json={'name':'alfa'}).status_code==409
    assert client.patch(f'/api/tournaments/{tid}/teams/{pid}',json={'name':'Nuovo nome'}).status_code==200
    assert client.delete(f'/api/tournaments/{tid}/teams/{pid}').status_code==204


def test_version_one_database_migrates_without_data_loss(tmp_path):
    from db import BASE
    path=tmp_path/'v1.sqlite3'
    with sqlite3.connect(path) as db:
        db.executescript((BASE/'migrations/001_initial.sql').read_text(encoding='utf-8'))
        db.execute("INSERT INTO tournaments(id,name,sport,format,public_token) VALUES (1,'Coppa esistente','Calcio','knockout','old-token')")
        db.execute("INSERT INTO stages(id,tournament_id,ordinal,kind) VALUES (1,1,0,'knockout')")
        db.executemany('INSERT INTO teams(id,tournament_id,name) VALUES (?,1,?)',[(1,'Alfa'),(2,'Beta')])
        db.execute('INSERT INTO matches(id,tournament_id,stage_id,round_no,home_team_id,away_team_id,home_score,away_score,winner_team_id) VALUES (1,1,1,1,1,2,3,1,1)')
    with TestClient(create_app(path,False)) as c:
        data=state(c,1)
        assert data['champion_team_id']==1 and data['matches'][0]['home_score']==3
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0]==5
        assert db.execute('PRAGMA foreign_key_check').fetchall()==[]
