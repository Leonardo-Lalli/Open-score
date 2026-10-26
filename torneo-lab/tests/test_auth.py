import time

import pytest
from fastapi.testclient import TestClient

from app import create_app
from auth import Auth, hash_password, verify_password

EMAIL = 'prof@test.local'
PASSWORD = 'password-lunga'
SECRET = 'segreto-di-test-lungo-abbastanza'


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / 'auth.sqlite3',
                               admin_email=EMAIL, admin_password=PASSWORD,
                               session_secret=SECRET)) as instance:
        yield instance


def test_health_reports_teacher_login(client):
    body = client.get('/api/health').json()
    assert body['auth'] == 'teacher-login'
    assert body['mode'] == 'school-lan'


def test_reads_stay_public_and_writes_need_a_teacher(client):
    assert client.get('/api/tournaments').status_code == 200
    assert client.get('/api/sports').status_code == 200
    assert client.get('/api/auth/session').json() == {
        'authenticated': False, 'role': 'student', 'teacher': None,
    }

    blocked = client.post('/api/tournaments', json={
        'name': 'Coppa riservata', 'sport': 'Calcio',
        'team_names': ['Alfa', 'Beta'],
    })
    assert blocked.status_code == 401
    assert blocked.json()['detail'] == 'Accesso richiesto'


def test_login_grants_and_logout_revokes_the_session(client):
    assert client.post('/api/auth/login', json={
        'email': EMAIL, 'password': 'sbagliata'}).status_code == 401
    assert client.post('/api/auth/login', json={
        'email': 'sconosciuto@test.local', 'password': PASSWORD}).status_code == 401

    login = client.post('/api/auth/login', json={'email': EMAIL, 'password': PASSWORD})
    assert login.status_code == 200, login.text
    assert login.json()['role'] == 'teacher'
    assert login.json()['teacher']['email'] == EMAIL
    session = client.get('/api/auth/session').json()
    assert session['authenticated'] is True
    assert session['teacher']['email'] == EMAIL

    created = client.post('/api/tournaments', json={
        'name': 'Coppa autorizzata', 'sport': 'Calcio',
        'team_names': ['Alfa', 'Beta'],
    })
    assert created.status_code == 201, created.text
    detail = client.get(f"/api/tournaments/{created.json()['id']}").json()
    assert detail['can_manage'] is True

    assert client.post('/api/auth/logout').status_code == 200
    assert client.get('/api/auth/session').json()['authenticated'] is False
    assert client.post('/api/tournaments', json={
        'name': 'Coppa negata', 'sport': 'Calcio', 'team_names': ['Alfa', 'Beta'],
    }).status_code == 401


def test_login_requires_a_valid_email(client):
    assert client.post('/api/auth/login', json={
        'email': 'non-una-email', 'password': PASSWORD}).status_code == 422
    assert client.post('/api/auth/login', json={'password': PASSWORD}).status_code == 422


def test_login_is_throttled_after_repeated_failures(client):
    for _ in range(5):
        assert client.post('/api/auth/login', json={
            'email': EMAIL, 'password': 'no'}).status_code == 401
    blocked = client.post('/api/auth/login', json={'email': EMAIL, 'password': 'no'})
    assert blocked.status_code == 429
    assert 'Riprova' in blocked.json()['detail']


def test_without_a_bootstrap_teacher_the_app_stays_read_only(tmp_path):
    with TestClient(create_app(tmp_path / 'open.sqlite3',
                               session_secret=SECRET)) as local:
        assert local.get('/api/health').json()['auth'] == 'teacher-login'
        assert local.get('/api/auth/session').json()['role'] == 'student'
        assert local.post('/api/auth/login', json={
            'email': EMAIL, 'password': PASSWORD}).status_code == 401
        assert local.post('/api/tournaments', json={
            'name': 'Coppa locale', 'sport': 'Calcio',
            'team_names': ['Alfa', 'Beta'],
        }).status_code == 401


def test_sessions_issued_in_the_same_second_are_unique():
    auth = Auth(secret=b'synthetic-test-secret')
    first = auth.issue(1, EMAIL, now=1000)
    second = auth.issue(1, EMAIL, now=1000)
    assert first != second
    assert auth.decode(first, now=1001) == auth.decode(second, now=1001)


def test_password_hash_round_trip():
    encoded = hash_password(PASSWORD)
    assert encoded.startswith('pbkdf2_sha256$')
    assert verify_password(PASSWORD, encoded) is True
    assert verify_password('sbagliata', encoded) is False
    assert verify_password(PASSWORD, 'formato-non-valido') is False
    with pytest.raises(ValueError):
        hash_password('corta')


def test_expired_and_tampered_tokens_are_rejected():
    auth = Auth(secret=SECRET.encode(), ttl=60)
    token = auth.issue(7, EMAIL, now=time.time() - 120)
    assert auth.valid(token) is False
    fresh = auth.issue(7, EMAIL)
    decoded = auth.decode(fresh)
    assert decoded is not None
    assert decoded['teacher_id'] == 7
    assert decoded['email'] == EMAIL
    assert auth.valid(fresh[:-1] + ('0' if fresh[-1] != '0' else '1')) is False
    assert auth.valid(None) is False
    assert auth.valid('non-un-token') is False
