from html.parser import HTMLParser

from db import BASE

LEGACY_PAGES = (
    'create.html',
    'gestione_partecipanti.html',
    'panoramica_torneo.html',
    'tabellone_torneo.html',
    'campione_sport_editorial.html',
)
FORBIDDEN_SPORTS = ('danza', 'padel', 'tennis', 'pallamano')


def test_legacy_urls_redirect_to_the_spa(client):
    for page in LEGACY_PAGES:
        root = client.get(f'/{page}', follow_redirects=False)
        assert root.status_code == 302
        assert root.headers['location'] == '/'

        static_page = client.get(f'/static/{page}')
        assert static_page.status_code == 200
        assert 'http-equiv="refresh"' in static_page.text
        assert 'url=/' in static_page.text


def test_no_demo_content_in_the_shell(client):
    markers = ('Esplora la demo', 'Carica esempi', 'Torneo dimostrativo',
               'DEMO SCOLASTICA', 'demo_key', '/demo')
    for path in (BASE / 'static' / 'index.html', BASE / 'static' / 'app.js'):
        text = path.read_text(encoding='utf-8')
        for marker in markers:
            assert marker not in text, f'{marker!r} trovato in {path.name}'


def test_static_ui_has_no_out_of_catalog_sports(client):
    assets = [*(BASE / 'static').glob('*.html'), BASE / 'static' / 'app.js']
    for path in assets:
        text = path.read_text(encoding='utf-8').lower()
        for sport in FORBIDDEN_SPORTS:
            assert sport not in text, f'{sport!r} trovato in {path.name}'


