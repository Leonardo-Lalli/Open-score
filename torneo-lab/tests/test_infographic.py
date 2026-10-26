"""SVG integrity tests for the shareable infographic.

The generator lives in `static/infographic.js`, so it can be exercised without
a browser. Tests are skipped when Node.js is not available.
"""
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    shutil.which('node') is None, reason='Node.js non disponibile')

BASE = Path(__file__).resolve().parents[1]
PROBE = BASE / 'tests' / 'infographic_probe.js'
SVG = '{http://www.w3.org/2000/svg}svg'


@pytest.fixture(scope='module')
def render():
    completed = subprocess.run(
        ['node', str(PROBE)], cwd=BASE, capture_output=True, text=True,
        check=True, timeout=60)
    return json.loads(completed.stdout)


def test_svg_is_valid_xml_with_the_expected_canvas(render):
    assert render['strict'].startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert render['inline'].startswith('<svg')
    for key in ('inline', 'noQr', 'minimal'):
        root = ET.fromstring(render[key])
        assert root.tag == SVG
        assert root.get('viewBox') == '0 0 1080 1350'
        assert root.get('width') == '1080'
        assert root.get('height') == '1350'
        assert root.get('role') == 'img'


def test_infographic_reads_payload_and_escapes_text(render):
    text = render['inline']
    assert 'Coppa &lt;5A&gt; &amp; amici' in text
    assert 'Coppa <5A>' not in text
    for marker in ('SQUADRE', 'STUDENTI', 'PARTITE', 'AVANZAMENTO', '40%',
                   'CAMPIONE', 'Girone A', 'Inquadra per seguire il torneo',
                   'Open Score', '5B', '5C'):
        assert marker in text, f'{marker!r} mancante nell’SVG'
    assert '<script' not in text
    assert '<foreignObject' not in text


def test_qr_modules_are_drawn_as_real_rects(render):
    assert render['qrRects'] >= 21 * 21
    assert render['noQrRects'] < 100


def test_empty_state_is_explicit_and_not_invented(render):
    text = render['noQr']
    assert 'Classifica in aggiornamento' in text
    assert 'Condivisione pubblica non attiva' in text
    assert 'CAMPIONE' not in text
    assert '5A' in text  # the title still comes from the real payload
    ET.fromstring(text)


def test_minimal_payload_does_not_throw(render):
    text = render['minimal']
    assert 'Torneo' in text
    assert 'Classifica in aggiornamento' in text
    ET.fromstring(text)


def test_infographic_module_contains_only_labels():
    source = (BASE / 'static' / 'infographic.js').read_text(encoding='utf-8')
    for hardcoded in ('5A', 'Falchi', 'Mario Rossi', 'Coppa d'):
        assert hardcoded not in source
    assert 'payload' in source
    assert 'module.exports' in source
