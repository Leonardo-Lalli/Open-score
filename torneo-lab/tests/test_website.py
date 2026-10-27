"""Static checks for the GitHub Pages presentation site.

The site is a standalone static directory: these tests guard structure, honest
claims, local assets, the Pages workflow and basic CSS/JS sanity.
"""
import json
import re
import shutil
import subprocess
import sys
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
    assert (SITE / 'site.config.json').exists()
    assert (ROOT / '.github' / 'scripts' / 'build_site.py').exists()
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
    assert not re.search(r'href="[^"]*demo[^"]*"', HTML, re.IGNORECASE)
    assert not re.search(r'>\s*Demo\s*<', HTML)
    assert 'La demo pubblica non è ancora disponibile' in HTML
    # The project license is not assigned yet.
    assert 'Licenza da definire' in HTML
    for claim in ('Licenza MIT', 'MIT License', 'Apache License',
                  'GNU General Public License'):
        assert claim not in HTML
    # Features are grouped by real status.
    assert 'Disponibili' in HTML
    assert 'Integrazione e collaudo' in HTML
    assert "manca l'API" not in HTML
    assert 'salvataggio è sequenziale' not in HTML
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
                              'data:', '__SITE_')):
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
    assert not re.search(r'<script[^>]+src="https?://', HTML, re.IGNORECASE)
    assert not re.search(
        r'<link[^>]+rel="stylesheet"[^>]+href="https?://', HTML, re.IGNORECASE)
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


def test_theme_selector_is_present_and_accessible():
    assert 'id="theme-toggle"' in HTML
    assert 'id="theme-menu"' in HTML
    assert 'aria-controls="theme-menu"' in HTML
    assert 'aria-expanded="false"' in HTML
    for value in ('light', 'dark', 'system'):
        assert f'name="site-theme" value="{value}"' in HTML
    for icon in ('theme-icon-light', 'theme-icon-dark', 'theme-icon-system'):
        assert icon in HTML
    assert 'html[data-theme-choice="light"] .theme-icon-light' in CSS
    assert 'html[data-theme-choice="dark"] .theme-icon-dark' in CSS
    assert 'html[data-theme-choice="system"] .theme-icon-system' in CSS
    assert '.theme-menu' in CSS
    assert '.header-actions' in CSS


def test_theme_is_applied_before_the_stylesheet():
    theme_script = HTML.index('document.documentElement.dataset.theme')
    stylesheet = HTML.index('<link rel="stylesheet" href="styles.css"')
    assert theme_script < stylesheet
    assert 'openScoreSiteTheme' in HTML
    assert 'prefers-color-scheme: dark' in HTML
    assert 'openScoreSiteTheme' in (SITE / 'script.js').read_text(encoding='utf-8')
    script = (SITE / 'script.js').read_text(encoding='utf-8')
    for marker in ('matchMedia', 'dataset.theme', 'dataset.themeChoice',
                   'localStorage.setItem', 'addEventListener("change"',
                   'aria-expanded'):
        assert marker in script, f'{marker!r} mancante in script.js'
    assert '[data-theme="dark"]' in CSS
    assert '@media (prefers-color-scheme: dark)' in CSS
    assert 'color-scheme: dark' in CSS


def _tokens(selector):
    match = re.search(rf'{selector}\s*\{{(.*?)\}}', CSS, re.DOTALL)
    assert match, f'blocco {selector!r} mancante'
    return dict(re.findall(r'(--[a-z-]+):\s*([^;]+);', match.group(1)))


def _resolve(tokens, value, depth=0):
    value = value.strip()
    match = re.fullmatch(r'var\((--[a-z-]+)\)', value)
    if match and depth < 6:
        return _resolve(tokens, tokens[match.group(1)], depth + 1)
    return value


