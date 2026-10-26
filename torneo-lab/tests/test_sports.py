import pytest
from pydantic import TypeAdapter, ValidationError

import sports


def value(raw):
    return TypeAdapter(sports.Score).validate_python(raw)


@pytest.mark.parametrize('variant', ['football-11', 'football-7', 'football-5'])
def test_football_variants_validate_goals_and_knockout_draws(variant):
    config = sports.configuration(variant)
    assert sports.validate_score(variant, config, value(dict(type='points', home=0, away=0))) == (0, 0)
    with pytest.raises(ValueError):
        sports.validate_score(variant, config, value(dict(type='points', home=1, away=1)), True)
    assert sports.metadata(variant)['result_schema']['properties']['home']['type'] == 'integer'


@pytest.mark.parametrize('score', [True, '2', 1.5, -1, 1000])
def test_strict_points(score):
    with pytest.raises(ValidationError):
        value(dict(type='points', home=score, away=1))


def test_basketball_requires_decisive_final_score():
    config = sports.configuration('basketball')
    with pytest.raises(ValueError):
        sports.validate_score('basketball', config, value(dict(type='points', home=50, away=50)))
    assert sports.validate_score('basketball', config, value(dict(type='points', home=54, away=50))) == (54, 50)
    with pytest.raises(ValueError):
        sports.configuration('basketball', {'allow_draw': True})


@pytest.mark.parametrize('sets', [
    [(25,20), (25,20)],  # Not enough sets to win best-of-five.
    [(25,24), (25,20), (25,20)],  # Insufficient winning margin.
    [(29,20), (25,20), (25,20)],  # Set should have ended earlier.
    [(25,20), (25,20), (25,20), (25,20)],  # Extra set after win.
    [(25,20), (20,25), (25,20), (20,25), (14,12)],  # Decider incomplete.
    [(25,20), (20,25), (25,20), (20,25), (25,20)],  # Decider overshoots.
])
def test_incomplete_or_impossible_volleyball_sets_rejected(sets):
    score = value(dict(type='sets', sets=[dict(home=a, away=b) for a, b in sets]))
    with pytest.raises(ValueError):
        sports.validate_score('volleyball-indoor', sports.configuration('volleyball-indoor'), score)


def test_volleyball_deuce_and_deciding_set():
    score = value(dict(type='sets', sets=[dict(home=a, away=b) for a, b in
                  [(27,25), (20,25), (25,23), (20,25), (18,16)]]))
    assert sports.validate_score('volleyball-indoor', sports.configuration('volleyball-indoor'), score) == (3, 2)


def test_score_types_are_not_interchangeable_and_forfeit_is_explicit():
    points = value(dict(type='points', home=3, away=0))
    with pytest.raises(ValueError):
        sports.validate_score('volleyball-indoor', sports.configuration('volleyball-indoor'), points)
    sets = value(dict(type='sets', sets=[dict(home=25, away=20)]*3))
    with pytest.raises(ValueError):
        sports.validate_score('football-5', sports.configuration('football-5'), sets)
    awarded = value(dict(type='forfeit', winner='away', reason='Decisione sintetica'))
    assert sports.validate_score('basketball', sports.configuration('basketball'), awarded) == (0, 20)
    assert sports.validate_score('volleyball-indoor', sports.configuration('volleyball-indoor'), awarded) == (0, 3)


def test_school_rules_can_be_configured_without_unknown_keys():
    rules = sports.configuration('football-7', dict(duration=30, periods=3, win_points=5))
    assert rules['duration'] == 30 and rules['periods'] == 3 and rules['win_points'] == 5
    with pytest.raises(ValueError):
        sports.configuration('unsupported')
    with pytest.raises(ValidationError):
        sports.configuration('football-5', dict(magic_rule=True))
