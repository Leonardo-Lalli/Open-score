# Handoff frontend → backend (Team B → Team A)

> Proprietario: Team B (frontend/UX). Non modificare in parallelo dal Team A.
> Branch: `max-develop` · Base: `main` @ `f0eedf9` · Data: 26 ottobre 2026 · Versione app: 0.8.0.
> Registro cronologico delle modifiche: [TEAM_B_LOG.md](TEAM_B_LOG.md).

Questo documento è l'audit iniziale del frontend e l'elenco delle richieste verso il Team A. Serve come contratto informale finché non sarà pronto `docs/contracts/API_V1.md` (ancora assente al momento della scrittura).

---

## 1. Architettura frontend attuale

- **SPA vanilla, senza build step**: nessun framework. `torneo-lab/static/index.html` + `torneo-lab/static/app.js` + `torneo-lab/static/styles.css`.
- Servita da FastAPI: `GET /` e `GET /public/{token}` restituiscono `static/index.html`; gli asset sono versionati (`?v=0.8.0`) e serviti con `Cache-Control: no-cache, must-revalidate`.
- **QR**: `static/vendor/qrcode.js` (qrcode-generator 1.4.4, MIT) genera localmente l'SVG della vista spettatore. Nessuna API e nessuna richiesta esterna.
- **Un solo file JS** (`app.js`, ~1.500 righe) con stato modulare globale, nessun modulo ES.
- **Routing hash** limitato al catalogo, al calendario e ai campi: `#/sport`, `#/sport/{sport}`, `#/sport/{sport}/{variante}`, `#/calendar`, `#/fields`, più l'alias invito `#/join/{token}`. La navigazione principale (dashboard, torneo, tab) è gestita via stato (`selectedId`, `tab`) e re-render del `<main id="content">`, non via URL.
- **Rendering lato client**: funzioni `render*` che producono stringhe HTML e le assegnano con `innerHTML`; `h()` esegue l'escape; `icon()`/`button()` sono helper.
- Nessun bundler, nessun framework CSS: `styles.css` (~4.200 righe) con token CSS in `:root`.

### Stato e helper principali (`app.js`)

| Area | Funzioni |
| --- | --- |
| Escape/icone/azioni | `h`, `icon`, `paths`, `button`, `label`, `stateLabel`, `tieLabel`, `avatar`, `teamName`, `dateText`, `roundName` |
| Client HTTP | `api(path, options)` — unico punto di accesso a `/api` |
| Sessione/ruolo | `loadSession`, `renderAuthControl`, `showRoleGate`, `hideRoleGate`, `enterStudentMode`, `loginTeacher`, `canEdit`, `canManage`, `requireManage`, `logout` |
| Catalogo sport | `loadSports`, `sportFor`, `variantFor`, `openCatalog`, `catalogSportCard`, `catalogVariantCard`, `renderCatalog` |
| Dashboard | `dashboard`, `refreshList`, `renderNav`, `renderDashboard`, `eventCard` |
| Torneo | `openTournament`, `renderTournament`, `overview`, `regulationView`, `bracket`, `matches`, `standings`, `teams`, `team view`, `champion` |
| Wizard | `startWizard`, `sportOptions`, `sportOptionsFor`, `variantOptionsFor`, `syncEditVariant`, `readWizard` |
| Azioni globali | `actions` map (`new`, `catalog`, `open`, `edit`, `share`, `download-qr`, `print-qr`, `share-qr`, `invite-join`, `generate`, `score`, `archive`, `restore`, `print`, `refresh`, `copy`, …) |
| Condivisione e inviti | `share`, `qrSvg`, `downloadQr`, `printQr`, `shareLink`, `inviteAdapter`, `inviteError`, `showInviteShell`, `openInvite`, `renderInvite`, `joinInvite` |
| Campi e calendario | `fieldsAdapter`, `fieldError`, `openFields`, `renderFields`, `fieldModal`, `fieldCard`, `knownFieldOptions`, `calendarAdapter`, `openCalendar`, `reloadCalendar`, `renderCalendar`, `buildCalendarEvents`, `detectCalendarConflicts`, `filterCalendarEvents`, `updateScheduleConflictHint`, `scheduleError` |
| Regole e metadati | `variantRuleSchema`, `fallbackRuleSchema`, `ruleInputHtml`, `ruleFieldsetHtml`, `ruleWarnings`, `derivedRuleItems`, `updateRuleWarnings`, `renderEditRules`, `readEditRules` |
| Avvio | `init` — carica sessione e catalogo, decide gate vs studente, delega il rendering |

