# Final review — audit iniziale e registro delle verifiche

27 ottobre 2026. Baseline analizzata: `d7a2dab2a24315bdd3c3067f49d9a75c16fe33b1`.
Stato iniziale pubblicato su `main` su richiesta dell'utente. Revisione esclusivamente
locale su `review/final-optimization`; nessun push delle nuove correzioni né deploy manuale.

Questo documento precede le modifiche al codice della revisione finale. Le voci
distinguono evidenza dal sorgente, riproduzione eseguibile e ipotesi da misurare.
I risultati definitivi, la scorecard e la bozza di PR verranno aggiornati qui.

## Architettura ricostruita

FastAPI/Pydantic, SQLite schema 8 con migrazioni delle due linee storiche, SPA
vanilla senza build, CSS e font locali. `app.py` compone API storiche, adapter
frontend e API V1. `services.py` e `platform_services.py` riutilizzano `engine.py`;
`sports.py` e il catalogo `sport_rules.py` conservano i due namespace delle varianti.
Account docenti collegati tramite `teacher_user_links`; rose/profili tramite
`team_players.student_id`. Transazioni `BEGIN IMMEDIATE` per le scritture.
Sito `website/` separato e build Pages `.github/scripts/build_site.py`.

## Baseline e perimetro

- Working tree iniziale pulita; checkpoint precedente `fa15d6e`, nuovo checkpoint `d7a2dab`.
- Dipendenze runtime fissate, ambiente Python 3.14.3 e Node locale; suite iniziale in corso.
- Lettura delle PR tramite API pubblica GitHub: nessuna voce aperta restituita.
  GitHub CLI non autenticato; non sono state cambiate credenziali.
- CI del precedente main `261f456`: successo. CI di `d7a2dab` avviata dal push;
  il suo esito verrà verificato separatamente dalle prove locali.
- Nessun requisito di riscrittura, cambio framework, PostgreSQL, nuova scuola/tenant
  o nuova disciplina viene introdotto automaticamente.

## Problemi e piano, prima delle modifiche

### FR-01 — Durata della fase finale del catalogo attraverso V1

- **Severità/area:** P1, logica torneo/calendario.
- **File/funzione:** `torneo-lab/platform_services.py`, `qualify` e `insert_bracket`.
- **Evidenza:** `insert_bracket` applica la durata da `rules_json` solo quando presente;
  i tornei del catalogo Team B hanno `rules_snapshot` e `rules_json` nullo.
- **Attuale/atteso:** la qualificazione tramite revisione V1 può usare il default DB
  anziché la durata della variante; deve coincidere con la qualificazione dell'API UI.
- **Impatto:** prenotazioni e conflitti calcolati su intervalli diversi.
- **Proposta:** riusare il percorso del catalogo per la qualificazione dei suoi tornei.
- **Rischio:** medio, progressione multifase; nessuna modifica di schema o contratto.
- **Test:** completamento gironi via V1 e proposte, confronto durate/squadre/finale,
  correzione retroattiva con invalidazione.
- **Stato iniziale:** evidenza da sorgente; riproduzione da eseguire.

### FR-02 — Elenco V1 calcola ogni dettaglio prima di paginare

- **Severità/area:** P2, performance backend/DB.
- **File/funzione:** `torneo-lab/v1_api.py:tournaments`, `v1_domain.detail`.
- **Evidenza:** ciclo su tutti i tornei, caricamento incontri/rose/classifiche e
  controllo accesso per ogni riga; solo alla fine viene applicata la paginazione.
- **Attuale/atteso:** costo cresce con numero e dimensione dei tornei; un riepilogo
  deve evitare il dettaglio e mantenere identici ordine, visibilità, filtri e cursori.
- **Impatto:** latenza e query superflue per docente e studente.
- **Proposta:** selezione delle risorse visibili e aggregati per riepilogo, senza cache.
- **Rischio:** medio, possibile divergenza di privacy/progress/status.
- **Test:** confronto integrale vecchio/nuovo payload, ruoli, pubblicazione,
  collaboratori, filtri e paginazione; misure ripetute e conteggio SELECT prima/dopo.
- **Stato iniziale:** N+1 da sorgente; entità del beneficio da misurare.

### FR-03 — Conflitti del calendario confrontati a coppie senza finestra temporale

- **Severità/area:** P2 potenziale, performance calendario.
- **File/funzione:** `torneo-lab/frontend_api.py:calendar_data`.
- **Evidenza:** ciclo annidato sulle partite programmate e parsing datetime in ogni coppia.
- **Attuale/atteso:** confronta anche giornate lontane; può limitarsi alle finestre sovrapposte.
- **Impatto:** da quantificare su dati sintetici, nessuna lentezza attribuita senza misura.
- **Proposta:** ordinamento temporale, parsing una volta e interruzione della scansione.
- **Rischio:** medio, confini degli intervalli, fusi e precedenza dei tipi di conflitto.
- **Test:** equivalenza con algoritmo di riferimento su date, durate e sovrapposizioni;
  benchmark ripetuto su calendario distribuito e caso con conflitti reali.
- **Stato iniziale:** ipotesi di ottimizzazione, implementare solo se misurata.

### FR-04 — URL di invito nei log di accesso

- **Severità/area:** P2, minimizzazione dei segreti nei log.
- **File/funzione:** avvio Uvicorn e route `/api/invites/{token}`.
- **Evidenza:** i token sono segmenti del percorso; il log di accesso predefinito
  registra il percorso completo. Il logging applicativo non lo oscura.
- **Attuale/atteso:** una capacità di invito può rimanere nei log; servono percorsi
  redatti mantenendo metodo, stato e diagnostica utile.
