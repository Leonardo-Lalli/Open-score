# Open Score

**Il tuo campo di gioco.** Una demo originale per organizzare tornei sportivi a scuola: partecipanti, gironi, risultati e un percorso fino alla finale.

Progetto di **Leonardo Lalli e del suo collaboratore**, da discutere con il professore di scienze motorie. Nome e scelte di prodotto restano provvisori. La proposta iniziale è conservata in [docs/PROPOSTA_PROGETTO.md](docs/PROPOSTA_PROGETTO.md).

## Prova la demo

Richiede **Python 3.10 o successivo** e un browser moderno. Scarica la repository da **Code → Download ZIP**, estraila e apri PowerShell nella cartella `torneo-lab` contenuta al suo interno. In alternativa:

```powershell
git clone https://github.com/Leonardo-Lalli/Open-score.git
cd Open-score\torneo-lab
```

Poi esegui i comandi:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Apri [http://127.0.0.1:8000](http://127.0.0.1:8000). Per fermare il server: **Ctrl+C**. Se PowerShell impedisce l'attivazione, puoi usare direttamente l'interprete, senza cambiare i criteri di sicurezza del sistema:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Su macOS/Linux: `python3 -m venv .venv`, `source .venv/bin/activate`, poi gli stessi comandi `python`.

## Cosa mostrare al professore in cinque minuti

1. **Knockout Bracket of Football:** il caso fornito, Team #1 contro Team #2. Apri il tabellone e inserisci un risultato per proclamare il campione.
2. **Coppa della palestra:** otto squadre, quarti già iniziati, semifinali e finale collegate. I vincitori avanzano automaticamente.
3. **Campionato d'istituto:** sei squadre, calendario e classifica. Inserisci un risultato e osserva punti e partite giocate.
4. **Giornata dello sport:** sedici squadre in quattro gironi. Completati tutti i gironi, le prime due di ciascuno passano ai quarti.
5. **Nuovo torneo:** crea un knockout a tre partecipanti per mostrare il passaggio automatico per BYE. Il wizard raccoglie nomi e regole e mostra un riepilogo prima della creazione.

I quattro esempi vengono salvati al primo avvio. I nomi, gli incontri e i risultati si possono cambiare; i dati persistono dopo il riavvio. Non c'è una scadenza di 24 ore. Gli esempi aggiuntivi sono sintetici; il campione JSON fornito è conservato come fixture con i relativi ID di provenienza.

## Funzioni della versione 0.2

- Dashboard e interfaccia italiana responsive, procedura guidata, partecipanti rinominabili.
- Girone di sola andata o andata/ritorno, anche con numero dispari di partecipanti.
- Knockout da 2 a 32 partecipanti, seeding, BYE, tabellone effettivo e campione.
- Gironi uguali → qualificazione automatica delle prime 1/2 → eliminazione diretta.
- Risultati e correzioni con controllo della versione, conferma per invalidare gli incontri dipendenti e storico delle modifiche.
- Data, ora, campo e durata inseriti manualmente; controlli sui conflitti conosciuti.
- Esportazione CSV e link alla vista spettatore di sola lettura.
- Database SQLite persistente, API documentate e test automatici.

**È una demo locale, non l'intera piattaforma del master prompt.** Non ci sono ancora account, ruoli, rose, punteggi a set, rigori, doppia eliminazione, Swiss, consolazione o scheduler automatico. Gli sport disponibili usano un punteggio numerico generico. La classifica usa punti → differenza → fatti → nome → ID: regole da concordare con il professore.

Il server resta su **127.0.0.1**. La vista spettatore non sostituisce le autorizzazioni del futuro servizio online. Il tuo amico può scaricare e avviare il codice sul proprio computer; i vostri database locali non si sincronizzano. Pubblicare la repository su GitHub non pubblica automaticamente il backend su Internet.

## Verifica e documentazione

Dalla cartella `torneo-lab`:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Sono verificati algoritmi, avanzamenti, multifase, correzioni, concorrenza, persistenza, validazioni, CSV e API. Risultati ed esatta copertura nel [report dei test](docs/TEST_REPORT.md). Documentazione interattiva: [localhost:8000/docs](http://127.0.0.1:8000/docs).

| Documento | Contenuto |
| --- | --- |
| [Proposta per il professore](docs/PROPOSTA_PROGETTO.md) | Introduzione originale e obiettivi scolastici |
| [Audit](docs/AUDIT.md) | Cosa conteneva lo ZIP e cosa è stato migliorato |
| [Analisi dei riferimenti](docs/REFERENCE_ANALYSIS.md) | Screenshot, JSON, fonti e limiti delle inferenze |
| [Matrice funzionale](docs/FEATURE_MATRIX.md) | Funzioni presenti, verificate e rimandate |
| [Schede funzionali](docs/FUNCTIONAL_SPECS.md) | Input, regole, dati, stati e casi limite |
| [Architettura](docs/ARCHITECTURE.md) · [Database](docs/DATABASE.md) · [API](docs/API.md) | Struttura effettiva della demo |
| [Piano di sviluppo](docs/DEVELOPMENT_PLAN.md) · [Decisioni](docs/DECISIONS.md) | Passi successivi e ipotesi da discutere |
| [Changelog](docs/CHANGELOG.md) | Incremento 0.2 |

Il codice è originale e non dipende dai server di Score7. La licenza per il rilascio open source stabile va concordata tra gli autori; non è ancora stata assegnata. Database, credenziali e ambienti locali non sono inclusi nella repository.

## Anteprima reale

Tabellone della prova eseguita dal browser, dopo inserimento e correzione dei risultati:

![Tabellone Open Score con BYE, semifinale, finale e campione](docs/images/demo-bracket.png)
