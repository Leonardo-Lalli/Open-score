# Contratto API condiviso — proposta V1

Data: 26 ottobre 2026. Branch backend: `leo-develop`, scelto dall'utente al posto di
`feature/core-engine`. Commit di partenza: `b541824fbfaf96f43d67c3d1e2f17b53ae1b4c54`.

**Stato: proposta da revisionare con entrambi gli sviluppatori e integrare in `main`.**
Questo documento distingue il contratto **disponibile della demo 0.2** dalla
**proposta V1 non implementata**. Il nome del documento non attiva `/api/v1`.
Non esistono ancora login, ruoli, studenti, inviti o approvazioni.

## 1. Fonte autorevole e sincronizzazione

Le route in `torneo-lab/app.py`, gli input in `schemas.py` e le regole in
`services.py` definiscono il comportamento attuale. [openapi.yaml](openapi.yaml)
è generato da `app.openapi()`: contiene soltanto le route esistenti, in sintassi
JSON, valida anche come YAML 1.2, senza una dipendenza aggiuntiva di serializzazione.

Dalla cartella `torneo-lab`, con le dipendenze di sviluppo installate:

```powershell
python scripts/export_openapi.py
python scripts/export_openapi.py --check
python -m pytest -q
```

L'esportatore usa un database temporaneo e non il database configurato dall'utente.
`--check` non scrive lo snapshot; fallisce se diverge. Il test
`tests/test_contract.py` confronta il documento con `/openapi.json` e viene già
eseguito dal workflow esistente. Rigenerare lo snapshot dopo modifiche agli input
o alle route; aggiornare questo documento per le regole e le risposte.

**Limite rilevato:** le route attuali non dichiarano `response_model`. OpenAPI
lascia generici i corpi di successo e non elenca tutti gli errori di dominio o
del middleware. Le sezioni 3–5 documentano questi dettagli dal codice; non si può
ancora generare un client con tipi di risposta completi dal solo OpenAPI.
Gli endpoint proposti nella sezione 6 non compaiono nello snapshot.

## 2. Convenzioni attuali e convenzioni proposte

| Aspetto | Disponibile nella demo | Proposta V1, da approvare |
| --- | --- | --- |
| Base URL | `http://127.0.0.1:8000/api` | `/api/v1`, stesso dominio della UI o reverse proxy |
| Versione | Applicazione `0.2.0`, prefisso non versionato | Aggiunta di route versionate; nessuna rinomina silenziosa delle vecchie |
| ID | Interi JSON locali; `source_id` solo provenienza | Conservare ID interi delle risorse esistenti, opachi al client; nessuna conversione a UUID implicita |
| Nomi JSON | `snake_case` | Mantenere `snake_case`, anche `ordered_team_ids` |
| Date | ISO 8601 con offset; scrittura calendario normalizzata UTC | UTC nelle risposte; `timezone` IANA separata per la programmazione |
| Assenza | Punteggi/avversari/orari `null`; liste vuote `[]` | `null` per valore assente; nessuno zero inventato |
| Elenchi | Array completi, nessuna paginazione o filtro server | `{items: [], next_cursor: null}`, `limit` 1–100, default 50; filtri espliciti per risorsa |
| Concorrenza | `version` obbligatoria nei risultati e negli orari | Versioni anche per ordine, membership, revisioni, inviti e risorse modificabili |
| Errori | `detail` stringa o lista Pydantic | Conservare `detail`, aggiungere `code` stabile e `current_version` nei conflitti di versione |
| Autenticazione | Assente; Host/Origin solo difesa locale | Sessione server tramite cookie `HttpOnly`, `Secure` in HTTPS, `SameSite=Lax`; protezione CSRF su tutte le scritture autenticate |
| Autorizzazione | Nessun proprietario/ruolo | Proprietario o collaboratore esplicito; studente partecipante; visitatore solo dati pubblicati |
| Compatibilità | La UI usa `/api` | Mantenere forme correnti; migrazione alla sessione concordata con Team B prima dell'esposizione online |

