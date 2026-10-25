import sqlite3

from fastapi.testclient import TestClient

from app import create_app
from conftest import make, score


def draft(client, **payload):
    body = {'name': 'Coppa in bozza', 'sport': 'Calcio', 'format': 'knockout',
            'team_names': ['Alfa', 'Beta', 'Gamma', 'Delta'], **payload}
    response = client.post('/api/tournaments', json=body)
    assert response.status_code == 201, response.text
    return response.json()['id']


def test_name_and_description_editable_after_generation(client):
    tid = make(client)
    response = client.patch(f'/api/tournaments/{tid}', json={
        'name': 'Coppa rinominata',
        'description': 'Nuova descrizione',
    })
    assert response.status_code == 200, response.text
    detail = client.get(f'/api/tournaments/{tid}').json()
    assert detail['tournament']['name'] == 'Coppa rinominata'
    assert detail['tournament']['description'] == 'Nuova descrizione'
    assert detail['tournament']['updated_at'] >= detail['tournament']['created_at']
    assert any(entry['action'] == 'updated' for entry in detail['audit'])


def test_structural_change_rejected_after_generation(client):
    tid = make(client)
    for change in ({'format': 'groups'}, {'sport': 'Pallavolo'},
                   {'variant': 'calcio-a-5'}, {'legs': 2}, {'qualifiers': 1}):
        response = client.patch(f'/api/tournaments/{tid}', json=change)
        assert response.status_code == 409, (change, response.text)
    detail = client.get(f'/api/tournaments/{tid}').json()
    assert detail['tournament']['format'] == 'round_robin'
    assert detail['tournament']['sport'] == 'Calcio'


def test_draft_accepts_format_sport_and_rules(client):
    tid = draft(client)
    response = client.patch(f'/api/tournaments/{tid}', json={
        'format': 'groups',
        'sport': 'Pallavolo',
        'group_count': 2,
        'qualifiers': 1,
        'win_points': 2,
    })
    assert response.status_code == 200, response.text
    detail = client.get(f'/api/tournaments/{tid}').json()
    tournament = detail['tournament']
    assert tournament['format'] == 'groups'
    assert tournament['sport'] == 'Pallavolo'
    assert tournament['sport_id'] == 7
    assert tournament['variant'] == 'pallavolo-6v6'
    assert tournament['qualifiers'] == 1
    assert tournament['win_points'] == 2
    assert detail['variant_config']['scoring_mode'] == 'sets'
    assert detail['regulation']

    assert client.patch(f'/api/tournaments/{tid}', json={'format': 'knockout', 'legs': 2}).status_code == 422
    assert client.patch(f'/api/tournaments/{tid}', json={'sport': 'Calcio', 'sport_id': 7}).status_code == 422
    assert client.patch(f'/api/tournaments/{tid}', json={}).status_code == 422
    assert client.patch(f'/api/tournaments/{tid}', json={'unknown': 1}).status_code == 422


def test_draft_update_without_format_preserves_current_structure(client):
    """The edit modal omits `format`, exactly like the SPA payload."""
    tid = draft(client)
    response = client.patch(f'/api/tournaments/{tid}', json={
        'name': 'Coppa aggiornata',
        'description': '',
        'sport': 'Pallavolo',
        'variant': 'pallavolo-6v6',
        'participant_kind': 'team',
        'legs': 1,
        'group_count': 2,
        'qualifiers': 2,
        'win_points': 3,
        'draw_points': 0,
        'loss_points': 0,
        'tie_breaker': 'goal_difference',
    })
    assert response.status_code == 200, response.text
    tournament = client.get(f'/api/tournaments/{tid}').json()['tournament']
    assert tournament['name'] == 'Coppa aggiornata'
    assert tournament['sport'] == 'Pallavolo'
    assert tournament['variant'] == 'pallavolo-6v6'
    assert tournament['format'] == 'knockout'


