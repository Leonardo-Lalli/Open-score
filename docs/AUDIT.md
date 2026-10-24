# Audit della baseline

Archivio fornito: `torneo-lab-mvp.zip`. SHA-256: `2ed0fbe1e6603de29a144f2e2d0bc84a13ff918277c3825ff39639e998910473`.

Il contenuto è stato estratto in una cartella di lavoro ignorata da Git. I nove file sono stati letti e confrontati: risultavano identici ai nove file della cartella `torneo-lab` già presente. Prima delle modifiche: **6 test passati**, Python 3.14.3. Il sandbox impediva le richieste del client di test; l'esecuzione locale con le autorizzazioni del terminale ha completato la verifica. Un warning Starlette/httpx non bloccante.

## Componenti riutilizzati

- FastAPI, file statici e SQLite come base di avvio semplice.
- Metodo del cerchio per gironi pari e dispari.
- Principio della classifica derivata dai risultati, con controllo dei risultati non ancora inseriti.
- Contratti `/api/tournaments` conservati dove compatibili; i risultati ora richiedono `version`.

## Limiti e problemi concreti osservati nel codice originale

| Problema della baseline | Intervento |
| --- | --- |
| Nome torneo validato prima di `strip()`: una sequenza di spazi poteva diventare un nome vuoto salvato | Vincoli applicati al testo già ripulito e CHECK SQL |
| Punteggi interi con coercizione predefinita di Pydantic | Interi rigorosi: booleani, decimali e stringhe numeriche rifiutati |
| Knockout limitato alle potenze di due | Albero completo con BYE e riferimenti tra incontri |
| Correzioni dei turni precedenti bloccate senza alternativa | Invalidazione esplicita, audit e rigenerazione/propagazione |
| Nessuna versione per modifiche concorrenti | Versione incontro e lock di scrittura prima della lettura |
| Backend e schema concentrati in app.py | Responsabilità separate e migrazione SQL versionata |
| Nessun modello di fasi/gironi | Fasi, gruppi, qualificazione e percorso 16→8→campione |
| Nomi duplicati sensibili alle maiuscole | Controllo `casefold()` e unicità SQL |
| Interfaccia a lista senza tabellone reale | Bracket con nodi, collegamenti, futuri avversari e stato |
| Dipendenze di test assenti da requirements | requirements-dev e comando riproducibile |

Non era presente codice originale di Score7 nello ZIP. Non è stata effettuata estrazione di un backend remoto. Le nuove funzioni sono implementazioni originali; non tutte le funzionalità del master prompt sono incluse nella demo.
