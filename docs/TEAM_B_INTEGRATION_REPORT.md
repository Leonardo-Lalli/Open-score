# Integrazione Team B su leo-develop

26 ottobre 2026 · app 0.9.0 · SQLite schema 8.

Checkpoint `7f35db6`, precedente al merge locale di `origin/max-develop`
@ `0896096365bc98aa797eb00a370925f6eb4928f1`. Nessun push, PR, deploy o DNS.
Frontend, sito, asset e script di deployment del Team B sono inclusi.
Gli script di deployment non sono stati eseguiti. I handoff originali del Team B
sono conservati senza modifiche; questo report risponde alle loro richieste.

## Risposte al handoff

| Richiesta | Implementazione |
| --- | --- |
| Riordino squadre | PATCH `/api/tournaments/{id}/teams/order`, `{team_ids,version}`. Usa order_version; non cambia il seeding. Adapter attivo. |
| Statistiche individuali | PUT `.../matches/{mid}/performances`, `{version,players:[{player_id,points}]}`; GET `.../player-statistics`. Solo dati registrati dal docente per incontri ufficiali numerici, entro il punteggio squadra. Nessun dato dedotto. UI dedicata ancora futura. |
| Import massivo | POST `.../teams/{team_id}/players/import`, `{rows:[{name,shirt_number}]}` oppure `{csv:"nome,numero\n..."}`. Validazione completa e rollback integrale. Pannello UI collegato. Excel futuro. |
| Disattivazione docente | POST `/api/teachers/{teacher_id}/deactivate` per il proprio account; CLI locale per altri. Revoca entrambe le sessioni e blocca entrambi i login. |
| Paginazione e filtri | V1 paginato; array legacy conservati per compatibilità. Calendario filtrato sul server. |
| Scheduler | Prenotazioni e conflitti verificati; assegnazione automatica futura, come nel handoff. |
| Dashboard | GET `/api/dashboard?mine=1`: upcoming, pending_proposals, student_count, conflicts. Caricamento UI senza N+1 dei dettagli. |
| Approvazione | Proposte separate, approva/rifiuta/correggi versionati, storico attribuito e avanzamento atomico. |
| Identità studente | Account reali, associazione esplicita/invito, visibilità per iscrizione; proposte soltanto per la propria squadra. |
| Archivio e spostamento | GET `/api/tournaments/{id}/students`: students e unassigned; PATCH `.../students/{sid}/team`, `{team_id,version}`. Archivio per torneo e UI di spostamento atomico collegati. Archivio anagrafico scolastico globale futuro. |
| Proposte API | GET `.../proposals?status=pending`; POST `.../matches/{mid}/proposals`, `{version,home_score,away_score}` o `{version,sets:[{home,away}]}`. PATCH `/api/proposals/{pid}`, `{action,version,match_version,reason?,...}`. Il docente vede i conflitti; lo studente solo le proprie proposte. |
| Inviti | GET `/api/invites/{token}`, POST `.../join`; POST `/api/tournaments/{id}/invites` con team_id opzionale, expires_at, max_uses, require_approval. Link `/#/join/{token}`, QR, capienza/scadenza/usi e revisione adesioni collegati alla UI. |
| Campi | GET/POST `/api/fields`, PATCH/DELETE `/api/fields/{id}` con version nelle modifiche. Metadati name/description/venue/sports/active. `availability` è una nota; `availability_intervals` contiene i vincoli effettivi. |
| Calendario | GET `/api/calendar` con filtri tournament/team/day/field/status, eventi e conflitti calcolati sul server. |
| config_schema | Catalogo con parametri del torneo accettati e tie-breaker. Le regole della variante restano autorevoli sul server. |

## Account, dati e visibilità

Il frontend continua a usare `/api`; `/api/v1` conserva il contratto autenticato.
Gli input e le risposte effettive sono in [OpenAPI](contracts/openapi.yaml).
Gli adapter per ordine, proposte, inviti, campi e calendario sono attivi.
Un solo client HTTP e nessun calcolo delle classifiche nel browser. CSS, font,
componenti, layout e sito Pages del Team B conservati.

