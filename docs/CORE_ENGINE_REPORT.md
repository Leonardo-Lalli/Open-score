# Report backend 0.3 — Prompt A

26 ottobre 2026. Branch **leo-develop**; baseline precedente
`4e15385` (audit/contratto), baseline demo `b541824`.
Commit dell'implementazione verificata: **`00a4d20`**, `feat(core): add authenticated tournament backend`.
L'utente ha richiesto espressamente di proseguire l'implementazione in locale,
senza push. Nessuna revisione del Team B, integrazione in main o pubblicazione
è stata simulata. Nessun altro branch modificato.

## Stato iniziale e Markdown

La demo 0.2 aveva FastAPI/SQLite, gironi/knockout/multifase, risultati diretti,
calendario testuale, CSV e UI statica. Nessun account, studente, proposta,
invito o campo come risorsa. Audit e prima proposta erano già nel commit
`4e15385`: [audit](CORE_ENGINE_AUDIT.md). I 14 Markdown della baseline e gli
ulteriori documenti A0/A1 sono stati analizzati; il codice reale prevale sulle
vecchie roadmap. Il prompt aggiornato è stato riletto prima dell'implementazione.

## Funzioni realizzate

- API additive `/api/v1`, input rigorosi e risposte tipizzate in OpenAPI.
- Sessioni server revocabili, password con hash salato, CSRF, rate limit,
  professori creati da CLI, registrazione solo studenti.
- Ownership e isolamento per professore/contesto, collaborazione esplicita,
  partecipazione studenti e separazione delle proiezioni pubbliche.
- Squadre, capienza, archiviazione, studenti/alias/account, assegnazioni e
  spostamenti, ricerca/filtri, iscrizioni e approvazioni, ordine persistente
  con versione di collezione indipendente dal seeding.
- Proposte discordanti conservate, revisione/approvazione/rifiuto/correzione,
  risultato ufficiale, audit attribuibile e transazione su classifiche,
  invalidazioni e progressione. Storico conservato anche dopo ricostruzione finale.
- Inviti con token hash, scadenza, revoca, usi e capienza; richieste pending
  o auto-iscrizione verificata, nessuna attribuzione amministrativa dal QR.
- Pubblicazione revocabile con URL JSON stabile e whitelist senza rose/email/audit.
- Campi/sedi per professore, disponibilità e compatibilità sportiva; calendario
  UTC/IANA con conflitti del campo tra tornei e controllo delle squadre note.
- Preset scolastici calcio 11/7/5, basket standard, pallavolo indoor con set,
  regole custom, spareggio decisivo, tavolino e penalità di classifica esplicite.
- Bracket con sorgenti e next slot, statistiche dai soli risultati ufficiali.
- Migrazioni schema 4, backup preventivo, assegnazione legacy esplicita,
  backup/restore con integrità verificata e riapertura dell'app sulla copia.

## Architettura e file

Conservati FastAPI, sqlite3, engine e servizi. Nuovi moduli: auth, sports,
v1_schemas/v1_dto, v1_api, v1_domain, v1_results, v1_resources; manage.py per
amministrazione locale. Modifiche limitate al backend, test, dipendenza tzdata,
migrazioni e documentazione. Nessuna modifica a static/, README principale o
workflow Pages. Il workflow tests.yml esistente include automaticamente le nuove
suite e lo snapshot OpenAPI; nessun required check cambiato.

## Compatibilità e migrazioni

La UI attuale funziona ancora in demo su tornei non assegnati. Le API legacy
non possono raggiungere i tornei V1. Service richiede host espliciti e origin
HTTPS e disabilita le route anonime legacy. Il Team B deve integrare UI V1:
login, cookie/CSRF, studenti, review, inviti/join e pagina pubblica.

Migrazioni 003/004 additive, backup prima degli aggiornamenti. Nessuna perdita
intenzionale o reset del DB. Owner nullo per vecchi tornei; claim da CLI dopo
scelta del professore e variante. Risultati legacy senza approvatore inventato.
Per rollback a schema 2 serve la copia pre-migrazione in un nuovo percorso,
non una down-migration distruttiva. [Database](DATABASE.md).

## Test effettivi

