"""Command-line administration for teacher accounts.

Examples:
    python manage.py list-teachers
    python manage.py create-teacher professore@scuola.it --name "Mario Rossi"
    python manage.py reset-password professore@scuola.it
"""

import argparse
import getpass
import os
import sys
from pathlib import Path

from auth import create_teacher, list_teachers, set_password
from db import BASE, database, initialize


def main() -> None:
    parser = argparse.ArgumentParser(description='Gestione docenti Open Score')
    parser.add_argument('command',
                        choices=['create-teacher', 'reset-password', 'list-teachers'])
    parser.add_argument('email', nargs='?')
    parser.add_argument('--name', default='')
    parser.add_argument('--db',
                        default=os.environ.get('TORNEO_DB_PATH',
                                               str(BASE / 'data' / 'open_score.sqlite3')))
    args = parser.parse_args()

    path = Path(args.db)
    initialize(path)

    if args.command == 'list-teachers':
        with database(path) as db:
            for teacher in list_teachers(db):
                print(f"{teacher['id']}\t{teacher['email']}\t{teacher['display_name']}")
        return

    if not args.email:
        parser.error('email obbligatoria per questo comando')

    password = getpass.getpass('Password: ')
    confirm = getpass.getpass('Ripeti password: ')
    if password != confirm:
        sys.exit('Le password non coincidono')

    with database(path, True) as db:
        try:
            if args.command == 'create-teacher':
                create_teacher(db, args.email, password, args.name)
                print('Docente creato.')
            else:
                set_password(db, args.email, password)
                print('Password aggiornata.')
        except ValueError as exc:
            sys.exit(str(exc))


if __name__ == '__main__':
    main()
