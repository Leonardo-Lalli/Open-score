# Registro Team B → Team A

> Registro cronologico delle modifiche del Team B sul branch `max-develop`, per rendere immediata l'integrazione con il Team A e con `main`.
> Base: `main` @ `f0eedf9` · Branch: `max-develop` · Ultimo aggiornamento: 26 ottobre 2026.

## Come usare questo file

- **Team A**: leggi la tabella commit e la sezione "API richieste"; i file toccati sono solo frontend, documentazione e test UI.
- **Team B**: aggiungi una riga a ogni commit e aggiorna "Stato corrente".
- **Integrazione**: `git log f0eedf9..max-develop` e `git diff f0eedf9..max-develop` sono la fonte autorevole.

## Stato corrente

- Branch: `max-develop` (HEAD `5939873`), working tree pulito.
- Base: `f0eedf9` (`main` / `origin/main`).
- Backend, migrazioni, modelli e contratti API: **non modificati**.
- Suite: **214 passed** (warning Starlette/httpx del TestClient, innocuo).
- Lint: `ruff check --select I,C4,UP,F .` pulito; `node --check static/app.js` OK.
- Push: nessuno; il branch resta locale finché il team non lo richiede.

## Commit del Team B

| Commit | Data | Modifica | File principali | API / contratto | Verifica |
| --- | --- | --- | --- | --- | --- |
| `5d8bb3f` | 26/10 11:36 | Audit frontend e richieste API | `docs/handoffs/FRONTEND_TO_BACKEND.md` | Elenco richieste | — |
| `cec5278` | 26/10 11:40 | Tavola del design system | `docs/design-system.md` | — | — |
| `d456a32` | 26/10 11:43 | Dashboard e bracket mobile | `static/app.js`, `static/styles.css`, `tests/test_static_ui.py` | Nessuna nuova | 191 passed |
| `472ca92` | 26/10 11:46 | QR del link spettatore | `static/index.html`, `static/app.js`, `static/styles.css`, `static/vendor/*` | Nessuna API; libreria MIT locale | 192 passed |
| `46acdd4` | 26/10 11:53 | Riordino partecipanti drag & drop | `static/app.js`, `static/styles.css`, `tests/test_static_ui.py` | Usa `team_names` esistente; futuro `PATCH /teams/order` | 193 passed |
| `6142b31` | 26/10 11:57 | Prossime partite in dashboard | `static/app.js`, `static/styles.css`, `docs/PROFESSOR_DASHBOARD.md`, `docs/handoffs/*` | Usa `GET /tournaments/{id}`; richiesta aggregato | 194 passed |
| `1856497` | 26/10 12:04 | Dashboard studenti in sola lettura | `static/app.js`, `tests/test_static_ui.py`, `docs/STUDENT_DASHBOARD.md`, `docs/handoffs/*` | Nessuna nuova API; visibilità studenti da concordare | 195 passed |
| `0b19581` | 26/10 12:12 | Gestione studenti nelle squadre | `static/app.js`, `static/styles.css`, `tests/test_static_ui.py`, `docs/STUDENT_MANAGEMENT.md`, `docs/handoffs/*` | Usa le rose esistenti; bulk sequenziale; unassigned/move in attesa API | 196 passed |
| `1ce99bd` | 26/10 12:20 | Tabella ordine squadre con drag and drop | `static/app.js`, `static/styles.css`, `tests/test_static_ui.py`, `docs/DRAG_DROP_ORDERING.md`, `docs/design-system.md`, `docs/handoffs/*` | Adapter `PATCH /teams/order` proposto, `ready: false`; anteprima locale con rollback su errore API | 197 passed |
| `3937ee3` | 26/10 12:30 | Interfacce proposte e approvazioni | `static/app.js`, `static/styles.css`, `tests/test_static_ui.py`, `docs/RESULT_APPROVALS.md`, `docs/design-system.md`, `docs/handoffs/*` | `resultProposalsAdapter` con `ready: false`; scheda Da verificare in attesa API; nessun dato finto | 198 passed |
| `1ef0152` | 26/10 13:10 | Condivisione QR completa e pagina inviti | `static/app.js`, `static/styles.css`, `tests/test_static_ui.py`, `docs/QR_SHARING.md`, `docs/design-system.md`, `docs/handoffs/FRONTEND_TO_BACKEND.md` | Azioni download/stampa/condividi; `inviteAdapter` con `ready: false`; anteprima invito via `GET /api/public/{token}` | 200 passed |
| `0f086ee` | 26/10 13:40 | Pagine campi e calendario | `static/app.js`, `static/styles.css`, `static/index.html`, `tests/test_static_ui.py`, `docs/FIELDS_AND_CALENDAR.md`, `docs/design-system.md`, `docs/handoffs/FRONTEND_TO_BACKEND.md` | `fieldsAdapter` e `calendarAdapter` con `ready: false`; conflitti client dichiarati; aggregazione dai tornei reali | 202 passed |
| `c73d519` | 26/10 14:15 | Form sport e regole guidati dai metadati | `static/app.js`, `static/styles.css`, `tests/test_static_ui.py`, `docs/SPORT_RULES_CONFIG.md`, `docs/design-system.md`, `docs/handoffs/FRONTEND_TO_BACKEND.md` | `config_schema`/`tie_breakers` proposti; fallback su `TournamentInput`; regole della variante in sola lettura | 204 passed |
| `5939873` | 26/10 14:45 | Tabellone a eliminazione completo e testato | `static/app.js`, `static/styles.css`, `static/index.html`, `static/bracket-layout.js`, `tests/test_bracket_layout.py`, `tests/bracket_layout_probe.js`, `tests/test_static_ui.py`, `docs/BRACKET.md`, `docs/design-system.md`, `docs/handoffs/FRONTEND_TO_BACKEND.md` | Nessuna nuova API; usa `source_home`/`source_away`, `winner_team_id`, `champion_team_id` | 214 passed |

