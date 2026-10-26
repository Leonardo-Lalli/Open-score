from fastapi.testclient import TestClient

from app import create_app


def test_unknown_host_is_rejected(tmp_path):
    app = create_app(tmp_path / 'hosts.sqlite3', session_secret='hosts-secret')
    with TestClient(app, base_url='http://evil.example') as client:
        assert client.get('/api/health').status_code == 400


def test_configured_lan_host_and_loopback_are_allowed(tmp_path):
    app = create_app(tmp_path / 'lan.sqlite3', session_secret='lan-secret',
                     allowed_hosts=['192.168.1.50', 'open-score.local'])
    with TestClient(app, base_url='http://192.168.1.50:8000') as client:
        assert client.get('/api/health').status_code == 200
    with TestClient(app, base_url='http://open-score.local:8000') as client:
        assert client.get('/api/health').status_code == 200
    with TestClient(app, base_url='http://127.0.0.1:8000') as client:
        assert client.get('/api/health').status_code == 200


def test_hosts_can_come_from_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv('TORNEO_ALLOWED_HOSTS', '10.0.0.7, open-score.local')
    app = create_app(tmp_path / 'env.sqlite3', session_secret='env-secret')
    assert app.state.allowed_hosts == [
        '127.0.0.1', 'localhost', 'testserver', '10.0.0.7', 'open-score.local',
    ]