Proposta: cookie `open_score_session`; `GET /auth/csrf` restituisce il token da
inviare nell'header `X-CSRF-Token` anche al login. CORS non abilitato implicitamente:
un frontend GitHub Pages su altro dominio richiede una decisione esplicita su
domini, cookie e CORS prima dell'integrazione. La registrazione pubblica, se
abilitata, crea solo studenti; il primo professore si crea con procedura locale
amministrativa, mai con un ruolo privilegiato scelto nel payload pubblico.

Prima della V1, i test degli account e dell'isolamento sono obbligatori. La demo
non può diventare un servizio multiutente conservando API amministrative anonime.
Per i tornei esistenti manca un proprietario: l'assegnazione richiederà una
migrazione esplicita del professore, con backup e report, non l'appropriazione
da parte del primo utente registrato.

## 3. Endpoint disponibili oggi

`tid`, `mid`, `team_id` sono interi. Tutti i corpi di input rifiutano campi extra.
Le operazioni non richiedono credenziali nella demo locale.

| Metodo | Percorso sotto `/api` | Input | Successo |
| --- | --- | --- | --- |
| GET | `/health` | Nessuno | 200 `{status:"ok",version:"0.2.0",mode:"local-demo"}` |
| GET | `/tournaments` | Nessuno; nessun filtro | 200 `TournamentSummary[]` |
| POST | `/tournaments` | `TournamentInput` | 201 `{id: integer}`; bozza, senza incontri |
| GET | `/tournaments/{tid}` | Nessuno | 200 `TournamentDetail` |
| POST | `/tournaments/{tid}/teams` | `{name}` | 201 `{id}`; solo prima della generazione |
| PATCH | `/tournaments/{tid}/teams/{team_id}` | `{name}` | 200 `{ok:true}`; anche dopo generazione |
| DELETE | `/tournaments/{tid}/teams/{team_id}` | Nessuno | 204 senza corpo; solo prima della generazione |
| POST | `/tournaments/{tid}/generate` | Nessuno | 200 `{created: integer}`; include nodi BYE |
| PATCH | `/tournaments/{tid}/matches/{mid}` | `ResultInput` | 200 `ResultMutation` |
| DELETE | `/tournaments/{tid}/matches/{mid}/result` | `ClearInput`, corpo JSON obbligatorio | 200 `ResultMutation` |
| PATCH | `/tournaments/{tid}/matches/{mid}/schedule` | `ScheduleInput` | 200 `{ok:true}` |
| GET | `/tournaments/{tid}/export.csv` | Nessuno | 200 CSV UTF-8 con BOM, attachment `torneo-{tid}.csv` |
| GET | `/public/{token}` | Token URL | 200 dettaglio spettatore, senza audit e due metadati del torneo |
| POST | `/demo` | Nessuno | 200 `{ids: integer[]}`; esempi idempotenti |

`/`, `/public/{token}` (senza `/api`) e `/static/*` servono la UI, non sono API.
`/docs`, `/redoc` e `/openapi.json` sono esposti da FastAPI.

### 3.1 Input e validazioni

`TournamentInput`:

| Campo | Tipo e default | Vincolo |
| --- | --- | --- |
| `name` | string, obbligatorio | Strip, 2–120 caratteri |
| `sport` | string, `Calcio` | `Calcio`, `Calcio a 5`, `Basket`, `Pallamano` |
| `format` | string, `round_robin` | `round_robin`, `knockout`, `groups` |
| `description` | string, `""` | Massimo 1000 caratteri |
| `participant_kind` | string, `team` | `team`, `individual`; non crea persone o rose |
| `win_points` / `draw_points` / `loss_points` | int, `3` / `1` / `0` | Rigorosi, 0–10 |
| `legs` | int, `1` | Rigoroso, 1 o 2; knockout solo 1 |
| `group_count` | int, `2` | Rigoroso, 2–8; usato in `groups` |
| `qualifiers` | int, `2` | Rigoroso, 1 o 2 |
| `random_seed` | int oppure null, `null` | Rigoroso, 0–2147483647; sorteggio knockout |
| `team_names` | string[], `[]` | Max 32, ogni nome strip 1–60, unici con `casefold()` |

