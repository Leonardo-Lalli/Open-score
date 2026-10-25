from db import BASE

LEGACY_PAGES = (
    'create.html',
    'gestione_partecipanti.html',
    'panoramica_torneo.html',
    'tabellone_torneo.html',
    'campione_sport_editorial.html',
)
FORBIDDEN_SPORTS = ('danza', 'padel', 'tennis', 'pallamano')


def test_legacy_urls_redirect_to_the_spa(client):
    for page in LEGACY_PAGES:
        root = client.get(f'/{page}', follow_redirects=False)
        assert root.status_code == 302
        assert root.headers['location'] == '/'

        static_page = client.get(f'/static/{page}')
        assert static_page.status_code == 200
        assert 'http-equiv="refresh"' in static_page.text
        assert 'url=/' in static_page.text


def test_static_ui_has_no_out_of_catalog_sports(client):
    assets = [*(BASE / 'static').glob('*.html'), BASE / 'static' / 'app.js']
    for path in assets:
        text = path.read_text(encoding='utf-8').lower()
        for sport in FORBIDDEN_SPORTS:
            assert sport not in text, f'{sport!r} trovato in {path.name}'


def test_index_references_versioned_assets_and_disables_cache(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'app.js?v=0.6.0' in response.text
    assert 'styles.css?v=0.6.0' in response.text
    assert 'no-cache' in response.headers['cache-control']


def test_mobile_shell_has_safe_area_and_touch_targets(client):
    html = client.get('/').text
    assert 'viewport-fit=cover' in html

    css = (BASE / 'static' / 'styles.css').read_text(encoding='utf-8')
    assert '100dvh' in css
    assert 'env(safe-area-inset-top)' in css
    assert 'env(safe-area-inset-bottom)' in css
    assert '@media (max-width: 800px)' in css
    assert 'min-height: 44px' in css
    assert 'font-size: 16px' in css
    assert css.count('{') == css.count('}')

    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    assert 'menu-open' in script
    assert 'modal-open' in script


def test_static_shell_assets_are_revalidated(client):
    for path in ('/static/app.js', '/static/styles.css', '/static/create.html'):
        response = client.get(path)
        assert response.status_code == 200
        assert 'no-cache' in response.headers['cache-control']


def test_spa_no_longer_links_to_legacy_design_pages(client):
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    for page in LEGACY_PAGES:
        assert page not in script
