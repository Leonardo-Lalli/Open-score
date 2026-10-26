# Handoff backend → Team B

> Aggiornamento 0.9.0, 26 ottobre 2026: integrazione locale di `max-develop`
> @ `0896096` in `leo-develop`, schema 8. Gli adapter frontend sono ora attivi.
> Il documento operativo corrente è [TEAM_B_INTEGRATION_REPORT.md](../TEAM_B_INTEGRATION_REPORT.md).
> Nessun push o deploy. Il testo 0.3 seguente è conservato come riferimento storico;
> le affermazioni su frontend non integrato, schema 4 e route disabilitate in service
> sono superate dal report corrente.

## Consegna storica 0.3

26 ottobre 2026, branch **leo-develop**, partenza `4e15385`.
Commit backend da integrare dopo revisione: **`00a4d20`**.
L'utente ha richiesto implementazione locale e **nessun push**. Nessuna PR aperta,
merge, pubblicazione o modifica del branch del Team B. Revisione congiunta ancora necessaria.

## Implementato

Account e sessioni server; professori creati da CLI, registrazione solo studenti;
permessi per proprietario/contesto e collaboratori espliciti; squadre e alias
studenti con capienza, spostamento e riordino versionato; richieste/iscrizioni;
proposte discordanti, approvazione/rifiuto/correzione con risultato ufficiale,
audit attribuibile, classifica e progressione atomici; inviti con hash, scadenza,
revoca e usi; pubblicazione revocabile con whitelist; sedi/campi e calendario con
conflitti tra tornei; calcio 11/7/5, basket e pallavolo indoor con regole custom,
set, tavolino e penalità; bracket con next slot e statistiche ufficiali.

Schema DB 4, migrazioni additive 003 e 004. Nessun dato precedente assegnato al
primo account. Backup automatico prima degli aggiornamenti di schema; comandi
backup/restore creano copie verificate senza sovrascrivere l'originale.

## Documenti da usare

- [Contratto attuale](../contracts/API_V1.md): endpoint realmente implementati, input, stati ed errori.
- [OpenAPI generato](../contracts/openapi.yaml): input e risposte V1 tipizzate, cookie e CSRF.
- [Deployment e prova locale](../DEPLOYMENT_BACKEND.md): account professore, migrazioni, backup/ripristino.
- [Report incremento](../CORE_ENGINE_REPORT.md): test, limiti e stato Git.
- [Matrice aggiornata](../CORE_ENGINE_MATRIX.md): confronto con il Prompt A.

La prima proposta rimane nella cronologia al commit `4e15385`. Differenze
implementative esplicite: catalogo sport come lista piatta di varianti;
organization current come oggetto organization nullable; cursor numerico a offset;
review conserva created_at e original_match_id; endpoint my-participation e penalty;
public_url punta alla API JSON funzionante, non a una pagina frontend inesistente.

## Integrazione frontend

La UI e gli asset statici non sono stati modificati. In **demo** il sito esistente
continua a usare le route `/api` per tornei non assegnati. Le API V1 richiedono
login anche in demo. In **service** le vecchie route sono disabilitate: serve il
client V1. Un torneo assegnato da CLI non compare più nella demo anonima.

Per login: GET `/api/v1/auth/csrf`, poi POST login con X-CSRF-Token; conservare il
nuovo token ricevuto e inviarlo con il cookie nelle scritture. Non usare bearer token
nei link QR. POST register crea solo studenti e ruota la sessione. La sessione è
HttpOnly, quindi il client non legge il cookie direttamente. Su stesso origin
fetch invia i cookie; eventuale altro dominio richiede accordo esplicito su proxy/CORS.

Le risposte 401 devono portare al login; 403 a permessi/CSRF; 404 a risorsa assente;
409 a rilettura e confronto. Non convertire automaticamente 409 in invalidate true.
Campi di errore: detail stringa/lista, code e current_version quando disponibile.
I messaggi legacy possono essere generici, non classificare dal testo italiano.
Host non valido può essere rifiutato dal middleware con testo anziché JSON.

Riordino: ordered_team_ids è la permutazione completa delle squadre attive;
version è order_version, non la versione torneo o squadra. Nessun cambio al seed.
Spostamenti studenti richiedono versione Student, risultato richiede match_version.
Rileggere il dettaglio dopo scritture: possono cambiare più incontri/versioni.
La durata iniziale degli incontri deriva dal preset; il calendario usa payload
completo con scheduled_at/timezone/field_id/duration/version, non merge parziale.

Form dinamici: GET sports e rules-schema. Il risultato è discriminato per type,
points/sets/forfeit. Un punteggio a set non è 3–0 numerico senza singoli set.
Proposte e risultati ufficiali sono separati: non aggiornare classifica/bracket
con score di una proposta pending. Le proposte obsolete sono segnalate da stale;
una correzione della fase finale può conservare proposte con match_id null e
original_match_id storico.

Gli inviti forniscono `/join#TOKEN` per il futuro flusso QR. **La pagina join non
esiste ancora**: leggere il frammento nel client e chiamare validate/accept dopo
login. public_url fornisce già JSON senza informazioni personali degli studenti;
realizzare una pagina spettatore V1 su questo contratto. Non esporre autori,
email, rose o audit nelle viste pubbliche.

Bracket: usare stage_id/round_no/position, source_home/source_away e next con
match_id/slot; BYE non è una partita né 0–0. Statistiche: dati derivati dai risultati
ufficiali, non dalle proposte. Nei multifase il totale cresce alla qualificazione,
con phases_pending_generation. Non interpretare 100% parziale come campione.

## Prova sintetica

Creare professore da manage.py, fare login da /docs, poi POST `/api/v1/tournaments`:

```json
{"name":"Coppa sintetica","variant_id":"football-5","format":"knockout","team_names":["Alfa","Beta","Gamma"]}
```

Usare l'ID ricevuto in generate; GET dettaglio. Registrare uno studente separato,
associarlo da account professore e assegnarlo a una squadra. Lo studente propone,
il professore approva. Per pallavolo usare variante volleyball-indoor e score sets.
Non esistono ID, token o credenziali fissi di produzione nelle fixture.

## Limiti e revisione

Restano UI e QR, recupero password via email, import massivo studenti,
cancellazione definitiva dati/tornei, CRUD completo sedi, regole modificabili dopo
generazione, ricalcolo penalità dopo qualificazione, scheduler, altre discipline,
PostgreSQL e pubblicazione reale. Preset scolastici, senza conformità federale dichiarata.

**132 test passati**, 1 warning di deprecazione, 103.27 secondi. Test con SQLite
reale e identità sintetiche; OpenAPI sincronizzato. Esito e comandi nel report.
La CI esistente esegue tutti i test, incluso OpenAPI; nessuna nuova esecuzione
remota è stata avviata o dichiarata verde. Nessuna nuova prova browser frontend.

Prima del merge revisionare convenzioni, cookie/CSRF, DTO, preset sportivi e flussi
studenti con entrambi gli sviluppatori. Nessun push o merge prima dell'autorizzazione.
