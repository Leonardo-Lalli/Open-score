"""Local administration. Never imports app.py or starts the HTTP server."""
import argparse
from contextlib import closing
import getpass
import json
import os
from pathlib import Path
import sqlite3

import auth
from db import BASE, SCHEMA_VERSION, database, initialize
import services as svc
import sports


def verified_copy(source: Path, output: Path):
    source, output = source.resolve(), output.resolve()
    if not source.is_file():
        raise ValueError('Database sorgente inesistente')
    if output.exists() or source == output:
        raise ValueError('La destinazione deve essere un nuovo file; nessuna sovrascrittura')
    output.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro', uri=True)) as original:
        if original.execute('PRAGMA quick_check').fetchone()[0] != 'ok' or original.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('Integrità della sorgente non valida')
        # Exclusive creation prevents accidentally overwriting a concurrent file.
        with output.open('xb'):
            pass
        with closing(sqlite3.connect(output)) as target:
            original.backup(target)
            if target.execute('PRAGMA quick_check').fetchone()[0] != 'ok' or target.execute('PRAGMA foreign_key_check').fetchone():
                raise ValueError('Copia non valida; non usarla per il ripristino')
    return output


def claim(db, tid, uid, variant_id):
    user = db.execute("SELECT * FROM users WHERE id=? AND role='teacher'", (uid,)).fetchone()
    if not user:
        raise ValueError('Il proprietario deve essere un professore esistente')
    tournament = svc.required(db, tid)
    if tournament['owner_id'] is not None:
        raise ValueError('Torneo già assegnato; nessuna riassegnazione implicita')
    config = sports.configuration(variant_id)
    if sports.VARIANTS[variant_id][2] != 'points' and svc.games(db, tid):
        raise ValueError('Non si possono reinterpretare incontri legacy numerici come set')
    if sports.VARIANTS[variant_id][2] == 'points':
        config.update(win_points=tournament['win_points'], draw_points=tournament['draw_points'], loss_points=tournament['loss_points'])
    for game in svc.games(db, tid):
        if game['home_score'] is not None:
            score = dict(type='points', home=game['home_score'], away=game['away_score'])
            sports.validate_score(variant_id, config, score, game['kind'] == 'knockout')
            db.execute('UPDATE matches SET score_json=? WHERE id=?', (json.dumps(score), game['id']))
    import secrets
    db.execute('UPDATE tournaments SET owner_id=?,organization_id=?,variant_id=?,rules_json=?,public_slug=?,version=version+1 WHERE id=?',
               (uid, user['organization_id'], variant_id, json.dumps(config), secrets.token_urlsafe(12), tid))
    db.execute("INSERT INTO audit_logs(tournament_id,actor_id,action,payload) VALUES (?,?,'legacy_claimed',?)",
               (tid, uid, json.dumps({'variant_id': variant_id, 'provenance': 'local-admin'})))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=Path(os.environ.get('TORNEO_DB_PATH', BASE/'data/open_score.sqlite3')))
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('migrate')
    teacher = commands.add_parser('create-teacher')
    teacher.add_argument('--email', required=True)
    teacher.add_argument('--display-name', required=True)
    organization = teacher.add_mutually_exclusive_group(required=True)
    organization.add_argument('--organization')
    organization.add_argument('--organization-id', type=int)
    assign = commands.add_parser('claim')
    assign.add_argument('--tournament', required=True, type=int)
    assign.add_argument('--teacher', required=True, type=int)
    assign.add_argument('--variant-id', required=True, choices=list(sports.VARIANTS))
    collaborator = commands.add_parser('add-collaborator')
    collaborator.add_argument('--tournament', required=True, type=int)
    collaborator.add_argument('--teacher', required=True, type=int)
    for name in ('backup', 'restore'):
        copy = commands.add_parser(name)
        copy.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command in ('backup', 'restore'):
            print(verified_copy(args.db, args.output))
            return 0
        initialize(args.db)
        if args.command == 'migrate':
            print(f'Schema {SCHEMA_VERSION}: {args.db.resolve()}')
            return 0
        with database(args.db, True) as db:
            if args.command == 'create-teacher':
                password = getpass.getpass('Password (12–128 caratteri): ')
                if password != getpass.getpass('Conferma password: '):
                    raise ValueError('Le password non coincidono')
                uid = auth.create_teacher(db, args.email, password, args.display_name, args.organization, args.organization_id)
                print(f'Professore creato: id={uid}')
            elif args.command == 'claim':
                claim(db, args.tournament, args.teacher, args.variant_id)
                print('Assegnazione completata; risultati e ID conservati')
            else:
                t = svc.required(db, args.tournament)
                user = db.execute("SELECT * FROM users WHERE id=? AND role='teacher'", (args.teacher,)).fetchone()
                if not user or not t['owner_id'] or user['organization_id'] != t['organization_id']:
                    raise ValueError('Serve un professore dello stesso contesto; nessuna autorizzazione implicita')
                db.execute('INSERT OR IGNORE INTO tournament_collaborators VALUES (?,?)', (args.tournament, args.teacher))
                db.execute("INSERT INTO audit_logs(tournament_id,actor_id,action,payload) VALUES (?,?,'collaborator_added',?)",
                           (args.tournament, t['owner_id'], json.dumps({'user_id': args.teacher, 'provenance': 'local-admin'})))
                print('Collaboratore associato')
    except (ValueError, sqlite3.Error) as exc:
        parser.exit(1, f'Operazione non completata: {exc}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
