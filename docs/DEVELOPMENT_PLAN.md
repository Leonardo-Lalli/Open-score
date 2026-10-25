# Piano per passi verificabili

## Incremento consegnato: sport, varianti e regole 0.4

Obiettivo: portare la demo da un unico modello numerico a sei sport con varianti selezionabili, rose dei giocatori e punteggi set per set, mantenendo tornei, classifiche, tabelloni, persistenza e protezione delle scritture già consegnati nella 0.3.

| Milestone | Stato in questa consegna | Criterio di completamento |
| --- | --- | --- |
| 0 — Audit | Eseguito | ZIP confrontato con la cartella, test originali eseguiti, limiti documentati |
| 1 — Fondamenta demo | Implementata e testata | Moduli separati, schema versionato, transazioni e validazioni; test riproducibili |
| 2 — Tornei e partecipanti | Implementata nel perimetro demo | Creare/elencare/modificare/archiviare tornei, aggiungere/rinominare/rimuovere partecipanti in bozza, rose con numero di maglia; manca l'import CSV |
| 3 — Motori base | Implementata e testata nel perimetro demo | Gironi sola andata/ritorno, dispari, knockout 2–32, BYE, avanzamento e correzioni coerenti |
| 4 — Multifase | Implementata e testata nel perimetro demo | 16 squadre → 4 gironi → 8 qualificate → 7 knockout → campione; niente promozione anticipata |
| 5 — Formati avanzati | Documentata, non implementata | Futuro: doppia eliminazione collegata, Swiss Classic e Pots distinti, Cup & Consolation; test propri prima della UI |
| 6 — Calendario | Parziale | Durata predefinita dalla variante, assegnazione manuale UTC e controllo conflitti noti; scheduler globale non implementato |
| 7 — Interfaccia demo | Implementata | Dashboard, catalogo sport, wizard gerarchico sport → variante, riepilogo, partecipanti, rose, scheda squadra, incontri, classifica, bracket, regolamento, diario, CSV e vista spettatore |
| 8 — Sicurezza e multiutenza | Implementata per un solo organizzatore | Password o token, sessione firmata, blocco scritture, host ammessi, limite ai tentativi e test 401/429; mancano account individuali e ruoli per torneo |
| 9 — Produzione LAN | Implementata e documentata | Avvio come attività pianificata o servizio systemd, backup `VACUUM INTO` con conservazione, ripristino, HTTPS tramite proxy esterno e lista di controllo |
| 10 — Sport, varianti e regole | Implementata e testata | Sei sport, sedici varianti, schermate dedicate con deep link, rose con minimo/massimo, durata e classifica derivate dalle regole, set per set, snapshot del regolamento |

## Sport e varianti della 0.4

| Sport | Varianti | Modello di punteggio | Rosa massima |
| --- | --- | --- | --- |
| Calcio | a 11, a 7, a 5 | reti, pareggio ammesso | 22 / 14 / 12 |
| Basket | 5 contro 5, 3x3 | punti, nessun pareggio | 12 / 4 |
| Pallavolo | 6 contro 6, 4 contro 4, beach volley 2 contro 2 | set con bonus al tie-break nella 6v6 | 14 / 8 / 2 |
| Badminton | singolare, doppio, doppio misto | set a 21 con limite a 30 | 1 / 2 / 2 |
| Ping pong | singolare, doppio, doppio misto | game a 11 | 1 / 2 / 2 |
| Biliardino | singolare, doppio | gol a tempo o a 5 | 1 / 2 |

Le varianti individuali iscrivono persone; quelle a squadre usano la rosa. Pallamano e Tennis non fanno più parte del catalogo: i tornei storici restano leggibili, ma ogni scrittura riceve 409.

## Prossimo incontro

Provare in palestra una variante a set (Pallavolo 6v6 o Ping pong) e una a squadre con rosa (Calcio a 5), verificando durata, numero di giocatori e criteri di classifica con il professore. Poi decidere se ampliare il catalogo o introdurre account e ruoli.

## Collaborazione iniziale

Una persona può curare UI e prove con il professore, l'altra motore, API e dati. Revisioni e regole restano condivise. Attività piccole in Issues; branch e pull request con controllo dei test prima dell'unione. Le durate dipendono dalla disponibilità dei due collaboratori: questa roadmap non promette una scadenza scolastica non concordata.

## Passo tecnico successivo consigliato

Confermare con la scuola i regolamenti delle varianti e aggiungere test sui casi reali emersi dalla prova. Completare importazione CSV e gestione delle rose durante il torneo. La LAN scolastica è già coperta da password unica, backup e avvio automatico; evitare di esporre il server a Internet senza un modello di autorizzazione più fine.
