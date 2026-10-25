import pytest
from fastapi.testclient import TestClient
from app import create_app

TEACHER_EMAIL = 'prof@test.local'
TEACHER_PASSWORD = 'password-di-test'


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path / 'test.sqlite3', seed=False,
                     admin_email=TEACHER_EMAIL, admin_password=TEACHER_PASSWORD,
                     session_secret='test-secret-lungo-abbastanza')
    with TestClient(app) as instance:
        response = instance.post('/api/auth/login', json={
            'email': TEACHER_EMAIL, 'password': TEACHER_PASSWORD})
        assert response.status_code == 200, response.text
        yield instance


def make(client, fmt='round_robin', n=4, **options):
    payload=dict(name='Torneo di prova',sport='Calcio',format=fmt,
                 team_names=[f'Squadra {i+1:02}' for i in range(n)])
    payload.update(options)
    response=client.post('/api/tournaments',json=payload)
    assert response.status_code==201,response.text
    tid=response.json()['id']
    response=client.post(f'/api/tournaments/{tid}/generate')
    assert response.status_code==200,response.text
    return tid


def state(client,tid):
    response=client.get(f'/api/tournaments/{tid}')
    assert response.status_code==200,response.text
    return response.json()


def score(client,tid,m,home=2,away=1,**extra):
    return client.patch(f'/api/tournaments/{tid}/matches/{m["id"]}',
                        json=dict(home_score=home,away_score=away,version=m['version'],**extra))
