# API effettive

Server di sviluppo: `http://127.0.0.1:8000`. Sulla LAN l'indirizzo è quello del computer server (per esempio `http://192.168.1.50:8000`) e deve comparire in `TORNEO_ALLOWED_HOSTS`. OpenAPI: `/openapi.json`; documentazione interattiva: `/docs`. Gli endpoint sotto `/api` sono originali. Non riproducono né chiamano l'API di Score7.

| Metodo | Percorso | Operazione |
| --- | --- | --- |
| GET | /api/health | Versione, modalità (`local-demo` o `school-lan`) e stato dell'autenticazione |
| GET | /api/auth/session | Stato della sessione: `authenticated`, `auth_required`, `role` |
| POST | /api/auth/login | Accesso con password; imposta il cookie di sessione |
| POST | /api/auth/logout | Cancella il cookie di sessione |
| GET | /api/sports | Catalogo sport letto da `sport_configs` |
| GET | /api/sports/{sport_name} | Regole e dimensioni di uno sport; 404 se assente |
| GET, POST | /api/tournaments | Elenco con stato e contatori (`?archived=exclude\|include\|only`); creazione (201) |
| GET | /api/tournaments/{id} | Torneo con `sport_config`, squadre, fasi, gironi, incontri, classifiche, campione e diario |
| GET | /api/tournaments/{id}/teams/{team_id} | Scheda partecipante: girone, posizione, classifica e incontri |
| PATCH | /api/tournaments/{id} | Modifica nome/descrizione sempre; sport, formato e regole solo in bozza |
| POST | /api/tournaments/{id}/archive | Archivia senza cancellare; nasconde dall'elenco predefinito |
| POST | /api/tournaments/{id}/restore | Ripristina un torneo archiviato |
| POST | /api/tournaments/{id}/teams | Aggiunge un partecipante prima della generazione (201) |
| PATCH, DELETE | /api/tournaments/{id}/teams/{team_id} | Rinomina; rimuove dalla bozza (204) |
| POST | /api/tournaments/{id}/generate | Genera una sola volta gironi o albero knockout |
| PATCH | /api/tournaments/{id}/matches/{match_id} | Inserisce/corregge un risultato, propaga avanzamenti |
| DELETE | /api/tournaments/{id}/matches/{match_id}/result | Cancella un risultato e gestisce le dipendenze |
| PATCH | /api/tournaments/{id}/matches/{match_id}/schedule | Data/ora con fuso, campo e durata |
| GET | /api/tournaments/{id}/export.csv | Esportazione degli incontri con mitigazione formule nei testi |
| GET | /api/public/{token} | Dati spettatore, senza diario o metadati privati del torneo |
| POST | /api/demo | Caricamento idempotente dei quattro esempi |

`/public/{token}` serve l'interfaccia spettatore. Non esistono endpoint di scrittura sotto `/api/public`. Con `TORNEO_ADMIN_PASSWORD` o `TORNEO_API_TOKEN` impostati, ogni altro metodo diverso da `GET`/`HEAD`/`OPTIONS` sotto `/api` richiede una sessione o un token; senza configurazione l'app resta in modalità demo locale e le scritture sono aperte. Dettagli e limiti in [SECURITY.md](SECURITY.md).

## Accesso e sessioni

```json
POST /api/auth/login
{"password": "..."}
```

Risposta `200`: `{"authenticated": true, "auth_required": true, "role": "admin"}` e cookie `open_score_session` (`HttpOnly`, `SameSite=Lax`, durata 12 ore salvo `TORNEO_SESSION_HOURS`). Password errata: `401`; troppi tentativi dallo stesso IP: `429` dopo 5 errori in 5 minuti, con blocco di 60 secondi. `POST /api/auth/logout` risponde `{"ok": true}` e cancella il cookie.

Gli script possono evitare il login con `Authorization: Bearer <TORNEO_API_TOKEN>`. Una scrittura senza credenziali valide riceve `401 {"detail": "Accesso richiesto"}`. Con autenticazione attiva la UI mostra **Accedi** e nasconde i comandi di modifica; un tentativo di scrittura da spettatore riapre la finestra di accesso. Senza password configurata `auth_required` è `false` e il ruolo locale è `admin`.

## Esempio riproducibile

