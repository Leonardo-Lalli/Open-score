# Decisioni e ipotesi — 25 ottobre 2026

1. **Consegna delimitata alla demo.** Il master prompt è una visione di piattaforma; la richiesta attuale privilegia una demo funzionante da mostrare. Formati avanzati e produzione non vengono dichiarati completi.
2. **Nome Open Score provvisorio.** TorneoLab è il nome dello starter e della cartella; il prodotto mostrato usa il nome della repository. La scelta finale resta del gruppo.
3. **Continuità Python.** Conservati FastAPI, SQLite e il metodo del cerchio, con moduli separati. Nessuna build Node necessaria per avviare la demo. React/TypeScript e ORM richiederebbero complessità non utile alla presentazione immediata.
4. **Nuovo schema isolato.** Nuovo file `data/open_score.sqlite3`; nessuna sovrascrittura automatica del vecchio database dello starter. Schema SQL versionato, importazione legacy rimandata e documentata.
5. **Correzioni esplicite.** Il vincitore di un incontro determina i nodi successivi. La conferma d'invalidazione è richiesta quando si perderebbero risultati già registrati o una qualificazione; lo storico viene conservato. Gli orari degli incontri invalidati sono azzerati.
6. **Regole trasparenti.** Classifica: punti e criterio scelto fra differenza, scontri diretti, reti fatte e vittorie, poi nome e ID. Sono criteri deterministici della demo, non un regolamento scolastico approvato o una copia dei criteri completi di Score7.
7. **Multifase ridotto.** Gironi uguali, prime 1/2 per gruppo, poi eliminazione singola. Nessun migliore terzo, qualificazione anticipata, Swiss o consolazione.
8. **Sport con punteggio numerico.** Calcio, calcio a 5, basket e pallamano condividono il modello numerico della demo. Set, rigori, supplementari e statistiche individuali sono futuri incrementi.
9. **LAN scolastica, non Internet.** Il server gira su un computer della scuola ed è raggiungibile dalla rete interna. GitHub condivide codice e istruzioni; non esegue il backend. Non si promette un servizio pubblico né un hosting remoto.
10. **Un solo organizzatore condiviso.** Una password (`TORNEO_ADMIN_PASSWORD`) protegge tutte le scritture; in alternativa uno script usa un Bearer token. Non si simulano account individuali o ruoli per torneo finché non esiste un modello utenti reale. Chi consulta non accede e il link pubblico resta di sola lettura.
11. **Segreti fuori dal repository.** Password, token, segreto di sessione, database e backup vivono solo sul server. Il segreto dei cookie è su file o variabile d'ambiente e può essere ruotato per invalidare tutte le sessioni.
12. **Dati di provenienza.** Gli ID del JSON fornito sono conservati come `source_id`. I punteggi vuoti diventano NULL, non zero. Tutti gli altri esempi sono sintetici.
13. **Dipendenze.** Versioni runtime fissate a quelle usate nella verifica. Il frontend non scarica font, immagini, script o asset da Score7.
14. **Un solo worker SQLite.** WAL, `busy_timeout` e `BEGIN IMMEDIATE` bastano per la LAN con un processo `uvicorn`. PostgreSQL e più worker richiederebbero una migrazione dedicata, non un cambio di configurazione.
15. **Backup online.** I backup usano `VACUUM INTO` e non la copia a caldo del file: con WAL una copia del solo database può essere incompleta. La conservazione predefinita è di 14 copie.
16. **Licenza.** Scelta da concordare con entrambi gli autori prima del rilascio open source stabile. La pubblicazione del codice della demo non viene presentata come sostituto di una licenza esplicita.
