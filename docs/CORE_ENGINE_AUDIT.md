# Audit core engine — incremento A0/A1

> Snapshot dell'audit iniziale al commit `4e15385`. L'utente ha successivamente
> richiesto di proseguire in locale senza push. Stato attuale e implementazione
> sono nel [report 0.3](CORE_ENGINE_REPORT.md), nella matrice e nel contratto aggiornati.

Data: 26 ottobre 2026. Questa analisi aggiorna il perimetro backend rispetto
all'[audit dello starter](AUDIT.md), che resta una registrazione storica.

## Stato Git verificato

- Repository: `https://github.com/Leonardo-Lalli/Open-score.git`, remote `origin`.
- Branch corrente: **`leo-develop`**, richiesto dall'utente; non creare o usare
  `feature/core-engine` per questo lavoro.
- Baseline: `b541824fbfaf96f43d67c3d1e2f17b53ae1b4c54`,
  `Record successful GitHub Actions verification`.
- `main`, `leo-develop` e il riferimento locale `origin/main` partono dallo stesso
  commit. `origin/HEAD` punta a `origin/main`.
- Altri branch locali: `ls`. Nessun `feature/ui-experience` nei riferimenti
  presenti. Nessun fetch eseguito: non è una verifica dei branch remoti attuali.
- Working tree iniziale pulita. Nessun reset, merge, push, deploy o modifica al
  branch del compagno. Nessuna modifica a UI, README principale o workflow.

## Documenti letti e riconciliazione

Tutti i 14 file Markdown tracciati della baseline sono stati letti; nessun MDX
o AGENTS.md rilevato nel repository, né AGENTS.md nelle directory superiori
controllate. Sono state lette anche le istruzioni allegate dall'utente.

| Documento | Uso nell'audit / discrepanza rispetto alla nuova richiesta |
| --- | --- |
| `README.md`, `torneo-lab/README.md` | Avvio, demo locale e limiti; non modificati perché condivisi col Team B |
| `docs/AUDIT.md` | Confronto storico dello ZIP; non è un audit del backend multiutente |
| `docs/API.md` | Route effettive `/api`; manca un contratto versionato condiviso |
| `docs/ARCHITECTURE.md` | FastAPI, servizi, motore puro, SQLite e statici; rispecchia il codice |
| `docs/DATABASE.md` | Schema 2, lock, audit, backup a server fermo; niente utenti/rose/inviti |
| `docs/DECISIONS.md` | Decisioni demo del 24 ottobre, non un veto alla nuova piattaforma richiesta |
| `docs/DEVELOPMENT_PLAN.md` | Account e produzione rimandati nella vecchia consegna; ora requisiti del nuovo percorso |
| `docs/FEATURE_MATRIX.md` | Copertura demo, riferimenti storici E2E; non equivale ai requisiti core engine |
| `docs/FUNCTIONAL_SPECS.md` | Formati e dati futuri distinti da quelli implementati |
| `docs/CHANGELOG.md` | Cronologia 0.2, senza attribuire nuovi completamenti alla baseline |
| `docs/PROPOSTA_PROGETTO.md` | Bozza storica, incluse tecnologie candidate; il codice attuale usa Python, non Next.js |
| `docs/REFERENCE_ANALYSIS.md` | Provenienza fixture e limiti delle inferenze su Score7; nessuna dipendenza remota |
| `docs/TEST_REPORT.md` | 85 test storici e verifica Actions del commit `234273f`; riverificati localmente, nessuna nuova esecuzione CI remota dichiarata |

Non sono state consultate nuovamente le pagine esterne citate nei documenti:
questo audit verifica il repository, non regolamenti sportivi o servizi di hosting.

## Architettura e proprietà

