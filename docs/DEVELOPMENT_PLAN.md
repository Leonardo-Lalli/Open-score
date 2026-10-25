# Piano per passi verificabili

## Incremento consegnato: sport, varianti e regole 0.4

Obiettivo: portare la demo da un unico modello numerico a sei sport con varianti selezionabili, rose dei giocatori e punteggi set per set, mantenendo tornei, classifiche, tabelloni, persistenza e protezione delle scritture già consegnati nella 0.3.

| Milestone | Stato in questa consegna | Criterio di completamento |
| --- | --- | --- |
| 0 — Audit | Eseguito | ZIP confrontato con la cartella, test originali eseguiti, limiti documentati |
| 1 — Fondamenta demo | Implementata e testata | Moduli separati, schema versionato, transazioni e validazioni; test riproducibili |
| 2 — Tornei e partecipanti | Implementata nel perimetro demo | Creare/elencare/modificare/archiviare tornei, aggiungere/rinominare/rimuovere partecipanti in bozza, rose con numero di maglia; manca l'import CSV |
| 3 — Motori base | Implementata e testata nel perimetro demo | Gironi sola andata/ritorno, dispari, knockout 2–32, BYE, avanzamento e correzioni coerenti |
| 4 — Multifase | Implementata e testata nel perimetro demo | 16 squadre → 4 gironi → 8 qualificate → 7 knockout → campione; niente promozione anticipata |
| 5 — Formati avanzati | Documentata, non implementata | Futuro: doppia eliminazione collegata, Swiss Classic e Pots distinti, Cup & Consolation; test propri prima della UI |
| 6 — Calendario | Parziale | Durata predefinita dalla variante, assegnazione manuale UTC e controllo conflitti noti; scheduler globale non implementato |
| 7 — Interfaccia demo | Implementata | SPA unica: dashboard, catalogo sport, wizard gerarchico sport → variante, riepilogo, partecipanti, rose, scheda squadra, incontri, classifica, bracket, regolamento, diario, CSV e vista spettatore; i vecchi URL di design reindirizzano alla SPA |
| 8 — Sicurezza e multiutenza | Implementata per i docenti | Account docente con email/password, sessione firmata, gate prof/studente, scritture protette e isolate per proprietario, host ammessi e limite ai tentativi; mancano ruoli amministrativi e disattivazione account dalla UI |
| 9 — Produzione LAN | Implementata e documentata | Avvio come attività pianificata o servizio systemd, backup `VACUUM INTO` con conservazione, ripristino, HTTPS tramite proxy esterno e lista di controllo |
| 10 — Sport, varianti e regole | Implementata e testata | Sei sport, sedici varianti, schermate dedicate con deep link, rose con minimo/massimo e lineup visibile, durata e classifica derivate dalle regole, set per set, snapshot del regolamento |

## Incremento 0.4.1 — affidabilità del flusso di modifica

Obiettivo: chiudere i difetti emersi durante la verifica del percorso sport → variante → modifica, senza cambiare catalogo, schema o dati già salvati.

| Milestone | Stato in questa consegna | Criterio di completamento |
| --- | --- | --- |
| Modifica di una bozza | Corretta e testata | Il payload della modale non invia più `format: null`; la struttura corrente resta invariata e il salvataggio risponde 200 |
| `null` espliciti | Corretta e testata | I campi non annullabili rifiutano `null` con 422 invece di provocare un errore 500 del database |
| Cambio sport in modifica | Corretta | La select `edit-sport` aggiorna varianti, rosa, durata e regolamento prima del salvataggio |
| Punti della variante | Corretta | Vittoria, pareggio e sconfitta usano i valori `win`/`draw`/`loss` della variante selezionata |
| Composizione della squadra | Corretta e testata | La scheda squadra mostra giocatori in campo, minimo per iniziare, rosa massima e giocatori mancanti; la pagina partecipanti riepiloga le rose pronte |
| Formato in bozza | Implementata e testata | La modale permette di scegliere eliminazione, girone unico o gironi + finali, con opzioni dei gironi dinamiche e controllo client sui gruppi |
| Integrità del catalogo | Testata | Un test verifica tutte le sedici varianti: slug univoci, lineup coerente, durata, modalità di punteggio, parametri set e regolamento |
| Regressioni | Testata | Cinque test nuovi o estesi; suite a **147 passed** |
| Conformità sport/varianti | Verificata | 32 test parametrizzati coprono tutte le 16 coppie sport/variante: regole, regolamento, creazione, generazione e durata; suite a **184 passed** |

