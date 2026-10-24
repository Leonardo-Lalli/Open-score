# Decisioni e ipotesi — 24 ottobre 2026

1. **Consegna delimitata alla demo.** Il master prompt è una visione di piattaforma; la richiesta attuale privilegia una demo funzionante da mostrare. Formati avanzati e produzione non vengono dichiarati completi.
2. **Nome Open Score provvisorio.** TorneoLab è il nome dello starter e della cartella; il prodotto mostrato usa il nome della repository. La scelta finale resta del gruppo.
3. **Continuità Python.** Conservati FastAPI, SQLite e il metodo del cerchio, con moduli separati. Nessuna build Node necessaria per avviare la demo. React/TypeScript e ORM richiederebbero complessità non utile alla presentazione immediata.
4. **Nuovo schema isolato.** Nuovo file `data/open_score.sqlite3`; nessuna sovrascrittura automatica del vecchio database dello starter. Schema SQL versionato, importazione legacy rimandata e documentata.
5. **Correzioni esplicite.** Il vincitore di un incontro determina i nodi successivi. La conferma d'invalidazione è richiesta quando si perderebbero risultati già registrati o una qualificazione; lo storico viene conservato. Gli orari degli incontri invalidati sono azzerati.
6. **Regole trasparenti.** Classifica: punti, differenza, fatti, nome e ID. Ultimi criteri deterministici della demo, non un regolamento scolastico approvato o una copia dei criteri completi di Score7.
7. **Multifase ridotto.** Gironi uguali, prime 1/2 per gruppo, poi eliminazione singola. Nessun migliore terzo, qualificazione anticipata, Swiss o consolazione.
8. **Sport con punteggio numerico.** Calcio, calcio a 5, basket e pallamano condividono il modello numerico della demo. Set, rigori, supplementari e statistiche individuali sono futuri incrementi.
9. **Presentazione locale.** GitHub condivide codice e istruzioni; non esegue il backend. Nessun deploy remoto o account con permessi fittizi. Un link loopback non rende il torneo raggiungibile dal computer dell'amico.
10. **Dati di provenienza.** Gli ID del JSON fornito sono conservati come `source_id`. I punteggi vuoti diventano NULL, non zero. Tutti gli altri esempi sono sintetici.
11. **Dipendenze.** Versioni runtime fissate a quelle usate nella verifica. Il frontend non scarica font, immagini, script o asset da Score7.
12. **Licenza.** Scelta da concordare con entrambi gli autori prima del rilascio open source stabile. La pubblicazione del codice della demo non viene presentata come sostituto di una licenza esplicita.