La creazione accetta una bozza anche con 0/1 partecipanti. `/generate` impone
2–32 partecipanti. `groups` impone gironi uguali, almeno due squadre per gruppo
e abbastanza squadre per le qualificazioni; questi controlli avvengono alla
generazione. Le regole configurabili oggi sono solo punti e andata/ritorno,
non regolamenti completi dello sport.

`TeamInput`: `name` stringa obbligatoria, strip, 1–60 caratteri.
Duplicati senza distinzione di maiuscole: 409 nelle aggiunte/rinomine;
duplicati in `team_names` alla creazione: 422.

`ResultInput`:

```json
{"home_score":2,"away_score":1,"version":1,"invalidate":false}
```

Punteggi interi rigorosi 0–999, mai booleani, float o stringhe numeriche.
`version` intero rigoroso >=1. `invalidate` booleano, default false; il modello
attuale usa la coercizione boolean Pydantic, non la validazione rigorosa.
Pareggio valido nel girone, 422 nel knockout. BYE/avversari non definiti: 409.
Una scrittura modifica subito il risultato autorevole; non è una proposta.

`ClearInput`: `{version: integer>=1, invalidate: boolean=false}`.
`ScheduleInput`:

```json
{"scheduled_at":"2026-11-03T10:00:00+01:00","location":"Campo A","duration":20,"version":1}
```

`scheduled_at` datetime o null, default null; se presente richiede il fuso.
`location` stringa massimo 80, default `""`, salvata strip e come null se vuota.
`duration` minuti, intero rigoroso 1–240, default 20. `version` obbligatoria.
La chiamata applica i default anche ai campi omessi: inviare solo `version`
cancella orario e campo e imposta durata 20. Non è un PATCH parziale dei soli
campi presenti. Ogni programmazione incrementa la versione dell'incontro.

### 3.2 Esempio di flusso attuale

```http
POST /api/tournaments
Content-Type: application/json

{"name":"Coppa sintetica","sport":"Calcio a 5","format":"knockout","team_names":["Alfa","Beta","Gamma"]}
```

Risposta 201, ad esempio `{"id":1}` su database vuoto. Chiamare
`POST /api/tournaments/1/generate`, poi `GET /api/tournaments/1`.
Selezionare un match `ready`, usare il suo ID e la sua `version` nel PATCH.
Dopo ogni scrittura rileggere il dettaglio: la risposta non contiene la nuova
versione del match e possono essere cambiati più nodi.

## 4. Risposte disponibili

I tipi seguenti descrivono il JSON effettivo; le proprietà non sono nuovi campi.

`TournamentRecord` contiene `id`, tutti i campi di configurazione tranne
`team_names`, più `public_token` (string), `demo_key` (string|null), `created_at`
(timestamp UTC). `TournamentSummary` è questo record più:

```json
{"status":"active","team_count":3,"progress":{"completed":0,"total":2},"champion_team_id":null}
```

L'elenco è ordinato per ID torneo decrescente, senza paginazione. Il totale
include solo incontri già generati senza BYE: nei multifase cresce quando nasce
il knockout, quindi la percentuale non è monotona tra le fasi.

`TournamentDetail`:

| Campo | Tipo / significato |
| --- | --- |
| `tournament` | `TournamentRecord` |
| `teams` | `Team[]`, ordine ID crescente; nessun ordine manuale |
| `matches` | `Match[]`, ordine fase/turno/posizione/ID |
| `groups` | `Group[]`, con classifica di ciascun girone |
| `stages` | `Stage[]`, ordine `ordinal` |
| `standings` | `Standing[]` solo per girone unico, altrimenti `[]` |
| `champion_team_id` | int oppure null, vincitore della finale knockout; null nel girone unico anche concluso |
| `status` | `draft`, `active`, `completed`, derivato |
| `progress` | `{completed: int, total: int}`, esclusi BYE |
| `public` | boolean, indica la proiezione richiesta |
| `audit` | Solo dettaglio organizzatore: ultimi 30 `{id,action,created_at}`, ordine ID decrescente; non include payload |

`Team`: `{id,tournament_id,name,group_id,source_id}`, ultimi due int|null.
`Stage`: `{id,tournament_id,ordinal,kind,source_id}`, `kind` round_robin/knockout,
`ordinal` da 0. `Group`: `{id,stage_id,name,standings: Standing[]}`.

