from typing import get_args

import pytest
from fastapi.testclient import TestClient

from app import create_app
from schemas import TournamentInput

CANONICAL = [
    'Calcio',
    'Basket',
    'Pallavolo',
    'Badminton',
    'Ping pong',
    'Biliardino',
]

VARIANTS = {
    'Calcio': ['calcio-a-11', 'calcio-a-7', 'calcio-a-5'],
    'Basket': ['basket-5v5', 'basket-3x3'],
    'Pallavolo': ['pallavolo-6v6', 'pallavolo-4v4', 'beach-volley-2v2'],
    'Badminton': ['badminton-singolare', 'badminton-doppio', 'badminton-doppio-misto'],
    'Ping pong': ['ping-pong-singolare', 'ping-pong-doppio', 'ping-pong-doppio-misto'],
    'Biliardino': ['biliardino-singolare', 'biliardino-doppio'],
}

ALL_VARIANTS = [(sport, slug) for sport, slugs in VARIANTS.items() for slug in slugs]


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / 'sports.sqlite3', seed=False)) as instance:
        yield instance


def test_sports_endpoint_reads_the_database_catalog(client):
    response = client.get('/api/sports')
    assert response.status_code == 200
    sports = response.json()['sports']
    assert [sport['name'] for sport in sports] == CANONICAL
    assert [sport['default_variant'] for sport in sports] == [
        'calcio-a-11', 'basket-5v5', 'pallavolo-6v6',
        'badminton-doppio', 'ping-pong-doppio', 'biliardino-doppio',
    ]
    assert all(sport['min_team_size'] <= sport['max_team_size'] for sport in sports)
    for sport in sports:
        assert [variant['slug'] for variant in sport['variants']] == VARIANTS[sport['name']]


def test_catalog_variants_have_coherent_roster_duration_and_scoring(client):
    sports = client.get('/api/sports').json()['sports']
    slugs = set()
    for sport in sports:
        assert sport['variants'], sport['name']
        for variant in sport['variants']:
            assert variant['slug'] not in slugs
            slugs.add(variant['slug'])
            assert variant['participant_kind'] in ('team', 'individual')
            assert 1 <= variant['min_lineup'] <= variant['players_on_field']
            assert variant['players_on_field'] <= variant['max_roster']
            assert variant['match_duration'] >= 10
            assert variant['scoring_mode'] in ('goals', 'points', 'sets')
            assert variant['standings']
            detail = client.get(f"/api/variants/{variant['slug']}").json()
            assert detail['regulation']
            if variant['supports_sets']:
                assert variant['sets_to_win'] >= 1
                assert variant['max_sets'] >= variant['sets_to_win']
                assert variant['points_per_set'] >= 1
                assert variant['tiebreak_points'] >= 1
    assert len(slugs) == 16


@pytest.mark.parametrize('sport,variant', ALL_VARIANTS)
def test_every_sport_variant_pair_has_rules_and_regulation(client, sport, variant):
    response = client.get(f'/api/sports/{sport}/variants/{variant}')
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['sport'] == sport
    assert body['slug'] == variant
    assert body['rules']
    assert body['regulation']


@pytest.mark.parametrize('sport,variant', ALL_VARIANTS)
def test_every_variant_drives_creation_generation_and_duration(client, sport, variant):
    """Each catalog pair must reach creation, match generation and its own rules."""
    info = client.get(f'/api/sports/{sport}/variants/{variant}').json()
    created = client.post('/api/tournaments', json={
        'name': f'Verifica {variant}',
        'sport': sport,
        'variant': variant,
        'format': 'knockout',
        'team_names': ['Alfa', 'Beta'],
    })
    assert created.status_code == 201, created.text
    tid = created.json()['id']
    detail = client.get(f'/api/tournaments/{tid}').json()
    assert detail['tournament']['variant'] == variant
    assert detail['tournament']['participant_kind'] == info['participant_kind']
    assert detail['variant_config']['slug'] == variant
    assert detail['rules']['match_duration'] == info['match_duration']
    assert detail['regulation'] == info['regulation']

    generated = client.post(f'/api/tournaments/{tid}/generate')
    assert generated.status_code == 200, generated.text
    matches = client.get(f'/api/tournaments/{tid}').json()['matches']
    assert len(matches) == 1
    assert matches[0]['duration'] == info['match_duration']


def test_single_sport_endpoint_lists_variants(client):
    response = client.get('/api/sports/Pallavolo')
    assert response.status_code == 200
    body = response.json()
    assert body['name'] == 'Pallavolo'
    assert body['supports_sets'] is True
    assert len(body['variants']) == 3
    assert body['variants'][0]['players_on_field'] == 6
    assert body['variants'][0]['min_lineup'] == 6
    assert body['variants'][0]['max_roster'] == 14
    assert client.get('/api/sports/Curling').status_code == 404


def test_variant_detail_exposes_rules_and_regulation(client):
    response = client.get('/api/sports/Pallavolo/variants/pallavolo-6v6')
    assert response.status_code == 200
    body = response.json()
    assert body['sport'] == 'Pallavolo'
    assert body['scoring_mode'] == 'sets'
    assert body['sets_to_win'] == 3
    assert body['max_sets'] == 5
    assert body['match_duration'] == 105
    assert body['rules']['standings']['win_tiebreak'] == 2
    assert 'tre set' in body['regulation'] or 'cinque set' in body['regulation']

    shortcut = client.get('/api/variants/calcio-a-5')
    assert shortcut.status_code == 200
    assert shortcut.json()['name'] == 'Calcio a 5'
    assert client.get('/api/variants/curling-1v1').status_code == 404
    assert client.get('/api/sports/Calcio/variants/pallavolo-6v6').status_code == 404


def test_tournament_detail_embeds_its_sport_and_variant(client):
    created = client.post('/api/tournaments', json={
        'name': 'Coppa Pallavolo',
        'sport': 'Pallavolo',
        'variant': 'pallavolo-6v6',
        'team_names': ['Alfa', 'Beta'],
    })
    assert created.status_code == 201, created.text
    detail = client.get(f"/api/tournaments/{created.json()['id']}").json()
    assert detail['sport_config']['name'] == 'Pallavolo'
    assert detail['variant_config']['slug'] == 'pallavolo-6v6'
    assert detail['tournament']['variant'] == 'pallavolo-6v6'
    assert detail['tournament']['scoring_system'] == 'sets'
    assert detail['rules']['max_sets'] == 5
    assert detail['regulation']


def test_schema_sport_literal_cannot_drift_from_catalog():
    annotation = TournamentInput.model_fields['sport'].annotation
    assert list(get_args(annotation)) == CANONICAL


@pytest.mark.parametrize('sport,variant,kind', [
    ('Calcio', 'calcio-a-5', 'team'),
    ('Basket', 'basket-3x3', 'team'),
    ('Badminton', 'badminton-singolare', 'individual'),
    ('Ping pong', 'ping-pong-doppio', 'team'),
    ('Biliardino', 'biliardino-singolare', 'individual'),
])
def test_every_variant_can_create_a_tournament(client, sport, variant, kind):
    response = client.post('/api/tournaments', json={
        'name': f'Torneo {variant}',
        'sport': sport,
        'variant': variant,
        'team_names': ['Alfa', 'Beta'],
    })
    assert response.status_code == 201, response.text
    body = client.get(f"/api/tournaments/{response.json()['id']}").json()
    assert body['tournament']['participant_kind'] == kind
    assert body['tournament']['variant'] == variant
    assert body['rules']['match_duration'] >= 10
