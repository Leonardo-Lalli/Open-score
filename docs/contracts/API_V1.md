# Contratto API V1 — backend 0.3

26 ottobre 2026, branch **leo-develop**, baseline della prima specifica `4e15385`.
Implementazione locale richiesta dall'utente, senza push. Revisione Team B e
integrazione in main non avvenute. Le schermate V1 e QR restano al Team B.

## Specifica autorevole

[openapi.yaml](openapi.yaml) viene generato da FastAPI in JSON valido anche come
YAML 1.2. Contiene input, risposte V1 tipizzate, cookie di sessione e header CSRF.
Il motore e le route legacy conservano i nomi esistenti. La prima proposta è
consultabile nella cronologia al commit `4e15385`; questo documento la sostituisce.

Da torneo-lab, nell'ambiente virtuale:

```powershell
python scripts/export_openapi.py
python scripts/export_openapi.py --check
python -m pytest -q
```

Due test controllano sincronizzazione e isolamento dell'esportatore dal database
utente. Le risposte legacy restano generiche in OpenAPI. I JSON Schema delle
regole e dei form risultato sono dinamici per definizione.

## Compatibilità, dati e concorrenza

Modalità **demo**: vecchia UI e `/api` funzionano per tornei non assegnati.
I tornei V1 non sono raggiungibili dalle route anonime legacy, neppure con il
vecchio public_token. Modalità **service**: vecchie route disabilitate eccetto
`/api/health`; solo API V1 protette e proiezioni pubblicate. Nessun frontend modificato.

ID interi JSON, snake_case, date ISO 8601 con offset e UTC in risposta. Gli ID
non attribuiscono permessi. Null significa assenza, non uno 0–0. Campi extra
rifiutati, punteggi e versioni interi rigorosi. Liste: `{items:[],next_cursor:null}`,
limit 1–100 (default 50), cursor come offset >=0. Non è uno snapshot: rileggere
dopo modifiche e riordini. Le mutazioni verificano version, order_version o
match_version in transazioni SQLite con lock prima della lettura.

Errore V1: `{detail:string|lista,code:string,current_version?:int}`. La lista di
validazione contiene solo loc/msg/type, senza input sensibili. Dopo 409 rileggere;
non ripetere automaticamente con invalidate true. Separare caricamento, errore
rete, lista vuota e risorsa assente. Non mostrare salvataggio prima del successo.

## Auth e ruoli

Tutti i percorsi seguenti sono sotto **/api/v1**.

1. GET `/auth/csrf`: pre-sessione HttpOnly e `{csrf_token}`.
2. POST `/auth/login`, `{email,password}` con header `X-CSRF-Token`.
   Risposta `{user:{id,display_name,role,organization_id},csrf_token}` e cookie ruotato.
3. Usare il nuovo token in tutte le scritture autenticate.
4. POST `/auth/logout`: 204, revoca server-side e rimozione cookie.

POST `/auth/register` accetta email/password/display_name, richiede pre-CSRF,
crea e autentica **solo studenti** (201). Nessun ruolo o contesto nel payload.
Professori solo da `manage.py create-teacher`. GET `/users/me` restituisce User;
GET `/organizations/current` restituisce `{organization:null|{id,name}}`.
Lo studente accede per iscrizione anche senza organizzazione amministrativa globale.

Password 12–128 caratteri, PBKDF2-HMAC-SHA256, 600000 iterazioni e salt per account.
Cookie open_score_session HttpOnly/SameSite=Lax, Secure in service; 8 ore assolute,
pre-sessione 30 minuti; nel DB solo hash del token. Rate limit per 15 minuti:
login 30/IP e 10/account+IP, register 10/IP, CSRF 120/IP, validate invite 60/IP.
Le chiavi sono hash; niente password/token grezzi in audit. Il proxy deve aggiungere
limiti globali prima dell'hosting. Origin estraneo rifiutato; CORS non abilitato.

Professore: propri tornei o collaborazione esplicita nello stesso contesto.
Studente: tornei con iscrizione approvata, proprie richieste/proposte; risultati
solo per la propria squadra. Nessuna lista studenti/audit allo studente.
Visitatori: proiezioni pubblicate. 401 sessione assente/scaduta, 404 fuori ambito,
403 ruolo insufficiente su risorsa accessibile. Login e register richiedono CSRF;
POST pubblico invites/validate è consultazione senza CSRF ma con rate limit.

