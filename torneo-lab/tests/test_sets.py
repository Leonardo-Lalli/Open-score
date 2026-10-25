import sqlite3

import pytest

from conftest import make, state


def create(client, sport, variant, names=('Alfa', 'Beta'), **extra):
    response = client.post('/api/tournaments', json={
        'name': f'Torneo {variant}',
        'sport': sport,
        'variant': variant,
        'team_names': list(names),
        **extra,
    })
    assert response.status_code == 201, response.text
    return response.json()['id']


def play(client, tid, match, sets):
    return client.patch(
        f'/api/tournaments/{tid}/matches/{match["id"]}',
        json={'sets': [{'home': h, 'away': a} for h, a in sets],
              'version': match['version']},
    )


def test_volleyball_five_set_bonus_points(client):
    tid = create(client, 'Pallavolo', 'pallavolo-6v6')
    client.post(f'/api/tournaments/{tid}/generate')
    match = state(client, tid)['matches'][0]

    response = play(client, tid, match, [(25, 20), (20, 25), (25, 20), (20, 25), (15, 10)])
    assert response.status_code == 200, response.text
    data = state(client, tid)
    assert data['matches'][0]['home_score'] == 3
    assert data['matches'][0]['away_score'] == 2
    assert data['matches'][0]['sets'][-1] == {'set': 5, 'home': 15, 'away': 10}
    points = {row['name']: row['points'] for row in data['standings']}
    assert points == {'Alfa': 2, 'Beta': 1}


def test_volleyball_three_one_uses_regular_points(client):
    tid = create(client, 'Pallavolo', 'pallavolo-6v6')
    client.post(f'/api/tournaments/{tid}/generate')
    match = state(client, tid)['matches'][0]

    assert play(client, tid, match, [(25, 20), (25, 18), (20, 25), (25, 15)]).status_code == 200
    points = {row['name']: row['points'] for row in state(client, tid)['standings']}
    assert points == {'Alfa': 3, 'Beta': 0}


@pytest.mark.parametrize('sets', [
    [(25, 24), (25, 20), (25, 20)],
    [(25, 20), (25, 20)],
    [(25, 20), (20, 25), (25, 20), (20, 25), (15, 14)],
    [(25, 20), (20, 25), (25, 20), (20, 25), (15, 13), (15, 13)],
    [(24, 20), (25, 20), (25, 20)],
])
def test_invalid_volleyball_set_scores_are_rejected(client, sets):
    tid = create(client, 'Pallavolo', 'pallavolo-6v6')
    client.post(f'/api/tournaments/{tid}/generate')
    match = state(client, tid)['matches'][0]
    assert play(client, tid, match, sets).status_code == 422
    assert state(client, tid)['progress']['completed'] == 0


def test_badminton_single_uses_cap_and_individual_participants(client):
    tid = create(client, 'Badminton', 'badminton-singolare', names=('Anna', 'Bruno'))
    detail = state(client, tid)
    assert detail['tournament']['participant_kind'] == 'individual'
    assert detail['tournament']['win_points'] == 1
    assert detail['tournament']['draw_points'] == 0
    assert detail['rules']['max_points'] == 30
    client.post(f'/api/tournaments/{tid}/generate')
    match = state(client, tid)['matches'][0]
    assert play(client, tid, match, [(30, 29), (21, 15)]).status_code == 200


def test_single_variant_rejects_team_participant_kind(client):
    response = client.post('/api/tournaments', json={
        'name': 'Errore',
        'sport': 'Badminton',
        'variant': 'badminton-singolare',
        'participant_kind': 'team',
        'team_names': ['Alfa', 'Beta'],
    })
    assert response.status_code == 422


def test_basket_does_not_allow_draws(client):
    tid = create(client, 'Basket', 'basket-5v5')
    assert state(client, tid)['tournament']['draw_points'] == 0
    client.post(f'/api/tournaments/{tid}/generate')
    match = state(client, tid)['matches'][0]
    draw = client.patch(f'/api/tournaments/{tid}/matches/{match["id"]}',
                        json={'home_score': 10, 'away_score': 10,
                              'version': match['version']})
    assert draw.status_code == 422
    win = client.patch(f'/api/tournaments/{tid}/matches/{match["id"]}',
                       json={'home_score': 11, 'away_score': 10,
                             'version': match['version']})
    assert win.status_code == 200


def test_numeric_result_rejected_for_set_variant(client):
    tid = create(client, 'Ping pong', 'ping-pong-doppio')
    client.post(f'/api/tournaments/{tid}/generate')
    match = state(client, tid)['matches'][0]
    response = client.patch(f'/api/tournaments/{tid}/matches/{match["id"]}',
                            json={'home_score': 3, 'away_score': 1,
                                  'version': match['version']})
    assert response.status_code == 422


def test_schedule_uses_variant_duration(client):
    tid = create(client, 'Calcio', 'calcio-a-7')
    client.post(f'/api/tournaments/{tid}/generate')
    match = state(client, tid)['matches'][0]
    assert match['duration'] == 50
    response = client.patch(
        f'/api/tournaments/{tid}/matches/{match["id"]}/schedule',
        json={'version': match['version'],
              'scheduled_at': '2026-11-03T10:00:00+01:00',
              'location': 'Campo A'},
    )
    assert response.status_code == 200, response.text
    assert response.json()['duration'] == 50
    assert state(client, tid)['matches'][0]['duration'] == 50


def test_regulation_snapshot_survives_catalog_changes(client, tmp_path):
    tid = create(client, 'Calcio', 'calcio-a-5')
    original = state(client, tid)['regulation']
    path = client.app.state.db_path
    with sqlite3.connect(path) as db:
        db.execute("UPDATE sport_variants SET regulation='Testo nuovo' WHERE slug='calcio-a-5'")
    assert state(client, tid)['regulation'] == original
    fresh = create(client, 'Calcio', 'calcio-a-5')
    assert state(client, fresh)['regulation'] == 'Testo nuovo'


def test_historical_sport_is_read_only(client, tmp_path):
    path = client.app.state.db_path
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO tournaments(id,name,sport,format,public_token) "
                   "VALUES (999,'Vecchio tennis','Tennis','knockout','legacy-token')")
    detail = state(client, 999)
    assert detail['legacy_sport'] is True
    assert detail['tournament']['sport'] == 'Tennis'
    assert detail['variant_config'] is None
    assert client.patch('/api/tournaments/999', json={'name': 'Nuovo nome'}).status_code == 409
    assert client.post('/api/tournaments/999/generate').status_code == 409