Residuo noto: la lineup minima è mostrata ma non bloccante; la generazione resta possibile anche con rose incomplete, scelta utile per la demo scolastica. Il formato è modificabile solo finché il torneo è in bozza, coerentemente con il blocco dei campi strutturali dopo la generazione.

## Incremento 0.5.0 — allineamento, pulizia e cache

Obiettivo: eliminare i disallineamenti tra branch e i contenuti legacy che mostravano sport non previsti, quindi rendere visibile lo stato reale del codice.

| Milestone | Stato in questa consegna | Criterio di completamento |
| --- | --- | --- |
| Merge `sport-e-regole` → `develop` | Allineato | `sport-e-regole` è antenato di `develop`; merge "Already up to date", nessun conflitto |
| Pulizia mockup legacy | Completata e testata | I cinque URL legacy reindirizzano alla SPA; nessun riferimento a sport fuori catalogo negli asset statici |
| Interfaccia unica | Completata | Rimosso il ramo JavaScript delle pagine di design; la SPA è l'unica UI |
| Cache file statici | Corretta e testata | Asset versionati (`app.js`, `styles.css`), dashboard e asset HTML/JS/CSS con `Cache-Control: no-cache` |
| Verifica | Testata | `test_static_ui` più suite completa a **184 passed** |

## Incremento 0.6.0 — ottimizzazione mobile

Obiettivo: rendere l’interfaccia utilizzabile senza attriti su iPhone e Android, prima di aggiungere nuove funzionalità.

| Milestone | Stato in questa consegna | Criterio di completamento |
| --- | --- | --- |
| Viewport e safe area | Implementata | `viewport-fit=cover`, `100dvh` e `env(safe-area-inset-*)` su shell, drawer, toast e modali |
| Touch target | Implementata | Pulsanti, icone, tab, filtri e navigazione almeno 44 px; input a 16 px contro lo zoom iOS |
| Navigazione mobile | Implementata | Topbar sticky, drawer con scrim, blocco scroll, chiusura con tap esterno, Escape o resize |
| Modali | Implementata | Full-screen su mobile, header/footer fissi e corpo scrollabile |
| Tabelle e bracket | Implementata | Scroll orizzontale, overscroll contenuto e larghezza minima leggibile |
| Verifica | Testata | `test_static_ui` aggiornato; suite a **185 passed** |

## Incremento 0.7.0 — ruoli prof/studente e isolamento per docente

Obiettivo: separare nettamente consultazione e gestione, con account docente individuali e tornei accessibili solo al proprietario.

| Milestone | Stato in questa consegna | Criterio di completamento |
| --- | --- | --- |
| Gate iniziale | Implementata | Due scelte immediate: **Sono un prof** (verde) e **Sono uno studente** (colore secondario) |
| Login docente | Implementata | Email e password, hash PBKDF2-SHA256, sessione firmata con `teacher_id` ed email |
| Modalità studente | Implementata e testata | UI senza comandi di modifica; ogni scrittura `/api` risponde 401 |
| Proprietà dei tornei | Implementata e testata | `tournaments.teacher_id`; un docente non può modificare tornei altrui (403) |
| Lista e dettaglio | Implementata | `?mine=1` per i propri tornei; `can_manage` su lista, dettaglio e scheda squadra |
| Bootstrap e gestione account | Implementata | `TORNEO_ADMIN_EMAIL`/`TORNEO_ADMIN_PASSWORD` e CLI `manage.py` |
| Verifica | Testata | `test_auth`, `test_teacher_isolation`, `test_static_ui`; suite a **189 passed** |
| Qualità statica | Implementata | `pyproject.toml` per ruff (target Python 3.10); 0 errori e 0 warning nel progetto |

