"""Geometry and dependency tests for the knockout bracket.

The layout lives in `static/bracket-layout.js` so it can be exercised without a
browser. If Node.js is not available the test is skipped instead of failing the
suite.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    shutil.which('node') is None, reason='Node.js non disponibile')

BASE = Path(__file__).resolve().parents[1]
PROBE = BASE / 'tests' / 'bracket_layout_probe.js'

COLUMN = 295
ROW = 128


@pytest.fixture(scope='module')
def scenarios():
    completed = subprocess.run(
        ['node', str(PROBE)], cwd=BASE, capture_output=True, text=True,
        check=True, timeout=60)
    return json.loads(completed.stdout)


def _final(scenario):
    return max(
        scenario['fixtures'],
        key=lambda match: (match['round_no'], match['position']))


@pytest.mark.parametrize(
    ('teams', 'rounds', 'labels', 'first'),
    [
        (4, 2, ['Semifinali', 'Finale'], 2),
        (8, 3, ['Quarti di finale', 'Semifinali', 'Finale'], 4),
        (16, 4, ['Ottavi di finale', 'Quarti di finale', 'Semifinali',
                 'Finale'], 8),
    ],
)
def test_bracket_size_and_round_labels(scenarios, teams, rounds, labels, first):
    scenario = scenarios[str(teams)]
    assert scenario['rounds'] == rounds
    assert scenario['labels'] == labels
    assert scenario['first'] == first
    assert scenario['width'] == (rounds + 1) * COLUMN - 48
    assert scenario['height'] == max(210, first * ROW + 60)
    assert len(scenario['paths']) == 2 * (first - 1) + 1


def test_champion_column_sits_after_the_final(scenarios):
    for key in ('4', '8', '16', '6', '5'):
        scenario = scenarios[key]
        final = _final(scenario)
        final_coord = scenario['coords'][str(final['id'])]
        champion = scenario['champion']
        assert champion['x'] == scenario['rounds'] * COLUMN
        assert champion['y'] == final_coord['y']


def test_connections_follow_backend_sources(scenarios):
    for key in ('4', '8', '16', '6', '5'):
        scenario = scenarios[key]
        parents = {
            str(match['id']): {
                str(source) for source in
                (match['source_home'], match['source_away'])
                if source is not None
            }
            for match in scenario['fixtures']
            if match['source_home'] is not None
            or match['source_away'] is not None
        }
        drawn = {}
        for path in scenario['paths']:
            assert path['d'].startswith('M')
            if path['toMatch'] == 'champion':
                assert path['fromMatch'] == str(_final(scenario)['id'])
                continue
            drawn.setdefault(path['toMatch'], set()).add(path['fromMatch'])
        assert drawn == parents


def test_byes_keep_the_tree_complete(scenarios):
    scenario = scenarios['6']
    assert scenario['byes'] == 2
    assert scenario['rounds'] == 3
    assert len(scenario['paths']) == 7
    # A BYE is a real round-one match: it still owns a card.
    assert len(scenario['coords']) == len(scenario['fixtures'])


def test_scores_and_array_order_do_not_move_cards(scenarios):
    for scenario in scenarios.values():
        assert scenario['scoreInvariant'] is True
        assert scenario['orderInvariant'] is True


def test_layout_module_uses_sources_not_array_positions():
    script = (BASE / 'static' / 'bracket-layout.js').read_text(encoding='utf-8')
    assert 'source_home' in script
    assert 'source_away' in script
    assert 'module.exports' in script
