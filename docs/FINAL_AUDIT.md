# Final review — audit iniziale e registro delle verifiche

27 ottobre 2026. Baseline analizzata: `d7a2dab2a24315bdd3c3067f49d9a75c16fe33b1`.
Stato iniziale pubblicato su `main` su richiesta dell'utente. Revisione esclusivamente
locale su `review/final-optimization`; nessun push delle nuove correzioni né deploy manuale.

Documento creato e committato prima delle modifiche al codice. Le voci iniziali
distinguono evidenza, riproduzione e ipotesi; le sezioni finali riportano esiti,
scorecard, limiti e bozza PR locale. Esito: **PRONTO PER TESTING CONTROLLATO**.

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
- Dipendenze runtime fissate, ambiente Python 3.14.3 e Node locale; baseline: 320 test passati.
- Lettura delle PR tramite API pubblica GitHub: nessuna voce aperta restituita.
  GitHub CLI non autenticato; non sono state cambiate credenziali.
- CI di main `261f456` e del checkpoint `d7a2dab`: successo, verificato separatamente dalle prove locali.
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

## Ordine operativo iniziale

1. Completare inventario documentale, baseline, controllo dipendenze e segreti.
2. Riprodurre FR-01 e correggere solo con regressioni; controllare altri sport/formati.
3. Verificare FR-04 e la minimizzazione di log/errori.
4. Misurare FR-02/03 prima di intervenire, mantenendo contratti e privacy.
5. Controllare UI, errori, tastiera, sito, build, responsive e coerenza documentale.
6. Suite finale, misure prima/dopo, piccoli commit locali e scorecard motivata.

## Stato della revisione

**PRONTO PER TESTING CONTROLLATO.** Nessuna attestazione di sicurezza garantita,
conformità WCAG/GDPR o prontezza per un servizio Internet scolastico.
Il checkpoint richiesto è stato pubblicato su main; tutte le correzioni di questa
revisione restano sul branch locale review/final-optimization.

## Esito finale e ulteriori rilievi

| ID | Priorità | Stato finale / evidenza |
| --- | --- | --- |
| FR-01 | P1 | Risolto: quattro riproduzioni fallivano 20 vs 40/10/105/30 minuti; qualificazione del catalogo delegata al suo servizio, regressioni verdi su sport numerici/set. |
| FR-02 | P2 | Risolto: visibilità SQL e aggregati senza dettaglio/classifiche per ogni torneo; campi del dettaglio caricati in blocco. DTO/ordine/cursori/ruoli equivalenti nei test. |
| FR-03 | P2 | Risolto dopo misura: parsing una volta e finestra temporale; stessi conflitti, orientamento e ordine, verificati contro riferimento pairwise con offset misti. |
| FR-04 | P2 | Risolto per Uvicorn: filtro idempotente, query omesse e token oscurati. Il reverse proxy deve essere configurato separatamente. |
| FR-05 | P2 | Risolto nel perimetro operativo: architettura, sicurezza, schema, deploy, contratto, README e sito riallineati. Consegne storiche indicate come tali, registri originali preservati. |
| FR-06 | P2/P3 | Parziale: IT/light/dark/tastiera/build verificati, Docker ora collaudato. EN assente, telefoni fisici/screen reader/Aruba reale ancora da verificare. |
| FR-07 | P1 | Risolto: output validato prima della rimozione, sorgenti/antenati/symlink/junction rifiutati; output non vuoti richiedono marker generato. Riproduzioni solo su directory temporanee. |
| FR-08 | P2 | Risolto: notifica dashboard, conteggio statistiche dal server associato al torneo, sconosciuto=null, risposte tardive ignorate. Filtri dashboard ricaricano anche gli aggregati. Node e browser con conteggi 1 e 2. |
| FR-09 | P2 | Risolto: services.save_result confrontava solo totali/set, ignorando il tipo forfeit. La correzione a giocato con stessi numeri ora aggiorna score/versione/storia; ripetizione dello stesso risultato giocato resta no-op. Regressione riprodotta prima della correzione. |
| FR-10 | P2 | Risolto per i colori misurati: --muted 3,84:1→5,57:1 su sfondo app; badge generico 3,49→5,43, bozza 3,72→5,11, attivo portato sopra 4,5. Restano dimensioni tipografiche piccole da verificare con utenti. |
| FR-11 | P2 | Risolto nel runtime verificato: immagine prima root/pip 25.0.1/Starlette 1.10.0 diversa dal locale. Ora UID/GID 10001, pip 26.2.2 e Starlette 1.9.0 esplicita. Health/persistenza/backup verificati; requisiti permessi Linux documentati. |
| FR-12 | P2/P3 | Aperto: policy registrazione solo QR, amministratore campi condivisi e collaborazione completa nella SPA non sono implementate. La registrazione studente è pubblica se abilitata; i campi sono del singolo docente e la collaborazione esplicita è V1. Serve una decisione di prodotto prima dell'uso fra scuole. |

