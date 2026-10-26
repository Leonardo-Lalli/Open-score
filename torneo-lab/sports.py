"""School presets and authoritative score validation, independent of HTTP/SQL."""
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from engine import build_standings


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid')


Number = Annotated[int, Field(strict=True, ge=0, le=999)]


class PointsScore(Model):
    type: Literal['points']
    home: Number
    away: Number


class SetScore(Model):
    home: Number
    away: Number


class SetsScore(Model):
    type: Literal['sets']
    sets: list[SetScore] = Field(min_length=1, max_length=7)


class ForfeitScore(Model):
    type: Literal['forfeit']
    winner: Literal['home', 'away']
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]


Score = Annotated[PointsScore | SetsScore | ForfeitScore, Field(discriminator='type')]


class PointsRules(Model):
    duration: int = Field(default=40, strict=True, ge=1, le=240)
    periods: int = Field(default=2, strict=True, ge=1, le=8)
    allow_draw: bool = Field(default=True, strict=True)
    win_points: int = Field(default=3, strict=True, ge=0, le=10)
    draw_points: int = Field(default=1, strict=True, ge=0, le=10)
    loss_points: int = Field(default=0, strict=True, ge=0, le=10)
    forfeit_score: int = Field(default=3, strict=True, ge=1, le=999)


class SetRules(Model):
    duration: int = Field(default=60, strict=True, ge=1, le=240)
    best_of: Literal[3, 5] = 5
    target: int = Field(default=25, strict=True, ge=1, le=99)
    deciding_target: int = Field(default=15, strict=True, ge=1, le=99)
    win_by: int = Field(default=2, strict=True, ge=2, le=10)
    decisive_win_points: int = Field(default=3, strict=True, ge=0, le=10)
    narrow_win_points: int = Field(default=2, strict=True, ge=0, le=10)
    narrow_loss_points: int = Field(default=1, strict=True, ge=0, le=10)
    loss_points: int = Field(default=0, strict=True, ge=0, le=10)


VARIANTS = {
    'football-11': ('Calcio', 'Calcio a 11', 'points', dict(duration=90)),
    'football-7': ('Calcio', 'Calcio a 7', 'points', dict(duration=50)),
    'football-5': ('Calcio a 5', 'Calcio a 5', 'points', dict(duration=40)),
    'basketball': ('Basket', 'Basket standard', 'points', dict(duration=40, periods=4,
                    allow_draw=False, win_points=2, draw_points=0, forfeit_score=20)),
    'volleyball-indoor': ('Pallavolo', 'Pallavolo indoor', 'sets', {}),
}


def configuration(variant_id, config=None):
    if variant_id not in VARIANTS:
        raise ValueError('Variante sportiva non supportata')
    sport, name, kind, defaults = VARIANTS[variant_id]
    model = SetRules if kind == 'sets' else PointsRules
    rules = model.model_validate({**defaults, **(config or {})}).model_dump()
    if variant_id == 'basketball' and rules['allow_draw']:
        raise ValueError('Il basket richiede un risultato finale decisivo')
    return rules


def metadata(variant_id):
    rules = configuration(variant_id)
    kind = VARIANTS[variant_id][2]
    return dict(variant_id=variant_id, defaults=rules,
                rules_schema=(SetRules if kind == 'sets' else PointsRules).model_json_schema(),
                result_schema=(SetsScore if kind == 'sets' else PointsScore).model_json_schema(),
                administrative_result_schema=ForfeitScore.model_json_schema(),
                standings_criteria=(['points', 'set_difference', 'rally_difference', 'name', 'team_id']
                                    if kind == 'sets' else ['points', 'goal_difference', 'goals_for', 'name', 'team_id']))


def validate_score(variant_id, rules, score, knockout=False):
    """Return engine-compatible totals; preserve the full score separately."""
    kind = VARIANTS[variant_id][2]
    value = score.model_dump() if isinstance(score, BaseModel) else score
    if value['type'] == 'forfeit':
        total = rules['best_of']//2 + 1 if kind == 'sets' else rules['forfeit_score']
        return (total, 0) if value['winner'] == 'home' else (0, total)
    if kind == 'points':
        if value['type'] != 'points':
            raise ValueError('Questa disciplina usa punti, non set')
        home, away = value['home'], value['away']
        if home == away and (knockout or not rules['allow_draw']):
            raise ValueError('Serve un vincitore; registrare il punteggio finale dopo lo spareggio')
        return home, away
    if value['type'] != 'sets':
        raise ValueError('Questa disciplina richiede i singoli set')
    home = away = 0
    needed = rules['best_of']//2 + 1
    for index, item in enumerate(value['sets']):
        if max(home, away) == needed:
            raise ValueError('Non si possono giocare set dopo la vittoria')
        a, b = item['home'], item['away']
        target = rules['deciding_target'] if index == rules['best_of']-1 else rules['target']
        high, low = max(a, b), min(a, b)
        if high < target or high-low < rules['win_by']:
            raise ValueError('Set incompleto o scarto insufficiente')
        if high > target and high-low != rules['win_by']:
            raise ValueError('Il set deve terminare al primo punteggio decisivo')
        home += a > b
        away += b > a
    if max(home, away) != needed:
        raise ValueError('Numero di set insufficiente per determinare il vincitore')
    return home, away


def standings(roster, fixtures, variant_id, rules, penalties=None):
    penalties = penalties or {}
    if VARIANTS[variant_id][2] == 'points':
        table = build_standings(roster, fixtures, rules['win_points'], rules['draw_points'], rules['loss_points'])
        for row in table:
            row['penalty_points'] = penalties.get(row['team_id'], 0)
            row['points'] -= row['penalty_points']
        return sorted(table, key=lambda r: (-r['points'], -r['goal_difference'], -r['goals_for'], r['name'].casefold(), r['team_id']))
    table = build_standings(roster, fixtures, 0, 0, 0)
    by_id = {r['team_id']: r for r in table}
    for row in table:
        row.update(sets_for=row['goals_for'], sets_against=row['goals_against'],
                   set_difference=row['goal_difference'], rallies_for=0, rallies_against=0)
    for match in fixtures:
        if match['home_score'] is None or match['is_bye']:
            continue
        a, b = match['home_score'], match['away_score']
        winner = by_id[match['home_team_id'] if a > b else match['away_team_id']]
        loser = by_id[match['away_team_id'] if a > b else match['home_team_id']]
        narrow = min(a, b) == rules['best_of']//2
        winner['points'] += rules['narrow_win_points'] if narrow else rules['decisive_win_points']
        loser['points'] += rules['narrow_loss_points'] if narrow else rules['loss_points']
        score = json.loads(match['score_json']) if match.get('score_json') else {}
        for item in score.get('sets', []):
            by_id[match['home_team_id']]['rallies_for'] += item['home']
            by_id[match['home_team_id']]['rallies_against'] += item['away']
            by_id[match['away_team_id']]['rallies_for'] += item['away']
            by_id[match['away_team_id']]['rallies_against'] += item['home']
    for row in table:
        row['rally_difference'] = row['rallies_for'] - row['rallies_against']
        row['penalty_points'] = penalties.get(row['team_id'], 0)
        row['points'] -= row['penalty_points']
    return sorted(table, key=lambda r: (-r['points'], -r['set_difference'],
                  -r['rally_difference'], r['name'].casefold(), r['team_id']))