def test_draft_ui_payload_can_switch_format_before_generation(client):
    tid = draft(client)
    payload = {
        'name': 'Coppa in gironi',
        'description': '',
        'format': 'groups',
        'sport': 'Calcio',
        'variant': 'calcio-a-11',
        'participant_kind': 'team',
        'legs': 2,
        'group_count': 2,
        'qualifiers': 2,
        'win_points': 3,
        'draw_points': 1,
        'loss_points': 0,
        'tie_breaker': 'goal_difference',
    }
    response = client.patch(f'/api/tournaments/{tid}', json=payload)
    assert response.status_code == 200, response.text
    tournament = client.get(f'/api/tournaments/{tid}').json()['tournament']
    assert tournament['format'] == 'groups'
    assert tournament['legs'] == 2
    assert tournament['group_count'] == 2

    payload.update(format='knockout', legs=1)
    response = client.patch(f'/api/tournaments/{tid}', json=payload)
    assert response.status_code == 200, response.text
    assert client.get(f'/api/tournaments/{tid}').json()['tournament']['format'] == 'knockout'


def test_explicit_null_is_rejected_without_touching_the_draft(client):
    tid = draft(client)
    for change in ({'format': None}, {'name': None}, {'description': None}):
        response = client.patch(f'/api/tournaments/{tid}', json=change)
        assert response.status_code == 422, (change, response.text)
    tournament = client.get(f'/api/tournaments/{tid}').json()['tournament']
    assert tournament['format'] == 'knockout'
    assert tournament['name'] == 'Coppa in bozza'


def test_archive_hides_tournament_and_blocks_writes(client):
    tid = make(client)
    detail = client.get(f'/api/tournaments/{tid}').json()
    match = detail['matches'][0]

    archived = client.post(f'/api/tournaments/{tid}/archive')
    assert archived.status_code == 200
    assert archived.json()['archived'] is True

    assert client.get('/api/tournaments').json() == []
    only = client.get('/api/tournaments', params={'archived': 'only'}).json()
    included = client.get('/api/tournaments', params={'archived': 'include'}).json()
    assert [tournament['id'] for tournament in only] == [tid]
    assert only[0]['archived'] is True
    assert [tournament['id'] for tournament in included] == [tid]

    # Archived tournaments stay readable...
    assert client.get(f'/api/tournaments/{tid}').json()['tournament']['archived_at']
    # ...but every write is refused.
    assert score(client, tid, match).status_code == 409
    assert client.patch(f'/api/tournaments/{tid}', json={'name': 'Nuovo nome'}).status_code == 409
    assert client.post(f'/api/tournaments/{tid}/generate').status_code == 409
    assert client.post(f'/api/tournaments/{tid}/teams', json={'name': 'Zeta'}).status_code == 409

    restored = client.post(f'/api/tournaments/{tid}/restore')
    assert restored.status_code == 200
    assert restored.json()['archived'] is False
    assert [tournament['id'] for tournament in client.get('/api/tournaments').json()] == [tid]
    assert score(client, tid, match).status_code == 200


def test_data_survives_application_restart(tmp_path):
    path = tmp_path / 'restart.sqlite3'
    admin_email, admin_password = 'prof@test.local', 'password-lunga'
    with TestClient(create_app(path, seed=False, admin_email=admin_email,
                               admin_password=admin_password)) as client:
        client.post('/api/auth/login', json={
            'email': 'prof@test.local', 'password': 'password-lunga'})
        tid = draft(client)
        team = client.get(f'/api/tournaments/{tid}').json()['teams'][0]
        client.post(f'/api/tournaments/{tid}/generate')
        match = client.get(f'/api/tournaments/{tid}').json()['matches'][0]
        assert score(client, tid, match, 3, 0).status_code == 200
        client.patch(f'/api/tournaments/{tid}', json={'name': 'Coppa persistente'})

    with TestClient(create_app(path, seed=False, admin_email=admin_email,
                               admin_password=admin_password)) as client:
        client.post('/api/auth/login', json={
            'email': 'prof@test.local', 'password': 'password-lunga'})
        detail = client.get(f'/api/tournaments/{tid}').json()
        assert detail['tournament']['name'] == 'Coppa persistente'
        assert detail['teams'][0]['name'] == team['name']
        assert any(m['home_score'] == 3 and m['away_score'] == 0 for m in detail['matches'])
        assert len(detail['matches']) == 3


def test_documented_online_backup_copies_every_tournament(tmp_path):
    path = tmp_path / 'source.sqlite3'
    backup = tmp_path / 'backup.sqlite3'
    with TestClient(create_app(path, seed=True)):
        pass

    with sqlite3.connect(path) as db:
        db.execute('VACUUM INTO ?', (str(backup),))

    with sqlite3.connect(backup) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 7
        assert db.execute('SELECT count(*) FROM tournaments').fetchone()[0] == 4
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