## Tornei, squadre e studenti

| Metodo e percorso | Input / filtri | Risposta / vincoli |
| --- | --- | --- |
| GET, POST `/tournaments` | GET status/cursor/limit; POST TournamentCreate | Pagina Summary / 201 id |
| GET, PATCH `/tournaments/{tid}` | PATCH version/name?/description? | Detail per ruolo / Tournament aggiornato |
| GET, PATCH `/tournaments/{tid}/rules` | PATCH version/variant_id/config | Regole/versione; modifica solo in bozza |
| GET, POST `/tournaments/{tid}/teams` | GET q/cursor/limit; POST name/max_members? | Pagina con order_version / 201 Team |
| PATCH, DELETE `/tournaments/{tid}/teams/{team_id}` | PATCH name/max_members/version; DELETE version | Team / 204 archiviazione in bozza senza membri |
| PATCH `/tournaments/{tid}/teams/order` | ordered_team_ids/version | Ordine e nuova versione collezione |
| PATCH `/tournaments/{tid}/teams/{team_id}/penalty` | points/reason/version | Penalità totale 0–999 e nuova versione squadra |
| GET, POST `/tournaments/{tid}/students` | GET q/team_id/cursor/limit; POST display_name/user_id? | Pagina / 201 Student, solo professore |
| PATCH `/tournaments/{tid}/students/{sid}/team` | team_id/version | Student; null rimuove assegnazione |
| GET `/tournaments/{tid}/my-participation` | — | student, soltanto propria identità |
| POST `/tournaments/{tid}/generate` | — | created; una volta, 2–32 squadre |
| POST `/tournaments/{tid}/enrollments` | team_id?/team_version? | 201 pending, solo torneo pubblicato; versione se scelta squadra |
| GET `/tournaments/{tid}/enrollments` | status/cursor/limit | Professore tutte; studente proprie anche in attesa |
| POST `/tournaments/{tid}/enrollments/{eid}/review` | decision/version/reason? | approve/reject, capienza riverificata |

TournamentCreate di esempio:

```json
{"name":"Coppa sintetica","variant_id":"football-5","format":"groups","group_count":2,"qualifiers":1,"team_names":["Alfa","Beta","Gamma","Delta"],"config":{"duration":30,"win_points":3}}
```

Default: variant football-5, format round_robin, description vuota, config vuoto,
team_names vuoto, legs 1, group_count 2, qualifiers 2, random_seed null. Nomi
strip 2–120 per torneo, 1–60 per squadra; formati round_robin/knockout/groups.
Gironi uguali, almeno due squadre, prime 1/2 promosse dopo tutti i risultati.
Knockout una gara. Lo sport deriva dalla variante, non da un'etichetta separata.

Riordino: permutazione completa delle squadre attive; versione incrementata anche
su aggiunta/archiviazione. Nessun effetto su seed, incontri o classifiche. Il motore
conserva seeding per ID. Alias studenti unici per torneo e un'associazione per account.
Capienza atomica, max_members null senza limite specifico. Penalità sottratte ai
punti con motivazione; bloccate dopo qualificazione multifase, non ammesse nel
knockout puro: serve ancora una procedura dedicata per rivedere quelle qualificazioni.

## Proposte e risultati

| Metodo / percorso | Input | Risposta |
| --- | --- | --- |
| POST `/tournaments/{tid}/matches/{mid}/proposals` | match_version/score | 201 Proposal, nessun effetto ufficiale |
| GET `/tournaments/{tid}/matches/{mid}/proposals` | status/cursor/limit | Professore tutte, studente proprie |
| POST `/tournaments/{tid}/matches/{mid}/proposals/{pid}/review` | decision/proposal_version/match_version/invalidate?/score?/reason? | Proposta, risultato, versione, dipendenze |
| GET `/tournaments/{tid}/matches/{mid}/result` | — | official_result e match_version |
| PATCH `/tournaments/{tid}/matches/{mid}/result` | match_version/score/reason/invalidate? | Risultato diretto/correzione professore |
| DELETE `/tournaments/{tid}/matches/{mid}/result` | match_version/reason/invalidate? | Rimozione ufficiale e dipendenze |

