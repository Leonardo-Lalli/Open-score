"""Application rules; callers own the atomic database transaction."""
import json
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from engine import build_standings, knockout_plan, round_robin
from schemas import PlayerInput, TournamentInput, TournamentUpdate
import sport_rules

STRUCTURAL_FIELDS = {
    'sport', 'sport_id', 'variant', 'variant_id', 'format', 'participant_kind',
    'win_points', 'draw_points', 'loss_points', 'legs', 'group_count',
    'qualifiers', 'random_seed', 'tournament_type', 'scoring_system',
    'tie_breaker',
}


def rows(db, sql, params=()):
    return [dict(r) for r in db.execute(sql, params)]


def required(db, tid):
    result = db.execute('SELECT * FROM tournaments WHERE id=?', (tid,)).fetchone()
    if result is None:
        raise HTTPException(404, 'Torneo non trovato')
    return dict(result)


def active(db, tid):
    """Reject writes on archived or historical tournaments."""
    tournament = required(db, tid)
    if tournament['archived_at']:
        raise HTTPException(409, 'Torneo archiviato: ripristinalo prima di modificarlo')
    if tournament['sport_id'] is None or tournament['variant_id'] is None:
        raise HTTPException(409, 'Sport storico non più supportato: il torneo è in sola lettura')
    return tournament


def audit(db, tid, action, payload):
    db.execute('INSERT INTO audit_logs(tournament_id,action,payload) VALUES (?,?,?)',
               (tid, action, json.dumps(payload, ensure_ascii=False)))


def _rules(tournament: dict) -> dict:
    try:
        parsed = json.loads(tournament.get('rules_snapshot') or '{}')
    except (TypeError, ValueError):
        parsed = {}
    return parsed if isinstance(parsed, dict) else {}


def _variant_for_tournament(db, tournament: dict):
    if tournament.get('variant_id'):
        variant = sport_rules.get_variant_by_id(db, tournament['variant_id'])
        if variant:
            return variant
    if tournament.get('variant'):
        variant = sport_rules.get_variant_by_slug(db, tournament['variant'])
        if variant:
            return variant
    if tournament.get('sport_id'):
        sport = sport_rules.get_sport_by_id(db, tournament['sport_id'])
        if sport:
            return sport.default_variant(tournament.get('participant_kind'))
    return None


def resolve_selection(db, sport_name: str, sport_id: int | None,
                      variant_slug: str | None, participant_kind: str,
                      kind_explicit: bool = False):
    """Resolve a parent sport and one compatible variant.

    The variant drives `participant_kind`; an explicit incompatible value is a
    validation error instead of a silent rewrite.
    """
    sport_row = db.execute('SELECT * FROM sport_configs WHERE name=?',
                           (sport_name,)).fetchone()
    if sport_row is None:
        raise HTTPException(422, 'Sport non supportato')
    if sport_id is not None and sport_id != sport_row['id']:
        raise HTTPException(422, 'Sport e sport_id non corrispondono')

    sport = sport_rules.get_sport_by_id(db, sport_row['id'])
    if sport is None or not sport.variants:
        raise HTTPException(422, 'Questo sport non ha varianti configurate')

    variant = None
    if variant_slug:
        variant = sport_rules.get_variant_by_slug(db, variant_slug)
        if variant is None or variant.sport_id != sport.id:
            raise HTTPException(422, 'Variante non valida per questo sport')
        if kind_explicit and participant_kind != variant.participant_kind:
            raise HTTPException(422, 'La variante non è compatibile con il tipo di partecipanti')
        participant_kind = variant.participant_kind
    else:
        matching = [v for v in sport.variants
                    if v.participant_kind == participant_kind]
        if kind_explicit and not matching:
            raise HTTPException(422, 'Nessuna variante disponibile per questo tipo di partecipanti')
        variant = (sorted(matching, key=lambda v: (v.sort_order, v.id))[0]
                   if matching else sport.default_variant())
        if variant is None:
            raise HTTPException(422, 'Nessuna variante disponibile per questo sport')
        participant_kind = variant.participant_kind

    return dict(sport_row), variant, participant_kind


def _variant_values(variant) -> dict:
    """Database values and snapshot for a selected variant."""
    return {
        'variant_id': variant.id,
        'variant': variant.slug,
        'participant_kind': variant.participant_kind,
        'rules_snapshot': json.dumps(variant.rules, ensure_ascii=False),
        'regulation_snapshot': variant.regulation,
        'scoring_system': 'sets' if variant.supports_sets else 'points',
    }