`Match`, esempio sintetico di finale in attesa:

```json
{
  "id":13,"tournament_id":1,"stage_id":2,"group_id":null,
  "round_no":2,"position":0,
  "home_team_id":null,"away_team_id":null,
  "source_home":11,"source_away":12,
  "home_score":null,"away_score":null,"winner_team_id":null,
  "is_bye":0,"version":1,"scheduled_at":null,"location":null,
  "duration":20,"source_id":null,"kind":"knockout","status":"waiting"
}
```

`round_no` parte da 1, `position` da 0; la chiave della posizione è
`(stage_id, round_no, position)`. `is_bye` è un **intero 0/1** nel JSON attuale.
Gli ID degli avversari/vincitore/sorgenti e `group_id` possono essere null.
`source_home` e `source_away` sono ID dei match da cui arriva il vincitore.
Il client disegna già gli archi con questi riferimenti; non esiste `/bracket`.
La V1 proporrà anche lo slot successivo esplicito, senza rimuovere le sorgenti.

`Standing`:

```json
{"team_id":1,"name":"Alfa","played":1,"won":1,"drawn":0,"lost":0,"goals_for":2,"goals_against":1,"goal_difference":1,"points":3}
```

Sono interi; `name` è stringa. L'ordine è punti decrescenti → differenza → fatti
→ nome `casefold()` → ID crescente. I nomi `goals_*` restano anche per Basket
e Pallamano: non rinominarli senza migrazione. Nessuna penalità, scontro diretto,
statistica individuale o qualifica anticipata.

`ResultMutation`: `{ok:true, invalidated: integer, champion_team_id: integer|null}`.
Il numero indica i nodi interessati, anche se senza risultato; un salvataggio
identico non incrementa la versione e restituisce `invalidated:0`.

### 4.1 Pubblico e privacy

`GET /api/public/{token}` usa la stessa struttura senza `audit`, `public_token`
e `demo_key`. Espone ancora nomi dei partecipanti, descrizione, `source_id`,
regole, calendario e ID interni. Non esiste scelta di pubblicazione, scadenza,
revoca o approvazione del link. Un token di lettura non è un invito.
La proiezione corrente non è adeguata automaticamente alle future rose di
studenti: serve una whitelist pubblica dedicata prima di introdurre dati personali.

Il CSV attuale esporta fase, girone, turno, casa, ospite, punteggi, data UTC e
campo; zero è conservato. I testi che iniziano con caratteri formula sono
preceduti da apostrofo. Non richiede autenticazione nella demo.

## 5. Stati, conflitti ed errori attuali

- Match: `waiting` se manca un avversario; `ready` con due avversari senza
  punteggio; `completed` con punteggio; `bye` per il passaggio automatico.
  `scheduled_at` non crea uno stato separato. Un risultato mancante è null.
- Torneo: `draft` senza incontri, `active` dopo generazione, `completed` con
  campione knockout o tutti gli incontri del girone unico completati.
- Gruppi: tutte le partite dei gironi devono finire prima della qualificazione.
  Correggere un girone dopo qualificazione ricostruisce il knockout, con nuovi ID.
- Risultati: una correzione che cambia vincitore può cancellare discendenti e
  relativi orari/campi. Se ci sono risultati dipendenti, oppure finali già create
  da gironi, serve `invalidate:true`. Se il vincitore non cambia, i discendenti
  knockout restano. Lo snapshot è conservato nell'audit.
- Calendario: intervalli `[inizio,fine)`, adiacenza consentita; conflitti di campo
  testuale senza distinzione maiuscole e avversari noti **nel solo torneo**.
  Controllo temporale sulle dipendenze dirette già programmate; nessuna garanzia
  globale, risorsa campo, disponibilità o verifica automatica dei futuri avversari.
- Atomicità: `BEGIN IMMEDIATE` prima della lettura; rollback su errore. La stessa
  versione non permette due risultati concorrenti diversi. Rileggere dopo 409,
  non reinviare automaticamente `invalidate:true`.