Score punti: `{"type":"points","home":2,"away":1}`. Score set:
`{"type":"sets","sets":[{"home":25,"away":20},{"home":25,"away":23},{"home":25,"away":22}]}`.
Tavolino solo professore: `{"type":"forfeit","winner":"home","reason":"Decisione sintetica"}`.
Interi 0–999 e validazione per variante. Tavolino esplicito, escluso dalle statistiche giocate.

Review decision approve/reject/correct: approve usa lo score originale; reject
richiede reason; correct richiede reason e score sostitutivo. invalidate default false.
Proposte discordanti preservate, nessun avanzamento prima dell'approvazione.
Proposta obsoleta: respingere, non approvare sul nuovo stato del match. Una proposta
nuova può comunicare una correzione del risultato ufficiale corrente.

Proposal include score originale, autore/timestamp, status pending/approved/rejected,
version, match_version, review e stale. original_match_id resta; match_id null
se la finale viene ricostruita. Revisioni e audit conservano la storia. OfficialResult
ha approvatore/timestamp/source_proposal_id e versione; import legacy mantiene
provenance legacy con approvatore e timestamp null, senza inventare una revisione.

Risposte di modifica: official_result/match_version/invalidated_match_ids e
invalidated quando applicabile; review aggiunge proposal. Rileggere il dettaglio.
Risultato, audit, classifica, progressione e verifica calendario sono atomici.
Correzioni distruttive dei discendenti richiedono invalidate true, altrimenti 409.
Stesso vincitore knockout conserva la finale; correggere solo rally a set ricalcola
comunque spareggi e qualificazioni multifase.

## Inviti e pubblicazione

| Metodo / percorso | Input | Risposta |
| --- | --- | --- |
| POST `/tournaments/{tid}/invites` | team_id?/expires_at/max_uses/require_approval? | 201 metadati, token e url |
| GET `/tournaments/{tid}/invites` | cursor/limit | Metadati, mai token o hash |
| DELETE `/tournaments/{tid}/invites/{iid}` | version | 204 revoca |
| POST `/invites/validate` | token | Nomi minimi, expires_at, requires_login |
| POST `/invites/accept` | token, studente autenticato | 201 approved oppure pending |
| PATCH `/tournaments/{tid}/publication` | published/version | published/public_slug/public_url/version |
| GET `/public/tournaments/{slug}` | Nessuna auth | Detail pubblico o 404 |
| GET `/public/tournaments/{slug}/statistics` | Nessuna auth | Riepilogo senza studenti/proposte/autori |

Token casuale 32 byte, hash nel DB; scadenza futura entro 90 giorni, max_uses
1–1000, require_approval default true. Nessun ruolo amministrativo. Accettazioni
attive idempotenti; ultimo posto/uso controllati atomicamente. Pending prenota uso;
review riverifica capienza, rifiuto restituisce uso se invito ancora valido.
Richieste respinte non si riaprono automaticamente con lo stesso invito.

URL invito `/join#TOKEN`: frammento escluso dagli access log. **La pagina join
resta da realizzare dal Team B**; provare ora validate/accept. public_url è una URL
API JSON già funzionante e stabile, senza token segreto. La pagina grafica pubblica
resta al Team B. Nessuna email, rosa, audit, owner, proposta o motivo del tavolino
nella proiezione pubblica.

## Campi e calendario

| Metodo / percorso | Input / filtri | Risposta |
| --- | --- | --- |
| GET, POST `/venues` | GET cursor/limit; POST name | Pagina / 201 sede propria |
| GET, POST `/fields` | GET venue_id/sport_variant_id/cursor/limit; POST FieldInput | Pagina / 201 campo proprio |
| PATCH, DELETE `/fields/{fid}` | PATCH FieldInput/version; DELETE version | Campo / 204 archiviazione |
| GET `/tournaments/{tid}/calendar` | from/to con offset, team_id/field_id/cursor/limit | Match filtrati, senza filtri date anche non programmati |
| PATCH `/tournaments/{tid}/matches/{mid}/schedule` | ScheduleInput | Match aggiornato |

