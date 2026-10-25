"""Deterministic tournament algorithms, independent of HTTP and persistence."""

from random import Random


def validate_ids(team_ids: list[int]) -> None:
    if not 2 <= len(team_ids) <= 32:
        raise ValueError('Servono da 2 a 32 partecipanti')
    if len(set(team_ids)) != len(team_ids):
        raise ValueError('I partecipanti devono essere distinti')


def round_robin(team_ids: list[int], legs: int = 1) -> list[tuple[int, int, int]]:
    """Circle method; missing opponent is a rest, never a scored match."""
    validate_ids(team_ids)
    if legs not in (1, 2):
        raise ValueError('Scegli sola andata o andata e ritorno')
    rotation: list[int | None] = list(team_ids)
    if len(rotation) % 2:
        rotation.append(None)
    fixtures = []
    n = len(rotation)
    for turn in range(1, n):
        for j in range(n // 2):
            home, away = rotation[j], rotation[-1-j]
            if home is not None and away is not None:
                if (turn + j) % 2 == 0:
                    home, away = away, home
                fixtures.append((turn, home, away))
        rotation = [rotation[0], rotation[-1], *rotation[1:-1]]
    if legs == 2:
        fixtures += [(r+n-1, b, a) for r, a, b in fixtures[:]]
    return fixtures


def knockout_plan(team_ids: list[int], seed: int | None = None) -> list[dict]:
    """Full dependency tree. source_* refers to indexes in the returned plan."""
    validate_ids(team_ids)
    ids = list(team_ids)
    if seed is not None:
        Random(seed).shuffle(ids)
    size = 1 << (len(ids)-1).bit_length()
    order = [1, 2]
    while len(order) < size:
        total = len(order)*2 + 1
        order = [slot for value in order for slot in (value, total-value)]
    slots = [ids[s-1] if s <= len(ids) else None for s in order]
    plan = []
    previous = []
    for position in range(size//2):
        home, away = slots[2*position:2*position+2]
        previous.append(len(plan))
        plan.append({'round_no': 1, 'position': position, 'home_team_id': home,
                     'away_team_id': away, 'source_home': None, 'source_away': None,
                     'is_bye': int(home is None or away is None)})
    turn = 2
    while len(previous) > 1:
        current = []
        for position in range(len(previous)//2):
            current.append(len(plan))
            plan.append({'round_no': turn, 'position': position, 'home_team_id': None,
                         'away_team_id': None, 'source_home': previous[2*position],
                         'source_away': previous[2*position+1], 'is_bye': 0})
        previous = current
        turn += 1
    return plan


def _empty_row(team: dict) -> dict:
    return {'team_id': team['id'], 'name': team['name'], 'played': 0, 'won': 0, 'drawn': 0,
            'lost': 0, 'goals_for': 0, 'goals_against': 0, 'goal_difference': 0, 'points': 0}


def _apply_match(row_home: dict, row_away: dict, match: dict, win_points: int,
                 draw_points: int, loss_points: int,
                 rules: dict | None = None) -> None:
    ga, gb = match['home_score'], match['away_score']
    if ga is None or gb is None or match.get('is_bye'):
        return
    for row, scored, conceded in ((row_home, ga, gb), (row_away, gb, ga)):
        row['played'] += 1
        row['goals_for'] += scored
        row['goals_against'] += conceded
    if ga == gb:
        for row in (row_home, row_away):
            row['drawn'] += 1
            row['points'] += draw_points
    else:
        winner, loser = (row_home, row_away) if ga > gb else (row_away, row_home)
        winner_points, loser_points = win_points, loss_points
        # Sports such as volleyball award a bonus point when the match goes to
        # the deciding set. `home_score`/`away_score` hold the sets won.
        profile = (rules or {}).get('standings') or {}
        max_sets = (rules or {}).get('max_sets')
        win_tiebreak = profile.get('win_tiebreak')
        if (max_sets and win_tiebreak is not None
                and (ga + gb) == int(max_sets)):
            winner_points = int(win_tiebreak)
            loser_points = int(profile.get('loss_tiebreak') or 0)
        winner['won'] += 1
        winner['points'] += winner_points
        loser['lost'] += 1
        loser['points'] += loser_points


def _finalise(table: dict[int, dict]) -> None:
    for row in table.values():
        row['goal_difference'] = row['goals_for'] - row['goals_against']


def _default_key(row: dict) -> tuple:
    return (-row['points'], -row['goal_difference'], -row['goals_for'],
            row['name'].casefold(), row['team_id'])


def _head_to_head(rows: list[dict], matches: list[dict], win_points: int,
                  draw_points: int, loss_points: int,
                  rules: dict | None = None) -> list[dict]:
    """Rank equal-points groups by a mini-table of their mutual matches."""
    ordered = sorted(rows, key=_default_key)
    result: list[dict] = []
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end]['points'] == ordered[start]['points']:
            end += 1
        group = ordered[start:end]
        if len(group) == 1:
            result.extend(group)
        else:
            ids = {row['team_id'] for row in group}
            mini = {row['team_id']: dict(row) for row in group}
            for row in mini.values():
                for field in ('played', 'won', 'drawn', 'lost', 'goals_for',
                              'goals_against', 'goal_difference', 'points'):
                    row[field] = 0
            for match in matches:
                if match['home_team_id'] in ids and match['away_team_id'] in ids:
                    _apply_match(mini[match['home_team_id']], mini[match['away_team_id']],
                                 match, win_points, draw_points, loss_points, rules)
            _finalise(mini)
            overall = {row['team_id']: row for row in group}
            ordered_mini = sorted(mini.values(), key=lambda row: (
                -row['points'], -row['goal_difference'], -row['goals_for'],
                -overall[row['team_id']]['goal_difference'],
                -overall[row['team_id']]['goals_for'],
                row['name'].casefold(), row['team_id']))
            result.extend(overall[row['team_id']] for row in ordered_mini)
        start = end
    return result


def build_standings(teams: list[dict], matches: list[dict], win_points: int = 3,
                    draw_points: int = 1, loss_points: int = 0,
                    tie_breaker: str = 'goal_difference',
                    rules: dict | None = None) -> list[dict]:
    table = {t['id']: _empty_row(t) for t in teams}
    for m in matches:
        if m['home_team_id'] in table and m['away_team_id'] in table:
            _apply_match(table[m['home_team_id']], table[m['away_team_id']], m,
                         win_points, draw_points, loss_points, rules)
    _finalise(table)

    if tie_breaker == 'head_to_head':
        return _head_to_head(list(table.values()), matches, win_points,
                             draw_points, loss_points, rules)
    keys = {
        'goals_for': lambda x: (-x['points'], -x['goals_for'], -x['goal_difference'],
                                x['name'].casefold(), x['team_id']),
        'wins': lambda x: (-x['points'], -x['won'], -x['goal_difference'],
                           -x['goals_for'], x['name'].casefold(), x['team_id']),
    }.get(tie_breaker, _default_key)
    return sorted(table.values(), key=keys)
