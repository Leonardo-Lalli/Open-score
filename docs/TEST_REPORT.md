# Report di verifica — 25 ottobre 2026

## Esecuzione automatica effettiva

Ambiente: Windows, Python 3.14.3; FastAPI 0.162.0, Pydantic 2.14.1, Uvicorn 0.54.0, pytest 9.1.1, httpx 0.28.1. Dipendenze runtime fissate nel progetto.

- Baseline ZIP, prima delle modifiche: **6 passed**.
- Suite della demo dopo implementazione e migrazione: **85 passed, 1 warning**, 3.79 secondi nell'ultima esecuzione locale.
- Dopo le fasi 3–4 (modifica, archivio, scheda squadra, criteri di spareggio): **106 passed**.
- Dopo la fase 5 (autenticazione, host LAN, backup, deploy): **118 passed**, 2.81 secondi.
- Dopo la fase 6 (sport, varianti, rose e punteggi set per set): **142 passed, 1 warning**, 4.01 secondi nell'ultima esecuzione locale.
- Dopo la correzione 0.4.1 del flusso di modifica, del formato in bozza, della lineup e dell'integrità del catalogo: **147 passed, 1 warning**, 5.62 secondi nell'ultima esecuzione locale.
- Dopo la verifica esaustiva delle sedici coppie sport/variante: **179 passed, 1 warning**, 6.64 secondi nell'ultima esecuzione locale.
- Dopo la pulizia dei mockup legacy e il cache-busting 0.5.0: **184 passed, 1 warning**, 6.60 secondi nell'ultima esecuzione locale.
- Il warning è la deprecazione Starlette relativa all'uso di httpx nel TestClient; non indica un fallimento dei test. L'ambiente di sviluppo contiene ancora httpx per compatibilità con il test client usato.
- Il sandbox impediva le richieste del TestClient. I test sono stati eseguiti realmente con il terminale autorizzato; non si è sostituito il risultato con un output simulato.

Comando dalla cartella `torneo-lab`: `python -m pytest -q`, dopo `python -m pip install -r requirements-dev.txt`.

## Copertura rilevante

| Area | Prove |
| --- | --- |
| Gironi | 2,3,4,5,8,16,32 partecipanti, una/due andate, conteggio e unicità, nessuna squadra due volte nello stesso turno |
| Knockout | Struttura e BYE per ogni numerosità da 2 a 32; percorso API completo per 2,3,4,5,8,16,32; n−1 incontri realmente giocati |
| Seeding | Sorteggio riproducibile, input non modificato |
| Classifica | Risultati mancanti esclusi, 0–0 valido, punteggio configurato, correzione; set vinti/persi e bonus 2/1 al quinto set della Pallavolo 6v6 |
| Sport e varianti | Catalogo di 6 sport e 16 varianti, variante predefinita, deep link, coppia sport/variante incoerente rifiutata, sport rimossi leggibili e non modificabili; integrità di slug, lineup, durata, punteggio, set e regolamento per ogni variante; 32 test parametrizzati su tutte le coppie sport/variante (regolamento, creazione, generazione e durata) |
| Rose | Aggiunta e rimozione giocatori, numero di maglia, duplicati, limite massimo della variante, rifiuto per le varianti individuali, rose modificabili a torneo avviato |
| Punteggio a set | Numero massimo di set, punti minimi, scarto di due, limite del set, vittoria con i set richiesti, rifiuto di risultati numerici sulle varianti a set |
| Regolamento | Snapshot di regole e regolamento alla creazione, indipendenza dalle modifiche successive del catalogo, scheda Regolamento e stampa |
| Dipendenze | Correzione semifinale, blocco senza conferma, reset finale, storico, stesso vincitore conserva risultato finale |
| Multifase | 16 squadre, 4 gruppi, 24 partite di girone, 8 promosse, 7 knockout, nessuna promozione anticipata, campione e riqualificazione |
| Richieste obsolete | Versione precedente rifiutata, due scritture concorrenti danno 200/409, ID non riciclati dopo ricostruzione delle finali |
| Validazione | Spazi nel nome, duplicati, sport o varianti non supportati, variante di un altro sport, punteggi booleani/decimali/stringhe/negativi, risultato incompatibile con la variante e rollback |
| Calendario | Conversione UTC, fuso obbligatorio, sovrapposizione campo, appuntamenti adiacenti consentiti, durata predefinita dalla variante |
| Dati | Riapertura database, migrazione schema 1→6 senza perdita di risultato, rimappatura di Calcio a 5, verifica FK, fixture utente e seed idempotente |
| Confini locali | Incontro di altro torneo rifiutato, Origin esterno rifiutato, Host inatteso rifiutato, endpoint spettatore solo GET |
| Modifica e archivio | Nome/descrizione sempre modificabili, formato e sport modificabili in bozza con opzioni gironi dinamiche, campi strutturali bloccati dopo la generazione, payload della modale senza `format` che conserva la struttura, `null` espliciti rifiutati con 422, archivio in sola lettura e ripristino, persistenza dopo riavvio, scritture 409 sui tornei di sport rimossi |
| Scheda squadra e spareggi | Girone, posizione, classifica e incontri del partecipante; giocatori in campo, lineup minima e rosa massima dalla variante; 404 per squadra di altro torneo; mini-classifica `head_to_head`; default `goal_difference` conservato dalla migrazione 005 |
| Autenticazione | Letture aperte, scritture 401 senza sessione, login/logout, cookie resistente al reload, Bearer token, token scaduto o manomesso rifiutato, 5 errori → 429, modalità demo senza password |
| Host LAN | Host sconosciuto 400, IP e nome configurati ammessi, `TORNEO_ALLOWED_HOSTS` letto dall'ambiente |
| Backup | `VACUUM INTO` leggibile con schema e dati completi, `integrity_check` e `foreign_key_check` puliti, conservazione dei più recenti |
| CSV | Punteggio zero conservato, dettaglio dei set esportato, testo che inizia con formula neutralizzato |
| Asset e URL legacy | Redirect 302 dei vecchi URL, stub di redirect per le pagine statiche, nessun riferimento a sport fuori catalogo in HTML/JS, asset versionati e HTML/JS/CSS con `no-cache` |

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

