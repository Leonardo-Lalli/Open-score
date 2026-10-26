from conftest import make, score, state


def listing(client):
    return {item['id']: item for item in
            client.get('/api/tournaments', params={'archived': 'include'}).json()}


def test_list_summary_matches_detail_for_every_state(client):
    draft = client.post('/api/tournaments', json={
        'name': 'Ancora da generare',
        'sport': 'Calcio',
        'variant': 'calcio-a-5',
        'team_names': ['Alfa', 'Beta'],
    }).json()['id']
    active = make(client, 'round_robin', 4)
    completed = make(client, 'knockout', 2)

    final = state(client, completed)['matches'][0]
    assert score(client, completed, final).status_code == 200

    items = listing(client)
    for tid in (draft, active, completed):
        detail = state(client, tid)
        item = items[tid]
        assert item['status'] == detail['status']
        assert item['progress'] == detail['progress']
        assert item['champion_team_id'] == detail['champion_team_id']
        assert item['team_count'] == len(detail['teams'])

    assert items[draft]['status'] == 'draft'
    assert items[active]['status'] == 'active'
    assert items[completed]['status'] == 'completed'
    assert items[completed]['champion_team_id'] is not None