def _apply_variant_defaults(values: dict, fields_set: set[str], variant) -> None:
    values.update(_variant_values(variant))
    standings = variant.standings
    if 'win_points' not in fields_set:
        values['win_points'] = int(standings.get('win', 3) or 0)
    if 'draw_points' not in fields_set:
        values['draw_points'] = int(standings.get('draw', 1) or 0)
    if 'loss_points' not in fields_set:
        values['loss_points'] = int(standings.get('loss', 0) or 0)
    if 'tie_breaker' not in fields_set:
        values['tie_breaker'] = variant.default_tie_breaker


def create(db, data: TournamentInput, demo_key=None):
    values = data.model_dump(exclude={'team_names'})
    fields_set = set(data.model_fields_set)
    sport_name = values.pop('sport')
    requested_variant = values.pop('variant', None)
    sport_id = values.get('sport_id')
    sport_row, variant, kind = resolve_selection(
        db, sport_name, sport_id, requested_variant,
        values.get('participant_kind', 'team'),
        'participant_kind' in fields_set,
    )
    values['sport'] = sport_row['name']
    values['sport_id'] = sport_row['id']
    values['participant_kind'] = kind
    _apply_variant_defaults(values, fields_set, variant)
    values.update(public_token=secrets.token_urlsafe(18), demo_key=demo_key)
    cols = ','.join(values)
    tid = db.execute(f'INSERT INTO tournaments({cols}) VALUES ({",".join("?" for _ in values)})',
                     list(values.values())).lastrowid
    db.executemany('INSERT INTO teams(tournament_id,name) VALUES (?,?)',
                   [(tid, n) for n in data.team_names])
    audit(db, tid, 'created', {'name': data.name, 'variant': variant.slug})
    return tid


def update_tournament(db, tid, data: TournamentUpdate):
    tournament = active(db, tid)
    values = data.model_dump(exclude_unset=True)
    fields_set = set(data.model_fields_set)
    if games(db, tid) and STRUCTURAL_FIELDS & values.keys():
        raise HTTPException(409, 'Formato, sport e regole non sono modificabili dopo la generazione degli incontri')

    sport_changed = 'sport' in values or 'sport_id' in values or 'variant' in values
    kind_changed = 'participant_kind' in values
    if sport_changed or kind_changed:
        sport_name = values.get('sport', tournament['sport'])
        sport_id = (values.get('sport_id') if 'sport' in values
                    else values.get('sport_id', tournament['sport_id']))
        requested_variant = values.pop('variant', None)
        if not sport_changed and not requested_variant:
            requested_variant = tournament['variant']
        kind = values.get('participant_kind', tournament['participant_kind'])
        kind_explicit = 'participant_kind' in fields_set
        sport_row, variant, kind = resolve_selection(
            db, sport_name, sport_id, requested_variant, kind, kind_explicit)
        values['sport'] = sport_row['name']
        values['sport_id'] = sport_row['id']
        # Keep explicit point overrides, otherwise re-apply variant defaults.
        defaults = dict(values)
        defaults_fields = set(fields_set)
        _apply_variant_defaults(defaults, defaults_fields, variant)
        for key in ('variant_id', 'variant', 'participant_kind', 'rules_snapshot',
                    'regulation_snapshot', 'scoring_system'):
            values[key] = defaults[key]
        for key in ('win_points', 'draw_points', 'loss_points', 'tie_breaker'):
            if key in fields_set:
                values[key] = getattr(data, key)
            else:
                values[key] = defaults[key]
    else:
        values.pop('variant', None)

    if values.get('format', tournament['format']) == 'knockout' and values.get('legs', tournament['legs']) != 1:
        raise HTTPException(422, 'La demo knockout prevede una sola gara per incontro')
    if not values:
        return {'ok': True, 'changed': 0}
    assignments = ','.join(f'{column}=?' for column in values)
    db.execute(f"UPDATE tournaments SET {assignments},updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
               [*values.values(), tid])
    audit(db, tid, 'updated', {'fields': sorted(values)})
    return {'ok': True, 'changed': len(values)}