## Verifica di conformità alla specifica

| Requisito | Implementazione | Verifica |
| --- | --- | --- |
| Sei sport selezionabili | `sport_configs` + `sport_rules.list_sports` + select del wizard | `test_sports_endpoint_reads_the_database_catalog` |
| Varianti standard per ogni sport | 16 righe in `sport_variants`, ognuna con slug, nome e regole | `test_every_sport_variant_pair_has_rules_and_regulation` |
| Selezione gerarchica sport → variante | `wizard-sport` aggiorna `wizard-variant`; `edit-sport` aggiorna `edit-variant`; catalogo `#/sport` → `#/sport/{sport}` → `#/sport/{sport}/{variante}` | `test_sports`, test browser della fase 6, payload della modale |
| Schermata dedicata per ogni combinazione | vista catalogo con regolamento, pillole delle regole, roster e CTA «Crea torneo» | deep link e `test_every_variant_drives_creation_generation_and_duration` |
| Composizione e gestione squadre | `participant_kind`, `players_on_field`, `min_lineup`, `max_roster`; limite rose e avvisi «mancano N» | `test_players`, `test_team_view_exposes_lineup_rules_from_the_variant` |
| Durata delle partite | `match_duration` usato in `generate` e come default in `schedule` | `test_schedule_uses_variant_duration`, test parametrizzato sulla durata |
| Regolamento applicato al torneo | `rules_snapshot` e `regulation_snapshot` copiati alla creazione; tab Regolamento | `test_tournament_detail_embeds_its_sport_and_variant`, test parametrizzato |

## Sport e varianti della 0.4

| Sport | Varianti | Modello di punteggio | Rosa massima |
| --- | --- | --- | --- |
| Calcio | a 11, a 7, a 5 | reti, pareggio ammesso | 22 / 14 / 12 |
| Basket | 5 contro 5, 3x3 | punti, nessun pareggio | 12 / 4 |
| Pallavolo | 6 contro 6, 4 contro 4, beach volley 2 contro 2 | set con bonus al tie-break nella 6v6 | 14 / 8 / 2 |
| Badminton | singolare, doppio, doppio misto | set a 21 con limite a 30 | 1 / 2 / 2 |
| Ping pong | singolare, doppio, doppio misto | game a 11 | 1 / 2 / 2 |
| Biliardino | singolare, doppio | gol a tempo o a 5 | 1 / 2 |

Le varianti individuali iscrivono persone; quelle a squadre usano la rosa. Pallamano e Tennis non fanno più parte del catalogo: i tornei storici restano leggibili, ma ogni scrittura riceve 409.

## Prossimo incontro

Provare in palestra una variante a set (Pallavolo 6v6 o Ping pong) e una a squadre con rosa (Calcio a 5), verificando durata, numero di giocatori e criteri di classifica con il professore. Con il professore verificare anche il flusso di accesso prof/studente e la creazione dei primi account docente.

## Collaborazione iniziale

Una persona può curare UI e prove con il professore, l'altra motore, API e dati. Revisioni e regole restano condivise. Attività piccole in Issues; branch e pull request con controllo dei test prima dell'unione. Le durate dipendono dalla disponibilità dei due collaboratori: questa roadmap non promette una scadenza scolastica non concordata.

## Passo tecnico successivo consigliato

Confermare con la scuola i regolamenti delle varianti e aggiungere test sui casi reali emersi dalla prova. Completare importazione CSV e gestione delle rose durante il torneo. La LAN scolastica è già coperta da account docenti, backup e avvio automatico; prima del push finale su `main` vanno rimossi i dati mock e va verificata la disattivazione degli account che lasciano la scuola.