Stato globale: `list`, `sports`, `auth {role, authenticated, teacher}`, `selectedId`, `data`, `tab`, `filter`, `matchFilter`, `search`, `wizard`, `wizardStep`, `catalogMode`, `catalogSport`, `catalogVariant`, `catalogDetail`, `calendarMode`, `fieldsMode`, `calendarState`, `calendarFilters`, `calendarError`, `calendarLoading`, `fieldsCache`, `fieldsError`, `inviteState`, `pendingInviteToken`.

### Client HTTP esistente

`api()` è già un client centralizzato minimale: base `/api`, header JSON, gestione 401 (riapre il gate), estrazione `detail` da errori Pydantic/FastAPI, `204` → `null`. Manca: timeout, retry sicuro (specie per `GET`), invalidazione cache e normalizzazione tipizzata delle risposte.

---

## 2. Design system attuale

- **Token** (`styles.css` `:root`): `--bg #f6f7f2`, `--paper #fff`, `--ink #1c3028`, `--muted #738077`, `--line #e3e8df`, `--lime #d6f473`, `--dark #182923`, `--green #2d694d`, `--radius 17px`.
- **Tipografia**: DM Sans servita localmente (4 file WOFF2, OFL) con fallback `Segoe UI`/Arial.
- **Componenti**: `.button` (primary/ghost/danger/compact), `.panel`, `.event-card`, `.catalog-card`, `.stat`, `.tag`, `.modal` (`<dialog>`), `.toast`, `.input`/`.select`, `.details-list`, `.rule-list`, `.table`/`.bracket`.
- **Responsive/mobile** (regole in coda al CSS): `100dvh`, `env(safe-area-inset-*)`, topbar sticky, drawer `.sidebar` con scrim, touch target ≥44px, input 16px, modali full-screen, tabelle/bracket con scroll orizzontale.
- **Accessibilità presente**: skip-link, `:focus-visible`, `aria-*` su gate/tab/modal, `role="status"` sul toast. Da verificare: contrasto su alcuni colori secondari, focus nei dialog annidati, `prefers-reduced-motion`.

---

## 3. UI già funzionante vs da sviluppare

### Funzionante (end-to-end)

- Gate prof/studente, login/logout, sessione e tag "Sola lettura".
- Dashboard con filtri, contatori e card torneo.
- Catalogo sport (6 sport / 16 varianti) con schede dedicate.
- Wizard di creazione (sport → variante → formato → partecipanti → riepilogo).
- Dettaglio torneo con tab: panoramica, incontri, classifica, tabellone, regolamento, squadre/partecipanti.
- Risultati numerici e set per set, correzioni, programmazione, archiviazione, condivisione e CSV.
- QR del link spettatore, generato nel browser senza servizi esterni.
- Modale di condivisione con copia link, download del QR in SVG, stampa del solo QR e Web Share API con fallback.
- Pagina di accettazione invito (`/?invite=<token>`, `#/join/<token>`) con anteprima reale tramite il link pubblico e adesione in attesa dell'API inviti.
- Pagina **Campi** (`#/fields`, solo docenti) con elenco, scheda, creazione/modifica/disattivazione predisposte e campi citati negli incontri.
- Pagina **Calendario** (`#/calendar`) con partite per giorno, filtri per torneo/squadra/giorno/campo/stato e conflitti visibili.
- Form di configurazione sport/regole guidati dai metadati della variante, condivisi tra wizard e modifica torneo, con validazione live e avviso sui tornei già iniziati.
- Tabellone a eliminazione con relazioni reali `source_home`/`source_away`, risultati ufficiali, BYE, colonna Campione, chip dei turni su mobile e test geometrici per 4/8/16 squadre.
- Riordino dei partecipanti nel wizard con drag & drop (mouse/touch) e tastiera; l'ordine viene inviato al backend in `team_names`.
- Vista spettatore (`/public/{token}`) in sola lettura con auto-refresh.

