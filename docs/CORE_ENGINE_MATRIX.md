# Matrice core engine — backend 0.3

26 ottobre 2026. Branch leo-develop, baseline precedente `4e15385`.
La matrice storica FEATURE_MATRIX descrive la demo 0.2. Qui si confronta il
Prompt A con l'implementazione locale; UI e revisione remota sono separate.
Esiti effettivi di test e limiti nel [report](CORE_ENGINE_REPORT.md).

| Requisito | Stato backend | Evidenza / limite |
| --- | --- | --- |
| Audit e lettura Markdown | Eseguiti | CORE_ENGINE_AUDIT, aggiornamenti nel report |
| Contratto condiviso | Implementato e generato | API_V1, OpenAPI, controllo automatico; revisione Team B non avvenuta |
| Persistenza e riapertura | Implementate e testate | SQLite reale, schema 4, riapertura risultati e permessi |
| Migrazioni conservative | Implementate e testate | 1/2→4, backup automatico, owner non assegnato implicitamente |
| Backup e restore | Implementati e testati | manage.py, destinazione nuova, integrità e riapertura applicativa |
| Account e password | Implementati e testati | Hash con salt, sessione HttpOnly, CSRF, logout, scadenza e rate limit |
| Proprietario/organizzazioni | Implementati e testati | Isolamento professori, studenti autorizzati, blocco bypass legacy |
| Collaboratori | Supporto esplicito locale | CLI e membership nello stesso contesto; nessuna UI di gestione |
| CRUD tornei | Parziale | Crea/legge/modifica; nessuna cancellazione definitiva |
| Squadre e archiviazione | Implementate e testate | Nomi unici, capienza, versioni; struttura bloccata dopo generazione |
| Studenti e rose | Implementati e testati | Alias, account opzionale, assegnazione/spostamento/rimozione squadra |
| Ricerca e filtri | Implementati | Squadre/studenti, calendario, match e stati; pagine a offset |
| Import studenti massivo | Non implementato | Richiede procedura di deduplicazione e report |
| Ordine persistente | Implementato e testato | Versione collezione, permutazione atomica; seed e match invariati |
| Iscrizioni e capienza | Implementate e testate | Richiesta, approvazione/rifiuto, ultimo posto concorrente |
| Proposte discordanti | Implementate e testate | Record separati, nessun cambiamento alla classifica prima di review |
| Review e risultato ufficiale | Implementati e testati | Ruoli, versioni, approvazione/correzione/rifiuto, storico e rollback |
| Audit attribuibile | Implementato | Actor, snapshot e revisioni; audit separato per campi/sedi |
| Pubblicazione revocabile | Implementata e testata | URL JSON stabile, whitelist pubblica, nessuna rosa/email/audit |
| Inviti QR server-side | Implementati e testati | Hash/scadenza/revoca/usi, identità, idempotenza, concorrenza |
| UI QR e join | Team B, non implementate | URL join previsto, validate/accept funzionanti da API |
| Campi e sedi | Implementati e testati nel perimetro | CRUD/archiviazione campi; sedi create/elencate, niente CRUD sedi completo |
| Disponibilità e calendario | Implementati e testati | UTC/IANA, sport, campo tra tornei, squadre e dipendenze dirette |
| Scheduler automatico | Non implementato | Gestione manuale validata |
| Calcio 11/7/5 | Implementato e testato | Preset scolastici, punti/durate/periodi, pareggi e knockout |
| Basket standard | Implementato e testato | Risultato finale decisivo, punti configurabili |
| Pallavolo indoor | Implementata e testata | Set completi/scarto/decisivo, custom best-of e punti classifica |
| Altre discipline/varianti | Non implementate | Nessuno sport aggiunto come segnaposto |
| Tavolino e penalità | Implementati con limiti | Tavolino esplicito, penalità classifica; blocco penalità dopo qualificazione |
| Round-robin e knockout | Conservati e testati | 2–32, BYE, andata/ritorno, correzioni e qualificazioni |
| Dati bracket espliciti | Implementati e testati | Sorgenti e next slot, campione, risultato ufficiale distinto |
| Statistiche | Implementate e testate | Squadre/studenti/match/proposte, percentuale, qualificate, pubblico sicuro |
| CI backend | Presente | Workflow tests.yml esteso automaticamente dalle nuove suite, nessun run remoto dichiarato |
| Deployment e Aruba | Documentati, non eseguiti | Config service, TLS/backup/rollback; prodotto Aruba sconosciuto |
| PostgreSQL | Valutato, non implementato | Necessari adapter e migrazioni dedicate |
| Frontend end-to-end | Non integrato | Asset e README principale invariati, handoff aggiornato |
| Push/PR/merge | Non eseguiti | Divieto esplicito dell'utente; solo commit locali |