## File toccati da `f0eedf9`

- SPA: `torneo-lab/static/app.js`, `index.html`, `styles.css`, `bracket-layout.js`.
- Vendor: `torneo-lab/static/vendor/qrcode.js` (+ `README.md` di provenienza e licenza MIT).
- Test UI: `torneo-lab/tests/test_static_ui.py`, `test_bracket_layout.py`, `bracket_layout_probe.js`.
- Documentazione: `docs/design-system.md`, `docs/PROFESSOR_DASHBOARD.md`, `docs/STUDENT_DASHBOARD.md`, `docs/STUDENT_MANAGEMENT.md`, `docs/DRAG_DROP_ORDERING.md`, `docs/RESULT_APPROVALS.md`, `docs/QR_SHARING.md`, `docs/FIELDS_AND_CALENDAR.md`, `docs/SPORT_RULES_CONFIG.md`, `docs/BRACKET.md`, `docs/handoffs/FRONTEND_TO_BACKEND.md`, questo registro.

Nessuna modifica a `app.py`, `services.py`, `schemas.py`, `db.py`, `migrations/`, `deploy/` o workflow CI.

## API consumate (già esistenti)

- `GET /api/tournaments?archived=...&mine=1` — elenco e contatori.
- `GET /api/tournaments/{id}` — dettaglio, squadre, incontri, classifiche, regole.
- `POST /api/tournaments`, `POST /api/tournaments/{id}/generate` — wizard.
- `GET/POST/PATCH/DELETE` su squadre, giocatori, risultati, programmazione — viste esistenti.
- `GET /api/public/{token}` — vista spettatore e QR.
- `POST /api/auth/login|logout`, `GET /api/auth/session` — gate ruoli.

## API richieste al Team A

Dettaglio e stati in [`FRONTEND_TO_BACKEND.md`](FRONTEND_TO_BACKEND.md), sezione 4. Sintesi:

1. `PATCH /api/tournaments/{id}/teams/order` (o estensione di `/generate`) per il riordino post-creazione. Nel wizard l'ordine usa già `team_names`.
2. Aggregati dashboard docente: prossime partite, conflitti, studenti, risultati da verificare.
3. Statistiche individuali / marcatori.
4. Import CSV partecipanti.
5. Disattivazione account docente.
6. Paginazione/filtri elenco tornei.
7. Scheduler automatico e gestione campi/arbitri.
8. Eventuale stato `pending` per l'approvazione dei risultati (da concordare).
9. `GET /api/invites/{token}` e `POST /api/invites/{token}/join` per la pagina inviti, con token opachi, stato invito e approvazione del docente. Dettaglio in [`../QR_SHARING.md`](../QR_SHARING.md).
10. CRUD campi docente (`GET/POST /api/fields`, `PATCH/DELETE /api/fields/{id}`) e aggregato calendario `GET /api/calendar` con conflitti. Dettaglio in [`../FIELDS_AND_CALENDAR.md`](../FIELDS_AND_CALENDAR.md).
11. Metadati delle regole per variante (`config_schema`, `tie_breakers`) per generare i form senza regole hardcoded. Dettaglio in [`../SPORT_RULES_CONFIG.md`](../SPORT_RULES_CONFIG.md).

Nessuna nuova API per il tabellone: usa `source_home`/`source_away`, `winner_team_id` e `champion_team_id` già presenti. Chiediamo solo che restino stabili nel contratto.