**Verifica finale: 132 passed, 1 warning, 103.27 secondi.** Include i precedenti
87 test e 45 nuove verifiche di integrazione/regole sportive. Passati anche
`scripts/export_openapi.py --check`, controllo tabelle/link dei documenti e
`git diff --check`. CLI `manage.py --help` verificata.

Copertura nuova: 401/403/404, registrazione senza escalation di ruolo, CSRF,
logout/scadenza e rate limit; isolamento proprietari e bypass legacy; CRUD
squadre, ordine concorrente indipendente dal seed, membership/capienza;
proposte discordanti, review/correzione/clear, approvazione concorrente,
storia dopo ricostruzione multifase; inviti con ultimo uso/posto concorrente,
pubblicazione/revoca/whitelist; campi tra tornei, fusi/disponibilità e conflitti;
set, spareggi, tavolino/penalità e correzione rally; backup/ripristino e
migrazione conservativa. Baseline intermedia: 87 passati; primi incrementi
nuovi: 42 passati, poi 24 API con DTO, prima dell'ultima suite completa.

Comando: `.venv\Scripts\python.exe -m pytest -q` dalla cartella torneo-lab,
Windows/Python 3.14.3. Test con DB SQLite reali e identità sintetiche, nessun mock
usato per dichiarare implementazione. Un warning già presente riguarda la
deprecazione Starlette/httpx. Il sandbox blocca cartelle temporanee/rete: i test
sono eseguiti con autorizzazione e tzdata è stato installato nell'ambiente del progetto.
Nessun nuovo run CI remoto dichiarato, né nuova verifica end-to-end del frontend.

## Limiti e attività rimaste

UI/QR non integrati; verifica automatica dell'email e recupero password via email,
import massivo, cancellazione
definitiva tornei/studenti e CRUD completo sedi non implementati. Regole bloccate
dopo generazione; penalità bloccate dopo qualificazione multifase finché non c'è
una procedura esplicita di revisione delle fasi. Scheduler e altre discipline
assenti. Preset scolastici con criteri dichiarati, non conformità federale completa.

Le pagine a offset non garantiscono snapshot durante mutazioni; rileggere.
Le prenotazioni verificano squadre note e dipendenze dirette; non costruiscono
un calendario globale ottimizzato. Il servizio è predisposto, ma il deployment
reale resta da scegliere/verificare; nessun adapter PostgreSQL. Il prodotto Aruba
del professore è sconosciuto. Il recupero account e i requisiti operativi sui dati
reali vanno concordati prima del servizio scolastico pubblico.

## Avvio e integrazione

[Guida locale/deployment](DEPLOYMENT_BACKEND.md),
[contratto](contracts/API_V1.md),
[handoff al Team B](handoffs/BACKEND_TO_FRONTEND.md),
[matrice](CORE_ENGINE_MATRIX.md).

Per avviare la demo: installare requirements-dev nell'ambiente esistente, poi
`python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000`. Per provare V1:
creare professore con manage.py, aprire /docs, ottenere CSRF e fare login.
Le nuove API sono testabili senza modificare la grafica.

Non sono stati osservati conflitti locali; il lavoro remoto del Team B non è
stato recuperato, quindi non si garantisce assenza di conflitti futuri. Il contratto
implementato rende esplicite le differenze dalla proposta: catalogo varianti piatto,
offset numerico, my-participation/penalty, DTO storico review e URL pubblica JSON.
Richiedono revisione congiunta prima del merge. Nessuna PR remota è stata creata
poiché il push è vietato dall'utente.

## Descrizione PR pronta per futura revisione

Titolo: `feat(core): add authenticated tournament backend`.

La demo consentiva scritture anonime e non distingueva risultati proposti da
quelli ufficiali. Questo incremento aggiunge API V1 protette per professori e
studenti, risultati da revisionare, iscrizioni/inviti, campi e regole sportive,
riutilizzando i motori esistenti. In service le route demo sono disabilitate;
in demo il frontend precedente resta disponibile su tornei non assegnati.

Schema 4 con migrazioni additive/backup, proprietà legacy assegnata solo da CLI,
audit e backup/restore verificabili. OpenAPI e handoff aggiornati. Verificare
contratto e integrazione Team B prima del merge; UI e deploy non inclusi.
Validazione: 132 test locali passati, un warning di deprecazione; OpenAPI
sincronizzato. Nessuna esecuzione CI remota dichiarata.