def set_archived(db, tid, archived: bool):
    required(db, tid)
    if archived:
        db.execute("UPDATE tournaments SET archived_at=strftime('%Y-%m-%dT%H:%M:%fZ','now'),"
                   "updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?", (tid,))
    else:
        db.execute("UPDATE tournaments SET archived_at=NULL,"
                   "updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?", (tid,))
    audit(db, tid, 'archived' if archived else 'restored', {})
    return {'ok': True, 'archived': archived}


def teams(db, tid):
    return rows(db, 'SELECT * FROM teams WHERE tournament_id=? ORDER BY id', (tid,))


def players(db, tid, team_id):
    team = db.execute('SELECT id FROM teams WHERE id=? AND tournament_id=?',
                      (team_id, tid)).fetchone()
    if team is None:
        raise HTTPException(404, 'Partecipante non trovato')
    return rows(db, 'SELECT id,name,shirt_number FROM team_players WHERE team_id=? '
                     'ORDER BY id', (team_id,))


def add_player(db, tid, team_id, data: PlayerInput):
    tournament = active(db, tid)
    if tournament['participant_kind'] != 'team':
        raise HTTPException(422, 'Le rose sono disponibili solo per i tornei a squadre')
    players(db, tid, team_id)
    variant = _variant_for_tournament(db, tournament)
    maximum = variant.max_roster if variant else 30
    if db.execute('SELECT count(*) FROM team_players WHERE team_id=?',
                  (team_id,)).fetchone()[0] >= maximum:
        raise HTTPException(422, f'La rosa può contenere al massimo {maximum} giocatori')
    if db.execute('SELECT 1 FROM team_players WHERE team_id=? AND name=? COLLATE NOCASE',
                  (team_id, data.name)).fetchone():
        raise HTTPException(409, 'Questo giocatore è già in rosa')
    cur = db.execute('INSERT INTO team_players(team_id,name,shirt_number) VALUES (?,?,?)',
                     (team_id, data.name, data.shirt_number))
    audit(db, tid, 'player_added', {'team_id': team_id, 'name': data.name})
    return {'id': cur.lastrowid}


def remove_player(db, tid, team_id, player_id):
    active(db, tid)
    cur = db.execute('DELETE FROM team_players WHERE id=? AND team_id=?',
                     (player_id, team_id))
    if not cur.rowcount:
        raise HTTPException(404, 'Giocatore non trovato')
    audit(db, tid, 'player_removed', {'team_id': team_id, 'player_id': player_id})
    return {'ok': True}


def games(db, tid):
    return rows(db, 'SELECT m.*,s.kind FROM matches m JOIN stages s ON s.id=m.stage_id '
                    'WHERE m.tournament_id=? ORDER BY s.ordinal,m.round_no,m.position,m.id',
                (tid,))


def _sets_by_match(db, tid):
    result: dict[int, list[dict]] = {}
    for row in rows(db,
                    'SELECT ms.match_id,ms.set_no,ms.home_points,ms.away_points '
                    'FROM match_sets ms JOIN matches m ON m.id=ms.match_id '
                    'WHERE m.tournament_id=? ORDER BY ms.match_id,ms.set_no', (tid,)):
        result.setdefault(row['match_id'], []).append(
            {'set': row['set_no'], 'home': row['home_points'],
             'away': row['away_points']})
    return result


def table(db, t, group_id=None):
    roster = teams(db, t['id'])
    fixtures = [m for m in games(db, t['id']) if m['kind'] == 'round_robin']
    if group_id is not None:
        roster = [p for p in roster if p['group_id'] == group_id]
        fixtures = [m for m in fixtures if m['group_id'] == group_id]
    return build_standings(roster, fixtures, t['win_points'], t['draw_points'],
                           t['loss_points'], t['tie_breaker'], _rules(t))


def match_status(m):
    return ('bye' if m['is_bye'] else
            ('completed' if m['home_score'] is not None else
             ('ready' if m['home_team_id'] and m['away_team_id'] else 'waiting')))


