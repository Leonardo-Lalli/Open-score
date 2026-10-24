# API effettive della demo

Server locale: `http://127.0.0.1:8000`. OpenAPI: `/openapi.json`; documentazione interattiva: `/docs`. Gli endpoint sotto `/api` sono originali. Non riproducono né chiamano l'API di Score7.

| Metodo | Percorso | Operazione |
| --- | --- | --- |
| GET | /api/health | Versione e modalità locale |
| GET, POST | /api/tournaments | Elenco con stato e contatori; creazione (201) |
| GET | /api/tournaments/{id} | Torneo, squadre, fasi, gironi, incontri, classifiche, campione e diario |
| POST | /api/tournaments/{id}/teams | Aggiunge un partecipante prima della generazione (201) |
| PATCH, DELETE | /api/tournaments/{id}/teams/{team_id} | Rinomina; rimuove dalla bozza (204) |
| POST | /api/tournaments/{id}/generate | Genera una sola volta gironi o albero knockout |
| PATCH | /api/tournaments/{id}/matches/{match_id} | Inserisce/corregge un risultato, propaga avanzamenti |
| DELETE | /api/tournaments/{id}/matches/{match_id}/result | Cancella un risultato e gestisce le dipendenze |
| PATCH | /api/tournaments/{id}/matches/{match_id}/schedule | Data/ora con fuso, campo e durata |
| GET | /api/tournaments/{id}/export.csv | Esportazione degli incontri con mitigazione formule nei testi |
| GET | /api/public/{token} | Dati spettatore, senza diario o metadati privati del torneo |
| POST | /api/demo | Caricamento idempotente dei quattro esempi |

`/public/{token}` serve l'interfaccia spettatore. Non esistono endpoint di scrittura sotto `/api/public`. Non esiste ancora autenticazione per le altre API: questa separazione è una vista locale, non una barriera di autorizzazione per un servizio online.

## Esempio riproducibile

```json
POST /api/tournaments
{
  "name": "Coppa del professore",
  "sport": "Calcio a 5",
  "format": "groups",
  "group_count": 2,
  "qualifiers": 2,
  "team_names": ["Alfa", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta"]
}
```

Dopo la risposta `{"id": ...}`, chiamare `/generate` e leggere il dettaglio. Ogni incontro contiene `version`, `status` e riferimenti ai suoi avversari/sorgenti.

```json
PATCH /api/tournaments/{id}/matches/{match_id}
{"home_score": 2, "away_score": 1, "version": 1, "invalidate": false}
```

Per cancellare un risultato, il corpo DELETE contiene `version` e facoltativamente `invalidate`. Se una correzione altera qualificazioni già avvenute o risultati registrati nei turni successivi, il server risponde 409 finché non viene inviata la conferma `invalidate: true`. Lo snapshot precedente resta nell'audit. Cambiare il solo punteggio mantenendo il vincitore non annulla una finale indipendente dal valore numerico.

Per la programmazione: `{"scheduled_at":"2026-11-03T10:00:00+01:00","location":"Campo A","duration":20,"version":1}`. `scheduled_at: null` rimuove l'orario. La risposta riletta contiene UTC.

## Contratti e stati

- Formati: `round_robin`, `knockout`, `groups`. Sport: Calcio, Calcio a 5, Basket, Pallamano, con solo punteggio numerico generico. Nessuna pretesa di implementare i regolamenti federali completi.
- Da 2 a 32 partecipanti per generazione. Gironi multifase di uguale dimensione, almeno 2 partecipanti ciascuno; 1 o 2 promossi per girone. Le qualificazioni attendono tutti i gironi.
- Incontri: `waiting` → `ready` → `completed`; `bye` è un passaggio automatico senza punteggio. Le correzioni possono riportare incontri dipendenti a `waiting`/`ready`.
- Tornei: `draft`, `active`, `completed`, derivati dai dati, non impostati manualmente dal browser.
- Nomi ripuliti e limitati; campi extra rifiutati. Punteggi interi 0–999; booleani, decimali e stringhe numeriche non accettati.
- 404 per risorse mancanti o incontro di un altro torneo; 409 per versioni obsolete, duplicati, sovrapposizioni e dipendenze da confermare; 422 per input/regole non validi; 403 per scritture da Origin diverso.
- Generazione ripetuta: 409 senza duplicati. Caricamento esempi ripetuto: stessi ID e risultati preservati. Le scritture su più tabelle sono atomiche. Paginazione, ruoli e API pubbliche stabili versionate restano da implementare.
