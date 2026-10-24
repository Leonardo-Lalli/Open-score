# Piano per passi verificabili

## Incremento consegnato: demo locale 0.2

Obiettivo: creare un torneo originale, registrare risultati reali, seguire un tabellone e una classifica, dimostrare qualificazioni e conservare i dati. Non equivale alla piattaforma completa del master prompt.

| Milestone | Stato in questa consegna | Criterio di completamento |
| --- | --- | --- |
| 0 — Audit | Eseguito | ZIP confrontato con la cartella, 6 test originali eseguiti, limiti documentati |
| 1 — Fondamenta demo | Implementata e testata | Moduli separati, schema versionato, transazioni e validazioni; test riproducibili |
| 2 — Tornei e partecipanti | Parziale | Creare/elencare tornei, aggiungere/rinominare/rimuovere partecipanti in bozza; mancano CRUD tornei, rose e import CSV |
| 3 — Motori base | Implementata e testata nel perimetro demo | Gironi sola andata/ritorno, dispari, knockout 2–32, BYE, avanzamento e correzioni coerenti |
| 4 — Multifase | Implementata e testata nel perimetro demo | 16 squadre → 4 gironi → 8 qualificate → 7 knockout → campione; niente promozione anticipata |
| 5 — Formati avanzati | Documentata, non implementata | Futuro: doppia eliminazione collegata, Swiss Classic e Pots distinti, Cup & Consolation; test propri prima della UI |
| 6 — Calendario | Parziale | Assegnazione manuale UTC, controllo conflitti noti; scheduler globale con campi/riposi/arbitri non implementato |
| 7 — Interfaccia demo | Implementata | Dashboard, wizard con riepilogo, partecipanti, incontri, classifica, vero bracket, diario, CSV e vista spettatore |
| 8 — Sicurezza e multiutenza | Da progettare | Account, sessioni, ruoli per torneo, test 401/403 e isolamento fra utenti; condizione per hosting pubblico |
| 9 — Produzione | Da progettare | Migrazioni PostgreSQL, backup verificato, deploy, monitoraggio e verifiche operative |

## Prossimo incontro

Mostrare prima la finale Team #1–Team #2; poi creare insieme un torneo da 3 partecipanti per spiegare il BYE; infine aprire il campionato e i quattro gironi. Concordare lo sport di partenza, i criteri di spareggio, il tempo in palestra e i ruoli di professore e studenti.

## Collaborazione iniziale

Una persona può curare UI e prove con il professore, l'altra motore, API e dati. Revisioni e regole restano condivise. Attività piccole in Issues; branch e pull request con controllo dei test prima dell'unione. Le durate dipendono dalla disponibilità dei due collaboratori: questa roadmap non promette una scadenza scolastica non concordata.

## Passo tecnico successivo consigliato

Confermare le regole, aggiungere test sui casi reali emersi dalla prova e completare CRUD/importazione. Poi scegliere tra approfondire il supporto allo sport e aggiungere account. Evitare di mettere online una demo senza autenticazione per anticipare il deployment.
