# 0.9.2 — revisione locale del 27 ottobre 2026

Durata delle finali coerente col catalogo anche via V1; correzione da tavolino
a giocato con punteggio identico; riepiloghi V1 aggregati e conflitti calendario
per finestre temporali; token minimizzati nei log; build Pages protetta;
conteggi proposte per torneo e notifica dashboard; contrasto corretto.
Docker senza privilegi, pip corretto e Starlette fissata alla versione verificata.
Documentazione/sito riallineati, screenshot sintetico reale. Nessuna migrazione
DB né modifica incompatibile delle API. Nuove correzioni non pubblicate:
[FINAL_AUDIT.md](FINAL_AUDIT.md) contiene prove, limiti e preparazione al rilascio.

---

# Integrazione locale 0.9.0 — 26 ottobre 2026

Integrato `max-develop` @ `0896096` in `leo-develop`, senza push/deploy.
Schema 8 compatibile con i due schemi originari, adapter attivi per proposte,
inviti, campi, calendario e ordine, import atomico e account studenti collegati.
Dettaglio, compatibilità e limiti nel [report integrazione](TEAM_B_INTEGRATION_REPORT.md).

---

# Changelog

## 0.8.0 — 26 ottobre 2026

- Rimosso ogni dato dimostrativo preinstallato: niente seed automatico all'avvio, niente `POST /api/demo`, eliminati `demo.py` e la fixture JSON.
- Il database parte vuoto; studenti e docenti vedono solo i tornei creati e persistiti.
- Rimossi i comandi **Esplora la demo** e **Carica esempi**, le etichette dimostrative e l'anteprima basata sui dati finti.
- Versione applicativa 0.8.0 e asset a `v=0.8.0`.

## 0.7.0 — 25 ottobre 2026

- Nuovo ingresso con due scelte: **Sono un prof** (login email/password) e **Sono uno studente** (sola lettura). La scelta studente nasconde i comandi di modifica; il backend rifiuta comunque ogni scrittura senza sessione docente con 401.
- Migrazione 007: tabella `teachers` con email unica e hash PBKDF2-SHA256, colonna `tournaments.teacher_id`. I tornei esistenti restano NULL e di sola lettura finché non vengono assegnati.
- Account docenti separati: ogni prof gestisce solo i propri tornei; i tornei altrui rispondono 403 alle scritture e mostrano `can_manage: false`. Lista `?mine=1` per la dashboard del docente.
- Bootstrap del primo docente con `TORNEO_ADMIN_EMAIL`/`TORNEO_ADMIN_PASSWORD`; CLI `manage.py` per creare docenti, elencarli e reimpostare la password. Rimosso il Bearer token globale.
- UI: gate iniziale con card verde per il prof e secondaria per lo studente, login dedicato, topbar con identità/ruolo, tag **Solo lettura** e azioni nascoste per studenti e tornei non propri.
- Versione applicativa 0.7.0, asset a `v=0.7.0` e **189 test**.
- Avvio con Docker tramite `Dockerfile` e `docker-compose.yml`; README root snellito, con dettagli e hosting spostati in `torneo-lab/README.md`.

## 0.6.0 — 25 ottobre 2026

- Ottimizzazione mobile iPhone/Android: `viewport-fit=cover`, `100dvh` e safe area su topbar, sidebar, main, footer, toast e modali.
- Topbar sticky, drawer con scrim e blocco dello scroll, chiusura con tap esterno, tasto Escape o resize; touch target minimo di 44 px.
- Modali full-screen con header e footer fissi e corpo scrollabile; input a 16 px per evitare lo zoom automatico di iOS; tabelle e bracket con scroll orizzontale e overscroll contenuto.
- Cache-busting degli asset a `v=0.6.0`; versione applicativa 0.6.0 e **185 test**.

## 0.5.0 — 25 ottobre 2026

