# Database e conservazione dei dati

Default: `torneo-lab/data/open_score.sqlite3`. Percorso configurabile con `TORNEO_DB_PATH`. Il file, i database di test e l'ambiente Python sono esclusi da Git. I quattro esempi vengono creati al primo avvio di un database nuovo. `POST /api/demo` aggiunge gli esempi mancanti senza azzerare i risultati esistenti.

## Schema effettivo (versione 5)

| Tabella | Chiave e relazioni | Dati e vincoli principali |
| --- | --- | --- |
| sport_configs | PK id; nome unico | Catalogo canonico degli sport: nome, descrizione, sistema di punteggio, regole JSON |
| tournaments | PK id; FK sport_configs; public_token e demo_key unici | Formato enumerato, nome non vuoto, sport testuale (snapshot) e `sport_id` coerente, tipo team/individual, regole dei punti, numero gironi e qualificate, andata/ritorno, seed, tipo torneo, sistema di punteggio, `archived_at`, `updated_at`, `tie_breaker` |
| stages | PK id; FK torneo; UNIQUE(torneo,ordinal) | Una fase round_robin o knockout; source_id opzionale per provenienza |
| groups | PK id; FK fase; UNIQUE(fase,nome) | Gironi della prima fase |
| teams | PK id; FK torneo e girone opzionale; UNIQUE(torneo,nome) | Partecipanti; il tipo squadra/individuale è definito sul torneo; source_id opzionale |
| matches | PK id; FK torneo, fase, girone, partecipanti, vincitore e incontri sorgente | Turno e posizione unici per fase, punteggi entrambi NULL o entrambi interi 0–999, avversari diversi, BYE, versione, programmazione |
| audit_logs | PK id; FK torneo | Azione, timestamp UTC e snapshot JSON delle modifiche o degli incontri invalidati |

Catalogo canonico in `sport_configs`: **Calcio, Calcio a 5, Basket, Pallamano, Badminton, Tennis, Pallavolo**. I nomi legacy `Volley` e `Pallacanestro` vengono normalizzati in `Pallavolo` e `Basket` dalla migrazione `003`; non esistono alias duplicati. Il server risolve `sport_id` dal nome e rifiuta con 422 una coppia sport/`sport_id` incoerente.

Indici su incontri/torneo/fase/turno, partecipanti/torneo e `tournaments(sport_id)`. Su ogni connessione: `PRAGMA foreign_keys=ON`, `busy_timeout=10000`, `journal_mode=WAL`. I nomi duplicati vengono controllati anche con `casefold()` nel servizio. La classifica non è una tabella: viene ricalcolata dai risultati validi, evitando copie divergenti. Il criterio a parità di punti è memorizzato in `tournaments.tie_breaker` con un `CHECK` sui quattro valori ammessi; `head_to_head` costruisce una mini-classifica dei soli scontri diretti tra le squadre appaiate.

```mermaid
erDiagram
  sport_configs ||--o{ tournaments : classifica
  tournaments ||--o{ stages : contiene
  tournaments ||--o{ teams : iscrive
  stages ||--o{ groups : divide
  groups o|--o{ teams : assegna
  stages ||--o{ matches : contiene
  teams o|--o{ matches : disputa
  matches o|--o{ matches : alimenta
  tournaments ||--o{ audit_logs : registra
```

`teams` è il nome tecnico conservato per continuità con lo starter; non esistono ancora rose, giocatori appartenenti alle squadre o organizzazioni. Gli ID del campione fornito sono memorizzati come `source_id`, senza usarli come chiavi locali.

## Transazioni, orari e modifiche

Ogni scrittura usa `BEGIN IMMEDIATE`: controlli e aggiornamenti sono atomici e serializzati. Un client che invia una versione precedente riceve 409. Tutte le correzioni sono validate prima del commit; in caso di errore viene eseguito rollback. I risultati rimossi dai knockout sono conservati negli snapshot di audit.

