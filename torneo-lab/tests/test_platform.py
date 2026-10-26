"""Real SQLite/API integration tests, synthetic identities only."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from datetime import timedelta
import json
import sqlite3

from fastapi.testclient import TestClient
import pytest

from app import create_app
import auth
from db import SCHEMA_VERSION, database, initialize
from manage import claim, verified_copy

PASSWORD = 'Synthetic-passphrase-123'
PREFIX = '/api/v1'


def ok(response, code=200):
    assert response.status_code == code, response.text
    return response.json() if response.content else None


class Actor:
    def __init__(self, client, email, name, register=False):
        self.client = client
        csrf = ok(client.get(PREFIX+'/auth/csrf'))['csrf_token']
        client.headers['X-CSRF-Token'] = csrf
        payload = dict(email=email, password=PASSWORD)
        if register:
            payload['display_name'] = name
        result = ok(client.post(PREFIX+('/auth/register' if register else '/auth/login'), json=payload), 201 if register else 200)
        client.headers['X-CSRF-Token'] = result['csrf_token']
        self.uid = result['user']['id']

    def get(self, route, **kwargs):
        return self.client.get(PREFIX+route, **kwargs)

    def post(self, route, data=None):
        return self.client.post(PREFIX+route, json=data)

    def patch(self, route, data):
        return self.client.patch(PREFIX+route, json=data)

    def delete(self, route, data):
        return self.client.request('DELETE', PREFIX+route, json=data)


@pytest.fixture
def lab(tmp_path):
    path = tmp_path/'platform.sqlite3'
    app = create_app(path, seed=False, mode='demo')
    with database(path, True) as db:
        auth.create_teacher(db, 'teacher-a@example.test', PASSWORD, 'Docente A', 'Contesto A')
        auth.create_teacher(db, 'teacher-b@example.test', PASSWORD, 'Docente B', 'Contesto B')
    with ExitStack() as stack:
        class Lab:
            def actor(self, name, register=True):
                client = stack.enter_context(TestClient(app))
                return Actor(client, name+'@example.test', name, register)
        item = Lab()
        item.path, item.app = path, app
        item.teacher = item.actor('teacher-a', False)
        item.other = item.actor('teacher-b', False)
        item.student = item.actor('Studente-A')
        item.second = item.actor('Studente-B')
        yield item


def tournament(actor, n=4, fmt='round_robin', variant='football-5', generate=True, **options):
    tid = ok(actor.post('/tournaments', dict(name='Coppa sintetica', format=fmt, variant_id=variant,
             team_names=[f'Squadra {i}' for i in range(n)], **options)), 201)['id']
    if generate:
        ok(actor.post(f'/tournaments/{tid}/generate'))
    return tid


def detail(actor, tid):
    return ok(actor.get(f'/tournaments/{tid}'))


def assign(lab, tid, student=None, index=0):
    student = student or lab.student
    s = ok(lab.teacher.post(f'/tournaments/{tid}/students', dict(display_name=f'Alias {student.uid}', user_id=student.uid)), 201)
    team = detail(lab.teacher, tid)['teams'][index]
    return ok(lab.teacher.patch(f'/tournaments/{tid}/students/{s["id"]}/team', dict(version=s['version'], team_id=team['id'])))


def score(actor, tid, game, home=2, away=1, invalidate=False):
    return actor.patch(f'/tournaments/{tid}/matches/{game["id"]}/result',
          dict(match_version=game['version'], score=dict(type='points', home=home, away=away), reason='Verifica sintetica', invalidate=invalidate))


def test_auth_sessions_csrf_and_role_boundaries(lab):
    anonymous = TestClient(lab.app)
    assert anonymous.get(PREFIX+'/users/me').status_code == 401
    assert anonymous.post(PREFIX+'/auth/login', json=dict(email='teacher-a@example.test', password=PASSWORD)).status_code == 403
    old_cookie = lab.teacher.client.cookies.get(auth.COOKIE)
    uid = ok(lab.teacher.get('/users/me'))['id']
    assert uid == lab.teacher.uid
    assert lab.student.post('/tournaments', dict(name='Non autorizzato')).status_code == 403
    tid = tournament(lab.teacher)
    assert lab.other.get(f'/tournaments/{tid}').status_code == 404
    assert lab.other.get('/tournaments').json()['items'] == []
    assign(lab, tid)
    assert lab.student.get(f'/tournaments/{tid}').status_code == 200
    assert lab.student.get(f'/tournaments/{tid}/students').status_code == 403
    assert lab.student.post(f'/tournaments/{tid}/generate').status_code == 403
    ok(lab.teacher.post('/auth/logout'), 204)
    assert lab.teacher.get('/users/me').status_code == 401
    anonymous.cookies.set(auth.COOKIE, old_cookie)
    assert anonymous.get(PREFIX+'/users/me').status_code == 401
    anonymous.close()


def test_no_privilege_injection_or_secret_reflection(lab):
    client = TestClient(lab.app)
    token = ok(client.get(PREFIX+'/auth/csrf'))['csrf_token']
    payload = dict(email='new@example.test', password=PASSWORD, display_name='Nuovo', role='teacher')
    response = client.post(PREFIX+'/auth/register', json=payload, headers={'X-CSRF-Token': token})
    assert response.status_code == 422
    assert PASSWORD not in response.text
    assert all('input' not in item for item in response.json()['detail'])
    payload.pop('role')
    payload['password'] = 'SecretShort'
    response = client.post(PREFIX+'/auth/register', json=payload, headers={'X-CSRF-Token': token})
    assert response.status_code == 422 and 'SecretShort' not in response.text
    with database(lab.path) as db:
        hashes = [r[0] for r in db.execute('SELECT password_hash FROM users')]
        assert len(set(hashes)) == len(hashes)
        assert all(PASSWORD not in h and h.startswith('pbkdf2_sha256$600000$') for h in hashes)
    client.close()


def test_session_expiry_and_failed_login_rate_limit(lab):
    with database(lab.path, True) as db:
        db.execute('UPDATE sessions SET expires_at=? WHERE user_id=?', ((auth.now()-timedelta(seconds=1)).isoformat(), lab.student.uid))
    assert lab.student.get('/users/me').status_code == 401
    client = TestClient(lab.app)
    csrf = ok(client.get(PREFIX+'/auth/csrf'))['csrf_token']
    for _ in range(10):
        assert client.post(PREFIX+'/auth/login', json=dict(email='missing@example.test', password=PASSWORD), headers={'X-CSRF-Token': csrf}).status_code == 401
    assert client.post(PREFIX+'/auth/login', json=dict(email='missing@example.test', password=PASSWORD), headers={'X-CSRF-Token': csrf}).status_code == 429
    client.close()


def test_owned_tournaments_cannot_escape_through_legacy_routes(lab):
    tid = tournament(lab.teacher)
    with database(lab.path) as db:
        token = db.execute('SELECT public_token FROM tournaments WHERE id=?', (tid,)).fetchone()[0]
    client = TestClient(lab.app)
    assert client.get('/api/tournaments').json() == []
    assert client.get(f'/api/tournaments/{tid}').status_code == 404
    assert client.get('/api/public/'+token).status_code == 404
    assert client.post(f'/api/tournaments/{tid}/generate').status_code == 404
    client.close()


def test_team_order_concurrency_and_seeding_are_independent(lab):
    tid = tournament(lab.teacher, fmt='knockout')
    before = detail(lab.teacher, tid)
    ids = [t['id'] for t in before['teams']]
    body = dict(version=before['tournament']['order_version'], ordered_team_ids=ids[::-1])
    assert lab.student.patch(f'/tournaments/{tid}/teams/order', body).status_code == 404
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: lab.teacher.patch(f'/tournaments/{tid}/teams/order', body).status_code, range(2)))
    assert sorted(statuses) == [200, 409]
    after = detail(lab.teacher, tid)
    assert [t['id'] for t in after['teams']] == ids[::-1]
    assert after['matches'] == before['matches']
    bad = dict(version=after['tournament']['order_version'], ordered_team_ids=[ids[0]]*4)
    assert lab.teacher.patch(f'/tournaments/{tid}/teams/order', bad).status_code == 422
    with TestClient(create_app(lab.path, False, mode='demo')) as client:
        actor = Actor(client, 'teacher-a@example.test', 'Docente', False)
        assert [t['id'] for t in detail(actor, tid)['teams']] == ids[::-1]


def test_team_crud_memberships_capacity_and_search(lab):
    tid = tournament(lab.teacher, n=0, generate=False)
    team = ok(lab.teacher.post(f'/tournaments/{tid}/teams', dict(name='Alfa', max_members=1)), 201)
    assert lab.teacher.post(f'/tournaments/{tid}/teams', dict(name='alfa')).status_code == 409
    assert lab.teacher.get(f'/tournaments/{tid}/teams?q=AL').json()['items'][0]['id'] == team['id']
    member = assign(lab, tid)
    second = ok(lab.teacher.post(f'/tournaments/{tid}/students', dict(display_name='Altro alias', user_id=lab.second.uid)), 201)
    assert lab.teacher.patch(f'/tournaments/{tid}/students/{second["id"]}/team', dict(version=1, team_id=team['id'])).status_code == 409
    assert lab.teacher.patch(f'/tournaments/{tid}/students/{member["id"]}/team', dict(version=1, team_id=None)).status_code == 409
    ok(lab.teacher.patch(f'/tournaments/{tid}/students/{member["id"]}/team', dict(version=member['version'], team_id=None)))
    ok(lab.teacher.patch(f'/tournaments/{tid}/students/{second["id"]}/team', dict(version=1, team_id=team['id'])))
    assert lab.teacher.delete(f'/tournaments/{tid}/teams/{team["id"]}', dict(version=1)).status_code == 409
    current = lab.teacher.get(f'/tournaments/{tid}/students?team_id={team["id"]}').json()['items'][0]
    ok(lab.teacher.patch(f'/tournaments/{tid}/students/{current["id"]}/team', dict(version=current['version'], team_id=None)))
    edited = ok(lab.teacher.patch(f'/tournaments/{tid}/teams/{team["id"]}', dict(version=1, name='Rinominata', max_members=2)))
    ok(lab.teacher.delete(f'/tournaments/{tid}/teams/{team["id"]}', dict(version=edited['version'])), 204)
    assert lab.teacher.get(f'/tournaments/{tid}/teams').json()['items'] == []
    assert lab.teacher.get(f'/tournaments/{tid}/students?q=Altro').json()['items'][0]['id'] == second['id']


def test_cross_tournament_membership_and_order_rejected(lab):
    a, b = tournament(lab.teacher), tournament(lab.teacher)
    s = assign(lab, a)
    foreign_team = detail(lab.teacher, b)['teams'][0]['id']
    assert lab.teacher.patch(f'/tournaments/{a}/students/{s["id"]}/team', dict(version=s['version'], team_id=foreign_team)).status_code == 404
    ids = [t['id'] for t in detail(lab.teacher, a)['teams']]
    assert lab.teacher.patch(f'/tournaments/{a}/teams/order', dict(version=1, ordered_team_ids=ids[:-1]+[foreign_team])).status_code == 422


def test_proposals_remain_unofficial_until_professor_review(lab):
    tid = tournament(lab.teacher, n=2)
    assign(lab, tid)
    assign(lab, tid, lab.second, 1)
    game = detail(lab.teacher, tid)['matches'][0]
    route = f'/tournaments/{tid}/matches/{game["id"]}'
    first = ok(lab.student.post(route+'/proposals', dict(match_version=game['version'], score=dict(type='points', home=2, away=1))), 201)
    second = ok(lab.second.post(route+'/proposals', dict(match_version=game['version'], score=dict(type='points', home=0, away=4))), 201)
    assert detail(lab.teacher, tid)['progress']['completed'] == 0
    assert lab.teacher.get(f'/tournaments/{tid}/statistics').json()['pending_proposals'] == 2
    assert len(lab.student.get(route+'/proposals').json()['items']) == 1
    assert lab.student.post(route+f'/proposals/{first["id"]}/review', dict(decision='approve', proposal_version=1, match_version=game['version'])).status_code == 403
    approved = ok(lab.teacher.post(route+f'/proposals/{first["id"]}/review', dict(decision='approve', proposal_version=1, match_version=game['version'])))
    assert approved['proposal']['status'] == 'approved'
    assert approved['official_result']['approved_by'] == lab.teacher.uid
    assert detail(lab.teacher, tid)['progress']['completed'] == 1
    assert detail(lab.teacher, tid)['standings'][0]['points'] == 3
    assert lab.teacher.post(route+f'/proposals/{second["id"]}/review', dict(decision='approve', proposal_version=1, match_version=approved['match_version'])).status_code == 409
    rejected = ok(lab.teacher.post(route+f'/proposals/{second["id"]}/review', dict(decision='reject', proposal_version=1, match_version=approved['match_version'], reason='Verificato dal docente')))
    assert rejected['proposal']['status'] == 'rejected'
    assert rejected['official_result']['score']['home'] == 2
    assert lab.teacher.post(route+f'/proposals/{first["id"]}/review', dict(decision='approve', proposal_version=2, match_version=approved['match_version'])).status_code == 409


def test_review_correction_and_atomic_knockout_invalidation(lab):
    tid = tournament(lab.teacher, n=4, fmt='knockout')
    initial = detail(lab.teacher, tid)
    for game in initial['matches'][:2]:
        ok(score(lab.teacher, tid, game))
    final = detail(lab.teacher, tid)['matches'][-1]
    ok(score(lab.teacher, tid, final))
    semi = detail(lab.teacher, tid)['matches'][0]
    champion = detail(lab.teacher, tid)['champion_team_id']
    assert score(lab.teacher, tid, semi, 0, 3).status_code == 409
    assert detail(lab.teacher, tid)['champion_team_id'] == champion
    ok(score(lab.teacher, tid, semi, 0, 3, True))
    after = detail(lab.teacher, tid)
    assert after['champion_team_id'] is None
    assert after['matches'][-1]['score'] is None
    assert lab.teacher.get(f'/tournaments/{tid}/matches/{final["id"]}/result').json()['official_result'] is None
    with database(lab.path) as db:
        assert db.execute('SELECT count(*) FROM result_reviews WHERE tournament_id=?', (tid,)).fetchone()[0] == 4
        assert db.execute("SELECT actor_id FROM audit_logs WHERE action='official_result_saved' ORDER BY id DESC").fetchone()[0] == lab.teacher.uid


def test_review_can_correct_score_and_result_can_be_cleared(lab):
    tid = tournament(lab.teacher, n=2)
    assign(lab, tid)
    game = detail(lab.teacher, tid)['matches'][0]
    route = f'/tournaments/{tid}/matches/{game["id"]}'
    p = ok(lab.student.post(route+'/proposals', dict(match_version=game['version'], score=dict(type='points', home=2, away=0))), 201)
    result = ok(lab.teacher.post(route+f'/proposals/{p["id"]}/review', dict(decision='correct', proposal_version=1, match_version=game['version'], score=dict(type='points', home=0, away=2), reason='Correzione docente')))
    assert result['proposal']['score']['home'] == 2
    assert result['official_result']['score']['home'] == 0
    ok(lab.teacher.delete(route+'/result', dict(match_version=result['match_version'], reason='Da rigiocare')))
    assert detail(lab.teacher, tid)['progress']['completed'] == 0


def test_students_cannot_propose_for_another_match(lab):
    tid = tournament(lab.teacher)
    membership = assign(lab, tid)
    game = next(m for m in detail(lab.teacher, tid)['matches'] if membership['team_id'] not in (m['home_team_id'], m['away_team_id']))
    assert lab.student.post(f'/tournaments/{tid}/matches/{game["id"]}/proposals', dict(match_version=game['version'], score=dict(type='points', home=1, away=0))).status_code == 403


def test_concurrent_approvals_only_one_is_committed(lab):
    tid = tournament(lab.teacher, n=2)
    assign(lab, tid)
    game = detail(lab.teacher, tid)['matches'][0]
    route = f'/tournaments/{tid}/matches/{game["id"]}'
    p = ok(lab.student.post(route+'/proposals', dict(match_version=game['version'], score=dict(type='points', home=2, away=1))), 201)
    body = dict(decision='approve', proposal_version=1, match_version=game['version'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: lab.teacher.post(route+f'/proposals/{p["id"]}/review', body).status_code, range(2)))
    assert sorted(statuses) == [200, 409]
    with database(lab.path) as db:
        assert db.execute('SELECT count(*) FROM result_reviews WHERE proposal_id=?', (p['id'],)).fetchone()[0] == 1


def publish(actor, tid, value=True):
    version = detail(actor, tid)['tournament']['version']
    return ok(actor.patch(f'/tournaments/{tid}/publication', dict(version=version, published=value)))


def invite(actor, tid, team_id=None, require_approval=False, max_uses=2):
    return ok(actor.post(f'/tournaments/{tid}/invites', dict(team_id=team_id, expires_at=(auth.now()+timedelta(days=1)).isoformat(),
                      max_uses=max_uses, require_approval=require_approval)), 201)


def test_invite_self_enrollment_idempotency_capacity_and_revocation(lab):
    tid = tournament(lab.teacher, generate=False)
    team = ok(lab.teacher.get(f'/tournaments/{tid}/teams'))['items'][0]
    ok(lab.teacher.patch(f'/tournaments/{tid}/teams/{team["id"]}', dict(version=team['version'], name=team['name'], max_members=1)))
    link = invite(lab.teacher, tid, team['id'])
    assert 'token' not in lab.teacher.get(f'/tournaments/{tid}/invites').text
    assert ok(lab.student.post('/invites/validate', dict(token=link['token'])))['requires_login']
    first = ok(lab.student.post('/invites/accept', dict(token=link['token'])), 201)
    assert first['status'] == 'approved'
    again = ok(lab.student.post('/invites/accept', dict(token=link['token'])), 201)
    assert again['id'] == first['id']
    assert lab.second.post('/invites/accept', dict(token=link['token'])).status_code == 409
    current = lab.teacher.get(f'/tournaments/{tid}/invites').json()['items'][0]
    assert current['used'] == 1
    ok(lab.teacher.delete(f'/tournaments/{tid}/invites/{link["id"]}', dict(version=current['version'])), 204)
    assert lab.student.post('/invites/validate', dict(token=link['token'])).status_code == 410
    with database(lab.path) as db:
        stored = db.execute('SELECT token_hash FROM invites WHERE id=?', (link['id'],)).fetchone()[0]
        assert stored != link['token'] and stored == auth.digest(link['token'])


def test_approval_enrollment_direct_requests_and_expiry(lab):
    tid = tournament(lab.teacher)
    publish(lab.teacher, tid)
    team = ok(lab.teacher.get(f'/tournaments/{tid}/teams'))['items'][0]
    pending = ok(lab.student.post(f'/tournaments/{tid}/enrollments', dict(team_id=team['id'], team_version=team['version'])), 201)
    assert pending['status'] == 'pending'
    assert lab.student.get(f'/tournaments/{tid}').status_code == 404
    assert lab.student.get(f'/tournaments/{tid}/enrollments').json()['items'][0]['id'] == pending['id']
    ok(lab.teacher.post(f'/tournaments/{tid}/enrollments/{pending["id"]}/review', dict(version=1, decision='approve')))
    assert lab.student.get(f'/tournaments/{tid}').status_code == 200
    link = invite(lab.teacher, tid, team['id'], True)
    p = ok(lab.second.post('/invites/accept', dict(token=link['token'])), 201)
    assert p['status'] == 'pending'
    ok(lab.teacher.post(f'/tournaments/{tid}/enrollments/{p["id"]}/review', dict(version=1, decision='reject', reason='Non ammesso')))
    assert lab.teacher.get(f'/tournaments/{tid}/invites').json()['items'][0]['used'] == 0
    with database(lab.path, True) as db:
        db.execute('UPDATE invites SET expires_at=? WHERE id=?', ((auth.now()-timedelta(seconds=1)).isoformat(), link['id']))
    assert lab.second.post('/invites/validate', dict(token=link['token'])).status_code == 410


def test_concurrent_invite_acceptances_respect_last_slot(lab):
    tid = tournament(lab.teacher)
    team = ok(lab.teacher.get(f'/tournaments/{tid}/teams'))['items'][0]
    ok(lab.teacher.patch(f'/tournaments/{tid}/teams/{team["id"]}', dict(version=1, name=team['name'], max_members=1)))
    link = invite(lab.teacher, tid, team['id'], False, 1)
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda actor: actor.post('/invites/accept', dict(token=link['token'])).status_code, [lab.student, lab.second]))
    assert sorted(statuses) == [201, 410]
    assert lab.teacher.get(f'/tournaments/{tid}/statistics').json()['student_count'] == 1


def test_publication_has_a_privacy_whitelist_and_is_revocable(lab):
    tid = tournament(lab.teacher)
    assign(lab, tid)
    link = publish(lab.teacher, tid)
    public = ok(lab.student.get('/public/tournaments/'+link['public_slug']))
    serialized = json.dumps(public)
    for forbidden in ('@example.test', 'Alias ', 'actor_id', 'owner_id', 'user_id', 'public_token', 'audit', 'password', 'source_id'):
        assert forbidden not in serialized
    stats = ok(lab.student.get('/public/tournaments/'+link['public_slug']+'/statistics'))
    assert 'student_count' not in stats and 'pending_proposals' not in stats
    assert public['teams'] and public['matches']
    publish(lab.teacher, tid, False)
    assert lab.student.get('/public/tournaments/'+link['public_slug']).status_code == 404


def field(actor, **options):
    venue = ok(actor.post('/venues', dict(name='Palestra sintetica')), 201)
    return ok(actor.post('/fields', dict(name='Campo A', venue_id=venue['id'], sport_variant_ids=['football-5'], **options)), 201)


def schedule(actor, tid, game, fid, timestamp='2026-11-03T10:00:00+01:00', **options):
    return actor.patch(f'/tournaments/{tid}/matches/{game["id"]}/schedule', dict(version=game['version'], field_id=fid,
                     scheduled_at=timestamp, timezone='Europe/Rome', duration=20, **options))


def test_fields_calendar_conflicts_across_tournaments_and_boundaries(lab):
    a, b = tournament(lab.teacher), tournament(lab.teacher)
    resource = field(lab.teacher)
    first = detail(lab.teacher, a)['matches'][0]
    other = detail(lab.teacher, b)['matches'][0]
    scheduled = ok(schedule(lab.teacher, a, first, resource['id']))
    assert scheduled['scheduled_at'] == '2026-11-03T09:00:00+00:00'
    assert schedule(lab.teacher, b, other, resource['id']).status_code == 409
    ok(schedule(lab.teacher, b, other, resource['id'], '2026-11-03T10:20:00+01:00'))
    assert schedule(lab.student, a, first, resource['id']).status_code == 404
    assert lab.other.patch(f'/fields/{resource["id"]}', dict(name='Rubato', sport_variant_ids=['football-5'], version=1)).status_code == 404
    assert lab.teacher.get(f'/tournaments/{a}/calendar?from=2026-11-03T09:00:00Z&to=2026-11-03T09:20:00Z').json()['items'][0]['id'] == first['id']
    assert lab.teacher.get(f'/tournaments/{a}/calendar?from=bad').status_code == 422


def test_availability_sport_timezone_and_archival_checks(lab):
    tid = tournament(lab.teacher)
    resource = field(lab.teacher, availability=[dict(starts_at='2026-11-03T09:00:00Z', ends_at='2026-11-03T10:00:00Z')])
    game = detail(lab.teacher, tid)['matches'][0]
    assert schedule(lab.teacher, tid, game, resource['id'], '2026-11-03T12:00:00+01:00').status_code == 422
    assert schedule(lab.teacher, tid, game, resource['id'], '2026-11-03T10:00:00+02:00').status_code == 422
    ok(schedule(lab.teacher, tid, game, resource['id']))
    change = dict(version=1, name='Nuovo campo', venue_id=resource['venue_id'], sport_variant_ids=['basketball'])
    assert lab.teacher.patch(f'/fields/{resource["id"]}', change).status_code == 422
    ok(lab.teacher.delete(f'/fields/{resource["id"]}', dict(version=1)), 204)
    current = detail(lab.teacher, tid)['matches'][0]
    assert current['field_id'] == resource['id']
    assert schedule(lab.teacher, tid, current, resource['id']).status_code == 404


def test_team_and_dependency_calendar_conflicts(lab):
    tid = tournament(lab.teacher, fmt='knockout')
    games = detail(lab.teacher, tid)['matches']
    ok(schedule(lab.teacher, tid, games[0], None))
    assert schedule(lab.teacher, tid, games[-1], None, '2026-11-03T10:00:00+01:00').status_code == 409
    rr = tournament(lab.teacher)
    games = detail(lab.teacher, rr)['matches']
    first = games[0]
    shared = next(m for m in games[1:] if first['home_team_id'] in (m['home_team_id'], m['away_team_id']))
    ok(schedule(lab.teacher, rr, first, None))
    assert schedule(lab.teacher, rr, shared, None).status_code == 409


def test_volleyball_official_scores_standings_custom_rules_and_restart(lab):
    tid = tournament(lab.teacher, n=2, variant='volleyball-indoor', config=dict(best_of=3, target=21))
    assign(lab, tid)
    game = detail(lab.teacher, tid)['matches'][0]
    route = f'/tournaments/{tid}/matches/{game["id"]}'
    payload = dict(type='sets', sets=[dict(home=21, away=15), dict(home=19, away=21), dict(home=15, away=13)])
    proposal = ok(lab.student.post(route+'/proposals', dict(match_version=game['version'], score=payload)), 201)
    ok(lab.teacher.post(route+f'/proposals/{proposal["id"]}/review', dict(decision='approve', proposal_version=1, match_version=game['version'])))
    state = detail(lab.teacher, tid)
    assert state['standings'][0]['points'] == 2 and state['standings'][1]['points'] == 1
    assert state['standings'][0]['sets_for'] == 2
    assert state['matches'][0]['score'] == payload
    assert lab.teacher.get(f'/tournaments/{tid}/statistics').json()['sport_statistics']['sets_played'] == 3
    with TestClient(create_app(lab.path, False, mode='demo')) as client:
        actor = Actor(client, 'teacher-a@example.test', 'Docente', False)
        assert detail(actor, tid)['matches'][0]['score'] == payload
    assert lab.teacher.patch(f'/tournaments/{tid}/rules', dict(version=1, variant_id='football-5', config={})).status_code == 409


def test_bracket_links_statistics_and_pagination(lab):
    tid = tournament(lab.teacher, n=3, fmt='knockout')
    tree = ok(lab.teacher.get(f'/tournaments/{tid}/bracket'))
    rounds = tree['stages'][0]['rounds']
    assert len(rounds) == 2
    assert all(m['next']['match_id'] == rounds[1]['matches'][0]['id'] for m in rounds[0]['matches'])
    assert rounds[1]['matches'][0]['next'] is None
    assert lab.teacher.get(f'/tournaments/{tid}/statistics').json()['matches_total'] == 2
    current = lab.teacher.get(f'/tournaments/{tid}/matches?limit=1').json()
    assert len(current['items']) == 1 and current['next_cursor'] == 1
    next_page = lab.teacher.get(f'/tournaments/{tid}/matches?limit=1&cursor=1').json()
    assert next_page['items'][0]['id'] != current['items'][0]['id']
    assert lab.teacher.get(f'/tournaments/{tid}/matches?limit=101').status_code == 422


def test_penalties_and_forfeit_are_explicit_and_do_not_invent_statistics(lab):
    tid = tournament(lab.teacher, n=2)
    state = detail(lab.teacher, tid)
    game = state['matches'][0]
    team = next(t for t in state['teams'] if t['id'] == game['home_team_id'])
    result = ok(lab.teacher.patch(f'/tournaments/{tid}/matches/{game["id"]}/result',
                dict(match_version=game['version'], score=dict(type='forfeit', winner='home', reason='Assenza sintetica'), reason='Decisione docente')))
    assert result['official_result']['score']['type'] == 'forfeit'
    changed = ok(lab.teacher.patch(f'/tournaments/{tid}/teams/{team["id"]}/penalty', dict(version=1, points=4, reason='Penalità sintetica')))
    state = detail(lab.teacher, tid)
    row = next(r for r in state['standings'] if r['team_id'] == team['id'])
    assert row['points'] == -1 and row['penalty_points'] == 4
    assert lab.teacher.get(f'/tournaments/{tid}/statistics').json()['sport_statistics']['points_scored'] == 0
    assert lab.teacher.patch(f'/tournaments/{tid}/teams/{team["id"]}/penalty', dict(version=1, points=0, reason='Obsoleto')).status_code == 409
    assign(lab, tid)
    assert lab.student.patch(f'/tournaments/{tid}/teams/{team["id"]}/penalty', dict(version=changed['version'], points=0, reason='Non autorizzato')).status_code == 403


def test_multiphase_rebuild_retains_proposals_and_attributed_review_history(lab):
    tid = tournament(lab.teacher, n=4, fmt='groups', group_count=2, qualifiers=1)
    assign(lab, tid)
    for game in detail(lab.teacher, tid)['matches']:
        ok(score(lab.teacher, tid, game))
    state = detail(lab.teacher, tid)
    final = next(m for m in state['matches'] if m['kind'] == 'knockout')
    # Associate a student with whichever team qualified to this final.
    student = lab.teacher.get(f'/tournaments/{tid}/students').json()['items'][0]
    ok(lab.teacher.patch(f'/tournaments/{tid}/students/{student["id"]}/team', dict(version=student['version'], team_id=final['home_team_id'])))
    route = f'/tournaments/{tid}/matches/{final["id"]}'
    proposal = ok(lab.student.post(route+'/proposals', dict(match_version=final['version'], score=dict(type='points', home=2, away=0))), 201)
    ok(lab.teacher.post(route+f'/proposals/{proposal["id"]}/review', dict(decision='approve', proposal_version=1, match_version=final['version'])))
    group_game = next(m for m in detail(lab.teacher, tid)['matches'] if m['kind'] == 'round_robin')
    ok(score(lab.teacher, tid, group_game, 0, 3, True))
    with database(lab.path) as db:
        item = db.execute('SELECT * FROM result_proposals WHERE id=?', (proposal['id'],)).fetchone()
        assert item['match_id'] is None and item['original_match_id'] == final['id']
        assert db.execute('SELECT reviewed_by FROM result_reviews WHERE proposal_id=?', (proposal['id'],)).fetchone()[0] == lab.teacher.uid
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
    assert final['id'] not in [m['id'] for m in detail(lab.teacher, tid)['matches']]


def test_correcting_only_volleyball_rallies_recalculates_tiebreaks(lab):
    tid = tournament(lab.teacher, n=2, variant='volleyball-indoor')
    game = detail(lab.teacher, tid)['matches'][0]
    route = f'/tournaments/{tid}/matches/{game["id"]}/result'
    first = dict(type='sets', sets=[dict(home=25, away=10)]*3)
    updated = ok(lab.teacher.patch(route, dict(match_version=game['version'], score=first, reason='Prima verifica')))
    second = dict(type='sets', sets=[dict(home=25, away=20)]*3)
    corrected = ok(lab.teacher.patch(route, dict(match_version=updated['match_version'], score=second, reason='Correzione rally')))
    assert corrected['match_version'] > updated['match_version']
    assert detail(lab.teacher, tid)['standings'][0]['rally_difference'] == 15


def test_backup_restore_and_explicit_legacy_claim(lab, tmp_path):
    with TestClient(lab.app) as legacy:
        tid = ok(legacy.post('/api/tournaments', json=dict(name='Legacy sintetico', team_names=['Uno','Due'])), 201)['id']
        ok(legacy.post(f'/api/tournaments/{tid}/generate'))
        game = legacy.get(f'/api/tournaments/{tid}').json()['matches'][0]
        ok(legacy.patch(f'/api/tournaments/{tid}/matches/{game["id"]}', json=dict(version=game['version'], home_score=2, away_score=1)))
    assert lab.teacher.get(f'/tournaments/{tid}').status_code == 404
    with database(lab.path, True) as db:
        claim(db, tid, lab.teacher.uid, 'football-5')
    assert detail(lab.teacher, tid)['matches'][0]['home_score'] == 2
    assert lab.teacher.get(f'/tournaments/{tid}/matches/{game["id"]}/result').json()['official_result']['provenance'] == 'legacy'
    backup = verified_copy(lab.path, tmp_path/'backup.sqlite3')
    restored = verified_copy(backup, tmp_path/'restored.sqlite3')
    with TestClient(create_app(restored, False, mode='demo')) as client:
        actor = Actor(client, 'teacher-a@example.test', 'Docente', False)
        assert detail(actor, tid)['progress']['completed'] == 1
    with pytest.raises(ValueError):
        verified_copy(lab.path, backup)


def test_service_mode_disables_legacy_and_requires_https_configuration(tmp_path, monkeypatch):
    with pytest.raises(ValueError):
        create_app(tmp_path/'unconfigured.sqlite3', False, mode='service')
    monkeypatch.setenv('TORNEO_PUBLIC_ORIGIN', 'https://testserver')
    monkeypatch.setenv('TORNEO_ALLOWED_HOSTS', 'testserver')
    app = create_app(tmp_path/'service.sqlite3', False, mode='service')
    with TestClient(app, base_url='https://testserver') as client:
        assert client.get('/api/tournaments').status_code == 404
        assert client.post('/api/demo').status_code == 404
        csrf = ok(client.get(PREFIX+'/auth/csrf'))['csrf_token']
        response = client.post(PREFIX+'/auth/register', headers={'X-CSRF-Token': csrf},
                   json=dict(email='service@example.test', password=PASSWORD, display_name='Alias'))
        assert response.status_code == 201
        assert 'Secure' in response.headers['set-cookie'] and 'HttpOnly' in response.headers['set-cookie']
        assert client.get(PREFIX+'/users/me').status_code == 200
        assert client.get('/api/health').json()['mode'] == 'service'
        assert client.post(PREFIX+'/auth/logout', headers={'X-CSRF-Token': response.json()['csrf_token'], 'Origin':'https://evil.example'}).status_code == 403
    with database(app.state.db_path) as db:
        assert db.execute('SELECT count(*) FROM tournaments').fetchone()[0] == 0


def test_migration_two_to_latest_preserves_data_and_creates_backup(tmp_path):
    from db import BASE
    path = tmp_path/'v2.sqlite3'
    with sqlite3.connect(path) as db:
        db.executescript((BASE/'migrations/001_initial.sql').read_text(encoding='utf-8'))
        db.executescript((BASE/'migrations/002_stable_match_ids.sql').read_text(encoding='utf-8'))
        db.execute("INSERT INTO tournaments(name,sport,format,public_token) VALUES ('Conservare','Calcio','knockout','legacy-token')")
    initialize(path)
    backups = list(tmp_path.glob(f'v2.pre-v{SCHEMA_VERSION}-*.sqlite3'))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as backup:
        assert backup.execute('PRAGMA user_version').fetchone()[0] == 2
    with database(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == SCHEMA_VERSION
        assert db.execute('SELECT name,owner_id FROM tournaments').fetchone()[0] == 'Conservare'
        assert db.execute('SELECT owner_id FROM tournaments').fetchone()[0] is None
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