Login docente `/api/auth/login`; registrazione/login studente `/api/v1/auth/register`
e `/api/v1/auth/login`. GET `/api/auth/session` distingue docente, studente e anonimo.
Il client acquisisce X-CSRF-Token da `/api/v1/auth/csrf` prima delle scritture.
Cookie HttpOnly distinti: `open_score_session` e `open_score_platform_session`,
Secure in service. Logout, reset password e disattivazione revocano le sessioni
server; il replay del cookie firmato non riapre l'accesso. La registrazione non crea docenti.

Gli ID di teachers e users sono collegati con teacher_user_links, senza assumere
uguaglianza. Le rose team_players e i profili students sono sincronizzati nella
stessa transazione. PATCH `.../students/{sid}`, `{user_id,version}`, permette al
docente di collegare esplicitamente un alias a un account studente. Non riassegna
un account già associato a un altro profilo.

Migrazione schema 8 da Team A 4 e Team B 7 con backup consistente preventivo
`*.pre-v8-*.sqlite3`, transazione e verifica foreign key. Preservati risultati,
proprietari e ordine manuale. platform_variant_id conserva il namespace Team A;
variant_id resta l'ID numerico del catalogo Team B. Una modifica strutturale via
catalogo rende autorevole quel regolamento; una semplice rinomina conserva le regole.

I tornei creati dalla UI mantengono l'impostazione LAN pubblicata del Team B,
ora revocabile da Condividi; quelli V1 sono privati inizialmente. Elenchi,
dettaglio, calendario, CSV e link pubblici rispettano la visibilità. Rose nominative,
audit, proprietari e motivazioni private non sono esposti nella vista spettatore.
In service il frontend rimane disponibile, con HTTPS e host espliciti.

Una correzione del risultato invalida le statistiche individuali collegate.
Le statistiche individuali dipendono dalla rosa attuale; eliminare una voce di
rosa elimina le sue prestazioni. L'archiviazione delle prestazioni indipendente
dalla rosa e la relativa UI richiedono un incremento dedicato.

## Avvio locale

Da `torneo-lab`, nell'ambiente esistente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Aprire `http://127.0.0.1:8000`. Gli account docente preesistenti sono conservati.
Non viene inserito un dataset dimostrativo. Il database reale viene migrato solo
quando si avvia l'app contro quel percorso, con backup automatico.

Creazione docente con password chiesta in modo protetto:

```powershell
.\.venv\Scripts\python.exe manage.py create-teacher --email docente@example.test --display-name Docente --organization "Scuola"
```

Per disattivare un altro account, l'amministratore locale può usare
`manage.py deactivate-teacher EMAIL`. Gli esempi non sono credenziali preinstallate.
Per l'uso LAN e il servizio persistente vedere DEPLOY.md; qui non sono stati installati servizi.

## Verifica e attività future

Verifica locale conclusa su Python 3.14: **311 test pytest passati** in 265 secondi,
Ruff pulito, JavaScript `node --check`, `pip check`, confronto OpenAPI e parsing
degli script PowerShell superati. Un avviso di deprecazione del client di test
Starlette/httpx rimane nella suite; nessun test fallito.
Browser reale su database isolato con identità sintetiche: login, wizard,
generazione tabellone, archivio/spostamento studente, invito con QR e creazione
campo verificati. Server di collaudo fermato al termine. Nessun database di test
versionato, nessuna modifica ai dati reali durante le prove.

Restano attività future dichiarate: scheduler automatico, import Excel, archivio
anagrafico globale, UI delle statistiche individuali e verifica dei regolamenti
con il professore. Non sono condizioni necessarie per provare localmente i flussi
integrati. La pubblicazione remota rimane da autorizzare separatamente.