- **Impatto:** chi accede ai log potrebbe recuperare link ancora validi.
- **Proposta:** filtro circoscritto dei log di accesso, nessuna modifica alle URL API.
- **Rischio:** basso/medio, compatibilità formato logging e logging configurato dall'host.
- **Test:** record reali Uvicorn con token in path/query, route ordinarie e registrazione
  ripetuta del filtro; assenza di token nei log acquisiti.
- **Stato iniziale:** evidenza dal percorso; verifica del logger/runtime da completare.

### FR-05 — Metadati di sicurezza e architettura obsoleti

- **Severità/area:** P2, documentazione operativa.
- **File:** `docs/SECURITY.md`, `ARCHITECTURE.md`, `DATABASE.md`, `DECISIONS.md` e handoff storici.
- **Evidenza:** descrivono schema 4/7, assenza di registrazione studente e revoca server,
  rose pubbliche e adapter disattivati; il codice e i test della baseline li smentiscono.
- **Attuale/atteso:** istruzioni divergenti; documenti operativi aggiornati e consegne
  storiche esplicitamente distinte, senza cancellare la cronologia dei due team.
- **Impatto:** configurazioni sbagliate e assunzioni errate su permessi/riservatezza.
- **Proposta:** correggere i documenti esistenti, collegare la fonte corrente ed evitare duplicati.
- **Rischio:** basso, nessun cambiamento di comportamento.
- **Test:** confronto con route/schema/comandi reali, link locali, build Pages e guardie docs.
- **Stato iniziale:** verificato con lettura e confronto del codice.

### FR-06 — Inglese, mobile fisico e infrastruttura non dimostrati

- **Severità/area:** P2/P3 secondo requisito di rilascio, copertura e preparazione.
- **Evidenza:** il sito dichiara `lang=it` e non promette una versione EN; Docker Desktop
  era spento nell'audit precedente. Non esiste evidenza di prove su telefoni fisici,
  screen reader o Aruba reale.
- **Attuale/atteso:** non attribuire completezza bilingue, conformità WCAG o prontezza
  produzione senza prove; distinguere prove locali, automatiche e manuali residue.
- **Impatto:** limita le dichiarazioni di release, non dimostra un guasto dell'app.
- **Proposta:** provare quanto disponibile, registrare i limiti; EN e decisioni organizzative
  richiedono un incremento concordato se diventano requisiti obbligatori.
- **Rischio:** nessuno per l'inventario; evitare espansioni indiscriminate.
- **Test:** sito IT/light/dark/build, viewport e tastiera; infrastruttura solo se disponibile.
- **Stato iniziale:** limiti verificati, nessuna dichiarazione di conformità completa.

## Ordine operativo

### FR-07 — Directory di output Pages cancellata senza verifica

- **Severità/area:** P1, protezione dati degli sviluppatori/tooling di build.
- **File/funzione:** `.github/scripts/build_site.py:render`.
- **Evidenza:** se `--out` esiste, viene eseguito `shutil.rmtree(out)` senza controllare
  se sia il repository, la sorgente del sito o una directory con file estranei.
- **Attuale/atteso:** un parametro errato può eliminare contenuti; la build deve
  rifiutare sorgenti/antenati e directory non riconosciute come output generato.
- **Impatto:** perdita locale di file; non è una vulnerabilità remota dell'app.
- **Proposta:** validare destinazione e provenienza prima della rimozione; build
  ripetibile sulle sole directory generate, nessuna cancellazione dei dati dell'utente.
- **Rischio:** basso/medio, compatibilità con output precedenti da documentare.
- **Test:** filesystem temporaneo con sentinelle; tentativi su sorgente/antenati,
  directory non posseduta e seconda build su output generato.
- **Stato iniziale:** verificato nel sorgente; riproduzione solo su directory di test.

### FR-08 — Conteggio proposte UI dipendente dalla scheda visitata

- **Severità/area:** P2, affidabilità e UX.
- **File/funzione:** `static/app.js:loadUpcoming`, `buildInfographicPayload`, `loadApprovals`.
- **Evidenza:** la dashboard usa solo upcoming dell'aggregato e ignora pending_proposals;
  le statistiche leggono approvalsCache, riempito soltanto aprendo Da verificare e
  senza una chiave di torneo. Il dato può essere zero o appartenere al torneo precedente.
- **Attuale/atteso:** il professore può non vedere le proposte o leggere un numero
  scorretto; il conteggio deve provenire dal server e riferirsi al torneo corrente.
- **Impatto:** proposte non notate e KPI non attendibili; nessun cambiamento dei risultati ufficiali.
- **Proposta:** mostrare il conteggio reale già disponibile nella dashboard e aggiornare
  il dato delle statistiche con cache esplicitamente associata al torneo; sconosciuto = `—`.
- **Rischio:** basso/medio, richieste asincrone e navigazione rapida.
- **Test:** due tornei con conteggi diversi, ingresso diretto nelle statistiche,
  navigazione durante una risposta e flusso studente/docente nel browser.
- **Stato iniziale:** evidenza da sorgente; riproduzione e test da completare.

1. Completare inventario documentale, baseline, controllo dipendenze e segreti.
2. Riprodurre FR-01 e correggere solo con regressioni; controllare altri sport/formati.
3. Verificare FR-04 e la minimizzazione di log/errori.
4. Misurare FR-02/03 prima di intervenire, mantenendo contratti e privacy.
5. Controllare UI, errori, tastiera, sito, build, responsive e coerenza documentale.
6. Suite finale, misure prima/dopo, piccoli commit locali e scorecard motivata.

## Stato della revisione

**IN CORSO — nessuna attestazione di prontezza al rilascio.**