def detail(db, tid, public=False):
    t = required(db, tid)
    fixtures = games(db, tid)
    roster = teams(db, tid)
    sets = _sets_by_match(db, tid)
    counts = {row['team_id']: row['total'] for row in rows(
        db, 'SELECT team_id,count(*) AS total FROM team_players '
            'WHERE team_id IN (SELECT id FROM teams WHERE tournament_id=?) '
            'GROUP BY team_id', (tid,))}
    for team in roster:
        team['player_count'] = counts.get(team['id'], 0)
    groups = rows(db, 'SELECT g.* FROM groups g JOIN stages s ON s.id=g.stage_id '
                      'WHERE s.tournament_id=? ORDER BY g.id', (tid,))
    for g in groups:
        g['standings'] = table(db, t, g['id'])
    for m in fixtures:
        m['status'] = match_status(m)
        m['sets'] = sets.get(m['id'], [])
    knockout = [m for m in fixtures if m['kind'] == 'knockout']
    champion = knockout[-1]['winner_team_id'] if knockout else None
    playable = [m for m in fixtures if not m['is_bye']]
    completed = sum(m['home_score'] is not None for m in playable)
    status = 'draft' if not fixtures else ('completed' if (champion or
             (t['format'] == 'round_robin' and completed == len(playable))) else 'active')
    sport = sport_rules.get_sport_by_id(db, t['sport_id']) if t['sport_id'] else None
    variant = _variant_for_tournament(db, t)
    rules = _rules(t) or (variant.rules if variant else {})
    regulation = t.get('regulation_snapshot') or (variant.regulation if variant else '')
    result = dict(tournament=t, teams=roster, matches=fixtures, groups=groups,
                  stages=rows(db, 'SELECT * FROM stages WHERE tournament_id=? ORDER BY ordinal', (tid,)),
                  standings=table(db, t) if t['format'] == 'round_robin' else [],
                  champion_team_id=champion, status=status,
                  progress=dict(completed=completed, total=len(playable)),
                  sport_config=sport_rules.summary(sport) if sport else None,
                  variant_config=sport_rules.variant_detail(variant) if variant else None,
                  rules=rules, regulation=regulation,
                  legacy_sport=bool(t['sport'] and (t['sport_id'] is None or variant is None)),
                  public=public)
    if public:
        result['tournament'] = {k: v for k, v in t.items()
                                if k not in ('public_token', 'demo_key')}
    else:
        result['audit'] = rows(db, 'SELECT id,action,created_at FROM audit_logs '
                                    'WHERE tournament_id=? ORDER BY id DESC LIMIT 30', (tid,))
    return result


def team_detail(db, tid, team_id):
    """Single-participant view: group, standing position, fixtures and results."""
    t = required(db, tid)
    row = db.execute('SELECT * FROM teams WHERE id=? AND tournament_id=?', (team_id, tid)).fetchone()
    if row is None:
        raise HTTPException(404, 'Partecipante non trovato')
    team = dict(row)
    group = db.execute('SELECT name FROM groups WHERE id=?', (team['group_id'],)).fetchone() \
        if team['group_id'] else None
    team['group_name'] = group['name'] if group else None

    roster = {p['id']: p['name'] for p in teams(db, tid)}
    fixtures = []
    sets = _sets_by_match(db, tid)
    for match in games(db, tid):
        if team_id not in (match['home_team_id'], match['away_team_id']):
            continue
        match['status'] = match_status(match)
        match['sets'] = sets.get(match['id'], [])
        match['home_name'] = roster.get(match['home_team_id'])
        match['away_name'] = roster.get(match['away_team_id'])
        match['opponent_name'] = roster.get(
            match['away_team_id'] if match['home_team_id'] == team_id else match['home_team_id'])
        fixtures.append(match)

    standing_rows = []
    if t['format'] == 'groups' and team['group_id']:
        standing_rows = table(db, t, team['group_id'])
    elif t['format'] == 'round_robin':
        standing_rows = table(db, t)
    standing = next((r for r in standing_rows if r['team_id'] == team_id), None)
    position = standing_rows.index(standing) + 1 if standing else None
    public_tournament = {k: t[k] for k in (
        'id', 'name', 'sport', 'variant', 'format', 'participant_kind',
        'win_points', 'draw_points', 'loss_points', 'qualifiers', 'tie_breaker')}
    variant = _variant_for_tournament(db, t)
    return {'team': team, 'standing': standing, 'position': position,
            'matches': fixtures, 'tournament': public_tournament,
            'players': players(db, tid, team_id) if t['participant_kind'] == 'team' else [],
            'max_roster': variant.max_roster if variant else 30,
            'players_on_field': variant.players_on_field if variant else 1,
            'min_lineup': variant.min_lineup if variant else 1,
            'variant_name': variant.name if variant else None,
            'participant_kind': t['participant_kind']}


