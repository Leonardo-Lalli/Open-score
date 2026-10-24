# Database e conservazione dei dati

Default: `torneo-lab/data/open_score.sqlite3`. Percorso configurabile con `TORNEO_DB_PATH`. Il file, i database di test e l'ambiente Python sono esclusi da Git. I quattro esempi vengono creati al primo avvio di un database nuovo. `POST /api/demo` aggiunge gli esempi mancanti senza azzerare i risultati esistenti.

## Schema effettivo

| Tabella | Chiave e relazioni | Dati e vincoli principali |
| --- | --- | --- |
| tournaments | PK id; public_token e demo_key unici | Formato enumerato, nome non vuoto, sport, tipo team/individual, regole dei punti, numero gironi e qualificate, andata/ritorno, seed |
| stages | PK id; FK torneo; UNIQUE(torneo,ordinal) | Una fase round_robin o knockout; source_id opzionale per provenienza |
| groups | PK id; FK fase; UNIQUE(fase,nome) | Gironi della prima fase |
| teams | PK id; FK torneo e girone opzionale; UNIQUE(torneo,nome) | Partecipanti; il tipo squadra/individuale è definito sul torneo; source_id opzionale |
| matches | PK id; FK torneo, fase, girone, partecipanti, vincitore e incontri sorgente | Turno e posizione unici per fase, punteggi entrambi NULL o entrambi interi 0–999, avversari diversi, BYE, versione, programmazione |
| audit_logs | PK id; FK torneo | Azione, timestamp UTC e snapshot JSON delle modifiche o degli incontri invalidati |

Indici su incontri/torneo/fase/turno e partecipanti/torneo. `PRAGMA foreign_keys=ON` su ogni connessione. I nomi duplicati vengono controllati anche con `casefold()` nel servizio. La classifica non è una tabella: viene ricalcolata dai risultati validi, evitando copie divergenti.

```mermaid
erDiagram
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

Non è esposta la cancellazione dei tornei. Le squadre si possono rimuovere solo prima della generazione. Gli ID degli incontri non vengono riutilizzati dopo una rigenerazione, così una richiesta obsoleta non può colpire un incontro nuovo. Le FK impediscono la rimozione accidentale di nodi ancora referenziati. Le invalidazioni eliminano i knockout dall'ultimo turno al primo e salvano prima gli snapshot.

## Migrazioni e backup

`migrations/001_initial.sql`, `002_stable_match_ids.sql` e `PRAGMA user_version=2` definiscono la nuova baseline. Il database originale dello starter (`tornei.sqlite3`) non viene modificato. Non erano presenti dati applicativi da migrare nella cartella iniziale. Puntando a un database legacy senza versione l'app si ferma con un errore esplicito: non tenta conversioni distruttive. Un importatore legacy e le migrazioni incrementali di produzione restano nel piano di sviluppo.

Per un backup locale, arrestare il server e copiare `data/open_score.sqlite3`; per ripristinarlo, arrestare il server e usare la copia attraverso `TORNEO_DB_PATH`. Il backup non va pubblicato su GitHub. PostgreSQL richiederà una migrazione dedicata, non il semplice cambio di percorso.
