"""Proposals never mutate official scores; reviews and advancement share one transaction."""
import json

import auth
from auth import fail, version
import services as svc
import sports
from v1_domain import audit


def match(db, tid, mid, expected=None):
    item = next((m for m in svc.games(db, tid) if m['id'] == mid), None)
    if not item:
        fail(404, 'not_found', 'Partita non trovata')
    if expected is not None:
        version(item, expected)
    return item


def score_totals(tournament, game, score):
    if not tournament['variant_id']:
        fail(409, 'rules_required', 'Assegnare un preset sportivo prima di usare il workflow V1')
    if game['is_bye'] or not game['home_team_id'] or not game['away_team_id']:
        fail(409, 'match_not_ready', 'Attendere gli avversari; un BYE non accetta risultati')
    try:
        return sports.validate_score(tournament['variant_id'], json.loads(tournament['rules_json']),
                                     score, game['kind'] == 'knockout')
    except ValueError as exc:
        fail(422, 'invalid_score', str(exc))


def proposal_dto(db, item):
    result = dict(item)
    result['score'] = json.loads(result.pop('score_json'))
    review = db.execute('SELECT * FROM result_reviews WHERE proposal_id=? ORDER BY id DESC LIMIT 1', (item['id'],)).fetchone()
    result['review'] = dict(review) if review else None
    if result['review']:
        result['review'].pop('score_json', None)
    current = db.execute('SELECT version FROM matches WHERE id=?', (item['match_id'],)).fetchone()
    result['stale'] = not current or current['version'] != item['match_version']
    return result


def propose(db, user, tid, mid, data):
    tournament = auth.access(db, user, tid)
    if user['role'] != 'student':
        fail(403, 'student_required', 'Le proposte sono riservate agli studenti partecipanti')
    game = match(db, tid, mid, data.match_version)
    member = db.execute('SELECT team_id FROM students WHERE tournament_id=? AND user_id=?', (tid, user['id'])).fetchone()
    if not member or member['team_id'] not in (game['home_team_id'], game['away_team_id']) or member['team_id'] is None:
        fail(403, 'match_participation_required', 'Puoi proporre risultati soltanto per la tua squadra')
    if data.score.type == 'forfeit':
        fail(403, 'teacher_required', 'Il risultato a tavolino è una decisione del professore')
    score_totals(tournament, game, data.score)
    ident = db.execute('INSERT INTO result_proposals(tournament_id,match_id,original_match_id,submitted_by,score_json,match_version) VALUES (?,?,?,?,?,?)',
             (tid, mid, mid, user['id'], json.dumps(data.score.model_dump()), data.match_version)).lastrowid
    audit(db, user, tid, 'result_proposed', {'match_id': mid, 'proposal_id': ident})
    return proposal_dto(db, db.execute('SELECT * FROM result_proposals WHERE id=?', (ident,)).fetchone())


def official(db, tid, mid):
    game = match(db, tid, mid)
    record = db.execute('SELECT * FROM official_results WHERE match_id=?', (mid,)).fetchone()
    result = None
    if record:
        result = dict(record)
        result['score'] = json.loads(result.pop('score_json'))
        result['winner_team_id'] = game['winner_team_id']
        result['version'] = game['version']
    elif game['home_score'] is not None:
        # Imported legacy result: preserve it, without fabricating an approver.
        result = dict(id=None, match_id=mid, score={'type': 'points', 'home': game['home_score'], 'away': game['away_score']},
                      winner_team_id=game['winner_team_id'], version=game['version'], approved_by=None,
                      approved_at=None, source_proposal_id=None, provenance='legacy')
    return dict(official_result=result, match_version=game['version'])


def save(db, user, tid, mid, expected, score, invalidate, reason, proposal_id=None):
    tournament = auth.access(db, user, tid, True)
    game = match(db, tid, mid, expected)
    before = {m['id']: m['version'] for m in svc.games(db, tid)}
    if score is None:
        outcome = svc.save_result(db, tid, mid, expected, invalidate=invalidate)
        db.execute('DELETE FROM official_results WHERE match_id=?', (mid,))
    else:
        home, away = score_totals(tournament, game, score)
        encoded = json.dumps(score.model_dump())
        outcome = svc.save_result(db, tid, mid, expected, home, away, invalidate, score.model_dump())
        # Same score reviewed a second time still changes the official revision.
        current = match(db, tid, mid)
        if current['version'] == expected:
            db.execute('UPDATE matches SET version=version+1 WHERE id=?', (mid,))
        db.execute('INSERT INTO official_results(match_id,score_json,approved_by,approved_at,source_proposal_id) VALUES (?,?,?,?,?) '
                   'ON CONFLICT(match_id) DO UPDATE SET score_json=excluded.score_json,approved_by=excluded.approved_by,'
                   'approved_at=excluded.approved_at,source_proposal_id=excluded.source_proposal_id',
                   (mid, encoded, user['id'], auth.now().isoformat(), proposal_id))
    db.execute('INSERT INTO result_reviews(tournament_id,match_id,proposal_id,reviewed_by,decision,reason,score_json) VALUES (?,?,?,?,?,?,?)',
               (tid, mid, proposal_id, user['id'], 'clear' if score is None else 'official', reason,
                json.dumps(score.model_dump()) if score else None))
    audit(db, user, tid, 'official_result_cleared' if score is None else 'official_result_saved',
          {'match_id': mid, 'proposal_id': proposal_id, 'reason': reason})
    after = {m['id']: m['version'] for m in svc.games(db, tid)}
    from v1_resources import validate_tournament_schedule
    validate_tournament_schedule(db, tid)
    return dict(**official(db, tid, mid), invalidated_match_ids=[ident for ident, ver in before.items()
                if ident != mid and after.get(ident) != ver], invalidated=outcome['invalidated'])


def review(db, user, tid, mid, pid, data):
    auth.access(db, user, tid, True)
    game = match(db, tid, mid, data.match_version)
    item = db.execute('SELECT * FROM result_proposals WHERE id=? AND tournament_id=? AND match_id=?', (pid, tid, mid)).fetchone()
    if not item:
        fail(404, 'not_found', 'Proposta non trovata')
    version(item, data.proposal_version)
    if item['status'] != 'pending':
        fail(409, 'already_reviewed', 'Proposta già revisionata')
    if data.decision != 'reject' and item['match_version'] != game['version']:
        fail(409, 'stale_proposal', 'La partita è cambiata: respingere la proposta e richiederne una nuova')
    if data.decision == 'reject':
        db.execute('INSERT INTO result_reviews(tournament_id,match_id,proposal_id,reviewed_by,decision,reason) VALUES (?,?,?,?,?,?)',
                   (tid, mid, pid, user['id'], 'reject', data.reason))
        outcome = official(db, tid, mid)
        outcome['invalidated_match_ids'] = []
        audit(db, user, tid, 'proposal_rejected', {'proposal_id': pid, 'reason': data.reason})
    else:
        from pydantic import TypeAdapter
        value = data.score or TypeAdapter(sports.Score).validate_python(json.loads(item['score_json']))
        outcome = save(db, user, tid, mid, data.match_version, value, data.invalidate, data.reason, pid)
        db.execute('UPDATE result_reviews SET decision=? WHERE id=(SELECT max(id) FROM result_reviews WHERE proposal_id=?)',
                   (data.decision, pid))
    db.execute('UPDATE result_proposals SET status=?,version=version+1 WHERE id=?',
               ('rejected' if data.decision == 'reject' else 'approved', pid))
    return dict(proposal=proposal_dto(db, db.execute('SELECT * FROM result_proposals WHERE id=?', (pid,)).fetchone()), **outcome)