def test_index_references_versioned_assets_and_disables_cache(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'app.js?v=0.9.0' in response.text
    assert 'styles.css?v=0.8.0' in response.text
    assert 'no-cache' in response.headers['cache-control']


def test_mobile_shell_has_safe_area_and_touch_targets(client):
    html = client.get('/').text
    assert 'viewport-fit=cover' in html

    css = (BASE / 'static' / 'styles.css').read_text(encoding='utf-8')
    assert '100dvh' in css
    assert 'env(safe-area-inset-top)' in css
    assert 'env(safe-area-inset-bottom)' in css
    assert '@media (max-width: 800px)' in css
    assert 'min-height: 44px' in css
    assert 'font-size: 16px' in css
    assert css.count('{') == css.count('}')

    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    assert 'menu-open' in script
    assert 'modal-open' in script


def test_static_shell_assets_are_revalidated(client):
    for path in ('/static/app.js', '/static/styles.css', '/static/create.html'):
        response = client.get(path)
        assert response.status_code == 200
        assert 'no-cache' in response.headers['cache-control']


def test_role_login_form_wraps_its_fields_and_submit(client):
    class FormParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.depth = 0
            self.names = []
            self.has_submit = False

        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            if tag == 'form' and attributes.get('id') == 'role-login-form':
                self.depth = 1
                return
            if not self.depth:
                return
            if tag == 'form':
                self.depth += 1
            elif tag == 'input':
                self.names.append(attributes.get('name'))
            elif tag == 'button' and attributes.get('type') == 'submit':
                self.has_submit = True

        def handle_endtag(self, tag):
            if self.depth and tag == 'form':
                self.depth -= 1

    parser = FormParser()
    parser.feed(client.get('/').text)
    assert parser.names == ['email', 'password']
    assert parser.has_submit


def test_mobile_dashboard_and_bracket_have_dedicated_rules(client):
    css = (BASE / 'static' / 'styles.css').read_text(encoding='utf-8')
    for selector in ('.bracket-mobile-nav', '.bracket-round-chip', '.hero-buttons .button'):
        assert selector in css
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    assert '"bracket-round"' in script
    assert 'role="region" aria-label="Tabellone del torneo"' in script
    assert 'tabindex="0"' in script


def test_wizard_reorder_is_accessible_and_uses_existing_contract(client):
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    for marker in ('function enableReorder', 'function moveItem',
                   'data-drag-handle', 'aria-live="polite"', 'wizard.order'):
        assert marker in script
    css = (BASE / 'static' / 'styles.css').read_text(encoding='utf-8')
    assert '.reorder-list' in css
    assert '.reorder-handle' in css
    assert 'touch-action: none' in css


def test_result_proposal_interfaces_are_prepared(client):
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    for marker in ('resultProposalsAdapter', 'approvalsView', 'loadApprovals',
                   'proposeResultModal', 'proposalCorrectModal',
                   'proposal-form', 'proposal-correct-form',
                   'propose-result', 'approve-proposal', 'reject-proposal',
                   'correct-proposal', 'proposalErrorMessage', 'approvals-list'):
        assert marker in script
    assert '/proposals' in script
    css = (BASE / 'static' / 'styles.css').read_text(encoding='utf-8')
    assert '.proposal-banner' in css
    assert '.proposal-actions' in css


def test_team_order_table_is_accessible_and_has_save_adapter(client):
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    for marker in ('teamOrderPanel', 'team-order-body', 'team-order-move',
                   'teamOrderAdapter', 'team-order-status', 'team-order-live',
                   'drag-target'):
        assert marker in script
    assert 'PATCH' in script
    assert 'team_ids' in script
    css = (BASE / 'static' / 'styles.css').read_text(encoding='utf-8')
    assert '.team-order-table' in css
    assert '.team-order-row.dragging' in css
    assert '.order-move' in css


def test_student_management_uses_existing_roster_api(client):
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    for marker in ('studentsView', 'loadStudentsDetail', 'parseStudentList',
                   'bulkImportPanel', 'students-unassigned', 'data-student-team',
                   'student-form'):
        assert marker in script
    assert '/players' in script
    css = (BASE / 'static' / 'styles.css').read_text(encoding='utf-8')
    assert '.students-layout' in css
    assert '.student-team' in css


def test_student_dashboard_is_read_only_and_hides_private_diary(client):
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    assert 'renderStudentDashboard' in script
    assert 'IN SOLA LETTURA' in script
    assert '!publicToken && canEdit()' in script
    assert 'Vuoi organizzare anche tu' in script


def test_professor_dashboard_has_upcoming_matches(client):
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    assert 'loadUpcoming' in script
    assert 'upcoming-matches' in script
    css = (BASE / 'static' / 'styles.css').read_text(encoding='utf-8')
    assert '.upcoming-row' in css


def test_share_modal_has_client_side_qr(client):
    html = client.get('/').text
    assert '/static/vendor/qrcode.js?v=0.8.0' in html
    assert html.index('vendor/qrcode.js') < html.index('/static/app.js')

    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    assert 'createSvgTag' in script
    assert 'share-qr' in script
    assert 'Stai usando localhost' in script
    assert 'canManage() ? button("Condividi", "share"' in script
    assert 'Solo chi organizza il torneo può condividerlo.' in script

    vendor = (BASE / 'static' / 'vendor' / 'qrcode.js').read_text(encoding='utf-8')
    assert 'MIT license' in vendor
    assert 'Kazuhiko Arase' in vendor


def test_share_actions_and_invite_landing_are_prepared(client):
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    for marker in ('downloadQr', 'printQr', 'shareLink', 'download-qr',
                   'print-qr', 'share-qr', 'share-actions', 'print-sheet',
                   'inviteAdapter', 'INVITE_MESSAGES', 'apiWithMessages', 'openInvite', 'renderInvite',
                   'joinInvite', 'invite-join', 'invite-login', 'invite-retry',
                   'inviteState', 'inviteStatusCopy', 'unverified',
                   '?invite=', '#/join/', '/invites/'):
        assert marker in script, f'{marker!r} mancante in app.js'

    css = (BASE / 'static' / 'styles.css').read_text(encoding='utf-8')
    for selector in ('.share-actions', '.share-invite', '.invite-page',
                     '.invite-status', '.invite-actions', '#print-sheet'):
        assert selector in css, f'{selector!r} mancante in styles.css'
    assert 'body.printing > *:not(#print-sheet)' in css
    assert css.count('{') == css.count('}')


def test_invite_landing_only_uses_real_server_data(client):
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    # Preview falls back to the existing public endpoint; no fake payloads.
    assert 'api("/public/"' in script
    assert 'Adesione non ancora disponibile' in script
    assert 'pendingInviteToken' in script
    # No invitatory data is persisted locally.
    assert 'inviteToken' in script
    assert 'localStorage.setItem("invite' not in script


def test_fields_and_calendar_interfaces_are_prepared(client):
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    for marker in ('fieldsAdapter', 'FIELD_MESSAGES', 'fieldModal', 'renderFields',
                   'openFields', 'field-card', 'field-form', 'field-new',
                   'field-edit', 'field-toggle', 'knownFieldOptions',
                   'calendarAdapter', 'CALENDAR_MESSAGES', 'openCalendar',
                   'reloadCalendar', 'renderCalendar', 'filterCalendarEvents',
                   'detectCalendarConflicts', 'calendar-conflict',
                   'data-calendar-filter', 'calendar-open', 'calendar-reset',
                   'updateScheduleConflictHint', 'schedule-conflict',
                   'known-fields', '/fields', '/calendar'):
        assert marker in script, f'{marker!r} mancante in app.js'

    html = (BASE / 'static' / 'index.html').read_text(encoding='utf-8')
    assert 'data-action="calendar"' in html
    assert 'data-action="fields"' in html
    assert 'data-teacher-only' in html

    css = (BASE / 'static' / 'styles.css').read_text(encoding='utf-8')
    for selector in ('.field-grid', '.field-card', '.field-actions',
                     '.calendar-filters', '.calendar-day', '.calendar-event',
                     '.calendar-main', '.calendar-conflict-panel',
                     '.schedule-conflict'):
        assert selector in css, f'{selector!r} mancante in styles.css'
    assert css.count('{') == css.count('}')


def test_fields_and_calendar_do_not_fake_saves_or_conflicts(client):
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    assert script.count('ready: true') >= 5
    assert 'Nessun dato è stato inviato' in script
    assert 'il server resta l’unica fonte autorevole' in script
    assert 'api("/tournaments/" + tournament.id)' in script
    # The schedule form surfaces server-side conflicts instead of forcing saves.
    assert 'function scheduleError' in script
    assert 'Conflitto di calendario' in script


def test_knockout_bracket_uses_real_sources_and_champion(client):
    html = client.get('/').text
    assert '/static/bracket-layout.js?v=0.8.0' in html
    assert html.index('bracket-layout.js') < html.index('/static/app.js')

    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    for marker in ('BracketLayout.layout', 'bracketSourceLabel', 'bracketStatus',
                   'champion-card', 'source_home', 'source_away',
                   'Il tabellone usa solo i risultati confermati',
                   'aria-label="Tabellone del torneo"', 'bracket-round'):
        assert marker in script, f'{marker!r} mancante in app.js'

    layout = (BASE / 'static' / 'bracket-layout.js').read_text(encoding='utf-8')
    for marker in ('source_home', 'source_away', 'champion', 'module.exports'):
        assert marker in layout, f'{marker!r} mancante in bracket-layout.js'

    css = (BASE / 'static' / 'styles.css').read_text(encoding='utf-8')
    for selector in ('.bracket-card.champion-card', '.bracket-trophy',
                     '.champion-name', '.bracket-card.bye'):
        assert selector in css, f'{selector!r} mancante in styles.css'


def test_bracket_layout_probe_is_versioned_with_the_suite(client):
    probe = BASE / 'tests' / 'bracket_layout_probe.js'
    assert probe.exists()
    text = probe.read_text(encoding='utf-8')
    assert 'planFor' in text
    assert 'scoreInvariant' in text


def test_sport_rule_forms_are_metadata_driven(client):
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    for marker in ('variantRuleSchema', 'fallbackRuleSchema', 'ruleFieldsetHtml',
                   'ruleInputHtml', 'ruleConstraintText', 'ruleWarnings',
                   'derivedRuleItems', 'formatRuleValue', 'config_schema',
                   'rule_schema', 'tie_breakers', 'wizard-rule-fields',
                   'edit-rule-fields', 'rule-warnings', 'rule-warning-banner',
                   'Regole definite dalla variante', 'Parametri configurabili',
                   'Torneo già iniziato'):
        assert marker in script, f'{marker!r} mancante in app.js'
    # The wizard and the edit modal both render rules through the same fieldset.
    assert script.count('ruleFieldsetHtml(') >= 4
    # Validation blocks incompatible rules before the request.
    assert 'warnings.join(" ")' in script
    assert 'Il backend valida ogni modifica' in script

    css = (BASE / 'static' / 'styles.css').read_text(encoding='utf-8')
    for selector in ('.rule-fieldset', '.rule-warnings', '.rule-warning-banner',
                     '.rule-config-list', '.rule-config-row'):
        assert selector in css, f'{selector!r} mancante in styles.css'
    assert css.count('{') == css.count('}')


def test_sport_rule_forms_do_not_override_backend_metadata(client):
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    # Variant rules stay read-only; only the declared schema is editable.
    assert 'field.scope !== "variant"' in script
    assert 'variant.rules' in script
    # The fallback is the shared TournamentInput contract, not a sport rulebook.
    assert 'Punti vittoria' in script
    assert 'name="target_goals"' not in script
    assert 'name="periods"' not in script


def test_statistics_and_infographic_are_wired(client):
    html = client.get('/').text
    assert '/static/infographic.js?v=0.8.0' in html
    assert html.index('infographic.js') < html.index('/static/app.js')

    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    for marker in ('statsView', 'buildInfographicPayload', 'infographicPodium',
                   'infographicQualifiers', 'infographicChampion', 'qrMatrix',
                   'periodLabel', 'exportInfographicSvg', 'exportInfographicPng',
                   'printInfographic', 'Infographic.buildSvg', 'export-svg',
                   'export-png', 'print-infographic', 'Statistiche',
                   'Infografica condivisibile', 'Nessun nome di studente'):
        assert marker in script, f'{marker!r} mancante in app.js'

    css = (BASE / 'static' / 'styles.css').read_text(encoding='utf-8')
    for selector in ('.stats-layout', '.podium', '.podium-card',
                     '.qualifier-list', '.infographic-preview', '.infographic-panel',
                     'body.printing #print-sheet.infographic-sheet'):
        assert selector in css, f'{selector!r} mancante in styles.css'
    assert css.count('{') == css.count('}')


def test_infographic_probe_is_versioned_with_the_suite(client):
    probe = BASE / 'tests' / 'infographic_probe.js'
    assert probe.exists()
    text = probe.read_text(encoding='utf-8')
    assert 'buildSvg' in text
    assert 'qr' in text


def test_role_gate_offers_teacher_login_and_student_read_only(client):
    html = client.get('/').text
    assert 'id="role-gate"' in html
    assert 'Sono un prof' in html
    assert 'Sono uno studente' in html
    assert 'id="role-login-form"' in html
    assert 'name="email"' in html
    assert 'name="password"' in html

    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    assert 'showRoleGate' in script
    assert 'enterStudentMode' in script
    assert 'loginTeacher' in script
    assert 'canManage' in script


def test_spa_no_longer_links_to_legacy_design_pages(client):
    script = (BASE / 'static' / 'app.js').read_text(encoding='utf-8')
    for page in LEGACY_PAGES:
        assert page not in script
