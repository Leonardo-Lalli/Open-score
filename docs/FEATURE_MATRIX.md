# Matrice funzionale — demo 0.7

Stati ammessi: **Non analizzata**, **Documentata**, **Progettata**, **Implementata**, **Testata**, **Verificata end-to-end**. Lo stato indica il livello massimo raggiunto per il perimetro scritto nella riga. Una funzione parziale non diventa completa per la presenza di una schermata. `tests/` e i file applicativi sono nella cartella `torneo-lab`.

Fonti: **U** = screenshot/JSON utente; **KB** = [indice ufficiale](https://kb.score7.io/docs/); **RR** = [campionati](https://www.score7.io/it/campionati); **MF** = [multifase](https://kb.score7.io/docs/getting-started/multi-stage-tournament/); **DE** = [doppia eliminazione](https://kb.score7.io/docs/getting-started/double-elimination/); **SW** = [Swiss](https://kb.score7.io/docs/getting-started/swiss-format/); **CC** = [consolazione](https://kb.score7.io/docs/getting-started/cup-and-consolation/); **SC** = [scheduler](https://kb.score7.io/docs/scheduling/auto-generate-schedule/).

| Funzione e perimetro | Stato | Fonte | File / verifica | Problemi aperti |
| --- | --- | --- | --- | --- |
| Creazione con wizard e riepilogo; elenco persistente | Verificata end-to-end | U, KB | app.py, schemas.py, app.js; test_api; prova browser tre squadre | Modifica/eliminazione torneo, paginazione |
| Configurazione iniziale sport/variante/regole | Verificata end-to-end | U, RR | schemas.py, services.py, sport_rules.py; test_sports, test_sets; browser | Modifica struttura bloccata dopo la generazione |
| Partecipanti team/individual; nomi e rimozione in bozza | Testata | U, KB | app.py; test_participant_editing… | Iscrizioni autonome |
| Catalogo sei sport e sedici varianti con schermate dedicate | Verificata end-to-end | Scelta originale | sport_rules.py, app.py, migrations/006, app.js; test_sports (32 test su tutte le coppie), test_migrations; browser | Regolamenti da confermare con il professore |
| Giocatori appartenenti alle squadre e rose | Testata | KB | team_players, app.py, services.py, app.js; test_players; browser | Statistiche individuali |
| Girone pari/dispari, andata/ritorno | Testata | RR | engine.py; test_round_robin_invariants | Andata/ritorno verificato nei test, non nel percorso browser |
| Risultati numerici, set per set e classifica | Verificata end-to-end | RR | services.py, app.js; test_sets; browser Pallavolo | Rigori, penalità e statistiche individuali |
| Knockout 2–32, BYE e campione | Verificata end-to-end | U, KB | engine.py, services.py; test_complete_knockout…; browser | Piazzamenti e più gare per incontro |
| Sorteggio riproducibile | Testata | Scelta originale | engine.py, random_seed via API; test_seed_reproducible | Controllo seed non esposto nel wizard |
| Correzioni e invalidazione dipendenze | Verificata end-to-end | KB, scelta originale | services.py; test_safe_knockout_correction…; browser con errore e conferma | Ripristino automatico da audit |
| 16 squadre, 4 gruppi, prime 2 ai quarti | Testata | MF | services.py; test_multiphase_16_teams_and_requalification | E2E browser fino al campione multifase non eseguito |
| Gironi→knockout generale ridotto | Testata | MF | services.py; API | Solo gruppi uguali, prime 1/2, tutti i gruppi completati |
| Migliori terzi, Swiss→finali, gironi→doppia eliminazione | Documentata | MF | FUNCTIONAL_SPECS | Non implementati |
| Doppia eliminazione | Documentata | DE | FUNCTIONAL_SPECS | Nessun motore upper/lower |
| Swiss Classic e criteri dedicati | Documentata | SW | FUNCTIONAL_SPECS | Nessun pairing Swiss o Buchholz/Sonneborn-Berger/ELO |
| Swiss with Pots | Documentata | SW | FUNCTIONAL_SPECS | Nessun generatore a vincoli |
| Cup & Consolation | Documentata | CC | FUNCTIONAL_SPECS | Nessun secondo tabellone indipendente |
| Data, campo, durata e conflitti conosciuti | Testata | U, SC | services.py; test_schedule_overlap_and_timezone | Non è uno scheduler globale |
| Scheduler automatico, riposi, disponibilità | Documentata | SC | FUNCTIONAL_SPECS | Non implementato |
| Sedi/campi e arbitri come risorse | Documentata | KB, SC | FUNCTIONAL_SPECS | Campo è solo testo, niente inventario o arbitri |
| Bracket con collegamenti e avversari futuri | Verificata end-to-end | U | app.js, styles.css; prova browser con BYE | Zoom/pan dedicati non presenti; scorrimento orizzontale |
| Tab Regolamento e regolamento congelato per torneo | Verificata end-to-end | Scelta originale | services.py, app.js; test_sets; browser | Stampa tramite finestra del browser |
| Statistiche aggregate dei risultati | Testata | Scelta originale | services.detail, dashboard; test_api | Statistiche individuali non implementate |
| Pagina spettatore locale | Verificata end-to-end | KB | GET public, app.js; test_public_read_only…; browser | Sola lettura; nessun hosting su Internet |
| Gate prof/studente, login email/password e blocco scritture | Implementata e testata | Scelta originale | auth.py, app.py, app.js, index.html; test_auth, test_static_ui | Manca una prova browser automatizzata del gate |
| Deployment in LAN, backup e segreto di sessione | Testata | Scelta originale | deploy/, backup.py; test_backup, test_hosts | HTTPS richiede un reverse proxy esterno |
| Personalizzazione nome/descrizione iniziale | Testata | U, KB | wizard, schemas.py | Loghi, temi e URL personalizzati non presenti |
| CSV export incontri con dettaglio set | Testata | KB | app.py; test_csv_zero_scores_and_formula_names | Import CSV e PDF non implementati |
| Ritiri e forfait | Documentata | KB | FUNCTIONAL_SPECS | Nessun esito a tavolino distinto da punteggio |
| Database persistente e schema versionato | Testata | Starter, scelta originale | db.py, migrations; test_persistence_and_migration, test_migrations | Import legacy e produzione PostgreSQL |
| URL legacy, asset statici e cache | Verificata | Scelta originale | app.py, static/*.html, static/app.js; test_static_ui | Vecchi URL reindirizzati alla SPA; asset versionati e dashboard no-cache |
| Interfaccia mobile iPhone/Android | Implementata e verificata staticamente | Scelta originale | styles.css, index.html, app.js; test_static_ui | Manca una prova su dispositivo reale o browser farm; layout responsive fino a 360 px |
| Account docenti e isolamento per torneo | Implementata e testata | KB, master prompt | migrations/007_teachers.sql, auth.py, services.py, app.py; test_teacher_isolation | Ogni prof gestisce solo i propri tornei; mancano disattivazione account e ruoli amministrativi |
| Varianti e regolamenti del catalogo standard | Implementata e verificata | — | migrations/006_sport_variants.sql; test_sports | Sedici varianti standard coperte e verificate una per una; eventuali nuovi formati vanno concordati con il professore |

Le fonti e il grado di certezza sono dettagliati in [REFERENCE_ANALYSIS.md](REFERENCE_ANALYSIS.md). L'architettura futura non è dichiarata esistente.
