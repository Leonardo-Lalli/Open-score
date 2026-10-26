"""Static checks for the GitHub Pages presentation site.

The site is a standalone static directory: these tests guard structure, honest
claims, local assets, the Pages workflow and basic CSS/JS sanity.
"""
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'website'
INDEX = SITE / 'index.html'
HTML = INDEX.read_text(encoding='utf-8')
CSS = (SITE / 'styles.css').read_text(encoding='utf-8')

SECTION_IDS = ('problema', 'soluzione', 'funzionalita', 'come-funziona',
               'per-chi', 'screenshot', 'roadmap', 'team')


def test_site_is_a_standalone_page():
    assert INDEX.exists()
    assert (SITE / 'styles.css').exists()
    assert (SITE / 'script.js').exists()
    assert (SITE / '404.html').exists()
    assert (SITE / '.nojekyll').exists()
    assert (SITE / 'assets' / 'mark.svg').exists()
    assert '<html lang="it">' in HTML
    assert '<meta charset="utf-8"' in HTML
    assert 'name="viewport"' in HTML
    assert '<title>Open Score' in HTML
    assert 'name="description"' in HTML
    assert 'property="og:title"' in HTML
    assert 'rel="icon"' in HTML
    assert 'href="styles.css"' in HTML
    assert 'src="script.js"' in HTML


def test_site_has_all_required_sections():
    for section in SECTION_IDS:
        assert f'id="{section}"' in HTML, f'sezione {section!r} mancante'
    assert 'data-screenshot-placeholder' in HTML
    assert HTML.count('class="screenshot-card"') == 3
    assert 'Il tuo campo' in HTML
    assert 'Scopri le funzionalità' in HTML


def test_site_does_not_promise_what_does_not_exist():
    # No demo button/link: the public demo does not exist yet.
    assert not re.search(r'href="[^"]*demo[^"]*"', HTML, re.I)
    assert not re.search(r'>\s*Demo\s*<', HTML)
    assert 'La demo pubblica non è ancora disponibile' in HTML
    # The project license is not assigned yet.
    assert 'Licenza da definire' in HTML
    for claim in ('Licenza MIT', 'MIT License', 'Apache License',
                  'GNU General Public License'):
        assert claim not in HTML
    # Features are grouped by real status.
    assert 'Disponibili' in HTML
    assert 'In sviluppo' in HTML
    assert 'Prospettive future' in HTML
    assert 'Score7' not in HTML


def test_site_uses_only_existing_people_and_links():
    assert 'Leonardo Lalli' in HTML
    assert 'Maximiliam Cichello' in HTML
    assert 'https://github.com/Leonardo-Lalli/Open-score' in HTML
    assert 'tree/main/docs' in HTML
    assert 'issues' in HTML
    assert 'Nessun nome reale di studente' in HTML


def test_all_local_assets_and_links_exist():
    targets = re.findall(r'(?:src|href)="([^"]+)"', HTML)
    for target in targets:
        if target.startswith(('#', 'http://', 'https://', 'mailto:', 'tel:',
                              'data:')):
            continue
        clean = target.split('#')[0].split('?')[0]
        if not clean:
            continue
        resolved = (SITE / clean).resolve()
        assert resolved.exists(), f'asset/link locale mancante: {target}'
    for url in re.findall(r'url\(["\']?([^"\')]+)["\']?\)', CSS):
        if url.startswith(('http://', 'https://', 'data:')):
            continue
        assert (SITE / url).resolve().exists(), f'font/asset CSS mancante: {url}'
    assert (SITE / 'assets' / 'fonts' / 'OFL.txt').exists()
    assert (SITE / 'assets' / 'screenshots' / 'README.md').exists()


def test_no_external_runtime_dependencies():
    assert not re.search(r'<script[^>]+src="https?://', HTML, re.I)
    assert not re.search(
        r'<link[^>]+rel="stylesheet"[^>]+href="https?://', HTML, re.I)
    assert '@import' not in CSS
    assert 'cdn.' not in HTML.lower()
    assert 'unpkg' not in HTML.lower()


def test_css_and_js_are_sane():
    assert CSS.count('{') == CSS.count('}')
    assert '@media (max-width: 820px)' in CSS
    assert '@media (max-width: 560px)' in CSS
    assert 'prefers-reduced-motion' in CSS
    assert ':focus-visible' in CSS
    assert '--lime: #d6f473' in CSS
    assert 'DM Sans' in CSS

    script = (SITE / 'script.js').read_text(encoding='utf-8')
    assert 'nav-toggle' in script
    assert 'aria-expanded' in script
    assert 'getElementById("year")' in script
    if shutil.which('node'):
        subprocess.run(['node', '--check', str(SITE / 'script.js')],
                       check=True, timeout=30)


def test_html_is_balanced_and_ids_are_unique():
    from html.parser import HTMLParser

    void = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'}

    class Balance(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack = []
            self.errors = []

        def handle_starttag(self, tag, attrs):
            if tag not in void:
                self.stack.append(tag)

        def handle_endtag(self, tag):
            if tag in void:
                return
            if not self.stack or self.stack.pop() != tag:
                self.errors.append(tag)

    for path in (INDEX, SITE / '404.html'):
        parser = Balance()
        parser.feed(path.read_text(encoding='utf-8'))
        assert not parser.stack, f'tag non chiusi in {path.name}: {parser.stack}'
        assert not parser.errors, f'tag sbilanciati in {path.name}'

    ids = re.findall(r'id="([^"]+)"', HTML)
    assert len(ids) == len(set(ids)), 'id duplicati nella pagina'
    for anchor in re.findall(r'href="#([^"]+)"', HTML):
        assert anchor in ids, f'ancora senza destinazione: #{anchor}'


def test_pages_workflow_deploys_the_website_directory():
    workflow = (ROOT / '.github' / 'workflows' / 'pages.yml')
    assert workflow.exists()
    text = workflow.read_text(encoding='utf-8')
    for marker in ('branches: [main]', 'workflow_dispatch', 'pages: write',
                   'id-token: write', 'upload-pages-artifact@v3',
                   'path: website', 'deploy-pages@v4'):
        assert marker in text, f'{marker!r} mancante nel workflow Pages'


def test_site_readme_and_root_link():
    readme = (SITE / 'README.md').read_text(encoding='utf-8')
    assert 'GitHub Actions' in readme
    assert 'assets/screenshots/' in readme
    assert 'Licenza da definire' in readme
    root_readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert 'leonardo-lalli.github.io/Open-score' in root_readme