### Da sviluppare (Team B)

- **Bracket interattivo e drag & drop del tabellone**: editing visivo del tabellone e riordino dei partecipanti di un torneo già creato (serve l'endpoint dedicato). Il componente generico di riordino è già pronto in `app.js`.
- **Infografiche/statistiche** più ricche (andamento, marcatori, distribuzione risultati).
- **Dashboard responsive riprogettata** per telefono (card ridotte, non solo larghezza minore).
- **GitHub Pages** come vetrina statica del progetto (separata dall'app reale).
- **README in inglese** e documentazione pubblica/presentazione.
- **Design system esplicitato** (tavola componenti, token, stati loading/empty/error).
- **Test frontend** (oggi solo test statici in `tests/test_static_ui.py`).

---

## 4. API necessarie (richieste al Team A)

Prima del contratto ufficiale, lavoro su attività indipendenti o con mock isolati. Le funzioni che richiedono backend sono:

1. **Riordino/seeding partecipanti** (per drag & drop nel wizard e nel tabellone).
   - *Serve*: riordinare le squadre **di un torneo già creato** e/o rigenerare con un ordine/seed esplicito. Nel wizard l'ordine è già supportato da `team_names`.
   - *Contratto proposto*: `PATCH /api/tournaments/{id}/teams/order` con `{"team_ids": [...]}`; risposta `{"ok": true, "team_ids": [...]}`. Il frontend ha `teamOrderAdapter` con `ready: false`: quando l'endpoint esiste, impostare `ready: true`.
   - *Semantica*: l'ordine è di **visualizzazione**, non classifica o seeding. Non usarlo per accoppiamenti senza un contratto esplicito.
   - *Rollback*: su rifiuto il frontend ricarica dal server; se il reload fallisce ripristina l'ordine precedente.
   - *Output/stati*: lista aggiornata; 409 se la generazione è già avvenuta, se questa è la regola concordata.

2. **Statistiche individuali / tabella marcatori**.
   - *Serve*: infografiche e dettagli giocatore.
   - *Input*: nessuno (derivato). *Output*: aggregati per giocatore/squadra.
   - *Nota*: oggi esiste solo il conteggio aggregato nel dettaglio torneo; l'individuale non è implementato.

3. **Import CSV partecipanti**.
   - *Serve*: creare squadre/giocatori da file.
   - *Input*: `multipart/form-data` o JSON. *Output*: riepilogo errori/creati.

4. **Disattivazione account docente** (oggi solo via database).
   - *Serve*: gestione account dalla UI. *Output*: stato account.

5. **Paginazione/filtri elenco tornei** (se cresce il numero di tornei).

6. **Scheduler automatico** (futuro, non prioritario): restrizioni campi/arbitri.

7. **Aggregati per la dashboard docente**.
   - *Serve*: mostrare in un'unica chiamata prossime partite, risultati da verificare, problemi di calendario e numero di studenti, evitando le richieste N+1 del frontend.
   - *Input*: `?mine=1` e opzionalmente un intervallo temporale.
   - *Output*: elenco incontri futuri con torneo/squadre/orario/campo, eventuali conflitti e conteggi.

8. **Approvazione risultati e gestione campi** (se previsti).
   - *Serve*: un flusso esplicito “risultato da approvare” e la gestione di campi/arbitri come risorse. Oggi il risultato è inserito direttamente e il campo è solo testo.
   - *Nota*: da concordare con il Team A se introdurre lo stato `pending` e un inventario campi.

9. **Identità studente e visibilità personalizzata**.
   - *Serve*: account/identità studente e appartenenza a una squadra per mostrare “la mia squadra”, “la mia prossima partita”, l'organizzatore e lo stato delle proprie proposte di risultato.
   - *Nota visibilità*: oggi `GET /api/tournaments` e `GET /api/tournaments/{id}` espongono `teacher_id`, `public_token` e (nel dettaglio) `audit` anche agli anonimi. Il frontend nasconde l'`audit` ai non docenti, ma il backend dovrebbe non esporre questi campi ai non proprietari o servire una vista “studente” dedicata.

10. **Archivio studenti e assegnazioni**.
   - *Serve*: elenco studenti non assegnati, spostamento atomico tra squadre, import massivo con esito per riga ed eventuale import Excel.
   - *Oggi*: le rose usano `GET/POST/DELETE /api/tournaments/{id}/teams/{team_id}/players`; il frontend offre anteprima CSV e salvataggio sequenziale, dichiarato come non atomico. Un endpoint bulk/assign renderebbe l'import sicuro e più veloce.

11. **Proposte di risultato e approvazione**.
   - *Contratto proposto*: `GET /api/tournaments/{id}/proposals?status=pending`; `POST /api/tournaments/{id}/matches/{match_id}/proposals` con punteggi o set e `version`; `PATCH /api/proposals/{id}` con `action` `approve`, `reject` o `correct`.
   - *Oggi*: `resultProposalsAdapter.ready` è `false`; la scheda “Da verificare” mostra lo stato di attesa e il pulsante studente è nascosto. Nessun dato finto.
   - *Serve*: identità studente, modello proposte, autore con visibilità, conflitti, cronologia e aggiornamento ufficiale dopo l'approvazione.

12. **Inviti e adesioni tramite QR**.
   - *Serve*: token di invito per torneo e per squadra, stato dell'invito e adesione con eventuale approvazione del docente. La pagina frontend è già pronta e documentata in [`../QR_SHARING.md`](../QR_SHARING.md).
   - *Contratto proposto*: `GET /api/invites/{token}` → `{status, kind, tournament, organizer?, team?, available_slots?, requires_approval}`; `POST /api/invites/{token}/join` → `{status, message}`. Errori: `401`, `403`, `404`, `409` (già iscritto/squadra completa), `410` (scaduto).
   - *Oggi*: `inviteAdapter.ready` è `false`; la pagina usa in sola lettura `GET /api/public/{token}` per l'anteprima e disabilita l'adesione. Nessuna iscrizione simulata.
   - *Privacità*: l'organizzatore va esposto solo se pubblicabile; il token deve essere opaco (niente email, password o token di sessione).
   - *Opzionale*: `GET /join/{token}` che restituisce `static/index.html` (come `/public/{token}`); oggi funzionano già `/?invite=<token>` e `#/join/<token>`.

13. **Campi e calendario aggregato**.
   - *Serve*: CRUD dei campi del docente (nome, descrizione, sede, sport supportati, disponibilità, stato) e un aggregato del calendario con conflitti calcolati dal server. Frontend e contratto sono documentati in [`../FIELDS_AND_CALENDAR.md`](../FIELDS_AND_CALENDAR.md).
   - *Contratto proposto*: `GET/POST /api/fields`, `PATCH/DELETE /api/fields/{id}`; `GET /api/calendar?tournament=&team=&day=&field=&status=` → `{events, teams, fields, conflicts}`.
   - *Conflitti*: campo occupato, squadra in doppio impegno, docente in doppio impegno, con `message` leggibile. Oggi il frontend rileva solo sovrapposizioni campo/squadra dai dati reali e le etichetta come anteprima client.
   - *Oggi*: `fieldsAdapter.ready` e `calendarAdapter.ready` sono `false`; nessun campo viene salvato e il calendario aggrega i tornei leggibili con le API esistenti.
   - *Vincolo*: la programmazione partita continua a usare `location` testuale; un eventuale `field_id` va aggiunto senza rompere il testo.

14. **Metadati delle regole configurabili**.
   - *Serve*: descrivere per ogni variante quali parametri sono modificabili, con limiti e opzioni, così il frontend non deve codificare il regolamento di ogni sport. Dettaglio in [`../SPORT_RULES_CONFIG.md`](../SPORT_RULES_CONFIG.md).
   - *Contratto proposto*: `config_schema` (alias `rule_schema`/`configurable`) nella variante, array di `{key, label, type, min, max, step, options, required, default, help, scope, stages, disabled}`; opzionale `tie_breakers: [{value,label}]`.
   - *Oggi*: senza `config_schema` il frontend usa come fallback il contratto di `TournamentInput` (punti, criterio a parità, gare, gironi, qualificate). Durata, tempi, set e regole di pareggio restano derivati da `variant.rules` in sola lettura.
   - *Vincolo*: il payload resta limitato ai campi accettati dal backend; il frontend non inventa chiavi e non forza un salvataggio quando il server risponde `409` o `422`.

Per QR, infografiche lato client, tabellone e GitHub Pages **non serve** alcuna nuova API. Il tabellone usa già `source_home`/`source_away`, `winner_team_id` e `champion_team_id`; chiediamo solo che restino stabili nel contratto. Il drag & drop del wizard usa già `team_names`; servono API per il riordino post-creazione (punto 1) e per gli aggregati dashboard (punto 7).

---

## 5. Blocchi tecnici e decisioni

- **Monolite frontend/backend**: il backend è in `app.py`/`services.py`, il frontend in `static/`. Non c'è sovrapposizione di file: il Team B può lavorare su `static/`, `README*`, `docs/handoffs/` e documentazione pubblica senza toccare i file backend.
- **`docs/API.md` contiene un residuo obsoleto**: riga 119 "Caricamento esempi ripetuto…" riferita all'endpoint `/api/demo` ormai rimosso. Chiedo al Team A di correggerla insieme al contratto ufficiale (non l'ho modificata per non toccare il contratto condiviso).
- **`docs/contracts/API_V1.md` e `docs/contracts/openapi.yaml` non esistono ancora**: le integrazioni backend restano in attesa.
- **Nessun framework nuovo**: si mantiene la SPA vanilla, si migliora in place. Nessuna introduzione di React/TypeScript o librerie UI ridondanti.
- **Cache degli asset**: bump di versione (`?v=`) a ogni modifica di `app.js`/`styles.css` per evitare cache stantia.

## 6. Test e commit di riferimento

- Test esistenti del frontend: `torneo-lab/tests/test_static_ui.py` (gate, accessibilità statica, cache, assenza contenuti demo, redirect legacy).
- Suite completa al baseline: **190 passed, 1 warning** (warning Starlette/httpx, innocuo).
- Lint: `ruff check --select I,C4,UP,F .` pulito; `node --check static/app.js` OK.
- Commit base: `f0eedf9` (`feat!: rimuovi i dati dimostrativi preinstallati`), uguale su `main`, `develop` e `max-develop`.

## 7. Prossimi passi proposti (indipendenti dal backend)

1. Tavola del design system (`docs/design-system.md`) con token e componenti censiti.
2. Riprogettazione responsive della dashboard e del bracket per schermi piccoli.
3. Componente QR (client-only) per il link spettatore.
4. Sito GitHub Pages di presentazione + README in inglese.
5. Test visivi/frontend aggiuntivi senza introdurre dipendenze pesanti.