- Allineamento branch: `sport-e-regole` è già antenato di `develop`; il merge è risultato "Already up to date", senza conflitti.
- Rimosse le pagine mockup legacy che contenevano sport non previsti dal progetto. I vecchi URL (`/create.html`, `/gestione_partecipanti.html`, `/panoramica_torneo.html`, `/tabellone_torneo.html`, `/campione_sport_editorial.html`) reindirizzano alla SPA.
- La SPA è l'unica interfaccia: rimosso il ramo JavaScript che collegava le pagine di design e i relativi rimandi.
- Cache e file statici: `index.html` referenzia gli asset versionati; dashboard e asset HTML/JS/CSS sono serviti con `Cache-Control: no-cache, must-revalidate`.
- Nuovi test su redirect legacy, assenza di sport fuori catalogo negli asset, versionamento e cache. Versione applicativa 0.5.0 e **184 test**.

## 0.4.1 — 25 ottobre 2026

- Corretto il salvataggio della modifica di una bozza: il form SPA inviava `format: null` e il server rispondeva 500 per il vincolo `NOT NULL`. Ora il formato viene omesso quando non è modificato e i `null` espliciti sui campi non annullabili ricevono 422.
- Corretto il cambio sport nella modale di modifica: l'id `edit-sport` non era collegato al listener, quindi l'elenco delle varianti restava fermo sullo sport precedente.
- Cambiando variante in modifica, i punti di vittoria/pareggio/sconfitta vengono riallineati ai valori della variante (prima la mappatura usava chiavi inesistenti).
- La modale di modifica espone ora il formato (eliminazione, girone unico, gironi + finali), mostra o nasconde le opzioni dei gironi e blocca le gare di ritorno nell'eliminazione. Il salvataggio valida i gruppi prima della richiesta.
- La scheda squadra espone `players_on_field`, `min_lineup` e il nome della variante; la pagina partecipanti riepiloga le rose pronte sul minimo e, per ogni squadra, i giocatori presenti e mancanti.
- Test di regressione per payload della modale, `null` espliciti, cambio formato, limiti della lineup e integrità di tutte le sedici varianti (slug, durata, punteggio, rosa e regolamento). Versione applicativa 0.4.1, suite a **147 test**.
- Verifica esaustiva delle sedici coppie sport/variante: 32 test parametrizzati su regole, regolamento, creazione, generazione e durata. Suite a **179 test**.

## 0.4.0 — 25 ottobre 2026

- Migrazione 006: catalogo di sei sport padre e sedici varianti in `sport_variants`, snapshot `rules_snapshot`/`regulation_snapshot`, rose `team_players`, dettaglio set `match_sets`.
- Catalogo definitivo: Calcio (a 11, a 7, a 5), Basket (5v5, 3x3), Pallavolo (6v6, 4v4, beach 2v2), Badminton (singolare, doppio, misto), Ping pong (singolare, doppio, misto), Biliardino (singolare, doppio).
- Calcio a 5 non è più uno sport separato; gli sport fuori catalogo sono rimossi e i relativi tornei restano leggibili in sola lettura con risposte 409 alle scritture.
- La variante determina tipo partecipante, durata degli incontri, punti di classifica, criterio predefinito, rosa e regolamento; i valori sono congelati alla creazione del torneo.
- Nuove API per varianti (`/api/sports/{sport}/variants/{slug}`, `/api/variants/{slug}`) e per le rose (`/teams/{id}/players`), con massimo da variante e duplicati bloccati.
- Punteggio set per set per Pallavolo, Badminton e Ping pong: validazione di set, punti minimi, scarto, limite e vittoria; classifica con set vinti/persi e bonus 2/1 al quinto set della Pallavolo 6v6.
- Validazioni specifiche: nessun pareggio in Basket e knockout, risultati numerici rifiutati sulle varianti a set e viceversa, durata di gara predefinita dalla variante.
- SPA: voce **Sport e regole**, catalogo con deep link `#/sport/...`, wizard gerarchico sport → variante con anteprima regole, tab **Regolamento**, inserimento risultati set per set e gestione rose nella scheda squadra.
- CSS dedicato a catalogo, regolamento, pillole delle regole, set e rose; stampa del regolamento.
- Export CSV arricchito con il dettaglio dei set.
- Versione applicativa 0.4.0, schema 6 e 142 test automatici; flusso SPA verificato con browser headless. La correzione 0.4.1 porta la suite a 144 test.
- Restano da implementare account individuali, ruoli per torneo, statistiche individuali, import CSV e scheduler automatico.