def insert_bracket(db, tid, sid, ids, seed=None, duration=20):
    mapping = {}
    for i, match in enumerate(knockout_plan(ids, seed)):
        m = dict(match)
        m['duration'] = duration
        for key in ('source_home', 'source_away'):
            if m[key] is not None:
                m[key] = mapping[m[key]]
        cols = ','.join(m)
        mapping[i] = db.execute(f'INSERT INTO matches(tournament_id,stage_id,{cols}) '
                               f'VALUES (?,?,{",".join("?" for _ in m)})',
                               [tid, sid, *m.values()]).lastrowid
    progress_bracket(db, tid)


def progress_bracket(db, tid):
    """Tree is topologically ordered by round; propagate winners exactly once."""
    known = {}
    for match in games(db, tid):
        if match['kind'] != 'knockout':
            continue
        m = dict(match)
        for side in ('home', 'away'):
            source = m['source_'+side]
            if source is not None:
                m[side+'_team_id'] = known[source]['winner_team_id']
        if m['is_bye']:
            m['winner_team_id'] = m['home_team_id'] or m['away_team_id']
        if (m['home_team_id'], m['away_team_id'], m['winner_team_id']) != (
                match['home_team_id'], match['away_team_id'], match['winner_team_id']):
            db.execute('UPDATE matches SET home_team_id=?,away_team_id=?,winner_team_id=?,version=version+1 WHERE id=?',
                       (m['home_team_id'], m['away_team_id'], m['winner_team_id'], m['id']))
        known[m['id']] = m


def generate(db, tid):
    t = active(db, tid)
    if games(db, tid):
        raise HTTPException(409, 'Incontri già generati: il comando non crea duplicati')
    ids = [p['id'] for p in teams(db, tid)]
    if not 2 <= len(ids) <= 32:
        raise HTTPException(422, 'Servono da 2 a 32 partecipanti')
    if t['format'] == 'groups':
        count = t['group_count']
        if len(ids) % count or len(ids)//count < max(2, t['qualifiers']):
            raise HTTPException(422, 'Per questa demo servono gironi uguali con almeno 2 squadre e abbastanza qualificate')
    variant = _variant_for_tournament(db, t)
    duration = variant.match_duration if variant else 20
    kind = 'knockout' if t['format'] == 'knockout' else 'round_robin'
    sid = db.execute('INSERT INTO stages(tournament_id,ordinal,kind) VALUES (?,0,?)', (tid,kind)).lastrowid
    if kind == 'knockout':
        insert_bracket(db, tid, sid, ids, t['random_seed'], duration)
    else:
        pools = [(None, ids)]
        if t['format'] == 'groups':
            pools = []
            for i in range(t['group_count']):
                gid = db.execute('INSERT INTO groups(stage_id,name) VALUES (?,?)', (sid, 'Girone '+chr(65+i))).lastrowid
                members = ids[i::t['group_count']]
                db.executemany('UPDATE teams SET group_id=? WHERE id=?', [(gid, p) for p in members])
                pools.append((gid, members))
        position = 0
        for gid, members in pools:
            for turn, home, away in round_robin(members, t['legs']):
                db.execute('INSERT INTO matches(tournament_id,stage_id,group_id,round_no,position,'
                           'home_team_id,away_team_id,duration) VALUES (?,?,?,?,?,?,?,?)',
                           (tid,sid,gid,turn,position,home,away,duration))
                position += 1
    audit(db, tid, 'generated', {'participants':len(ids)})
    return {'created':len(games(db, tid))}


def qualify(db, tid):
    t = required(db, tid)
    if t['format'] != 'groups':
        return
    fixtures = games(db, tid)
    if any(m['kind'] == 'knockout' for m in fixtures):
        return
    group_games = [m for m in fixtures if m['kind'] == 'round_robin']
    if not group_games or any(m['home_score'] is None for m in group_games):
        return
    gids = rows(db, 'SELECT DISTINCT group_id FROM teams WHERE tournament_id=? ORDER BY group_id', (tid,))
    tables = [table(db, t, g['group_id']) for g in gids]
    # Ranked tiers, then group order. Standard bracket seeding distributes groups.
    ids = [standings[rank]['team_id'] for rank in range(t['qualifiers']) for standings in tables]
    variant = _variant_for_tournament(db, t)
    sid = db.execute("INSERT INTO stages(tournament_id,ordinal,kind) VALUES (?,1,'knockout')", (tid,)).lastrowid
    insert_bracket(db, tid, sid, ids, duration=variant.match_duration if variant else 20)
    audit(db, tid, 'qualified', {'team_ids':ids})


