# Report di verifica — 24 ottobre 2026

## Incremento backend 0.3 — 26 ottobre 2026

Suite locale finale: **132 passed, 1 warning**, 103.27 secondi, Windows e Python
3.14.3; comando `python -m pytest -q` da torneo-lab nell'ambiente virtuale.
Include i precedenti 87 controlli e 45 nuovi test su account/ruoli/CSRF,
isolamento, squadre/studenti/ordine, approvazioni, inviti, calendario/campi,
sport a set, penalità, tavolino, storico multifase e backup/restore.
OpenAPI generato e `scripts/export_openapi.py --check` passato. Database SQLite
reali e identità sintetiche. Nessuna nuova prova browser o esecuzione CI remota.
Il warning Starlette/httpx è quello già presente; i test sono stati eseguiti
fuori dal sandbox con autorizzazione per le directory temporanee.
Dettagli, limiti e avvio nel [report backend](CORE_ENGINE_REPORT.md).

## Report storico demo 0.2

## Esecuzione automatica effettiva

Ambiente: Windows, Python 3.14.3; FastAPI 0.162.0, Pydantic 2.14.1, Uvicorn 0.54.0, pytest 9.1.1, httpx 0.28.1. Dipendenze runtime fissate nel progetto.

- Baseline ZIP, prima delle modifiche: **6 passed**.
- Suite della demo dopo implementazione e migrazione: **85 passed, 1 warning**, 3.79 secondi nell'ultima esecuzione locale.
- Il warning è la deprecazione Starlette relativa all'uso di httpx nel TestClient; non indica un fallimento dei test. L'ambiente di sviluppo contiene ancora httpx per compatibilità con il test client usato.
- Il sandbox impediva le richieste del TestClient. I test sono stati eseguiti realmente con il terminale autorizzato; non si è sostituito il risultato con un output simulato.

Comando dalla cartella `torneo-lab`: `python -m pytest -q`, dopo `python -m pip install -r requirements-dev.txt`.

## Copertura rilevante

| Area | Prove |
| --- | --- |
| Gironi | 2,3,4,5,8,16,32 partecipanti, una/due andate, conteggio e unicità, nessuna squadra due volte nello stesso turno |
| Knockout | Struttura e BYE per ogni numerosità da 2 a 32; percorso API completo per 2,3,4,5,8,16,32; n−1 incontri realmente giocati |
| Seeding | Sorteggio riproducibile, input non modificato |
| Classifica | Risultati mancanti esclusi, 0–0 valido, punteggio configurato, correzione |
| Dipendenze | Correzione semifinale, blocco senza conferma, reset finale, storico, stesso vincitore conserva risultato finale |
| Multifase | 16 squadre, 4 gruppi, 24 partite di girone, 8 promosse, 7 knockout, nessuna promozione anticipata, campione e riqualificazione |
| Richieste obsolete | Versione precedente rifiutata, due scritture concorrenti danno 200/409, ID non riciclati dopo ricostruzione delle finali |
| Validazione | Spazi nel nome, duplicati, sport/formati non supportati, punteggi booleani/decimali/stringhe/negativi e rollback |
| Calendario | Conversione UTC, fuso obbligatorio, sovrapposizione campo, appuntamenti adiacenti consentiti |
| Dati | Riapertura database, migrazione schema 1→2 senza perdita di risultato, verifica FK, fixture utente e seed idempotente |
| Confini locali | Incontro di altro torneo rifiutato, Origin esterno rifiutato, Host inatteso rifiutato, endpoint spettatore solo GET |
| CSV | Punteggio zero conservato, testo che inizia con formula neutralizzato |

## Verifica browser effettiva

Browser integrato, anteprima locale `127.0.0.1:8000`, viewport osservata circa 690 px. Eseguite operazioni tramite interfaccia:

1. Dashboard caricata con quattro tornei e contatori reali.
2. Wizard: torneo «Prova col professore», tre squadre con nomi personalizzati, riepilogo e generazione.
3. Tabellone con BYE per Falchi e semifinale Leoni–Aquile; risultato 2–1, avanzamento alla finale.
4. Finale 3–1: campione Falchi visualizzato.
5. Correzione semifinale 0–2: errore senza conferma; con conferma la finale perde il risultato, cambia avversario e il campione scompare.
6. Campionato: inserito 0–0; il numero delle partite completate passa da 6 a 7. La classifica mostra giocate e pareggi aggiornati.
7. Apertura del link spettatore in una scheda separata: stessi dati, nessun pulsante per inserire/modificare risultati.
8. Ricaricamento dell'app: il torneo creato e il pareggio sono ancora presenti. La finale corretta viene rigiocata e il tabellone concluso è salvato in [anteprima](images/demo-bracket.png).

La copertura end-to-end indicata nella matrice si riferisce a queste prove manuali assistite dal browser. Non esiste ancora una suite Playwright autonoma nel repository. Il percorso multifase completo è stato eseguito nei test API, non tramite 31 inserimenti nel browser.

## Limiti di verifica

Nessuna prova su hardware mobile reale o su tutti i browser. La UI ha regole responsive fino a schermi piccoli; l'anteprima osservata verifica una larghezza intermedia. Nessuna verifica di carico, account, autorizzazioni di produzione, scheduler globale, sport a set o formati avanzati: non sono implementati.

## Verifica GitHub Actions

Il workflow con matrice Python 3.11 e 3.14 su Linux ha completato con **successo** il controllo del commit applicativo `234273f`. Lo stato `completed / success` è stato letto dall'API pubblica GitHub dopo il push: [esecuzione 40115770441](https://github.com/Leonardo-Lalli/Open-score/actions/runs/40115770441).

Questo esito è distinto dagli 85 test eseguiti localmente su Windows. L'aggiornamento successivo registra il risultato nella documentazione, senza modificare il codice verificato.