FieldInput: name, venue_id nullable, sport_variant_ids, availability default [].
Disponibilità come intervalli starts_at/ends_at con offset e senza sovrapposizioni;
lista vuota senza restrizione. Aggiornamento verifica prenotazioni già esistenti.

```json
{"scheduled_at":"2026-11-03T10:00:00+01:00","timezone":"Europe/Rome","field_id":1,"duration":30,"version":1}
```

Offset coerente con timezone/data, durata 1–240. Payload completo, non merge;
null in data e field_id rimuove programmazione. Intervalli [inizio,fine), adiacenza
consentita. Controlli sport/disponibilità, campo tra tornei del contesto, squadre
note e dipendenze dirette. Approval riverifica conflitti dopo progressione.
Nessuno scheduler automatico. Campi archiviati preservano riferimenti storici.

## Sport, bracket e statistiche

GET `/sports`: lista piatta di varianti con id/sport/name/score_type/preset/defaults.
GET `/sports/variants/{vid}/rules-schema`: defaults, rules_schema, result_schema,
administrative_result_schema, standings_criteria per form dinamici.
Varianti implementate e testate: **football-11, football-7, football-5, basketball,
volleyball-indoor**. Preset scolastici espliciti, non regolamenti federali completi.
Calcio: durata/periodi/V-N-P/pareggio/tavolino configurabili; knockout decisivo.
Basket: risultato finale dopo eventuale spareggio, mai pareggio. Pallavolo:
best-of 3/5, target/decisivo/scarto >=2 configurabili, set completi senza set dopo
vittoria; punti vittoria netta/stretta/sconfitta stretta. Default 25/15, best-of-5,
3/2/1/0. Nessuno sport segnaposto.

GET `/tournaments/{tid}/matches`: pagina Match, filtri stage_id/group_id/team_id/status.
GET `/tournaments/{tid}/standings`: rows, groups, criteria.
GET `/tournaments/{tid}/bracket`: stages/rounds/matches e champion_team_id.
Match include fase, turno da 1, position da 0, avversari, score/totali, status,
versione, data/timezone/campo e source_home/source_away. Nel bracket aggiunge next
con match_id/slot oppure null in finale, official_result sintetico. BYE esplicito,
is_bye intero 0/1, mai partita giocata. Stati match waiting/ready/completed/bye;
torneo draft/active/completed, derivati sul server.

Classifica numerica: punti/differenza/fatti/nome/ID; nomi goals_* conservati anche
nel basket. Set: punti/differenza set/differenza rally/nome/ID. Penalità sottratte
ai punti e mostrate in penalty_points. Criteri scolastici, senza scontri diretti.

GET `/tournaments/{tid}/statistics`: team_count, matches_total/completed/remaining,
completion_percentage, phases_pending_generation, champion_team_id,
qualified_team_ids, standings, groups, sport_statistics. Privato aggiunge
student_count, solo professore pending_proposals. Proposte mai ufficiali. Percentuale
sui match generati, 0 se totale 0; nei multifase totale cresce dopo qualificazione,
segnalato dal flag. points_scored/sets_played escludono tavolino/BYE.

## Errori e limiti

401 authentication_required/invalid_credentials; 403 csrf_invalid/origin_forbidden,
teacher_required/student_required/match_participation_required; 404 not_found;
409 stale_version, duplicate_team/student, already_enrolled/reviewed, team_full,
teams_locked/rules_locked/qualification_locked, stale_proposal, field_busy/team_busy/
dependency_conflict; 410 invite_unavailable; 422 validation_error/invalid_rules/
invalid_score/invalid_team_order/sport_incompatible/outside_availability; 429 rate_limited.
Il motore conservato può ancora restituire conflict/invalid_input generici.

Restano: UI/QR, recupero email automatico, import studenti massivo, cancellazione
definitiva tornei/studenti, CRUD completo sedi, modifica regole dopo generazione,
revisione penalità dopo qualificazione, scheduler, altre discipline, adapter
PostgreSQL e deployment reale. Il contratto va revisionato con Team B prima del merge.
