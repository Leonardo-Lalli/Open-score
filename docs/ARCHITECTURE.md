# Architettura — integrazione 0.9.2

FastAPI/Pydantic, SQLite schema **8** e SPA vanilla sullo stesso origin.
Nessun framework frontend, ORM o servizio remoto necessario. `website/` è una
vetrina separata: GitHub Pages non esegue l'applicazione.

| Moduli | Responsabilità |
| --- | --- |
| app.py, access_logging.py | Factory, Host/Origin, cookie, statici, CSV, minimizzazione log |
| frontend_api.py, schemas.py | Adapter usati dalla SPA: studenti, import, proposte, campi/calendario/dashboard |
| v1_api.py, v1_schemas.py, v1_dto.py | API autenticate, input rigorosi, risposte con whitelist e paginazione |
| auth.py, platform_auth.py, identity_bridge.py | Login storico, utenti/sessioni e collegamento dei due namespace |
| services.py, sport_rules.py | Catalogo di sei sport/sedici varianti e snapshot dei tornei |
| platform_services.py, sports.py | Preset V1, risultati, delega al catalogo quando autorevole |
| v1_domain.py, v1_results.py, v1_resources.py | Permessi, squadre/studenti, revisioni, inviti e prenotazioni |
| roster_bridge.py | Sincronizzazione atomica fra profili e rose |
| engine.py | Gironi, seeding/BYE, knockout e classifica |
| db.py, migrations/ | Migrazioni conservative, FK, WAL, lock e rollback |
| manage.py, platform_manage.py, backup.py | Amministrazione locale e copie consistenti |
| static/ | UI italiana; bracket e infografica in moduli puri testabili con Node |

Il browser invia una richiesta al router; i servizi verificano permessi e
versioni e usano il motore puro; `db.py` gestisce la transazione SQLite.
Ogni richiesta possiede una connessione. Le scritture prendono `BEGIN IMMEDIATE`
prima della lettura. Revisione, risultato, audit, classifica, avanzamento e
controllo calendario condividono la transazione. Il client rilegge dopo il commit.
Conferma esplicita per invalidare risultati dipendenti; l'ordine visuale delle
squadre ha una versione separata e non cambia il seed.

I due cookie sono revocabili sul server; `teacher_user_links` collega ID distinti.
`team_players.student_id` collega rose e profili. Classifiche derivate senza cache;
riepiloghi V1 aggregati e calendario con confronto delle finestre sovrapposte.
La doppia linea di servizi/regole rimane debito di manutenzione: non è stata
unificata con un refactoring esteso durante la revisione.

`demo` indica configurazione locale, non scritture anonime o dati dimostrativi.
`service` richiede origin HTTPS e host espliciti e mantiene SPA e autorizzazioni.
Proprietari, collaboratori V1 e iscritti hanno accessi distinti; i collaboratori
non hanno ancora tutte le azioni nella SPA storica. Pubblicazione revocabile,
proiezioni pubbliche senza rose, email, audit o proposte.

Un'istanza, un worker, disco persistente locale. TLS, riavvio e backup restano
responsabilità dell'installazione. Vedere [sicurezza](SECURITY.md),
[database](DATABASE.md), [API V1](contracts/API_V1.md),
[deployment](DEPLOYMENT_BACKEND.md) e [audit finale](FINAL_AUDIT.md).
