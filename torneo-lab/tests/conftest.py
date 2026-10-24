import pytest
from fastapi.testclient import TestClient
from app import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path/'test.sqlite3',seed=False)) as instance:
        yield instance


def make(client, fmt='round_robin', n=4, **options):
    payload=dict(name='Torneo di prova',sport='Calcio',format=fmt,
                 team_names=[f'Squadra {i+1:02}' for i in range(n)],**options)
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