| HTTP | Corpo attuale | Casi |
| --- | --- | --- |
| 404 | `{"detail":"Torneo non trovato"}` o altra stringa | Torneo, match/squadra inesistenti o non appartenenti al torneo, token sconosciuto |
| 409 | `{"detail":"Dati cambiati: aggiorna la pagina prima di salvare"}` o altra stringa | Versione obsoleta, duplicati, generazione ripetuta, squadre bloccate, match non pronto, conflitti orari, invalidazione da confermare |
| 422 | `{"detail":"Serve un vincitore..."}` o lista di errori | Regole di dominio oppure validazione Pydantic; lista con `loc`, `msg`, `type` e possibili `input`/`ctx` |
| 403 | Testo `Origine non consentita` | Scrittura con Origin diverso da `request.base_url`; può essere testo non JSON |
| 400 | Testo `Invalid host header` | Host diverso da localhost/127.0.0.1/testserver |
| 405 | Errore framework | Metodo non esposto, inclusa scrittura sul percorso pubblico |

Non sono implementati 401/403 per ruoli. Errori SQLite, lock oltre timeout o
guasti imprevisti non hanno ancora un codice applicativo stabile. Un 404 è una
risorsa assente; array vuoto è una collezione caricata ma vuota; errore di rete è
uno stato client distinto. Non mostrare un successo prima della risposta 2xx.

## 6. Proposta V1 — nessuno degli endpoint seguenti è implementato

Tutti i percorsi seguenti sono **sotto `/api/v1`**, candidati alla revisione.
`T` = professore proprietario/collaboratore autorizzato, `S` = studente con
iscrizione approvata, `A` = utente autenticato, `P` = visitatore pubblico.
Per risorse private fuori dal proprio ambito: 404; utente noto ma ruolo
insufficiente nella risorsa accessibile: 403; sessione assente/scaduta: 401.
Errori V1 proposti: `{detail: string|ValidationError[], code: string}`.

### 6.1 Auth, utenti e contesto

| Metodo / percorso proposto | Accesso | Input → risposta proposta |
| --- | --- | --- |
| GET `/auth/csrf` | P | → 200 `{csrf_token}` legato alla sessione/pre-sessione |
| POST `/auth/register` | P + CSRF | `{email,password,display_name}` → 201 `{user:{id,display_name,role:"student"}}`; email privata; nessun ruolo nel payload |
| POST `/auth/login` | P + CSRF | `{email,password}` → 200 `{user}` e cookie sessione; 401 credenziali non valide; 429 rate limit |
| POST `/auth/logout` | A + CSRF | → 204 e revoca server-side |
| GET `/users/me` | A | → 200 `{id,display_name,role,organization_id}`; mai email nei DTO pubblici |
| GET `/organizations/current` | A | → 200 `{id,name}`; contesto autorizzato, non selezionabile per aggirare isolamento |

Password con hash; nessuna password o token in audit/log. Durata sessioni,
recupero account e parametri di rate limit da definire prima dell'implementazione.
Più organizzazioni sono un'estensione: ogni risorsa futura deve avere ambito e
proprietario verificati anche quando si inizia da un solo professore.

### 6.2 Tornei, squadre, studenti e iscrizioni

| Metodo / percorso proposto | Accesso | Input → risposta proposta |
| --- | --- | --- |
| GET, POST `/tournaments` | T; S solo lettura autorizzata | Lista paginata, filtro `status`; creazione compatibile con input attuale più sport/variante validati → 201 `{id}` |
| GET `/tournaments/{tid}` | T/S | Dettaglio distinto per ruolo; studente senza audit e dati privati altrui |
| PATCH `/tournaments/{tid}` | T | `{version,name?,description?}` → record aggiornato; regole a torneo avviato solo con procedura esplicita |
| GET, POST `/tournaments/{tid}/teams` | T/S GET, T POST | Lista paginata/ricerca `q`; `{name,max_members?}` → squadra |
| PATCH, DELETE `/tournaments/{tid}/teams/{team_id}` | T | Modifica versionata / archiviazione; blocco se compromette incontri già generati |
| PATCH `/tournaments/{tid}/teams/order` | T | `{ordered_team_ids:integer[],version:integer}` → `{ordered_team_ids,version}` |
| GET, POST `/tournaments/{tid}/students` | T | Elenco paginato `q`, `team_id`; `{display_name,user_id?}` → profilo minimale, senza richiesta di dati anagrafici superflui |
| PATCH `/tournaments/{tid}/students/{student_id}/team` | T | `{team_id,version}`, ID intero oppure null → membership aggiornata; null rimuove l'assegnazione |
| POST `/tournaments/{tid}/enrollments` | A studente | `{team_id?,team_version?}` → 201 richiesta `{id,status:"pending"}`; identità dalla sessione |
| GET `/tournaments/{tid}/enrollments` | T; A solo proprie | Lista paginata, filtro `status`; nessuna lista completa esposta agli studenti |
| POST `/tournaments/{tid}/enrollments/{eid}/review` | T | `{decision,version,reason?}`, decision approve/reject → richiesta aggiornata |