| Modulo / area | Responsabilità effettiva | Proprietà per i prossimi incrementi |
| --- | --- | --- |
| `torneo-lab/app.py` | Factory FastAPI, route, middleware, CSV, statici | Backend; preservare le route della UI |
| `schemas.py` | Input Pydantic e validazioni | Backend |
| `services.py` | Creazione, generazione, risultati, qualificazioni, programmazione | Backend |
| `engine.py` | Girone, knockout, seeding, classifica | Backend; riutilizzare gli algoritmi testati |
| `db.py`, `migrations/*.sql` | SQLite, schema versionato e transazioni | Backend; mantenere dati e preparare migrazioni additive |
| `demo.py`, `fixtures/score7_sample.json` | Quattro esempi idempotenti e provenienza del campione | Backend, solo dati sintetici nei test |
| `tests/`, `requirements*.txt`, `pytest.ini` | Suite e dipendenze | Backend |
| `static/index.html`, `static/app.js`, `static/styles.css`, `static/mark.svg` | Frontend senza build | Team B; letti, non modificati |
| README principale / eventuale Pages | Presentazione e pubblicazione UI | Team B / condivisi, non modificati |
| `.github/workflows/tests.yml` | Test Python 3.11/3.14 su Linux | CI backend già presente, non richiede un duplicato |

I moduli sono già separati: non serve estrarre HTML da un monolite o introdurre
React, ORM o un database diverso per iniziare. Non è presente un sito GitHub Pages
né un workflow Pages nella baseline; non crearli come parte del backend.

## Flussi ricostruiti dal codice

**Creazione:** wizard → `POST /api/tournaments` salva torneo, token pubblico e
squadre in transazione → `POST .../generate` crea fase/gironi/incontri → GET
dettaglio. La bozza rimane salvata se la generazione fallisce.

**Partecipanti:** record `teams`, anche con `participant_kind=individual`; non
sono account o studenti. Aggiunta/rimozione solo prima della generazione,
rinomina anche dopo. Ordine ID crescente usato anche come input iniziale del
motore; non esiste un ordine visuale separato. Nomi unici tramite `casefold()`.

**Risultati:** PATCH con `version` aggiorna subito il risultato. `BEGIN IMMEDIATE`
serializza lettura/controllo/scrittura. Il servizio propaga il vincitore,
ricostruisce le qualificazioni quando necessario e registra audit. Non esistono
proposte, revisore o identità dell'autore; questi dati non possono essere
ricostruiti retroattivamente dai log attuali.

**Motori:** metodo del cerchio per 2–32 squadre, una/due andate; knockout con
prossima potenza di due, BYE, riferimenti tra match e avanzamenti. `groups`
distribuisce squadre in gruppi uguali e promuove prime 1/2 solo dopo tutti i
risultati. Classifiche derivate dai punteggi salvati, BYE esclusi.

**Programmazione:** timestamp con offset → UTC, campo testuale, durata in minuti.
Controlli solo tra incontri dello stesso torneo, con squadre già note e
dipendenze dirette già pianificate. Nessun inventario campi o sede.

**Consultazione:** tutti gli endpoint organizzatore sono anonimi. Il token pubblico
sceglie una proiezione senza audit e due metadati; non protegge gli endpoint
amministrativi. La UI nasconde i controlli nella vista spettatore, non autentica.

## Persistenza verificata

SQLite configurato da `TORNEO_DB_PATH`, default `data/open_score.sqlite3`.
Tabelle: tournaments, teams, stages, groups, matches, audit_logs. Due migrazioni
SQL, `PRAGMA user_version=2`, FK per connessione, indici, unicità e CHECK.
La migrazione 2 preserva gli incontri e rende i loro ID non riutilizzabili.
Le altre PK non usano AUTOINCREMENT: non promettere ID non riciclati dopo future
cancellazioni senza una migrazione. Classifiche e riepiloghi sono derivati.

La suite riapre un'app sullo stesso database e controlla persistenza e migrazione
1→2. Non è stata eseguita una prova di ripristino di un backup reale o una
migrazione PostgreSQL. Database non versionato non vuoto: errore esplicito;
nessuna importazione legacy automatica. Nessun database utente cancellato.

## Rischi e lacune ordinate per priorità

