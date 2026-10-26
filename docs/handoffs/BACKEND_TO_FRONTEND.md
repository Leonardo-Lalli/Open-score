# Handoff backend → Team B

Data: 26 ottobre 2026. Branch **`leo-develop`**, baseline
`b541824fbfaf96f43d67c3d1e2f17b53ae1b4c54`. Il commit di consegna è identificabile
con `git log --oneline --grep="docs(api): define shared tournament contracts"`.
Il messaggio individua questo incremento, non un commit futuro già pubblicato.

## Consegna A0/A1

La demo usa FastAPI/SQLite e frontend statico senza React. Questo incremento
aggiunge documentazione e un controllo OpenAPI; non cambia il comportamento
di route, autenticazione, ID o JSON correnti. Nessuna modifica a `static/`,
README principale, workflow o branch del Team B. Nessuna migrazione nuova.

- [Contratto API_V1](../contracts/API_V1.md): sezioni 1–5 disponibili, sezione 6
  proposta e **non implementata**.
- [OpenAPI generato](../contracts/openapi.yaml): solo endpoint effettivi `/api`.
- [Audit](../CORE_ENGINE_AUDIT.md) e [matrice](../CORE_ENGINE_MATRIX.md): stato e lacune.
- [Bozza PR](CORE_ENGINE_CONTRACT_PR.md): titolo, descrizione e checklist revisione.

## Cosa si può integrare subito

| UI / funzione | API disponibile | Note |
| --- | --- | --- |
| Elenco e wizard | GET/POST `/api/tournaments`, POST `/{tid}/generate` | Creazione e generazione separate; se la seconda fallisce conservare la bozza |
| Squadre | POST `/{tid}/teams`, PATCH/DELETE `/{tid}/teams/{team_id}` sotto `/api/tournaments` | Aggiunta/rimozione solo prima della generazione; nomi unici |
| Partite, classifiche, gruppi | GET `/api/tournaments/{tid}` | Tutto nel dettaglio, non chiamare endpoint standalone inesistenti |
| Risultato e cancellazione | PATCH `/{tid}/matches/{mid}`, DELETE `/{tid}/matches/{mid}/result` | `version` obbligatoria, risultato immediatamente autorevole |
| Calendario manuale | PATCH `/{tid}/matches/{mid}/schedule` | Corpo completo, UTC in risposta; campo ancora testuale |
| Tabellone | `detail.matches` con kind knockout | Usare source_home/source_away, stage_id/round_no/position; BYE non è punteggio |
| Statistiche demo | team_count nell'elenco, progress/campione nel dettaglio | Nessun conteggio studenti o proposte; totale solo fasi generate |
| Link spettatore | GET `/api/public/{token}`, UI `/public/{token}` | Solo demo locale; non è invito, nessuna revoca |
| Export | GET `/api/tournaments/{tid}/export.csv` | CSV con BOM e mitigazione formule |

Per le righe con percorsi abbreviati il prefisso è `/api/tournaments`.
I dettagli esatti degli input/risposte/errori sono nel contratto, evitando una
seconda specifica divergente qui.

Esempio sintetico da creare in un DB di sviluppo isolato:

```json
{"name":"Coppa sintetica","sport":"Calcio a 5","format":"knockout","team_names":["Alfa","Beta","Gamma"]}
```

Inviare a POST `/api/tournaments`; usare l'ID ricevuto per generare e rileggere.
Nessun ID o token fornito nell'esempio va considerato costante o credenziale.
`POST /api/demo` carica i quattro esempi senza azzerare risultati esistenti;
non chiamarlo come parte di un futuro ambiente di produzione.

## Cosa resta proposto

Non collegare ancora le schermate a `/api/v1`: non esiste. Sono proposti login,
studenti/rose, iscrizioni, ordine squadre, proposte/revisioni, pubblicazione
revocabile, inviti, campi/sedi, regole sportive, bracket e statistiche dedicate.
La sezione 6 specifica metodi, percorsi, payload e autorizzazioni candidate.
Usare prototipi di interfaccia chiaramente indicati come tali finché il backend
non passa da proposto a implementato e testato; non simulare conferme riuscite.