```json
POST /api/tournaments
{
  "name": "Coppa del professore",
  "sport": "Calcio a 5",
  "format": "groups",
  "group_count": 2,
  "qualifiers": 2,
  "tie_breaker": "head_to_head",
  "team_names": ["Alfa", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta"]
}
```

Dopo la risposta `{"id": ...}`, chiamare `/generate` e leggere il dettaglio. Ogni incontro contiene `version`, `status` e riferimenti ai suoi avversari/sorgenti. `sport_id` è facoltativo: se omesso il server lo ricava da `sport`; se inviato deve corrispondere al nome. `tie_breaker` accetta `goal_difference` (predefinito), `head_to_head`, `goals_for` o `wins`.

La scheda partecipante restituisce `team` (con `group_name`), `standing`, `position`, gli `matches` del solo partecipante con `opponent_name` e lo stato, più una copia ridotta del torneo. Un `team_id` di un altro torneo restituisce 404.

```json
PATCH /api/tournaments/{id}/matches/{match_id}
{"home_score": 2, "away_score": 1, "version": 1, "invalidate": false}
```

Per cancellare un risultato, il corpo DELETE contiene `version` e facoltativamente `invalidate`. Se una correzione altera qualificazioni già avvenute o risultati registrati nei turni successivi, il server risponde 409 finché non viene inviata la conferma `invalidate: true`. Lo snapshot precedente resta nell'audit. Cambiare il solo punteggio mantenendo il vincitore non annulla una finale indipendente dal valore numerico.

Per la programmazione: `{"scheduled_at":"2026-11-03T10:00:00+01:00","location":"Campo A","duration":20,"version":1}`. `scheduled_at: null` rimuove l'orario. La risposta riletta contiene UTC.

```json
PATCH /api/tournaments/{id}
{"name": "Coppa del professore", "description": "Fase scolastica"}
```

La modifica parziale accetta solo i campi inviati. Nome e descrizione sono sempre modificabili; `sport`, `format`, `participant_kind`, punti, `legs`, `group_count`, `qualifiers`, `random_seed`, `tournament_type`, `scoring_system` e `tie_breaker` rispondono 409 dopo la generazione degli incontri. Un corpo vuoto, un campo sconosciuto o una coppia sport/`sport_id` incoerente restituiscono 422. `POST .../archive` imposta `archived_at` e rende il torneo di sola lettura; `POST .../restore` lo riattiva. Nessun endpoint cancella un torneo.

## Contratti e stati

- Formati: `round_robin`, `knockout`, `groups`. Sport ammessi (catalogo `sport_configs`): Calcio, Calcio a 5, Basket, Pallamano, Badminton, Tennis, Pallavolo, con punteggio numerico generico. Il server risolve `sport_id` dal nome; una coppia incoerente restituisce 422. Nessuna pretesa di implementare i regolamenti federali completi.
- Da 2 a 32 partecipanti per generazione. Gironi multifase di uguale dimensione, almeno 2 partecipanti ciascuno; 1 o 2 promossi per girone. Le qualificazioni attendono tutti i gironi.
- Incontri: `waiting` → `ready` → `completed`; `bye` è un passaggio automatico senza punteggio. Le correzioni possono riportare incontri dipendenti a `waiting`/`ready`.
- Classifiche: ricalcolate dai risultati validi. A parità di punti il criterio è `tie_breaker` (`goal_difference`, `head_to_head`, `goals_for`, `wins`), poi nome e ID. Con `head_to_head` si confrontano solo gli incontri tra le squadre appaiate.
- Tornei: `draft`, `active`, `completed`, derivati dai dati, non impostati manualmente dal browser.
- Nomi ripuliti e limitati; campi extra rifiutati. Punteggi interi 0–999; booleani, decimali e stringhe numeriche non accettati.
- 404 per risorse mancanti o incontro di un altro torneo; 409 per versioni obsolete, duplicati, sovrapposizioni, tornei archiviati e dipendenze da confermare; 422 per input/regole non validi; 401 per scritture senza sessione quando l'autenticazione è attiva; 429 per troppi tentativi di accesso; 403 per scritture da Origin diverso; 400 per Host non consentito.
- Generazione ripetuta: 409 senza duplicati. Caricamento esempi ripetuto: stessi ID e risultati preservati. Le scritture su più tabelle sono atomiche. Paginazione e account individuali restano da implementare.