FR-09: impatto su semantica/storia e statistiche giocate; correzione interna a
basso rischio, test include risultato ufficiale e no-op successivo.
FR-10: colori modificati solo dove il rapporto misurato era insufficiente;
nessuna riprogettazione e nessuna dichiarazione di conformità completa.
FR-11: nessuna modifica ricorsiva dei permessi del server utente; directory
bind su Linux da predisporre con UID 10001 dopo backup/verifica. Runtime e
installer fissati, non aggiornamento indiscriminato delle dipendenze.
Il type check limitato trovava una sola annotazione mancante in engine.py:
aggiunta list[dict[str,int|None]], nessuna modifica dell'algoritmo.

## Baseline, prove eseguite e limiti

Ambiente locale: Windows, Python 3.14.3, SQLite 3.50.4, Node disponibile;
FastAPI 0.162.0, Pydantic 2.14.1, Uvicorn 0.54.0, Starlette 1.9.0.

| Verifica | Esito e perimetro |
| --- | --- |
| Baseline completa | 320 passed, 1 warning, 807.45 s su d7a2dab. |
| Suite completa revisione | **338 passed, 1 warning, 1006.63 s**. Il warning noto Starlette/httpx è invariato. |
| Incrementi finali | Dopo la suite completa: sola annotazione, etichette studente, separazione file test e contenuti sito; **116 passed, 1 warning, 141.06 s** sui moduli finali; ulteriori 56 controlli rapidi passati. |
| Ruff | I,C4,UP,F,E9: pulito. |
| Python / JS | Compilazione moduli e node --check di app/sito superati. Frontend senza bundler: nessuna build npm dichiarata. |
| OpenAPI | --check sincronizzato; cambia soltanto info.version a 0.9.2, non gli input/DTO. |
| Dipendenze | pip check pulito. pip-audit ambiente e dipendenze effettive container: nessun advisory noto nel controllo puntuale. |
| Tipi | mypy su engine.py, sports.py, schemas.py, platform_schemas.py, access_logging.py: nessun errore; follow-imports=skip/ignore-missing-imports. Non è un type check dell'intero backend/frontend. |
| Pages | Build prod con placeholder risolti, 19 test statici passati; ripetibilità e output protetto verificati. Nessuna pubblicazione di questa revisione. |
| Database | Suite migrazioni A4/B7→8, rollback, riapertura, integrità e backup; nessun DB reale usato per queste prove. Nessuna nuova migrazione. |
| Docker | Build Linux/Python 3.12, health 0.9.2, UID 10001, torneo creato e presente dopo ricreazione; integrità ok, FK vuote, backup VACUUM INTO schema 8 leggibile. |
| Segreti | Scansione pattern di chiavi/token nei file tracciati senza corrispondenze; fixture con identità sintetiche. Non equivale a scansione certificata di tutta la cronologia. |
| CI remota | Checkpoint main d7a2dab: success, run 40483215977. Non attribuito al branch locale di revisione. |

Comandi da torneo-lab: python -m pytest -q; python -m ruff check --select
I,C4,UP,F,E9 .; python scripts/export_openapi.py --check; python -m pip check.
Per Pages dalla radice: python .github/scripts/build_site.py; python -m pytest
--noconftest -q torneo-lab/tests/test_website.py. Node deve essere disponibile
per i test eseguibili del bracket/infografica/adapter: in questa revisione lo era.

I log completi e le misure grezze sono nelle directory ignorate
.work/final-review e torneo-lab/.work/final-review. Le fixture/test riproducibili
sono versionati; nessun DB, cookie o credenziale reale è stato aggiunto al repository.

