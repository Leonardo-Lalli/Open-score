from typing import get_args

import pytest
from fastapi.testclient import TestClient

from app import create_app
from schemas import TournamentInput

CANONICAL = [
    'Calcio',
    'Calcio a 5',
    'Basket',
    'Pallamano',
    'Badminton',
    'Tennis',
    'Pallavolo',
]


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / 'sports.sqlite3', seed=False)) as instance:
        yield instance


def test_sports_endpoint_reads_the_database_catalog(client):
    response = client.get('/api/sports')
    assert response.status_code == 200
    sports = response.json()['sports']
    assert [sport['name'] for sport in sports] == CANONICAL
    assert [sport['id'] for sport in sports] == [1, 2, 3, 4, 5, 6, 7]
    assert all(sport['min_team_size'] <= sport['max_team_size'] for sport in sports)


def test_single_sport_endpoint_returns_rules(client):
    response = client.get('/api/sports/Pallavolo')
    assert response.status_code == 200
    body = response.json()
    assert body['id'] == 7
    assert body['supports_sets'] is True
    assert body['rules']['max_team_size'] == 6
    assert client.get('/api/sports/Curling').status_code == 404


def test_tournament_detail_embeds_its_sport_config(client):
    created = client.post('/api/tournaments', json={
        'name': 'Coppa Pallavolo',
        'sport': 'Pallavolo',
        'team_names': ['Alfa', 'Beta'],
    })
    assert created.status_code == 201, created.text
    detail = client.get(f"/api/tournaments/{created.json()['id']}").json()
    assert detail['sport_config']['id'] == 7
    assert detail['sport_config']['name'] == 'Pallavolo'
    assert detail['tournament']['sport_id'] == 7


def test_schema_sport_literal_cannot_drift_from_catalog():
    annotation = TournamentInput.model_fields['sport'].annotation
    assert list(get_args(annotation)) == CANONICAL