## Verifiche browser delle fasi 3–5

Con server temporaneo e database separato, pilotando Chromium tramite Playwright:

- **Modifica e archivio**: modifica del nome in bozza, blocco dei campi strutturali dopo la generazione, archivio con scomparsa dall'elenco, ripristino, salvataggio di risultato e orario, dati ancora presenti dopo ricarica e riavvio del server.
- **Criteri e scheda squadra**: quattro criteri nel wizard, nota della classifica coerente («scontri diretti»), modale partecipante con girone, tre incontri e quattro riquadri statistici, vista pubblica di sola lettura con aggiornamento automatico dopo 30 secondi.
- **Autenticazione**: scrittura anonima 401, letture e link pubblico aperti, password errata con messaggio, accesso con cookie persistente al reload, pulsanti di modifica nascosti da anonimo, click su un risultato che riapre l'accesso, logout che torna alla dashboard. Host `192.168.1.50` rifiutato con 400 quando non configurato e loopback ammesso. Nessun errore JavaScript osservato.

## Verifica browser della fase 6

Con server temporaneo su `127.0.0.1:8765`, database separato e Chromium pilotato da Playwright:

- **Catalogo**: la voce «Sport e regole» apre sei schede, una per sport, senza Pallamano né Tennis. Il click su Calcio mostra le tre varianti e il deep link arriva a `#/sport/Calcio/calcio-a-5`.
- **Wizard**: selezionando Pallavolo il selettore delle varianti si aggiorna, l'anteprima mostra «Pallavolo 6 contro 6» con durata, rosa e punteggio, e il riepilogo riporta sport e variante prima della creazione.
- **Set per set**: su un girone a due squadre il risultato apre cinque righe di set; inserendo 25-20, 25-20 e 25-20 il torneo salva il dettaglio, la classifica assegna 3/0 punti e la scheda Regolamento mostra le regole congelate.
- **Rosa**: dalla scheda squadra si aggiunge «Luca Bianchi» con numero 7; il giocatore compare nella rosa e il limite della variante resta visibile. Il flusso termina senza errori di pagina o di console.

La suite Playwright non è versionata nel repository: la verifica è stata eseguita con uno script temporaneo. Il percorso completo da 16 squadre a 4 gironi e 7 knockout resta coperto dai test API, non da 31 inserimenti nel browser.

## Limiti di verifica

Nessuna prova su hardware mobile reale o su tutti i browser. La UI ha regole responsive fino a schermi piccoli; l'anteprima osservata verifica una larghezza intermedia. Nessuna verifica di carico, account individuali, ruoli per torneo, scheduler globale, statistiche individuali o formati avanzati: non sono implementati. I regolamenti delle sedici varianti sono scelte della demo da confermare con il professore. L'autenticazione è verificata su un solo organizzatore condiviso; il limite ai tentativi è in memoria e non è stato provato con più IP simultanei.

## Verifica GitHub Actions

Il workflow con matrice Python 3.11 e 3.14 su Linux ha completato con **successo** il controllo del commit applicativo `234273f`. Lo stato `completed / success` è stato letto dall'API pubblica GitHub dopo il push: [esecuzione 40115770441](https://github.com/Leonardo-Lalli/Open-score/actions/runs/40115770441).

Questo esito è distinto dai 85 test della prima consegna eseguiti localmente su Windows (oggi 142). L'aggiornamento successivo registra il risultato nella documentazione, senza modificare il codice verificato.