L'audit iniziale trovava 10 record advisory riferiti soltanto a pip 25.3 locale:
5 problemi unici, con duplicazioni fra feed. Le dipendenze applicative non avevano
avvisi nel controllo. Aggiornato soltanto pip locale a 26.2.2; nel container
rilevato pip 25.0.1 e corretto in Dockerfile. Verifica advisory tramite API
GitHub, per esempio [GHSA-qwm4-qh6w-59xr](https://github.com/advisories/GHSA-qwm4-qh6w-59xr).
Nessuna scansione CVE dell'immagine OS/reverse proxy eseguita; il lock completo
con hash delle dipendenze transitive rimane miglioramento possibile.

## Performance: misure prima/dopo

Harness versionato tests/benchmark_final_review.py, TestClient su SQLite reale
locale temporaneo: 60 tornei, 6 squadre ciascuno, **900 partite programmate**,
nessuna sovrapposizione; docente autenticato. 2 warmup e 9 richieste misurate
per route, mediana e p95 campionario (con 9 campioni coincide col massimo).
Le SELECT sono contate su una richiesta separata con trace SQLite. Nessuna
cache aggiunta. Le due prove sono sulla stessa macchina, non a carico isolato.

| Route | Mediana prima → dopo | p95 prima → dopo | SELECT prima → dopo |
| --- | --- | --- | --- |
| /api/v1/tournaments?limit=50 | 170,257 → 53,950 ms | 180,084 → 65,068 ms | 1687 → 10 |
| /api/calendar | 1568,703 → 159,421 ms | 2222,425 → 169,604 ms | 8 → 8 |

Payload invariati: elenco 27.959 byte, calendario 339.345 byte; confronto JSON
uguale escludendo solo created_at/public_slug generati fra i due dataset.
La regressione sullo stesso DB confronta integralmente riepiloghi vecchio
percorso-detail/nuovo aggregato per proprietario, collaboratore, membro e
non membro; include filtri, cursori, archiviati e torneo altrui pubblicato.
Conflitti confrontati col riferimento pairwise su sovrapposizioni e offset misti.

Limiti: nessun carico multi-client, nessuna misura WAN o telefono. Nel caso
denso in cui tutte le partite si sovrappongano il numero di conflitti è
intrinsecamente quadratico. Il calendario restituisce ancora tutti gli eventi
visibili, non una nuova API paginata. Nessun indice aggiunto senza misura.

Frontend misurato: app.js circa 204 kB (gzip teorico 55 kB), CSS app 69 kB
(gzip 12,5 kB); bracket 4,2 kB e infografica 11,8 kB. Sono dimensioni di file,
non misure LCP/INP o trasferimenti realmente compressi: Uvicorn non abilita
GZip con questa revisione. Asset/font locali, nessuna CDN runtime. Non introdotti
bundler, virtualizzazione o cache senza evidenza sufficiente.

## Flussi, sport, privacy e browser

La suite verifica gironi 2–32 pari/dispari/andata-ritorno, knockout/BYE,
seeding, gruppi→finali, correzioni retroattive e richieste obsolete; set/rally,
pareggi consentiti/vietati, penalità e tavolino, roster/import atomico,
ordine persistente distinto dal seed, iscrizioni/inviti e ultimo posto
concorrente, review concorrente, revoca/CSRF/isolamento e proiezioni pubbliche.
Le 16 varianti del catalogo hanno i test parametrizzati esistenti; V1 offre
cinque preset, non fingere che i due cataloghi siano identici. Le regole sono
scolastiche: vanno confermate col professore, non è certificazione federale.

Browser reale su 127.0.0.1:8021, DB isolato e account sintetici:
login docente; dashboard 3 proposte; ingresso diretto nelle statistiche con
1 proposta nel torneo Nord e 2 nel Sud; approvazione Nord e avanzamento 3–1
in finale; logout; login studente; invio proposta 5–1 nel Sud con risultato
ufficiale ancora nullo. Nessuna azione Approva per lo studente. Modale chiusa
con focus restituito al pulsante, schede navigabili con freccia destra.
Le prove browser precedenti di calendario/campi/inviti restano distinte
(APP_AUDIT_2026_10_27); qui la regressione API li riverifica.

Screenshot reale sintetico del tabellone in website/assets/screenshots/bracket.png,
senza alias studente, credenziali o token. Due riquadri del sito restano
segnaposto dichiarati. Sito IT verificato localmente in tema chiaro e scuro, con tema scuro persistente
al reload e menu chiuso con Escape; tema chiaro e scuro e contrasto token
coperti anche dai test. Non esiste traduzione EN. Browser disponibile senza
API di viewport: nessuna verifica simulata su smartphone dichiarata.
Telefoni fisici, screen reader, zoom testo completo e browser farm restano aperti.

## Scorecard motivata (scala 0–10, giudizio tecnico)

| Categoria | Voto | Evidenze/miglioramento | Rischio residuo e prossima azione |
| --- | --- | --- | --- |
| Architettura | 7 | Confini servizi/engine/DB e adattatori conservati | Doppia linea di regole; pianificare unificazione graduale con contratti |
| Qualità codice | 7 | Lint e regressioni; un'annotazione corretta | app.js e servizi lunghi, typing parziale; incrementi piccoli |
| Backend/API | 8 | 338 test complessivi, DTO stabili, N+1 rimosso | Liste calendario grandi; misurare carico scolastico |
| Database | 8 | Migrazioni, rollback, FK, persistenza e copie verificate | Un worker/disco locale; provare restore operativo con scuola |
| Logica sportiva | 8 | Algoritmi/set/correzioni testati, durata finali corretta | Regolamenti scolastici da approvare; niente formati avanzati inventati |
| Sicurezza | 7 | Permessi, revoca, CSRF, inviti, log e Docker senza root | Proxy/TLS, retention e cancellazione account da completare |
| Privacy | 7 | Whitelist pubbliche e dati sintetici nelle prove | Policy scuola/minori e cancellazione definitiva da concordare |
| Performance | 8 | Riduzione query e tempi misurata | Benchmark locale, non carico reale o prestazioni WAN |
| Frontend/UX | 7 | Proposte visibili e conteggi corretti, feedback reale | Tipografia piccola, etichette/collaborazione SPA ancora migliorabili |
| Accessibilità/mobile | 6 | Contrasto corretto, tastiera/modali e CSS responsive | Nessuna conformità AA completa; telefoni e screen reader da provare |
| GitHub Pages | 7 | Build protetta, IT/temi, roadmap fedele e screenshot reale | EN assente, due screenshot mancanti; nessun deploy locale implicito |
| Test/CI | 8 | Baseline/finale reali, nuovi test, CI main verde | Nessuna CI delle nuove correzioni finché non pubblicate |
| Documentazione | 8 | Fonti operative corrette, storia esplicitata | Molti documenti storici; continuare consolidamento senza duplicarli |
| Deployment | 7 | Container non root, health/ricreazione/backup passati | Permessi Linux, TLS, restart host e Aruba reale da collaudare |
| Manutenibilità | 7 | Commit distinti, nessuna riscrittura/migrazione | Due namespace e file grandi richiedono disciplina nei prossimi incrementi |

## Rischi residui e prossima prova scolastica

1. Concordare con la scuola registrazione solo QR oppure pubblica, gestione
   campi condivisi e responsabilità; le idee precedenti non sono funzioni già implementate.
2. Scegliere server/prodotto Aruba, TLS/host/proxy fidati, permessi UID/ACL,
   backup esterno e prova di ripristino/riavvio. Un dominio non è un server ASGI.
3. Provare con professore/studenti autorizzati un torneo numerico e uno a set,
   su iPhone/Android, tastiera e screen reader; approvare i regolamenti.
4. Definire licenza, informativa, alias minimi, conservazione/cancellazione e
   gestione incidenti prima di dati reali o pubblico Internet.
5. Se EN è obbligatorio per il rilascio, realizzarlo e collaudarlo come incremento
   dedicato; non dichiarare completo un sito soltanto IT.

Questi limiti motivano **PRONTO PER TESTING CONTROLLATO**, anziché una candidatura
al rilascio pubblico. Il testing controllato iniziale usa dati sintetici e un
server supervisionato. Nessun hosting, DNS, firewall o servizio del professore
è stato modificato e nessun aggiornamento del DB reale è stato lanciato.

## Revisione Git e bozza PR locale

Checkpoint pubblicato su main: d7a2dab2a24315bdd3c3067f49d9a75c16fe33b1.
GitHub REST ha restituito [] per le PR aperte, nessuna integrazione pendente
rilevata in quella verifica. La CI del checkpoint è
[verde](https://github.com/Leonardo-Lalli/Open-score/actions/runs/40483215977).
Il lavoro Team B è già nel punto di partenza; i nomi branch del prompt erano storici.

Commit revisione: 5192468 audit prima del codice; 299570b backend/tooling;
b4e1c79 UI; 3a4d2f9 Docker; successivi commit documentali/sito nella cronologia.
I file modificati sono elencati da git diff --stat d7a2dab..HEAD; nuove regressioni
in tests/test_final_review.py, test_final_review_ui.py e final_review_probe.js;
benchmark in tests/benchmark_final_review.py.

Titolo PR proposto: **fix: harden integrated tournament flows and validate local release readiness**.
Base futura main, head review/final-optimization. Descrizione:

> La revisione corregge finali con durata errata tramite V1, semantica delle
> correzioni da tavolino e conteggi UI delle proposte. Riduce query e confronti
> del calendario con equivalenza verificata, minimizza i log sensibili e protegge
> gli output Pages. Runtime Docker allineato e senza root; documentazione e sito
> rappresentano l'integrazione reale. Nessuna migrazione DB o API incompatibile.
> Validazione: 338 test completi più controlli finali mirati, benchmark sintetico,
> browser, build/persistenza/backup Docker. Pronto per testing controllato;
> EN/mobile fisico/Aruba e decisioni scuola rimangono aperti.

Per revisionare: git diff --stat d7a2dab..HEAD; git diff d7a2dab..HEAD -- torneo-lab;
ripetere i comandi sopra in DB sintetico e leggere i limiti. Verificare in particolare
permessi V1, mantenimento degli snapshot sportivi e ownership dei bind mount Linux.
**Nessuna PR remota aperta:** l'istruzione diretta richiede la revisione IN LOCALE.
La bozza è pronta qui; pubblicare il branch/PR richiederebbe una nuova pubblicazione.

## Inventario documenti pertinente

44 Markdown tracciati alla baseline, nessun MDX/AGENTS.md rilevato. Confrontati
con architettura, route/schema, test, handoff e configurazioni. I documenti di
consegna non sono specifiche correnti quando il codice successivo li supera.
Elenco dei percorsi (FINAL_AUDIT è il nuovo documento, non parte della baseline):

- `README.md`
- `docs/API.md`
- `docs/APP_AUDIT_2026_10_27.md`
- `docs/ARCHITECTURE.md`
- `docs/AUDIT.md`
- `docs/BRACKET.md`
- `docs/CHANGELOG.md`
- `docs/CORE_ENGINE_AUDIT.md`
- `docs/CORE_ENGINE_MATRIX.md`
- `docs/CORE_ENGINE_REPORT.md`
- `docs/DATABASE.md`
- `docs/DECISIONS.md`
- `docs/DEPLOY.md`
- `docs/DEPLOYMENT_BACKEND.md`
- `docs/DEVELOPMENT_PLAN.md`
- `docs/DRAG_DROP_ORDERING.md`
- `docs/FEATURE_MATRIX.md`
- `docs/FIELDS_AND_CALENDAR.md`
- `docs/FUNCTIONAL_SPECS.md`
- `docs/GITHUB_PAGES_DOMAIN.md`
- `docs/INFOGRAPHICS.md`
- `docs/PROFESSOR_DASHBOARD.md`
- `docs/PROPOSTA_PROGETTO.md`
- `docs/QR_SHARING.md`
- `docs/QUALITY.md`
- `docs/REFERENCE_ANALYSIS.md`
- `docs/RESULT_APPROVALS.md`
- `docs/SECURITY.md`
- `docs/SPORT_RULES_CONFIG.md`
- `docs/STUDENT_DASHBOARD.md`
- `docs/STUDENT_MANAGEMENT.md`
- `docs/TEAM_B_INTEGRATION_REPORT.md`
- `docs/TEST_REPORT.md`
- `docs/contracts/API_V1.md`
- `docs/design-system.md`
- `docs/handoffs/BACKEND_TO_FRONTEND.md`
- `docs/handoffs/CORE_ENGINE_CONTRACT_PR.md`
- `docs/handoffs/FRONTEND_TO_BACKEND.md`
- `docs/handoffs/TEAM_B_LOG.md`
- `docs/sports_support.md`
- `torneo-lab/README.md`
- `torneo-lab/static/vendor/README.md`
- `website/README.md`
- `website/assets/screenshots/README.md`

### Chiusura delle verifiche

Gli incrementi successivi alla suite completa sono passati in 116 test mirati
(test_final_review, test_final_review_ui, engine, static_ui e website),
1 warning noto, 141.06 secondi. Type check limitato: 5 moduli senza errori.
Ultimo controllo Ruff/JS/pip/OpenAPI pulito. Immagine Docker ricostruita anche
dopo gli ultimi ritocchi. I server e il progetto Compose di collaudo sono stati
fermati al termine; dati sintetici/log restano ignorati per riproducibilità.