def _luminance(hex_color):
    value = hex_color.lstrip('#')
    channels = [int(value[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [
        channel / 12.92 if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(foreground, background):
    a, b = _luminance(foreground), _luminance(background)
    high, low = max(a, b), min(a, b)
    return (high + 0.05) / (low + 0.05)


def test_theme_tokens_have_sufficient_contrast():
    pairs = (
        ('--ink', '--bg', 7.0),
        ('--ink', '--paper', 7.0),
        ('--muted', '--bg', 4.5),
        ('--muted', '--bg-alt', 4.5),
        ('--muted', '--paper', 4.5),
        ('--green', '--bg', 4.5),
        ('--btn-primary-ink', '--btn-primary-bg', 4.5),
        ('--status-done-ink', '--status-done-bg', 4.5),
        ('--status-wip-ink', '--status-wip-bg', 4.5),
        ('--status-next-ink', '--status-next-bg', 4.5),
        ('--chip-ink', '--chip-bg', 4.5),
        ('--badge-ink', '--badge-bg', 4.5),
        ('--on-dark', '--cta-bg', 4.5),
        ('--on-dark-muted', '--cta-bg', 4.5),
    )
    for selector in (r':root', r'\[data-theme="dark"\]'):
        tokens = _tokens(selector)
        for foreground, background, minimum in pairs:
            assert foreground in tokens, f'{foreground} mancante in {selector}'
            assert background in tokens, f'{background} mancante in {selector}'
            ratio = _contrast(
                _resolve(tokens, tokens[foreground]),
                _resolve(tokens, tokens[background]),
            )
            assert ratio >= minimum, (
                f'contrasto insufficiente in {selector}: {foreground} su '
                f'{background} = {ratio:.2f} (minimo {minimum})'
            )


def test_theme_works_on_mobile():
    mobile = CSS[CSS.index('@media (max-width: 560px)'):]
    assert '.theme-toggle' in mobile
    assert 'width: 44px' in mobile
    assert '.theme-toggle-label' in mobile
    assert 'display: none' in mobile


def test_pages_workflow_deploys_the_website_directory():
    workflow = (ROOT / '.github' / 'workflows' / 'pages.yml')
    assert workflow.exists()
    text = workflow.read_text(encoding='utf-8')
    for marker in ('branches: [main]', 'workflow_dispatch', 'needs: verify',
                   "if: github.ref == 'refs/heads/main'", 'pages: write',
                   'id-token: write', 'contents: read',
                   'cancel-in-progress: false', 'upload-pages-artifact@v4',
                   'path: _site', 'deploy-pages@v4', 'build_site.py',
                   'node --check website/script.js',
                   'python -m pytest --noconftest', 'python -m pip check'):
        assert marker in text, f'{marker!r} mancante nel workflow Pages'
    assert 'path: website' not in text
    assert 'secrets.' not in text
    assert 'pull_request' not in text


def test_site_has_no_secret_material():
    patterns = re.compile(
        r'ghp_[A-Za-z0-9]{20,}|github_pat_|AKIA[0-9A-Z]{16}|'
        r'-----BEGIN [A-Z ]*PRIVATE KEY-----|client_secret\s*[:=]|'
        r'api_key\s*[:=]', re.IGNORECASE)
    for path in (INDEX, SITE / '404.html', SITE / 'styles.css',
                 SITE / 'script.js', SITE / 'site.config.json'):
        text = path.read_text(encoding='utf-8')
        assert not patterns.search(text), f'possibile segreto in {path.name}'


def test_site_config_matches_the_pages_placeholders():
    config = json.loads((SITE / 'site.config.json').read_text(encoding='utf-8'))
    assert config['base'].startswith('/') and config['base'].endswith('/')
    assert config['url'].startswith('https://') and config['url'].endswith('/')
    domain = config['custom_domain']
    if domain:
        assert config['base'] == '/'
        assert config['url'].lower().startswith(f'https://{domain.lower()}/')
    else:
        assert config['base'] == '/Open-score/'
        assert config['url'].endswith(config['base'])
    assert '<base href="__SITE_BASE__" />' in (SITE / '404.html').read_text(
        encoding='utf-8')
    assert '__SITE_URL__' in HTML
    absolute = re.findall(r'(?:src|href)="(/[^/][^"]*)"', HTML)
    assert absolute == [], f'percorsi assoluti non portabili: {absolute}'


def test_build_renders_the_site_without_placeholders(tmp_path):
    config = json.loads((SITE / 'site.config.json').read_text(encoding='utf-8'))
    out = tmp_path / 'site'
    subprocess.run(
        [sys.executable, str(ROOT / '.github' / 'scripts' / 'build_site.py'),
         '--out', str(out)],
        check=True, timeout=60,
    )
    index = (out / 'index.html').read_text(encoding='utf-8')
    error = (out / '404.html').read_text(encoding='utf-8')
    for page in (index, error):
        assert '__SITE_' not in page
    assert f'<base href="{config["base"]}" />' in error
    assert f'href="{config["url"]}"' in index
    assert not (out / 'site.config.json').exists()
    assert not (out / 'README.md').exists()
    assert (out / 'styles.css').exists()
    assert (out / '.nojekyll').exists()
    assert (out / 'assets' / 'fonts' / 'OFL.txt').exists()


def test_images_have_alt_text():
    pages = (HTML, (SITE / '404.html').read_text(encoding='utf-8'))
    for page in pages:
        for tag in re.findall(r'<img\b[^>]*>', page, re.IGNORECASE):
            assert 'alt=' in tag, f'immagine senza alt: {tag}'


def test_site_declares_italian():
    assert '<html lang="it">' in HTML
    assert '<html lang="it">' in (SITE / '404.html').read_text(encoding='utf-8')


def test_site_readme_and_root_link():
    readme = (SITE / 'README.md').read_text(encoding='utf-8')
    assert 'GitHub Actions' in readme
    assert 'assets/screenshots/' in readme
    assert 'Licenza da definire' in readme
    root_readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert 'leonardo-lalli.github.io/Open-score' in root_readme