def validate_sets(sets, rules: dict) -> list[dict]:
    """Validate a complete set-by-set score and return normalised rows."""
    if not sets:
        raise HTTPException(422, 'Inserisci almeno un set')
    sets_to_win = int(rules.get('sets_to_win') or 0)
    max_sets = int(rules.get('max_sets') or len(sets))
    points_per_set = int(rules.get('points_per_set') or 0)
    tiebreak_points = int(rules.get('tiebreak_points') or points_per_set)
    win_by_two = bool(rules.get('win_by_two', False))
    max_points = rules.get('max_points')
    if not sets_to_win or not points_per_set:
        raise HTTPException(422, 'Regole set non configurate per questa variante')
    if len(sets) > max_sets:
        raise HTTPException(422, f'La partita può avere al massimo {max_sets} set')

    wins = [0, 0]
    normalised = []
    for index, item in enumerate(sets, start=1):
        home = item['home'] if isinstance(item, dict) else item.home
        away = item['away'] if isinstance(item, dict) else item.away
        if home == away:
            raise HTTPException(422, f'Il set {index} non può finire in parità')
        winner, loser = max(home, away), min(home, away)
        target = tiebreak_points if index == max_sets else points_per_set
        if winner < target:
            raise HTTPException(422, f'Il set {index} deve arrivare almeno a {target} punti')
        if max_points is not None and winner > int(max_points):
            raise HTTPException(422, f'Il set {index} supera il limite di {max_points} punti')
        if not (max_points is not None and winner == int(max_points)):
            if win_by_two and winner - loser < 2:
                raise HTTPException(422, f'Il set {index} richiede almeno 2 punti di scarto')
        won_by = 0 if home > away else 1
        wins[won_by] += 1
        if wins[won_by] == sets_to_win and index < len(sets):
            raise HTTPException(422, 'La partita è già terminata: rimuovi i set in più')
        normalised.append({'home': home, 'away': away})
    if sets_to_win not in wins:
        raise HTTPException(422, f'Serve un vincitore con {sets_to_win} set')
    return normalised


def required_match(db, tid, mid, version):
    active(db, tid)
    m = next((m for m in games(db, tid) if m['id'] == mid), None)
    if m is None:
        raise HTTPException(404, 'Partita non trovata')
    if m['version'] != version:
        raise HTTPException(409, 'Dati cambiati: aggiorna la pagina prima di salvare')
    return m


def descendants(fixtures, mid):
    result, parents = [], {mid}
    for m in fixtures:
        if m['source_home'] in parents or m['source_away'] in parents:
            parents.add(m['id'])
            result.append(m)
    return result