L'ordine visuale non cambierà seeding o tabelloni; la relativa versione sarà di
collezione. Le proposte non cambieranno classifica o campione finché un professore
non le approverà. Il QR conterrà un URL, senza assegnare privilegi o identità.

## Errori e stati client

- Dopo successo di un risultato/orario rileggere il dettaglio e la versione.
- 409 versione: offrire aggiornamento e mantenere l'input per confronto, senza
  sovrascrivere automaticamente. 409 dipendenze: chiedere conferma esplicita
  prima di `invalidate:true`.
- 422: visualizzare `detail` stringa o lista di errori. Non fare affidamento sul
  testo italiano per classificare l'errore: V1 proporrà `code` stabile.
- Origin 403 e Host 400 possono essere testo, non JSON. Gestire il fallback.
- `[]` significa lista caricata vuota, `null` significa valore assente; nessun
  risultato ancora inserito non equivale a 0–0. Distinguere caricamento,
  errore di rete, risorsa 404 e assenza di incontri.
- Nei multifase il totale cresce quando viene generato il knockout: la
  percentuale attuale è sulle fasi generate, non sull'intero percorso futuro.

## Autorizzazioni e migrazione da concordare

Attualmente nessuna API organizzatore richiede login. Host/Origin e vista pubblica
non sono ruoli. Restare in locale e usare dati sintetici.
La proposta introduce sessione HttpOnly, CSRF e controllo proprietario/contesto.
L'attivazione richiede adattamenti espliciti del client e una migrazione di
assegnazione dei tornei esistenti. Il frontend dovrà distinguere 401, 403 e 404;
mai consentire allo studente di inviare ruolo o identità del revisore.

La scelta di un frontend GitHub Pages con backend su dominio diverso richiede
una revisione su cookie/CORS/HTTPS. Nessun hosting, DNS o deploy scelto in questa
consegna; il dominio Aruba da solo non indica la capacità di eseguire FastAPI.

## Verifiche e limiti

Baseline eseguita: **85 passed, 1 warning**, Python 3.14.3 su Windows.
Il warning è la deprecazione Starlette/httpx. L'esecuzione sandbox era bloccata
dalle directory temporanee; la suite completa è stata eseguita con autorizzazione.

Verifica finale: **87 passed, 1 warning**, 14.50 s. Include confronto dello
snapshot con `/openapi.json` e prova in un processo separato che `--check`
non apra/modifichi il database configurato dall'utente né riscriva lo snapshot.
Eseguito anche `python scripts/export_openapi.py --check`: sincronizzato.
La CI esistente esegue automaticamente anche il nuovo test, ma non è stata
avviata/verificata una nuova esecuzione GitHub Actions. Nessuna nuova prova UI.

Limiti principali: risposte non tipizzate in OpenAPI, nessuna autenticazione o
privacy scolastica completa, nessun workflow studenti, sport solo numerici,
conflitti calendario interni al torneo. Le future API richiedono codice,
migrazioni, autorizzazioni e test: il contratto da solo non le implementa.

## Procedura di integrazione

1. Revisionare il contratto insieme: prefisso, sessione/CSRF, ID, DTO, errori,
   membership, approvazioni, inviti e primi preset sportivi.
2. Il push su `leo-develop` richiede autorizzazione esplicita dell'utente come
   previsto dall'allegato. La PR va verso `main`; niente force push o merge automatico.
3. Dopo revisione dei due sviluppatori e integrazione del contratto, procedere
   con incrementi A2–A9 aggiornando handoff, schema e matrice ad ogni consegna.

La PR e la revisione non sono ancora avvenute. Nessun conflitto locale rilevato;
non è stato confrontato il lavoro non disponibile del Team B, quindi non si
garantisce assenza di conflitti nei suoi commit futuri.