## Integrazione con `main`

1. `git fetch` e verifica che `main`/`leo-develop` non abbiano modificato gli stessi file.
2. `git diff f0eedf9..max-develop` — revisione.
3. Eseguire `pytest`, `ruff` e `node --check`.
4. Merge di `max-develop` in `main` (o cherry-pick dei commit) solo dopo la review.
5. Conflitti attesi solo in `static/app.js` e `static/styles.css`; non toccare i file backend del Team A.
6. Dopo il merge: verificare dashboard, QR da LAN, drag & drop con mouse/touch/tastiera, mobile.

## Cose da non perdere

- Il QR usa `location.origin`: da `localhost` non è raggiungibile dal telefono, e il modale lo segnala.
- La libreria QR è locale e MIT: se si aggiorna, aggiornare anche `static/vendor/README.md`.
- Gli asset sono a `?v=0.8.0` con `no-cache`; se si cambia la versione app, allineare `index.html` e i test.
- Il riordino nel wizard è end-to-end; il riordino di un torneo esistente resta in attesa dell'API.
- Le "prossime partite" fanno una chiamata per torneo gestito: accettabile in LAN, da sostituire con l'aggregato quando disponibile.
- L'import studenti in blocco è **sequenziale** e non atomico: usa l'API di aggiunta singola e lo dichiara nella UI. Studenti non assegnati, spostamento tra squadre e import Excel attendono il Team A.
- L'ordine delle squadre è **solo di visualizzazione**: non tocca classifica o seeding. `teamOrderAdapter.ready` è `false` finché il Team A non espone `PATCH /teams/order`; fino ad allora l'ordine resta in anteprima locale e al reload torna quello del server.
- Le proposte di risultato hanno `resultProposalsAdapter.ready: false`: la scheda “Da verificare” è visibile ma in attesa API, il pulsante studente è nascosto e nessun salvataggio viene simulato. Le azioni approva/respingi/correggi ricaricano il torneo dal server.
- Condivisione QR: download in SVG, stampa via `#print-sheet` + `body.printing`, condivisione con `navigator.share` e fallback copia. Tutto client-side, nessun servizio esterno.
- Pagina inviti: `/?invite=<token>` e `#/join/<token>`. Con `inviteAdapter.ready: false` mostra l'anteprima reale del torneo tramite `GET /api/public/{token}` e disabilita l'adesione: nessuna iscrizione finta, nessun token in `localStorage`.
- Il QR contiene `location.origin`: da `localhost` non è raggiungibile dal telefono.
- Calendario: `calendarAdapter.ready: false` aggrega un dettaglio per torneo (N+1) e rileva solo conflitti campo/squadra visibili. Sono dichiarati come anteprima client; il server resta autorevole.
- Campi: `fieldsAdapter.ready: false`. La modale si apre in anteprima e il submit blocca il salvataggio ("Nessun dato è stato inviato"). I “campi citati” derivano dai `location` reali degli incontri.
- Programmazione partita: il conflitto `409` viene mostrato come “Conflitto di calendario: …” dentro la modale, senza forzare il salvataggio. Il campo resta un testo con suggerimenti (`datalist`), compatibile con il contratto attuale.
- Regole sport: wizard e modifica usano lo stesso `ruleFieldsetHtml`. Senza `config_schema` i campi modificabili sono solo quelli di `TournamentInput`; durata, tempi, set e pareggio sono mostrati in sola lettura da `variant.rules`. Gli avvisi live non sostituiscono il backend: `409`/`422` restano visibili e bloccano il salvataggio.
- Tornei già avviati: la modifica non invia campi strutturali (solo nome e descrizione) e mostra il banner «Torneo già iniziato». Non si cerca di aggirare il `409` del backend.
- Tabellone: geometria e linee vivono in `static/bracket-layout.js` (UMD, testabile con Node). Le relazioni vengono da `source_home`/`source_away`; la colonna Campione usa `champion_team_id`. Le proposte non approvate non modificano `matches` e quindi non fanno avanzare nessuno.
- Test tabellone: `test_bracket_layout.py` copre 4/8/16 squadre, BYE (6 e 5 squadre), incontri incompleti e invarianza all’ordine dell’array; skip automatico se Node non è installato.

## Aggiornare il registro

A ogni nuovo commit del Team B aggiungere una riga con hash, data, modifica, file, dipendenze API e numero di test. Il comando per rigenerare l'elenco:

```bash
git log f0eedf9..max-develop --format="%h|%ad|%s" --date=format:"%d/%m/%Y %H:%M"
```
