"""Guardie sulle regole di qualità del frontend.

Queste verifiche non guardano l'estetica: impediscono le regressioni che il
prompt 26 elenca come inaccettabili (client HTTP duplicato, azioni senza
handler, classifiche calcolate nel browser, ritorno del vecchio CSS, dati demo).
"""
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
STATIC = BASE / 'static'
SCRIPT = (STATIC / 'app.js').read_text(encoding='utf-8')
CSS = (STATIC / 'styles.css').read_text(encoding='utf-8')


def test_single_http_client():
    assert SCRIPT.count('fetch(') == 1
    assert 'async function api(' in SCRIPT
    assert 'async function apiWithMessages(' in SCRIPT
    for marker in ('PROPOSAL_MESSAGES', 'INVITE_MESSAGES', 'FIELD_MESSAGES',
                   'CALENDAR_MESSAGES'):
        assert marker in SCRIPT


def test_every_literal_action_has_a_handler():
    used = set(re.findall(r'data-action="([^"$]+)"', SCRIPT))
    used |= set(re.findall(r'button\([^,]+,\s*"([a-z0-9-]+)"', SCRIPT))
    block = re.search(r'const actions = \{(.*?)\n\};', SCRIPT, re.DOTALL)
    assert block is not None, 'mappa actions non trovata'
    registered = set(re.findall(
        r'^\s{2}"?([a-z0-9-]+)"?\s*[:,]', block.group(1), re.MULTILINE))
    assert len(used) >= 30, 'parser delle azioni non sta trovando i pulsanti'
    assert used <= registered, f'azioni senza handler: {sorted(used - registered)}'


def test_standings_are_provided_by_the_backend():
    assert 'data.standings' in SCRIPT
    assert 'g.standings' in SCRIPT
    for forbidden in ('function buildStandings', 'function computeStandings',
                      'function calculateStandings'):
        assert forbidden not in SCRIPT


def test_stylesheet_has_a_single_design_system():
    assert CSS.count(':root {') == 1
    for legacy in ('--primary:', '--on-surface:', 'body.design-page',
                   '.create-steps', '.display-large', '.btn-primary'):
        assert legacy not in CSS, f'residuo del vecchio design system: {legacy}'
    assert '.subsection-title' in CSS
    assert 'font-family: "DM Sans", "Segoe UI", Arial, sans-serif;' in CSS
    assert len(CSS.splitlines()) < 4000, 'il CSS sta tornando a crescere senza controllo'
    assert CSS.count('{') == CSS.count('}')


def test_share_link_uses_the_public_token_and_is_not_shown_to_students():
    assert 'location.origin + "/public/" + token' in SCRIPT
    assert 'data?.tournament?.public_token' in SCRIPT
    assert 'canManage() ? button("Condividi", "share"' in SCRIPT


def test_no_demo_dataset_or_private_metadata_in_the_shell():
    html = (STATIC / 'index.html').read_text(encoding='utf-8')
    for text in (SCRIPT, html):
        for forbidden in ('Torneo di prova', 'Squadra 1', 'demo_key',
                          'public_token = "'):
            assert forbidden not in text, f'dato demo o privato nel frontend: {forbidden}'
