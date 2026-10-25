"""Idempotent local examples. External IDs are provenance, never local keys."""
import json

from db import BASE
from schemas import TournamentInput
from services import create, games, generate, save_result


def load_examples(db, teacher_id=None):
    result = []
    if teacher_id is not None:
        db.execute('UPDATE tournaments SET teacher_id=? '
                   'WHERE demo_key IS NOT NULL AND teacher_id IS NULL', (teacher_id,))
    specs = [
        ('reference', 'Knockout Bracket of Football', 'knockout', ['Team #1','Team #2'],
         'Il caso di partenza: due squadre, una finale. Dati del campione JSON fornito da Leonardo.'),
        ('school-cup', 'Coppa della palestra', 'knockout',
         ['Falchi','Leoni','Tigri','Lupi','Aquile','Pantere','Orsi','Delfini'],
         'Otto squadre, un obiettivo. Prova il tabellone e accompagna una squadra fino alla finale.'),
        ('school-league', 'Campionato d’istituto', 'round_robin',
         ['3A · Falchi','3B · Leoni','3C · Tigri','4A · Lupi','4B · Aquile','4C · Pantere'],
         'Un girone per giocare tutti contro tutti. Segui risultati e classifica giornata dopo giornata.'),
        ('sport-day', 'Giornata dello sport', 'groups', [f'Classe {i}{s}' for i in range(1,5) for s in 'ABCD'],
         'Sedici squadre, quattro gironi. Le prime due di ogni gruppo passano ai quarti di finale.')
    ]
    for key,name,fmt,names,description in specs:
        existing = db.execute('SELECT id FROM tournaments WHERE demo_key=?', (key,)).fetchone()
        if existing:
            result.append(existing[0])
            continue
        tid = create(db,TournamentInput(name=name,format=fmt,team_names=names,description=description,
                                       group_count=4 if fmt=='groups' else 2), key, teacher_id)
        generate(db,tid)
        if key == 'reference':
            sample = json.loads((BASE/'fixtures/score7_sample.json').read_text(encoding='utf-8'))
            match = sample['participant']['matches'][0]
            db.execute('UPDATE stages SET source_id=? WHERE tournament_id=?', (sample['stages'][0]['id'],tid))
            db.execute('UPDATE matches SET source_id=? WHERE tournament_id=?', (match['matchId'],tid))
            for side in ('homeParticipant','awayParticipant'):
                p = match[side]
                db.execute('UPDATE teams SET source_id=? WHERE tournament_id=? AND name=?', (p['id'],tid,p['name']))
        if key in ('school-cup','school-league'):
            count = 2 if key == 'school-cup' else 6
            for i,m in enumerate(games(db,tid)[:count]):
                save_result(db,tid,m['id'],m['version'],(i%3)+1,i%2)
        result.append(tid)
    return {'ids':result}