Timestamp di creazione e programmazione in UTC; la UI mostra gli incontri in `Europe/Rome`. Il modulo di inserimento usa il fuso del dispositivo e invia un ISO 8601 con offset. Sovrapposizioni di campo/partecipanti conosciuti e dipendenze con orari già assegnati sono controllate. Nessuna garanzia di pianificazione globale per avversari ancora sconosciuti.

Non è esposta la cancellazione dei tornei: si archiviano con `archived_at` e si ripristinano. Un torneo archiviato resta leggibile ma rifiuta ogni scrittura (409). Le squadre si possono rimuovere solo prima della generazione. Gli ID degli incontri non vengono riutilizzati dopo una rigenerazione, così una richiesta obsoleta non può colpire un incontro nuovo. Le FK impediscono la rimozione accidentale di nodi ancora referenziati. Le invalidazioni eliminano i knockout dall'ultimo turno al primo e salvano prima gli snapshot.

`updated_at` viene aggiornato a ogni modifica del torneo. Formato, sport, regole, gironi e qualificazioni sono modificabili solo in bozza: dopo la generazione il server risponde 409. Nome e descrizione restano sempre modificabili.

## Migrazioni e backup

`migrations/001_initial.sql`, `002_stable_match_ids.sql`, `003_sports_expansion.sql`, `004_archive_and_updates.sql`, `005_tie_breaker.sql` e `PRAGMA user_version=5` definiscono la baseline corrente. Il runner in `db.py` applica le migrazioni mancanti in ordine e aggiorna la versione; un database più recente del programma viene rifiutato. Il database originale dello starter (`tornei.sqlite3`) non viene modificato. Non erano presenti dati applicativi da migrare nella cartella iniziale. Puntando a un database legacy senza versione l'app si ferma con un errore esplicito: non tenta conversioni distruttive. Un importatore legacy e le migrazioni incrementali di produzione restano nel piano di sviluppo.

SQLite in modalità WAL è la scelta per la LAN scolastica: un solo processo `uvicorn` (un worker), scritture serializzate con `BEGIN IMMEDIATE` e letture concorrenti. PostgreSQL richiederà una migrazione dedicata, non il semplice cambio di percorso, e sarà valutato solo se serviranno più server o molte scritture simultanee.

Per un backup consistente usare l'API SQLite (`VACUUM INTO` o `sqlite3.Connection.backup`) invece di copiare il file a caldo: con WAL il file principale da solo può essere incompleto. `backup.py` usa `VACUUM INTO` e produce `backup/open_score-AAAAMMGG-HHMMSS-microsecondi.sqlite3`, con conservazione configurabile:

```powershell
.venv\Scripts\python.exe backup.py --keep 14
```

Il backup è eseguibile mentre il server scrive, perché `VACUUM INTO` legge uno snapshot transazionale. Il file prodotto è un database SQLite completo e autonomo: non servono `-wal` o `-shm`. Su Windows lo script `deploy/backup-open-score.ps1` aggiunge data, esito e percorso a `backup/backup.log`. Per ripristinare: fermare il server, spostare `data/open_score.sqlite3` e i file `-wal`/`-shm`, copiare il backup come `data/open_score.sqlite3`, riavviare. I backup contengono tutti i dati e non vanno pubblicati su GitHub né lasciati senza protezione.

## Segreto delle sessioni

Quando l'autenticazione è attiva, i cookie sono firmati con HMAC-SHA256. Il segreto si legge da `TORNEO_SECRET`; se assente, `auth.py` crea `data/session.secret` con permessi ristretti e lo riusa ai successivi avvii. Cancellare o sostituire quel file invalida tutte le sessioni esistenti, senza toccare i tornei. Il segreto non è nel database: un backup del solo `.sqlite3` non contiene cookie validi, mentre serve il file del segreto per continuare le sessioni dopo un ripristino su un altro computer. Sia il database sia il segreto sono esclusi da Git.