## 0.3.0 — 25 ottobre 2026

- Migrazioni applicate fino alla versione 5: `sport_id`, catalogo sport canonico, `archived_at`, `updated_at` e `tie_breaker`.
- SQLite in WAL con `busy_timeout`; sport risolto lato server e coerente con il nome.
- Catalogo sport unico letto da `sport_configs` tramite `/api/sports`; il wizard carica gli sport dal server.
- Il dettaglio torneo espone `sport_config`; le pagine di design restano mockup statici e mostrano un avviso.
- Modifica parziale del torneo con blocco dei campi strutturali dopo la generazione.
- Archiviazione e ripristino al posto della cancellazione; i tornei archiviati sono di sola lettura.
- Criterio a parità di punti configurabile (`goal_difference`, `head_to_head`, `goals_for`, `wins`) nel wizard e nella modifica in bozza.
- Scheda partecipante con girone, posizione, classifica e incontri tramite `/api/tournaments/{id}/teams/{team_id}` e modale dedicata.
- Vista pubblica in sola lettura con aggiornamento automatico ogni 30 secondi, sospeso a scheda nascosta o modale aperta.
- Accesso dell'organizzatore con `TORNEO_ADMIN_PASSWORD` o Bearer `TORNEO_API_TOKEN`; scritture `/api` protette, letture e link pubblico aperti, ruolo unico `admin`.
- Sessione con cookie `open_score_session` firmato HMAC, `HttpOnly`, `SameSite=Lax`, durata configurabile e logout.
- Limite di 5 tentativi errati in 5 minuti per IP con blocco di 60 secondi; intestazioni CSP, `nosniff` e `Referrer-Policy`.
- Host della LAN ammessi tramite `TORNEO_ALLOWED_HOSTS`; con autenticazione assente resta la modalità demo locale aperta.
- UI di accesso e uscita, comandi di modifica nascosti agli spettatori e richiesta di accesso al primo click su un risultato.
- Backup online consistente con `VACUUM INTO`, conservazione configurabile e verifica di integrità.
- Asset di deployment: attività pianificata Windows, servizio systemd, esempio di configurazione e script di backup.
- Documentazione di installazione LAN, sicurezza e ripristino; versione applicativa 0.3.0.
- 118 test automatici e verifiche browser di modifica, archivio, criteri, scheda squadra, accesso, host e vista pubblica.
- Restano da implementare account individuali, ruoli per torneo, rose, set/rigori e scheduler automatico.

## 0.2.0 — 24 ottobre 2026

- Audit dello starter ZIP e baseline dei sei test originali.
- Backend separato in entry point, servizi, validazioni, database, fixture e motore.
- Dashboard e wizard originali, viste partecipanti/partite/classifiche, tabellone collegato e adattamento responsive.
- Knockout da 2 a 32 partecipanti anche dispari, BYE, seeding riproducibile via API, avanzamento per incontro e gestione delle correzioni con audit.
- Gironi andata/ritorno e percorso a più fasi con qualificazioni automatiche e controllate.
- Programmazione manuale con UTC, conflitti di campo/partecipanti conosciuti e versioni per evitare salvataggi obsoleti.
- Quattro esempi locali, incluso il JSON fornito; vista spettatore di sola lettura ed export CSV.
- Test degli algoritmi/API e documentazione concreta del perimetro. Formati avanzati, set e account restano da implementare.