def save_result(db, tid, mid, version, home=None, away=None, invalidate=False, sets=None):
    m = required_match(db, tid, mid, version)
    tournament = required(db, tid)
    rules = _rules(tournament)
    variant = _variant_for_tournament(db, tournament)
    if m['is_bye'] or not m['home_team_id'] or not m['away_team_id']:
        raise HTTPException(409, 'Incontro non giocabile: attendi gli avversari o il passaggio per BYE')

    clearing = home is None and away is None and sets is None
    if variant and variant.supports_sets:
        if clearing:
            normalised = []
        else:
            if home is not None or away is not None:
                raise HTTPException(422, 'Questa variante richiede il punteggio set per set')
            if sets is None:
                raise HTTPException(422, 'Inserisci il punteggio set per set')
            normalised = validate_sets(sets, rules)
            home = sum(1 for s in normalised if s['home'] > s['away'])
            away = len(normalised) - home
    else:
        if clearing:
            normalised = []
        else:
            if sets is not None:
                raise HTTPException(422, 'Questa variante usa un punteggio unico, non i set')
            if home is None or away is None:
                raise HTTPException(422, 'Inserisci entrambi i punteggi')
            normalised = []
            if home == away and not bool(rules.get('draw_allowed', True)):
                raise HTTPException(422, 'Questa variante non ammette pareggi')
            if m['kind'] == 'knockout' and home == away:
                raise HTTPException(422, 'Serve un vincitore: questa variante non ammette pareggi')

    if not clearing and m['kind'] == 'knockout' and home == away:
        raise HTTPException(422, 'Serve un vincitore. Inserisci un punteggio decisivo')
    winner = None if home is None or home == away else (m['home_team_id'] if home > away else m['away_team_id'])
    fixtures = games(db, tid)
    affected = []
    if m['kind'] == 'round_robin':
        affected = [g for g in fixtures if g['kind'] == 'knockout']
    elif winner != m['winner_team_id']:
        affected = descendants(fixtures, mid)
    current_sets = rows(db, 'SELECT home_points,away_points FROM match_sets WHERE match_id=? ORDER BY set_no',
                        (mid,))
    current_normalised = [{'home': s['home_points'], 'away': s['away_points']}
                          for s in current_sets]
    changed = ((home, away) != (m['home_score'], m['away_score'])
               or normalised != current_normalised)
    if changed and affected:
        if (m['kind'] == 'round_robin' or any(g['home_score'] is not None for g in affected)) and not invalidate:
            raise HTTPException(409, 'La correzione modifica le fasi successive. Conferma l’annullamento dei risultati dipendenti')
        audit(db, tid, 'invalidated', {'matches': affected})
        if m['kind'] == 'round_robin':
            # Remove dependencies before nodes; retain snapshots in the audit log.
            for g in reversed(affected):
                db.execute('DELETE FROM matches WHERE id=?', (g['id'],))
            db.execute("DELETE FROM stages WHERE tournament_id=? AND ordinal=1", (tid,))
        else:
            for g in affected:
                db.execute('UPDATE matches SET home_score=NULL,away_score=NULL,winner_team_id=NULL,'
                           'scheduled_at=NULL,location=NULL,version=version+1 WHERE id=?', (g['id'],))
                db.execute('DELETE FROM match_sets WHERE match_id=?', (g['id'],))
    if changed:
        db.execute('UPDATE matches SET home_score=?,away_score=?,winner_team_id=?,version=version+1 WHERE id=?',
                   (home,away,winner,mid))
        db.execute('DELETE FROM match_sets WHERE match_id=?', (mid,))
        if normalised:
            db.executemany('INSERT INTO match_sets(match_id,set_no,home_points,away_points) VALUES (?,?,?,?)',
                           [(mid, i, s['home'], s['away']) for i, s in enumerate(normalised, start=1)])
        audit(db, tid, 'result_cleared' if home is None else 'result_saved',
              {'match_id':mid, 'before':[m['home_score'],m['away_score']],
               'after':[home,away], 'sets':normalised})
    progress_bracket(db, tid)
    qualify(db, tid)
    state = detail(db, tid)
    return {'ok':True, 'invalidated':len(affected) if changed else 0,
            'champion_team_id':state['champion_team_id']}


def schedule(db, tid, mid, data):
    m = required_match(db, tid, mid, data.version)
    if m['is_bye']:
        raise HTTPException(422, 'Un BYE non occupa un campo')
    tournament = required(db, tid)
    variant = _variant_for_tournament(db, tournament)
    duration = data.duration or (variant.match_duration if variant else 20)
    timestamp = data.scheduled_at.astimezone(timezone.utc) if data.scheduled_at else None
    location = data.location.strip()
    fixtures = games(db, tid)
    if timestamp:
        end = timestamp + timedelta(minutes=duration)
        ids = {m['home_team_id'],m['away_team_id']} - {None}
        for other in fixtures:
            if other['id'] == mid or not other['scheduled_at']:
                continue
            start = datetime.fromisoformat(other['scheduled_at'])
            finish = start + timedelta(minutes=other['duration'])
            field_clash = location and location.casefold() == (other['location'] or '').casefold()
            team_clash = ids & {other['home_team_id'],other['away_team_id']}
            if timestamp < finish and start < end and (field_clash or team_clash):
                raise HTTPException(409, 'Orario in conflitto: campo o partecipante già impegnato')
            if other['id'] in (m['source_home'],m['source_away']) and finish > timestamp:
                raise HTTPException(409, 'La partita deve iniziare dopo gli incontri da cui dipende')
            if mid in (other['source_home'],other['source_away']) and end > start:
                raise HTTPException(409, 'La partita deve finire prima del turno successivo pianificato')
    db.execute('UPDATE matches SET scheduled_at=?,location=?,duration=?,version=version+1 WHERE id=?',
               (timestamp.isoformat() if timestamp else None,location or None,duration,mid))
    audit(db, tid, 'scheduled', {'match_id':mid, 'utc':timestamp.isoformat() if timestamp else None,
                                 'location':location, 'duration':duration})
    return {'ok':True, 'duration':duration}
