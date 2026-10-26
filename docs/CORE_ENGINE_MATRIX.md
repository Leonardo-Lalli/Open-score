# Matrice backend rispetto al Prompt A

Data: 26 ottobre 2026. Baseline `b541824`, branch `leo-develop`.
La [matrice storica](FEATURE_MATRIX.md) descrive la demo 0.2. Questa matrice
confronta i nuovi requisiti con il codice, senza promuovere una proposta a funzione.

Stati: **Testato** = presente e verificato nella suite locale per il perimetro
scritto; **Parziale** = soltanto una parte esiste; **Proposto** = contratto
revisionabile, nessuna implementazione; **Da realizzare** = manca il componente.

| Area richiesta | Stato effettivo | Evidenza / limite | Incremento dopo revisione |
| --- | --- | --- | --- |
| Audit e inventario Markdown | Completato | CORE_ENGINE_AUDIT, 14 Markdown baseline, codice e configurazioni letti | A0 |
| Contratto disponibile `/api` | Documentato e sincronizzato | API_V1 e openapi.yaml da FastAPI; risposta non tipizzata in OpenAPI | A1 |
| Nuovi endpoint `/api/v1` | Proposti | Sezione 6 del contratto; nessuna route V1 attiva | A2–A8 |
| Conservazione dopo riapertura | Testato | test_persistence_and_migration | Mantenere |
| Migrazioni versionate e integrità | Testato / parziale | 1→2 senza perdita; nessun import legacy/PostgreSQL | A2/A9 |
| Backup/restore operativo | Da realizzare | Solo istruzioni copia a server fermo; restore non provato | A9 |
| Account professore/studente | Proposto | Nessun login, password hash o sessione corrente | A2 |
| Organizzazioni e isolamento proprietario | Proposto | Nessun owner o organizzazione nel DB | A2 |
| Visitatore pubblico | Parziale | GET spettatore testato, nessuna policy pubblicazione o whitelist per studenti | A2/A5 |
| CRUD tornei | Parziale | Crea/elenca/legge; niente modifica/cancellazione API | A3 |
| CRUD squadre | Parziale testato | Crea/rinomina/elimina in bozza; nessuna archiviazione | A3 |
| Studenti, rose e membership | Proposto | `teams` non è un modello studente | A3 |
| Ricerca, import e duplicati | Parziale | Duplicati nomi gestiti; niente ricerca server/import strutturato | A3 |
| Iscrizioni e capienza | Proposto | Nessuna tabella o API | A3/A5 |
| Ordine visuale persistente | Proposto | Ordine attuale per ID, nessuna versione di collezione | A3 |
| Spostamento studenti tra squadre | Proposto | Nessuna membership attuale | A3 |
| Risultato diretto e correzione | Testato | Versione, transazione, invalidazione e audit demo | Mantenere con autorizzazioni |
| Proposte multiple degli studenti | Proposto | Nessuna entità proposta | A4 |
| Approvazione/rifiuto/correzione professore | Proposto | Nessuna revisione o autore nel DB | A4 |
| Atomicità risultati / concorrenza | Testato / parziale | 200/409 su risultato concorrente; workflow approvazione mancante | A4 |
| Audit amministrativo attribuibile | Parziale | Azione e snapshot, senza identità autore | A2/A4 |
| Link di sola lettura | Parziale testato | Token sempre attivo; niente revoca/pubblicazione intenzionale | A5 |
| Inviti QR e accettazione identificata | Proposto | Nessun invito o uso/scadenza nel DB | A5 |
| Campi/sedi personalizzati | Proposto | `location` è testo, non risorsa | A6 |
| Calendario manuale con UTC | Parziale testato | Versione e conflitti noti dentro il singolo torneo | A6 |
| Disponibilità e conflitti tra tornei | Proposto | Nessun inventario condiviso | A6 |
| Sport a punteggio numerico | Parziale | Calcio/Calcio a 5/Basket/Pallamano come etichette con regole generiche | A7 |
| Varianti, preset e form dinamici | Proposto | Nessun catalogo o schema di regole servito | A7 |
| Punteggi a set e vincitore validato | Proposto | Pallavolo attualmente rifiutata; niente validatore set | A7 |
| Penalità, tavolino e spareggi dedicati | Da realizzare | Nessuna rappresentazione esplicita | A7, con regole e test propri |
| Round-robin pari/dispari e due andate | Testato | test_round_robin_invariants | Mantenere |
| Knockout 2–32, BYE e progressione | Testato | test_bracket_tree_and_byes, test_complete_knockout_with_byes | Mantenere |
| Gironi e qualificazioni | Testato | 16→4 gironi→8 finaliste; correzioni con ricostruzione | Mantenere |
| Dati bracket | Parziale testato | ID/turno/posizione/sorgenti/vincitore presenti; manca slot successivo esplicito | A8 |
| Classifiche | Testato nel perimetro demo | Punti/differenza/fatti/nome/ID; nessuna regola specifica sport | A7/A8 |
| Statistiche e percentuale | Parziale | progress, team_count e campione; niente studenti/proposte; totale cresce tra fasi | A8 |
| CI backend | Presente | tests.yml, Python 3.11/3.14; nessuna nuova esecuzione remota dichiarata | Mantenere |
| Deployment backend / Aruba | Da realizzare | Hosting sconosciuto, nessun deploy autorizzato | A9 |
| Handoff e PR coordinamento | Preparati localmente | BACKEND_TO_FRONTEND e bozza PR; revisione e integrazione non avvenute | A1 |

Verifica iniziale: **85 test passati**, 1 warning di deprecazione. Verifica
finale: **87 test passati**, stesso warning, inclusi i due controlli del
contratto/esportatore. `export_openapi.py --check` passato. Nessuna nuova verifica
end-to-end frontend dichiarata.
