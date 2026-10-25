# Changelog

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
