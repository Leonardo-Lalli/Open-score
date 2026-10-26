# Architettura dell'applicazione

## Estensione backend 0.3

La struttura sotto è la baseline conservata. Il backend attuale aggiunge
`v1_api.py` (route), `v1_schemas.py` (input), `v1_dto.py` (risposte), `auth.py`
(sessioni/CSRF/permessi), `v1_domain.py`, `v1_results.py`, `v1_resources.py`
(operazioni transazionali) e `sports.py` (regole pure). `manage.py` gestisce
account professore, migrazione/assegnazione legacy e backup/restore.

Le route V1 riutilizzano engine e servizi esistenti con estensioni compatibili:
classifiche sportive, score completo a set e invalidazione dei dati ufficiali.
Ogni richiesta possiede una connessione; le scritture prendono il lock prima
della lettura. Le approvazioni comprendono audit, risultato e progressione nella
stessa transazione. Il calendario viene riverificato dopo l'avanzamento.

La modalità demo mantiene la UI precedente su dati non assegnati; la modalità
service esclude le API anonime. Le route legacy non possono leggere/modificare
tornei assegnati. API pubbliche con whitelist separata, senza rose personali.
Schema 4, nessun cambio framework/DB. Nessun frontend o deploy modificato.
Dettagli: [contratto](contracts/API_V1.md), [database](DATABASE.md),
[deployment](DEPLOYMENT_BACKEND.md), [report](CORE_ENGINE_REPORT.md).

## Architettura storica della demo

Questa è l'architettura originale di Open Score, non l'architettura interna di Score7.

```mermaid
flowchart TD
  UI[HTML + CSS + JavaScript] <--> HTTP[app.py: FastAPI / OpenAPI]
  HTTP --> Validation[schemas.py: Pydantic]
  HTTP --> Service[services.py: regole applicative]
  Service --> Engine[engine.py: algoritmi puri]
  HTTP --> DB[db.py: transazioni SQLite]
  DB --> Data[(data/open_score.sqlite3)]
```

## Responsabilità

- `torneo-lab/app.py`: application factory, endpoint, file statici, controllo Host/Origin, CSV.
- `schemas.py`: contratti in ingresso, limiti, nomi ripuliti, punteggi interi rigorosi.
- `services.py`: creazione, generazione, qualificazioni, avanzamenti, correzioni, calendario e diario.
- `engine.py`: metodo del cerchio per i gironi, albero knockout con seeding e BYE, classifica derivata.
- `db.py` e `migrations/001_initial.sql`: schema versionato e transazione per operazione.
- `static/`: interfaccia italiana responsive, finestre native `dialog`, tabellone SVG/HTML con collegamenti reali.

## Una modifica attraversa il sistema

Il browser invia punteggio e `version`. La transazione acquisisce il lock SQLite prima della lettura. Il servizio verifica torneo, incontro, versione e avversari; salva il risultato e lo storico, invalida eventuali dipendenze con conferma e propaga i vincitori. Solo dopo il commit il browser rilegge i dati. Non mostra un salvataggio riuscito se il server lo rifiuta.

Il tabellone esiste interamente dalla generazione: gli incontri futuri hanno riferimenti `source_home`/`source_away`, non squadre inventate. Un BYE non è uno 0–0 e non conta tra le partite giocate. Se cambia il vincitore, tutti gli incontri discendenti perdono risultati e programmazione; i rami indipendenti restano intatti.

Nei tornei multifase, tutte le partite dei gironi devono essere complete prima di creare i knockout. Le prime 1 o 2 di ciascun girone vengono ordinate per posizione e girone, poi distribuite dal seeding standard. Correggere un girone dopo la qualificazione richiede conferma e ricostruisce la fase finale; lo storico precedente resta nel diario.

## Confine di questa consegna

È un'applicazione per uno spazio di lavoro scolastico, utilizzabile sulla LAN. La pagina spettatore e il suo endpoint sono di sola lettura. All'ingresso si sceglie **Sono un prof** (login email/password) o **Sono uno studente** (sola lettura). Ogni docente ha un account in `teachers` e gestisce solo i tornei con il proprio `teacher_id`; i tornei altrui restano leggibili ma non modificabili. Il server può ascoltare sulla LAN, ma non è destinato a Internet; installazione, host ammessi e backup sono descritti in [DEPLOY.md](DEPLOY.md) e [SECURITY.md](SECURITY.md).

Frontend senza build e SQLite riducono i passaggi per presentarla a scuola. React/TypeScript, SQLAlchemy/Alembic e PostgreSQL restano opzioni per la piattaforma successiva; ruoli amministrativi, recupero password e revoca centralizzata richiederebbero un servizio di identità più completo.
