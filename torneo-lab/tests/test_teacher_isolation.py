from auth import create_teacher
from db import database
from conftest import TEACHER_EMAIL, TEACHER_PASSWORD

OTHER_EMAIL = 'altro.prof@test.local'
OTHER_PASSWORD = 'altra-password'


def add_teacher(client, email, password):
    with database(client.app.state.db_path, True) as db:
        return create_teacher(db, email, password, 'Secondo Prof')


def login(client, email, password):
    response = client.post('/api/auth/login', json={'email': email, 'password': password})
    assert response.status_code == 200, response.text


def test_teachers_cannot_manage_each_others_tournaments(client):
    created = client.post('/api/tournaments', json={
        'name': 'Coppa del primo prof',
        'sport': 'Calcio',
        'team_names': ['Alfa', 'Beta', 'Gamma', 'Delta'],
    })
    assert created.status_code == 201, created.text
    tid = created.json()['id']
    assert client.post(f'/api/tournaments/{tid}/generate').status_code == 200
    first = client.get(f'/api/tournaments/{tid}').json()
    team_id = first['teams'][0]['id']
    match_id = first['matches'][0]['id']
    match_version = first['matches'][0]['version']

    add_teacher(client, OTHER_EMAIL, OTHER_PASSWORD)
    client.post('/api/auth/logout')
    login(client, OTHER_EMAIL, OTHER_PASSWORD)

    detail = client.get(f'/api/tournaments/{tid}').json()
    assert detail['can_manage'] is False
    assert client.get('/api/tournaments?mine=1').json() == []

    blocked = [
        ('PATCH', f'/api/tournaments/{tid}', {'name': 'Rubato'}),
        ('POST', f'/api/tournaments/{tid}/archive', None),
        ('POST', f'/api/tournaments/{tid}/teams', {'name': 'Zeta'}),
        ('PATCH', f'/api/tournaments/{tid}/teams/{team_id}', {'name': 'Zeta'}),
        ('DELETE', f'/api/tournaments/{tid}/teams/{team_id}', None),
        ('POST', f'/api/tournaments/{tid}/teams/{team_id}/players',
         {'name': 'Giocatore', 'shirt_number': 7}),
        ('POST', f'/api/tournaments/{tid}/generate', None),
        ('PATCH', f'/api/tournaments/{tid}/matches/{match_id}',
         {'home_score': 1, 'away_score': 0, 'version': match_version}),
    ]
    for method, path, payload in blocked:
        response = client.request(method, path, json=payload)
        assert response.status_code == 403, (method, path, response.text)

    # The second teacher can still create and manage their own tournament.
    own = client.post('/api/tournaments', json={
        'name': 'Coppa del secondo prof',
        'sport': 'Basket',
        'variant': 'basket-5v5',
        'team_names': ['Rossi', 'Blu'],
    })
    assert own.status_code == 201, own.text
    own_id = own.json()['id']
    assert client.get(f'/api/tournaments/{own_id}').json()['can_manage'] is True
    assert [item['id'] for item in client.get('/api/tournaments?mine=1').json()] == [own_id]

    client.post('/api/auth/logout')
    login(client, TEACHER_EMAIL, TEACHER_PASSWORD)
    assert client.get(f'/api/tournaments/{tid}').json()['can_manage'] is True
    assert client.get(f'/api/tournaments/{own_id}').json()['can_manage'] is False
    assert client.patch(f'/api/tournaments/{tid}', json={'name': 'Coppa aggiornata'}).status_code == 200
    assert client.patch(f'/api/tournaments/{own_id}', json={'name': 'No'}).status_code == 403


def test_students_and_anonymous_users_are_read_only(client):
    created = client.post('/api/tournaments', json={
        'name': 'Coppa da leggere',
        'sport': 'Pallavolo',
        'variant': 'pallavolo-6v6',
        'team_names': ['Alfa', 'Beta'],
    })
    tid = created.json()['id']
    client.post('/api/auth/logout')

    session = client.get('/api/auth/session').json()
    assert session == {'authenticated': False, 'role': 'student', 'teacher': None}
    detail = client.get(f'/api/tournaments/{tid}').json()
    assert detail['can_manage'] is False
    assert client.get('/api/tournaments').status_code == 200

    assert client.patch(f'/api/tournaments/{tid}', json={'name': 'No'}).status_code == 401
    assert client.post(f'/api/tournaments/{tid}/generate').status_code == 401
    assert client.post('/api/tournaments', json={
        'name': 'No', 'sport': 'Calcio', 'team_names': ['Alfa', 'Beta'],
    }).status_code == 401
