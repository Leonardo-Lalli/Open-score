import time

import pytest
from fastapi.testclient import TestClient

from app import create_app
from auth import Auth

PASSWORD = 'corretta-cavallo-batteria'
TOKEN = 'token-per-gli-script'
SECRET = 'segreto-di-test-lungo-abbastanza'


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / 'auth.sqlite3', seed=False,
                               admin_password=PASSWORD, api_token=TOKEN,
                               session_secret=SECRET)) as instance:
        yield instance


def test_health_reports_required_auth(client):
    body = client.get('/api/health').json()
    assert body['auth'] == 'required'
    assert body['mode'] == 'school-lan'


def test_reads_stay_public_and_writes_need_a_session(client):
    assert client.get('/api/tournaments').status_code == 200
    assert client.get('/api/sports').status_code == 200
    assert client.get('/api/auth/session').json() == {
        'authenticated': False, 'auth_required': True, 'role': 'viewer',
    }

    blocked = client.post('/api/tournaments', json={
        'name': 'Coppa riservata', 'sport': 'Calcio',
        'team_names': ['Alfa', 'Beta'],
    })
    assert blocked.status_code == 401
    assert blocked.json()['detail'] == 'Accesso richiesto'


def test_login_grants_and_logout_revokes_the_session(client):
    assert client.post('/api/auth/login', json={'password': 'sbagliata'}).status_code == 401

    login = client.post('/api/auth/login', json={'password': PASSWORD})
    assert login.status_code == 200, login.text
    assert login.json()['role'] == 'admin'
    assert client.get('/api/auth/session').json()['authenticated'] is True

    created = client.post('/api/tournaments', json={
        'name': 'Coppa autorizzata', 'sport': 'Calcio',
        'team_names': ['Alfa', 'Beta'],
    })
    assert created.status_code == 201, created.text

    assert client.post('/api/auth/logout').status_code == 200
    assert client.get('/api/auth/session').json()['authenticated'] is False
    assert client.post('/api/tournaments', json={
        'name': 'Coppa negata', 'sport': 'Calcio', 'team_names': ['Alfa', 'Beta'],
    }).status_code == 401


def test_bearer_token_allows_scripted_writes(client):
    headers = {'Authorization': f'Bearer {TOKEN}'}
    created = client.post('/api/tournaments', headers=headers, json={
        'name': 'Coppa da script', 'sport': 'Calcio', 'team_names': ['Alfa', 'Beta'],
    })
    assert created.status_code == 201, created.text
    assert client.post('/api/tournaments', headers={'Authorization': 'Bearer errato'},
                       json={'name': 'No', 'sport': 'Calcio',
                             'team_names': ['Alfa', 'Beta']}).status_code == 401


def test_login_is_throttled_after_repeated_failures(client):
    for _ in range(5):
        assert client.post('/api/auth/login', json={'password': 'no'}).status_code == 401
    blocked = client.post('/api/auth/login', json={'password': 'no'})
    assert blocked.status_code == 429
    assert 'Riprova' in blocked.json()['detail']


def test_auth_can_stay_disabled_for_the_local_demo(tmp_path):
    with TestClient(create_app(tmp_path / 'open.sqlite3', seed=False,
                               session_secret=SECRET)) as local:
        assert local.get('/api/health').json()['auth'] == 'disabled'
        assert local.get('/api/auth/session').json()['authenticated'] is True
        assert local.post('/api/tournaments', json={
            'name': 'Coppa locale', 'sport': 'Calcio', 'team_names': ['Alfa', 'Beta'],
        }).status_code == 201


def test_expired_and_tampered_tokens_are_rejected():
    auth = Auth(password=PASSWORD, secret=SECRET.encode(), ttl=60)
    token = auth.issue(now=time.time() - 120)
    assert auth.valid(token) is False
    fresh = auth.issue()
    assert auth.valid(fresh) is True
    assert auth.valid(fresh[:-1] + ('0' if fresh[-1] != '0' else '1')) is False
    assert auth.valid(None) is False
    assert auth.valid('non-un-token') is False
