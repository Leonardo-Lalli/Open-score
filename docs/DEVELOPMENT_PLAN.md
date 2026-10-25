# Piano per passi verificabili

## Incremento consegnato: LAN scolastica 0.3

Obiettivo: creare un torneo originale, registrare risultati reali, seguire un tabellone e una classifica, dimostrare qualificazioni, conservare i dati e proteggere le scritture sulla rete della scuola. Non equivale alla piattaforma completa del master prompt.

| Milestone | Stato in questa consegna | Criterio di completamento |
| --- | --- | --- |
| 0 — Audit | Eseguito | ZIP confrontato con la cartella, 6 test originali eseguiti, limiti documentati |
| 1 — Fondamenta demo | Implementata e testata | Moduli separati, schema versionato, transazioni e validazioni; test riproducibili |
| 2 — Tornei e partecipanti | Implementata nel perimetro demo | Creare/elencare/modificare/archiviare tornei, aggiungere/rinominare/rimuovere partecipanti in bozza; mancano rose e import CSV |
| 3 — Motori base | Implementata e testata nel perimetro demo | Gironi sola andata/ritorno, dispari, knockout 2–32, BYE, avanzamento e correzioni coerenti |
| 4 — Multifase | Implementata e testata nel perimetro demo | 16 squadre → 4 gironi → 8 qualificate → 7 knockout → campione; niente promozione anticipata |
| 5 — Formati avanzati | Documentata, non implementata | Futuro: doppia eliminazione collegata, Swiss Classic e Pots distinti, Cup & Consolation; test propri prima della UI |
| 6 — Calendario | Parziale | Assegnazione manuale UTC, controllo conflitti noti; scheduler globale con campi/riposi/arbitri non implementato |
| 7 — Interfaccia demo | Implementata | Dashboard, wizard con riepilogo, partecipanti, scheda squadra, incontri, classifica, vero bracket, diario, CSV e vista spettatore |
| 8 — Sicurezza e multiutenza | Implementata per un solo organizzatore | Password o token, sessione firmata, blocco scritture, host ammessi, limite ai tentativi e test 401/429; mancano account individuali e ruoli per torneo |
| 9 — Produzione LAN | Implementata e documentata | Avvio come attività pianificata o servizio systemd, backup `VACUUM INTO` con conservazione, ripristino, HTTPS tramite proxy esterno e lista di controllo |

## Prossimo incontro

Mostrare prima la finale Team #1–Team #2; poi creare insieme un torneo da 3 partecipanti per spiegare il BYE; infine aprire il campionato e i quattro gironi. Concordare lo sport di partenza, i criteri di spareggio, il tempo in palestra e i ruoli di professore e studenti.

## Collaborazione iniziale

Una persona può curare UI e prove con il professore, l'altra motore, API e dati. Revisioni e regole restano condivise. Attività piccole in Issues; branch e pull request con controllo dei test prima dell'unione. Le durate dipendono dalla disponibilità dei due collaboratori: questa roadmap non promette una scadenza scolastica non concordata.

## Passo tecnico successivo consigliato

Confermare le regole, aggiungere test sui casi reali emersi dalla prova e completare importazione e rose. Poi scegliere tra approfondire il supporto allo sport e introdurre account individuali. La LAN scolastica è già coperta da password unica, backup e avvio automatico; evitare comunque di esporre il server a Internet senza un modello di autorizzazione più fine.
