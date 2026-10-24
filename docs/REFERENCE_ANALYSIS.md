# Analisi funzionale dei riferimenti

Data: 24 ottobre 2026. Fonti: screenshot e JSON forniti da Leonardo, demo pubblica consultata in precedenza, documentazione ufficiale collegata sotto. Nessun backend remoto recuperato; nessun token, cookie o HAR richiesto. La demo funziona senza comunicazioni con Score7.

## Dati effettivamente osservati

Gli screenshot delle intestazioni mostrano tre richieste GET con risposta 200:

- `/v2/tournaments/ftzop9r2jt/stages`;
- `/v2/tournaments/ftzop9r2jt/overview`;
- `/v2/calendarComponents/53882425/matches`.

Il dominio osservato è `api.score7.io`. `Content-Type: application/json` e intestazione server nginx non permettono di determinare linguaggio, framework, database o struttura dei servizi interni. Il codice JavaScript è indicato dal browser come iniziatore delle richieste; il nome del bundle non rivela il sorgente originale.

Gli altri nomi Network — `limits`, `participants`, `bracket`, `byes`, `calendarComponents`, `handSetPairings`, `mvtEvents`, `public-counts`, `prices?currency=EUR` — restano etichette osservate: non sono contratti API ricostruiti. Non conosciamo payload, significato completo o autorizzazioni di quelle operazioni. Il CORS osservato non implica permessi di scrittura o API supportata per terzi.

Le schermate applicative mostrano: scelta di sport/partecipanti/formato, due squadre, una finale, panoramica e voci amministrative. La presenza delle voci non dimostra l'intera implementazione delle relative funzioni.

## Campione JSON fornito

Il file [score7_sample.json](../torneo-lab/fixtures/score7_sample.json) conserva i dati forniti, separando la lista di fasi e l'oggetto del partecipante in un contenitore locale:

| Dato | Valore verificabile nel campione | Interpretazione nella demo |
| --- | --- | --- |
| Fase | id 53882484, KNOCKOUT_STAGE, SINGLE_KNOCKOUT, ordinal 0 | Una fase knockout, ID esterno in source_id |
| Partecipanti | 23045803 Team #1; 23045804 Team #2 | Due record locali con ID di provenienza |
| Incontro | matchId 117234055 | Finale tra le due squadre |
| Punteggi | homeScore e awayScore vuoti | Risultato non inserito, NULL; non uno 0–0 |
| Programmazione | timestamp e location null | Nessuna data o campo assegnati |
| Esito/conferme | outcome, confirmationStatus e submission null | Nessuna deduzione sui workflow di conferma |
| Pareggio | drawAllowed null | Regola non stabilita dal campione; la demo sceglie esplicitamente il vincitore obbligatorio nel knockout |
| attributes | Oggetto vuoto | Nessuna configurazione ulteriore deducibile |

I punteggi array non dimostrano da soli la semantica dei set o l'ordine dei valori. L'adattatore iniziale importa solo questo campione vuoto, non è un importatore generico dell'API di Score7. Le regole, gli endpoint e il modello relazionale di Open Score sono scelte originali.

## Riferimenti ufficiali consultati

- [Centro assistenza](https://kb.score7.io/docs/): indice delle aree funzionali; usato per la copertura preliminare delle funzioni future.
- [Girone e classifica](https://www.score7.io/it/campionati): sola andata/ritorno, classifica derivata e condivisione.
- [Tornei multifase](https://kb.score7.io/docs/getting-started/multi-stage-tournament/): gruppi e qualificazioni; include l'esempio 16 squadre e 8 promosse.
- [Doppia eliminazione](https://kb.score7.io/docs/getting-started/double-elimination/): upper/lower collegati e grand final senza reset nel modello descritto da Score7. Documentato, non implementato qui.
- [Swiss](https://kb.score7.io/docs/getting-started/swiss-format/): Classic con accoppiamenti per turno e Pots con calendario predisposto. Documentati, non implementati qui.
- [Cup & Consolation](https://kb.score7.io/docs/getting-started/cup-and-consolation/): due tabelloni indipendenti alimentati dalla fase precedente, due campioni. Il testo multifase usa una descrizione meno precisa; per questa distinzione si segue la pagina dedicata. Non implementato qui.
- [Calcolo classifiche](https://kb.score7.io/docs/standings/standings-calculation/): riferimento documentale; i criteri fissi della demo sono dichiarati separatamente.
- [Programmazione](https://kb.score7.io/docs/scheduling/auto-generate-schedule/): riferimento per un futuro scheduler; la demo assegna orari manualmente.

Queste sono descrizioni ufficiali consultate, non prove dirette di ogni caso limite. L'osservazione pubblica non consente di garantire equivalenza completa con Score7.