| Priorità | Evidenza nel codice | Intervento successivo |
| --- | --- | --- |
| P0 prima di hosting | Nessun login, owner o isolamento per professore/scuola | Account, sessioni, organizzazioni minime, autorizzazioni e migrazione esplicita dei tornei esistenti |
| P0 prima di studenti reali | Pubblico restituisce nomi e descrizione; nessuna policy di pubblicazione | Proiezioni per ruolo e whitelist pubblica, revoca/pubblicazione |
| P1 | Risultato diretto unico in `matches`, audit senza autore | Proposte persistenti distinte, revisione atomica, risultato ufficiale e audit attribuibile |
| P1 | Nessuna rosa, membership, iscrizione, capienza o ordine | Entità e API separate; ordine senza effetti sul seeding |
| P1 | `sport` è solo una enum, stesso validatore 0–999 per tutti | Regole/preset sportivi veri e risultato a set; niente sport segnaposto |
| P1 | Calendario confronta solo `games(db, tid)` | Campi/sedi per contesto e conflitti tra tornei dello stesso contesto |
| P1 | `response_model` assente; errori di dominio non descritti in OpenAPI | Tipizzare risposte in incremento compatibile dopo l'accordo |
| P2 | Inizializzazione eseguita all'importazione di `app.py` | Separare lifecycle prima del deployment; esportatore attuale isola il DB |
| P2 | `with sqlite3.connect` in initialize gestisce commit ma non chiude esplicitamente | Chiudere esplicitamente la connessione; il generatore forza la raccolta prima di rimuovere il DB temporaneo su Windows |
| P2 | Elenco tornei ricalcola dettagli/classifiche più volte, nessuna paginazione | Query aggregate e paginazione V1 quando i dati crescono |
| P2 | SQLite e migrazioni specifiche, nessun runbook produzione | Backup/restore verificati, deployment e rollback; PostgreSQL solo con migrazione dedicata |

I limiti di sicurezza non sono mitigati da Host/Origin, dal token di lettura
o dalla sola presenza di foreign key. Il backend resta una demo locale.

## Test effettivamente eseguiti

Baseline: **85 passed, 1 warning**, 5.66 s, Windows e Python 3.14.3.
Dipendenze presenti nell'ambiente locale: FastAPI 0.162.0, Pydantic 2.14.1,
Starlette 1.9.0, Uvicorn 0.54.0, pytest 9.1.1, httpx 0.28.1.
Comando, dalla cartella `torneo-lab`: `.venv\Scripts\python.exe -m pytest -q`.

Il primo tentativo sandbox è fallito nella creazione delle directory temporanee
di pytest, prima delle verifiche API. Il comando autorizzato fuori dal sandbox
ha eseguito l'intera suite. Il warning Starlette segnala la deprecazione di
httpx nel TestClient. Non è un errore funzionale.

Copertura effettiva: gironi, knockout 2–32/BYE, multifase 16 squadre,
correzioni e invalidazioni, concorrenza risultati, migrazioni e riapertura DB,
validazioni, CSV, controllo Host/Origin e proiezione spettatore.
Nessun test attuale dimostra ruoli, studenti, inviti o regole a set.
La prova browser riportata nel vecchio report non è stata ripetuta qui.

Verifica finale A1: **87 passed, 1 warning**, 14.50 s, stesso ambiente.
I due nuovi test controllano l'uguaglianza del contratto con OpenAPI del server
e l'esecuzione isolata dell'esportatore, senza aprire o modificare il database
configurato dall'utente. Anche `scripts/export_openapi.py --check` è passato.

## Incremento consegnato e passo successivo

A0: audit e [matrice backend](CORE_ENGINE_MATRIX.md).
A1: [contratto disponibile e proposta V1](contracts/API_V1.md), snapshot OpenAPI,
esportatore isolato, controllo automatico e [handoff](handoffs/BACKEND_TO_FRONTEND.md).
Nessuna migrazione o modifica al comportamento applicativo in questo incremento.

L'allegato richiede che il contratto sia revisionato da entrambi e integrato in
`main` prima dei grandi cambiamenti incompatibili. Preparare questa PR di
coordinamento e attendere tale revisione; non interpretarla come già ottenuta.
Il push richiede inoltre autorizzazione esplicita. La
[bozza PR](handoffs/CORE_ENGINE_CONTRACT_PR.md) è pronta localmente, non aperta su GitHub.

Ordine proposto dopo la revisione: A2 account/isolamento e migrazione conservativa;
A3 studenti/squadre/ordine; A4 proposte e approvazioni; A5 inviti/pubblicazione;
A6 campi/calendario; A7 regole/preset e set; A8 arricchimento bracket/statistiche;
A9 test, documentazione database, `docs/DEPLOYMENT_BACKEND.md` e report conclusivo.
Riutilizzare motori e persistenza già verificati. La scelta effettiva di hosting
Aruba richiede i dettagli del servizio: il solo dominio non identifica un server.