Ordine squadre: inviare una permutazione completa delle squadre attive, senza
duplicati né ID estranei. Versione dell'ordine indipendente, aggiornata anche
quando cambia l'insieme delle squadre; vecchia versione → 409 `stale_version`.
Nessuna modifica a seed, gironi, incontri o classifiche. Riordino e spostamento
studenti sono transazioni; capienza ed esclusività della membership si
controllano nella stessa transazione. Iscrizioni duplicate → 409
`already_enrolled`; squadra piena → 409 `team_full`. Nessun ruolo deriva da un ID.
`team_version` è obbligatoria quando si indica una squadra; arriva dal record
squadra e protegge il controllo sulla sua configurazione/capienza. La capienza
si riverifica comunque in transazione. `max_members:null` significa nessun
limite specifico di squadra; un valore intero deve essere positivo.
Import strutturato e cancellazione definitiva degli studenti richiedono una
proposta separata su deduplicazione, conservazione e audit.

### 6.3 Risultati proposti, ufficiali e revisioni

| Metodo / percorso proposto | Accesso | Input → risposta proposta |
| --- | --- | --- |
| POST `/tournaments/{tid}/matches/{mid}/proposals` | S autorizzato alla partita | `{match_version,score}` → 201 `Proposal` |
| GET `/tournaments/{tid}/matches/{mid}/proposals` | T; S solo proprie | Lista paginata, filtro `status` |
| POST `/tournaments/{tid}/matches/{mid}/proposals/{pid}/review` | T | `{decision,proposal_version,match_version,invalidate:false,score?,reason?}` → `{proposal,official_result,match_version,invalidated_match_ids}` |
| GET `/tournaments/{tid}/matches/{mid}/result` | T/S | → 200 `{official_result,match_version}`, risultato ufficiale oppure null |
| PATCH `/tournaments/{tid}/matches/{mid}/result` | T | `{score,match_version,invalidate:false,reason}` → risultato ufficiale e nuova versione |
| DELETE `/tournaments/{tid}/matches/{mid}/result` | T | `{match_version,invalidate:false,reason}` → risultato rimosso e nuova versione |

Schema proposto `Score` discriminato da `type`:

```json
{"type":"points","home":2,"away":1}
```

```json
{"type":"sets","sets":[{"home":25,"away":20},{"home":25,"away":23},{"home":25,"away":22}]}
```

`Proposal`: `{id,match_id,submitted_by,score,status,version,match_version,created_at,review}`;
`status` = pending/approved/rejected; `review` null o
`{decision,reviewed_by,reviewed_at,reason,official_result_id}`.
`OfficialResult`: `{id,match_id,score,winner_team_id,version,approved_by,approved_at,source_proposal_id}`.
Correzioni con storico, mai sovrascrittura delle proposte discordanti.
`decision` = approve/reject/correct; `correct` richiede `score` e `reason`,
`reject` richiede `reason`, `approve` usa lo score originale.

Le proposte non incrementano `progress.completed`, non modificano classifica,
vincitore o bracket. La creazione controlla partecipazione e versione del match;
la revisione verifica entrambe le versioni, mantiene la proposta e aggiorna
risultato, dipendenze e audit atomicamente. Proposta già revisionata o partita
modificata → 409; duplicati discordanti rimangono distinti. Una seconda proposta
su un match nel frattempo ufficializzato richiede revisione esplicita come
correzione, mai sostituzione automatica. Rifiutare non modifica il risultato.
La proiezione pubblica non espone autore, motivazioni o proposte.

