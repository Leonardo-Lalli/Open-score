#!/usr/bin/env python3
"""Render the static site for GitHub Pages.

`website/` keeps two deployment placeholders so the same files work on a
project site (`/Open-score/`) and on a custom domain (`/`):

- `__SITE_BASE__`  -> the base path used by `404.html`
- `__SITE_URL__`   -> the canonical/Open Graph URL

Values live in `website/site.config.json`. This script writes the publishable
copy to `_site/`; it uses only the standard library.
"""
import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'website'
CONFIG = SITE / 'site.config.json'
PLACEHOLDERS = ('__SITE_BASE__', '__SITE_URL__')
DOMAIN = re.compile(
    r'^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$')


def load_config() -> dict:
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    base = config.get('base')
    url = config.get('url')
    domain = config.get('custom_domain')
    if not isinstance(base, str) or not (base.startswith('/') and base.endswith('/')):
        raise SystemExit('site.config.json: "base" deve iniziare e finire con "/"')
    if not isinstance(url, str) or not url.startswith('https://') or not url.endswith('/'):
        raise SystemExit('site.config.json: "url" deve essere https e finire con "/"')
    if domain:
        if not isinstance(domain, str) or not DOMAIN.match(domain.lower()):
            raise SystemExit('site.config.json: "custom_domain" non è un dominio valido')
        if base != '/':
            raise SystemExit('Con un dominio personalizzato "base" deve essere "/"')
        if not url.lower().startswith(f'https://{domain.lower()}/'):
            raise SystemExit('"url" deve iniziare con il dominio personalizzato')
    else:
        if base == '/':
            raise SystemExit('Senza dominio personalizzato "base" non può essere "/"')
        if not url.endswith(base):
            raise SystemExit('"url" deve terminare con "base"')
    return config


def render(out: Path) -> None:
    config = load_config()
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(SITE, out, ignore=shutil.ignore_patterns(
        'site.config.json', '*.md'))
    replacements = {'__SITE_BASE__': config['base'], '__SITE_URL__': config['url']}
    for path in out.rglob('*.html'):
        text = path.read_text(encoding='utf-8')
        for key, value in replacements.items():
            text = text.replace(key, value)
        if any(marker in text for marker in PLACEHOLDERS):
            raise SystemExit(f'placeholder non risolto in {path}')
        path.write_text(text, encoding='utf-8', newline='\n')
    print(f'Sito generato in {out} (base {config["base"]}, url {config["url"]})')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / '_site',
                        help='cartella di output (predefinita: _site)')
    args = parser.parse_args()
    render(args.out.resolve())


if __name__ == '__main__':
    main()
