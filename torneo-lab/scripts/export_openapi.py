"""Export the live FastAPI schema without opening the application's database."""
import argparse
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / 'docs/contracts/openapi.yaml'


def render(schema):
    # JSON is a YAML 1.2 subset. No extra serializer or parallel specification.
    return json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + '\n'


def generate():
    # app.py creates its default app on import. Redirect that initialization too.
    previous = os.environ.get('TORNEO_DB_PATH')
    previous_mode = os.environ.get('TORNEO_MODE')
    with TemporaryDirectory(prefix='open-score-contract-') as folder:
        os.environ['TORNEO_DB_PATH'] = str(Path(folder) / 'schema.sqlite3')
        os.environ['TORNEO_MODE'] = 'demo'
        sys.path.insert(0, str(ROOT / 'torneo-lab'))
        try:
            from app import app
            return render(app.openapi())
        finally:
            sys.path.pop(0)
            if previous is None:
                os.environ.pop('TORNEO_DB_PATH', None)
            else:
                os.environ['TORNEO_DB_PATH'] = previous
            if previous_mode is None:
                os.environ.pop('TORNEO_MODE', None)
            else:
                os.environ['TORNEO_MODE'] = previous_mode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail on schema drift; do not write files')
    args = parser.parse_args()
    content = generate()
    if args.check:
        if not SNAPSHOT.exists() or SNAPSHOT.read_text(encoding='utf-8') != content:
            print('OpenAPI non sincronizzato: eseguire python scripts/export_openapi.py', file=sys.stderr)
            return 1
        print('OpenAPI sincronizzato con FastAPI')
        return 0
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(content, encoding='utf-8', newline='\n')
    print(SNAPSHOT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