### 6.4 Inviti, pubblicazione e link QR

| Metodo / percorso proposto | Accesso | Input → risposta proposta |
| --- | --- | --- |
| PATCH `/tournaments/{tid}/publication` | T | `{published,version}` → `{published,public_slug,public_url,version}` |
| GET `/public/tournaments/{slug}` | P | Dettaglio pubblicato con whitelist; 404 se privato/revocato |
| GET, POST `/tournaments/{tid}/invites` | T | Lista metadati; `{team_id?,expires_at,max_uses,require_approval}` → 201 `{id,url,token,expires_at,version}` |
| DELETE `/tournaments/{tid}/invites/{iid}` | T | `{version}` → 204 revoca |
| POST `/invites/validate` | P | `{token}` → metadati minimi `{valid,tournament_name,team_name,expires_at,requires_login:true}` |
| POST `/invites/accept` | A studente | `{token}` → 201 iscrizione approved o pending secondo la modalità |

Token casuale ad alta entropia, hash nel database; il token grezzo si restituisce
solo alla creazione, non nell'elenco. Scadenza UTC obbligatoria; `max_uses`
intero positivo. Token scaduto/revocato/esaurito → 410 `invite_unavailable`;
token inesistente → 404. Nessun dato sensibile nei log del body. L'invito non
assegna mai ruolo professore. Accettazione verifica identità, appartenenza,
capienza e uso disponibile atomicamente; accettazioni ripetute non duplicano
la membership né consumano altri usi. In modalità approvazione la richiesta
prenota un uso, ma capienza e appartenenza si riverificano all'approvazione;
rifiuto restituisce l'uso prenotato se l'invito è ancora attivo.

Pubblicazione: URL stabile con slug indipendente da token segreti; nessun token
per leggere un torneo intenzionalmente pubblico. Revoca → 404 pubblico.
Nessuna email, user ID, rosa personale, audit o proposta nella whitelist.
Team B trasforma `url` in QR e gestisce login/richiesta; il QR non identifica
automaticamente lo studente.

### 6.5 Campi, sedi e calendario

| Metodo / percorso proposto | Accesso | Input → risposta proposta |
| --- | --- | --- |
| GET, POST `/venues` | T | Lista per contesto; `{name}` → sede |
| GET, POST `/fields` | T | Lista `venue_id`, `sport_variant_id`; `{name,venue_id?,sport_variant_ids,availability}` → campo |
| PATCH, DELETE `/fields/{fid}` | T | Modifica versionata / archiviazione, senza cancellare riferimenti storici |
| GET `/tournaments/{tid}/calendar` | T/S | Incontri con data, fuso, campo, sede; filtri `from`, `to`, `team_id`, `field_id` |
| PATCH `/tournaments/{tid}/matches/{mid}/schedule` | T | `{scheduled_at,timezone,field_id,duration,version}` → match aggiornato |

`availability`: array di `{starts_at,ends_at}` con offset; intervalli validi e
non sovrapposti, `[]` significa nessuna restrizione oraria configurata.
`Field`: `{id,name,venue_id,sport_variant_ids,availability,archived,version}`.
Orario e campo possono essere null per rimuovere l'assegnazione. Il payload
V1 del calendario è completo, non un merge parziale; `duration` minuti 1–240.
`timezone` IANA serve a ripresentare l'orario civile e deve essere coerente
con l'offset di `scheduled_at` nella data indicata.

Controlli proposti: isolamento dell'organizzatore, compatibilità sportiva,
disponibilità, conflitti dello stesso campo **tra tutti i tornei del contesto**,
conflitti squadra e ordine delle dipendenze. Campo archiviato non assegnabile
nuovamente; prenotazioni esistenti conservate. Codici 409 `field_busy`,
`team_busy`, `dependency_conflict`; 422 `outside_availability` o
`sport_incompatible`. Scheduler automatico fuori dal primo incremento.

### 6.6 Sport, varianti, regole, bracket e statistiche

