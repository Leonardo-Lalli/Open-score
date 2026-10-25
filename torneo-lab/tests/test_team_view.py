from conftest import make, score, state


def test_team_view_reports_standing_and_fixtures(client):
    tid = make(client, 'round_robin', 4)
    detail = state(client, tid)
    team = detail['teams'][0]

    response = client.get(f'/api/tournaments/{tid}/teams/{team["id"]}')
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['team']['name'] == team['name']
    assert body['position'] in (1, 2, 3, 4)
    assert body['standing']['played'] == 0
    assert len(body['matches']) == 3
    assert all(team['id'] in (m['home_team_id'], m['away_team_id']) for m in body['matches'])
    assert all(m['opponent_name'] for m in body['matches'])
    assert all(m['status'] == 'ready' for m in body['matches'])

    match = next(m for m in body['matches'] if m['home_team_id'] == team['id'])
    assert score(client, tid, match, 2, 0).status_code == 200
    updated = client.get(f'/api/tournaments/{tid}/teams/{team["id"]}').json()
    assert updated['standing']['played'] == 1
    assert updated['standing']['won'] == 1
    assert updated['standing']['points'] == 3
    played = next(m for m in updated['matches'] if m['id'] == match['id'])
    assert played['status'] == 'completed'
    assert played['home_score'] == 2


def test_team_view_in_groups_uses_group_standing(client):
    tid = make(client, 'groups', 8, group_count=2, qualifiers=2)
    body = state(client, tid)
    team = body['teams'][0]
    response = client.get(f'/api/tournaments/{tid}/teams/{team["id"]}')
    assert response.status_code == 200
    data = response.json()
    assert data['team']['group_name']
    assert len(data['matches']) == 3
    assert data['standing']['team_id'] == team['id']


def test_team_view_exposes_lineup_rules_from_the_variant(client):
    created = client.post('/api/tournaments', json={
        'name': 'Calcio a 5',
        'sport': 'Calcio',
        'variant': 'calcio-a-5',
        'format': 'round_robin',
        'team_names': ['Alfa', 'Beta', 'Gamma', 'Delta'],
    })
    assert created.status_code == 201, created.text
    tid = created.json()['id']
    team = state(client, tid)['teams'][0]

    body = client.get(f'/api/tournaments/{tid}/teams/{team["id"]}').json()
    assert body['variant_name'] == 'Calcio a 5'
    assert body['players_on_field'] == 5
    assert body['min_lineup'] == 5
    assert body['max_roster'] == 12
    assert body['players'] == []


def test_team_view_rejects_wrong_tournament(client):
    first = make(client, 'round_robin', 4)
    second = make(client, 'round_robin', 4)
    team = state(client, first)['teams'][0]
    assert client.get(f'/api/tournaments/{second}/teams/{team["id"]}').status_code == 404
    assert client.get(f'/api/tournaments/{first}/teams/9999').status_code == 404


def test_tie_breaker_is_configurable_and_locked_after_generation(client):
    created = client.post('/api/tournaments', json={
        'name': 'Coppa testa a testa',
        'sport': 'Calcio',
        'format': 'round_robin',
        'tie_breaker': 'head_to_head',
        'team_names': ['Alfa', 'Beta', 'Gamma', 'Delta'],
    })
    assert created.status_code == 201, created.text
    tid = created.json()['id']
    assert client.get(f'/api/tournaments/{tid}').json()['tournament']['tie_breaker'] == 'head_to_head'

    assert client.patch(f'/api/tournaments/{tid}', json={'tie_breaker': 'wins'}).status_code == 200
    assert client.get(f'/api/tournaments/{tid}').json()['tournament']['tie_breaker'] == 'wins'
    assert client.patch(f'/api/tournaments/{tid}', json={'tie_breaker': 'coin_toss'}).status_code == 422

    assert client.post(f'/api/tournaments/{tid}/generate').status_code == 200
    assert client.patch(f'/api/tournaments/{tid}', json={'tie_breaker': 'goals_for'}).status_code == 409
