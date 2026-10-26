from auth import create_teacher
from conftest import make, state
from db import database

OTHER_EMAIL = 'altro.prof.privacy@test.local'
OTHER_PASSWORD = 'altra-password'
PRIVATE_FIELDS = ('public_token', 'teacher_id', 'demo_key')


def add_teacher(client, email=OTHER_EMAIL, password=OTHER_PASSWORD):
    with database(client.app.state.db_path, True) as db:
        create_teacher(db, email, password, 'Secondo Prof')


def login(client, email=OTHER_EMAIL, password=OTHER_PASSWORD):
    response = client.post('/api/auth/login',
                           json={'email': email, 'password': password})
    assert response.status_code == 200, response.text


def listing_item(client, tid):
    items = client.get('/api/tournaments', params={'archived': 'include'}).json()
    return next(item for item in items if item['id'] == tid)


def assert_private_fields_hidden(payload):
    for field in PRIVATE_FIELDS:
        assert field not in payload


def test_anonymous_reads_hide_internal_fields(client):
    tid = make(client)
    token = state(client, tid)['tournament']['public_token']
    client.post('/api/auth/logout')

    detail = client.get(f'/api/tournaments/{tid}').json()
    assert detail['can_manage'] is False
    assert 'audit' not in detail
    assert_private_fields_hidden(detail['tournament'])
    assert_private_fields_hidden(listing_item(client, tid))

    public = client.get(f'/api/public/{token}').json()
    assert public['public'] is True
    assert 'audit' not in public
    assert_private_fields_hidden(public['tournament'])


def test_owner_keeps_share_token_diary_and_team_controls(client):
    tid = make(client)
    detail = state(client, tid)
    assert detail['can_manage'] is True
    assert detail['tournament']['public_token']
    assert 'audit' in detail

    item = listing_item(client, tid)
    assert item['can_manage'] is True
    assert item['public_token'] == detail['tournament']['public_token']

    team_id = detail['teams'][0]['id']
    team_view = client.get(f'/api/tournaments/{tid}/teams/{team_id}').json()
    assert team_view['can_manage'] is True
    assert 'teacher_id' not in team_view['tournament']


def test_other_teachers_never_receive_private_fields(client):
    tid = make(client)
    add_teacher(client)
    client.post('/api/auth/logout')
    login(client)

    detail = client.get(f'/api/tournaments/{tid}').json()
    assert detail['can_manage'] is False
    assert 'audit' not in detail
    assert_private_fields_hidden(detail['tournament'])
    assert_private_fields_hidden(listing_item(client, tid))

    team_id = detail['teams'][0]['id']
    team_view = client.get(f'/api/tournaments/{tid}/teams/{team_id}').json()
    assert team_view['can_manage'] is False
    assert 'teacher_id' not in team_view['tournament']