| Metodo / percorso proposto | Accesso | Risposta/input proposti |
| --- | --- | --- |
| GET `/sports` | A | `{items:[{id,name,variants:[{id,name,score_type,presets}]}],next_cursor}`; solo supporti testati |
| GET `/sports/variants/{vid}/rules-schema` | A | `{variant_id,defaults,rules_schema,result_schema,standings_criteria}`; JSON Schema per form dinamici |
| GET, PATCH `/tournaments/{tid}/rules` | T/S GET, T PATCH | `{variant_id,config,version}`; modifiche in bozza, 409 se già generato salvo futura procedura dedicata |
| POST `/tournaments/{tid}/generate` | T | Stessi vincoli motore attuale; nessun cambio seed dovuto all'ordine visuale |
| GET `/tournaments/{tid}/matches` | T/S | Lista paginata, filtri `stage_id`, `group_id`, `status`, `team_id` |
| GET `/tournaments/{tid}/standings` | T/S | `{groups:[{group_id,rows}],criteria}`; soltanto risultati ufficiali |
| GET `/tournaments/{tid}/bracket` | T/S | `{stages:[{id,rounds:[{round_no,matches}]}],champion_team_id}` |
| GET `/tournaments/{tid}/statistics` | T/S | Riepilogo sotto; autore delle proposte visibile solo a T |
| GET `/public/tournaments/{slug}/statistics` | P | Riepilogo senza studenti, proposte, autori o dati privati |

Nodo bracket proposto: campi `Match` attuali più
`next:{match_id,slot:"home"|"away"}|null` e `official_result:OfficialResult|null`;
`next` null nella finale. Nessuna progressione su proposte; BYE esplicito,
mai risultato 0–0. Cancellare/correggere invalida solo le dipendenze autorizzate.

Riepilogo proposto:

```json
{
  "team_count":4,"student_count":12,"matches_total":3,
  "matches_completed":1,"matches_remaining":2,"pending_proposals":2,
  "completion_percentage":33.33,"phases_pending_generation":false,"champion_team_id":null,
  "qualified_team_ids":[],"standings":[],"sport_statistics":{}
}
```

Pubblico: omettere `student_count` e `pending_proposals`. Percentuale = completate
/ totale generato * 100, arrotondata a due decimali, 0 con totale 0; indicare
con `phases_pending_generation` la presenza di fasi ancora da generare per
evitare di far passare un 100% parziale
per completamento del torneo. `qualified_team_ids` solo dopo qualificazione
effettiva; nessuna previsione. Statistiche sportive assenti se non supportate.

Primo gruppo proposto: calcio con varianti 11/7/5 (punteggio numerico), basket
standard senza pareggi finali, pallavolo indoor con set. Un preset scolastico
esplicito non equivale al regolamento federale. Il server deve validare durata,
periodi, set, vittoria, spareggi e criteri dichiarati; non basta elencare uno
sport. Per pallavolo: set normali a 25, decisivo a 15, scarto minimo 2,
best-of-5, nessun set dopo il terzo vinto; criteri 3/0 per 3–0 e 3–1,
2/1 per 3–2, da confermare con il professore. I limiti e tutte le regole
configurabili devono provenire dal `rules-schema`. Altri sport, forfait e
penalizzazioni richiedono regole e test propri, senza preset vuoti.

## 7. Revisione e modifiche successive

1. Revisionare baseline, convenzioni V1, migrazione account e metadati sport con
   Team B; scegliere i preset scolastici con il professore.
2. Integrare questa piccola PR in `main` dopo la revisione di entrambi. Il branch
   del compagno non è stato modificato né verificato come esistente da remoto.
3. Implementare incrementi backend su `leo-develop`; per ogni gruppo di route
   convertire lo stato proposto in implementato solo dopo test e aggiornamento
   dell'OpenAPI, handoff e matrice.
4. Ogni cambiamento incompatibile deve avere proposta, endpoint/campi coinvolti,
   impatto per Team B e migrazione revisionabile. Le proposte di questa versione
   non autorizzano una rottura delle API correnti prima dell'accordo.

Handoff: [BACKEND_TO_FRONTEND.md](../handoffs/BACKEND_TO_FRONTEND.md).
Audit e priorità: [CORE_ENGINE_AUDIT.md](../CORE_ENGINE_AUDIT.md).
