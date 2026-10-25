from conftest import make, state


def test_roster_add_list_and_remove(client):
    tid = make(client, 'round_robin', 2, sport='Calcio', variant='calcio-a-5')
    team = state(client, tid)['teams'][0]
    url = f'/api/tournaments/{tid}/teams/{team["id"]}/players'

    created = client.post(url, json={'name': 'Luca Bianchi', 'shirt_number': 7})
    assert created.status_code == 201, created.text
    assert client.post(url, json={'name': 'luca bianchi'}).status_code == 409

    listing = client.get(url)
    assert listing.status_code == 200
    assert listing.json()['players'][0]['name'] == 'Luca Bianchi'
    assert listing.json()['players'][0]['shirt_number'] == 7

    detail = client.get(f'/api/tournaments/{tid}/teams/{team["id"]}').json()
    assert detail['max_roster'] == 12
    assert detail['players'][0]['name'] == 'Luca Bianchi'
    assert state(client, tid)['teams'][0]['player_count'] == 1

    removed = client.delete(f'{url}/{created.json()["id"]}')
    assert removed.status_code == 204
    assert client.get(url).json()['players'] == []


def test_roster_respects_variant_maximum(client):
    tid = make(client, 'round_robin', 2, sport='Calcio', variant='calcio-a-5')
    team = state(client, tid)['teams'][0]
    url = f'/api/tournaments/{tid}/teams/{team["id"]}/players'
    for index in range(12):
        assert client.post(url, json={'name': f'Giocatore {index + 1}'}).status_code == 201
    assert client.post(url, json={'name': 'Giocatore 13'}).status_code == 422


def test_individual_tournament_has_no_roster(client):
    tid = make(client, 'round_robin', 2, sport='Badminton',
               variant='badminton-singolare')
    participant = state(client, tid)['teams'][0]
    response = client.post(
        f'/api/tournaments/{tid}/teams/{participant["id"]}/players',
        json={'name': 'Anna'},
    )
    assert response.status_code == 422
