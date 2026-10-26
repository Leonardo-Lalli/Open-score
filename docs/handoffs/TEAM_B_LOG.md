# Registro Team B → Team A

> Registro cronologico delle modifiche del Team B sul branch `max-develop`, per rendere immediata l'integrazione con il Team A e con `main`.
> Base: `main` @ `f0eedf9` · Branch: `max-develop` · Ultimo aggiornamento: 26 ottobre 2026.

## Come usare questo file

- **Team A**: leggi la tabella commit e la sezione "API richieste"; i file toccati sono solo frontend, documentazione e test UI.
- **Team B**: aggiungi una riga a ogni commit e aggiorna "Stato corrente".
- **Integrazione**: `git log f0eedf9..max-develop` e `git diff f0eedf9..max-develop` sono la fonte autorevole.

## Stato corrente

- Branch: `max-develop` (HEAD `1ce99bd`), working tree pulito.
- Base: `f0eedf9` (`main` / `origin/main`).
- Backend, migrazioni, modelli e contratti API: **non modificati**.
- Suite: **197 passed** (warning Starlette/httpx del TestClient, innocuo).
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

## File toccati da `f0eedf9`

- SPA: `torneo-lab/static/app.js`, `index.html`, `styles.css`.
- Vendor: `torneo-lab/static/vendor/qrcode.js` (+ `README.md` di provenienza e licenza MIT).
- Test UI: `torneo-lab/tests/test_static_ui.py`.
- Documentazione: `docs/design-system.md`, `docs/PROFESSOR_DASHBOARD.md`, `docs/STUDENT_DASHBOARD.md`, `docs/STUDENT_MANAGEMENT.md`, `docs/DRAG_DROP_ORDERING.md`, `docs/handoffs/FRONTEND_TO_BACKEND.md`, questo registro.

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

## Aggiornare il registro

A ogni nuovo commit del Team B aggiungere una riga con hash, data, modifica, file, dipendenze API e numero di test. Il comando per rigenerare l'elenco:

```bash
git log f0eedf9..max-develop --format="%h|%ad|%s" --date=format:"%d/%m/%Y %H:%M"
```
