# API effettive

Server di sviluppo: `http://127.0.0.1:8000`. Sulla LAN l'indirizzo è quello del computer server (per esempio `http://192.168.1.50:8000`) e deve comparire in `TORNEO_ALLOWED_HOSTS`. OpenAPI: `/openapi.json`; documentazione interattiva: `/docs`. Gli endpoint sotto `/api` sono originali. Non riproducono né chiamano l'API di Score7.

| Metodo | Percorso | Operazione |
| --- | --- | --- |
| GET | /api/health | Versione, modalità `school-lan` e stato `teacher-login` |
| GET | /api/auth/session | Stato della sessione: `authenticated`, `role` (`teacher` o `student`) e dati del docente |
| POST | /api/auth/login | Accesso con `email` e `password`; imposta il cookie di sessione |
| POST | /api/auth/logout | Cancella il cookie di sessione |
| GET | /api/sports | Catalogo degli sport padre con le varianti annidate |
| GET | /api/sports/{sport_name} | Sport, varianti e regole della variante predefinita; 404 se assente |
| GET | /api/sports/{sport_name}/variants/{variant_slug} | Regole e regolamento di una variante; 404 se assente o di un altro sport |
| GET | /api/variants/{variant_slug} | Scorciatoia per leggere una variante senza indicare lo sport |
| GET, POST | /api/tournaments | Elenco con stato, contatori e `can_manage` (`?archived=exclude\|include\|only`, `?mine=1` per i propri tornei); creazione docente (201) |
| GET | /api/tournaments/{id} | Torneo con sport/variante, regole e regolamento, squadre, fasi, gironi, incontri con set, classifiche, campione, diario e `can_manage` |
| GET | /api/tournaments/{id}/teams/{team_id} | Scheda partecipante: girone, posizione, classifica, incontri, rosa e massimo della variante |
| PATCH | /api/tournaments/{id} | Modifica nome/descrizione sempre; sport, variante, formato e regole solo in bozza |
| POST | /api/tournaments/{id}/archive | Archivia senza cancellare; nasconde dall'elenco predefinito |
| POST | /api/tournaments/{id}/restore | Ripristina un torneo archiviato |
| POST | /api/tournaments/{id}/teams | Aggiunge un partecipante prima della generazione (201) |
| PATCH, DELETE | /api/tournaments/{id}/teams/{team_id} | Rinomina; rimuove dalla bozza (204) |
| GET, POST | /api/tournaments/{id}/teams/{team_id}/players | Elenca la rosa; aggiunge un giocatore (201) |
| DELETE | /api/tournaments/{id}/teams/{team_id}/players/{player_id} | Rimuove un giocatore dalla rosa (204) |
| POST | /api/tournaments/{id}/generate | Genera una sola volta gironi o albero knockout, con la durata della variante |
| PATCH | /api/tournaments/{id}/matches/{match_id} | Inserisce/corregge un risultato numerico o set per set, propaga avanzamenti |
| DELETE | /api/tournaments/{id}/matches/{match_id}/result | Cancella un risultato e gestisce le dipendenze |
| PATCH | /api/tournaments/{id}/matches/{match_id}/schedule | Data/ora con fuso, campo e durata |
| GET | /api/tournaments/{id}/export.csv | Esportazione degli incontri con mitigazione formule nei testi |
| GET | /api/public/{token} | Dati spettatore, senza diario o metadati privati del torneo |

Non esiste un endpoint di seed o di caricamento di dati dimostrativi: il database parte vuoto e i tornei nascono solo dalle richieste dei docenti.

`/public/{token}` serve l'interfaccia spettatore. Non esistono endpoint di scrittura sotto `/api/public`. Ogni metodo diverso da `GET`/`HEAD`/`OPTIONS` sotto `/api` richiede una sessione docente, tranne `login` e `logout`: studenti e anonimi ricevono `401`. Ogni scrittura su un torneo richiede inoltre che il torneo appartenga al docente autenticato, altrimenti `403`. Le letture restano pubbliche. Dettagli e limiti in [SECURITY.md](SECURITY.md).

## Accesso e sessioni

```json
POST /api/auth/login
{"email": "prof@scuola.it", "password": "..."}
```

Risposta `200`: `{"authenticated": true, "role": "teacher", "teacher": {"id": 1, "email": "prof@scuola.it", "display_name": "Amministratore"}}` e cookie `open_score_session` (`HttpOnly`, `SameSite=Lax`, durata 12 ore salvo `TORNEO_SESSION_HOURS`). Credenziali errate: `401`; email non valida: `422`; troppi tentativi dallo stesso IP: `429` dopo 5 errori in 5 minuti, con blocco di 60 secondi. `POST /api/auth/logout` risponde `{"ok": true}` e cancella il cookie.

La sessione contiene l'id e l'email del docente ed è firmata con HMAC-SHA256. Una scrittura senza sessione riceve `401 {"detail": "Accesso richiesto"}`; una scrittura su un torneo di un altro docente riceve `403`. La UI mostra il gate iniziale **Sono un prof** / **Sono uno studente**, nasconde i comandi di modifica agli studenti e mostra **Solo lettura** sui tornei non gestibili. Non esiste più il Bearer token globale: l'isolamento è per account docente.

## Esempio riproducibile

```json
POST /api/tournaments
{
  "name": "Coppa del professore",
  "sport": "Calcio",
  "variant": "calcio-a-5",
  "format": "groups",
  "group_count": 2,
  "qualifiers": 2,
  "tie_breaker": "head_to_head",
  "team_names": ["Alfa", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta"]
}
```

Dopo la risposta `{"id": ...}`, chiamare `/generate` e leggere il dettaglio. Ogni incontro contiene `version`, `status` e riferimenti ai suoi avversari/sorgenti. `sport_id` e `variant` sono facoltativi: se omessi il server sceglie la variante predefinita compatibile con `participant_kind`; se inviati devono appartenere allo sport. La variante determina `participant_kind`, punti di classifica, durata degli incontri e regolamento; i valori espliciti di `win_points`, `draw_points`, `loss_points` e `tie_breaker` hanno precedenza. `tie_breaker` accetta `goal_difference` (predefinito), `head_to_head`, `goals_for` o `wins`.

La scheda partecipante restituisce `team` (con `group_name`), `standing`, `position`, gli `matches` del solo partecipante con `opponent_name` e lo stato, la `players` della rosa, `max_roster` e `participant_kind`, più una copia ridotta del torneo. Un `team_id` di un altro torneo restituisce 404.

```json
POST /api/tournaments/{id}/teams/{team_id}/players
{"name": "Luca Bianchi", "shirt_number": 7}
```

La rosa è disponibile solo per le varianti a squadre. Omonimi, anche con maiuscole diverse, restituiscono 409; superare `max_roster` o usare una variante individuale restituisce 422.

```json
PATCH /api/tournaments/{id}/matches/{match_id}
{"home_score": 2, "away_score": 1, "version": 1, "invalidate": false}
```

Per le varianti a set si invia il dettaglio, senza i punteggi finali:

```json
PATCH /api/tournaments/{id}/matches/{match_id}
{
  "sets": [
    {"home": 25, "away": 20},
    {"home": 20, "away": 25},
    {"home": 25, "away": 20},
    {"home": 20, "away": 25},
    {"home": 15, "away": 10}
  ],
  "version": 1
}
```

Il server valida numero massimo di set, punti minimi, scarto di due, limite del set e vittoria con il numero richiesto di set; poi calcola `home_score`/`away_score` come set vinti. In Pallavolo 6v6 una partita conclusa al quinto set assegna 2 punti alla vincente e 1 alla perdente; negli altri risultati valgono i punti della variante. Inviare `home_score` a una variante a set (o `sets` a una variante numerica) restituisce 422. Il dettaglio letto espone `sets` su ogni incontro.

Per cancellare un risultato, il corpo DELETE contiene `version` e facoltativamente `invalidate`. Se una correzione altera qualificazioni già avvenute o risultati registrati nei turni successivi, il server risponde 409 finché non viene inviata la conferma `invalidate: true`. Lo snapshot precedente resta nell'audit. Cambiare il solo punteggio mantenendo il vincitore non annulla una finale indipendente dal valore numerico.

Per la programmazione: `{"scheduled_at":"2026-11-03T10:00:00+01:00","location":"Campo A","duration":20,"version":1}`. `duration` è facoltativo: se assente usa `rules_snapshot.match_duration`. `scheduled_at: null` rimuove l'orario. La risposta riletta contiene UTC.

```json
PATCH /api/tournaments/{id}
{"name": "Coppa del professore", "description": "Fase scolastica"}
```

La modifica parziale accetta solo i campi inviati. Nome e descrizione sono sempre modificabili; `sport`, `variant`, `format`, `participant_kind`, punti, `legs`, `group_count`, `qualifiers`, `random_seed`, `tournament_type`, `scoring_system` e `tie_breaker` rispondono 409 dopo la generazione degli incontri. Un corpo vuoto, un campo sconosciuto, una coppia sport/`sport_id` incoerente o una variante di un altro sport restituiscono 422. `POST .../archive` imposta `archived_at` e rende il torneo di sola lettura; `POST .../restore` lo riattiva. Nessun endpoint cancella un torneo: un torneo con sport storico rimosso resta leggibile ma rifiuta ogni scrittura con 409.

## Contratti e stati

- Formati: `round_robin`, `knockout`, `groups`. Sport ammessi (`sport_configs`): Calcio, Basket, Pallavolo, Badminton, Ping pong, Biliardino. Varianti ammesse: `calcio-a-11`, `calcio-a-7`, `calcio-a-5`, `basket-5v5`, `basket-3x3`, `pallavolo-6v6`, `pallavolo-4v4`, `beach-volley-2v2`, `badminton-singolare`, `badminton-doppio`, `badminton-doppio-misto`, `ping-pong-singolare`, `ping-pong-doppio`, `ping-pong-doppio-misto`, `biliardino-singolare`, `biliardino-doppio`. Le varianti individuali richiedono `participant_kind: "individual"`. Nessuna pretesa di implementare i regolamenti federali completi.
- Punteggi: varianti `goals`/`points` usano `home_score` e `away_score`; varianti `sets` usano l'array `sets`. Il pareggio è rifiutato dove `draw_allowed` è falso e nei knockout. Un risultato numerico su una variante a set, o viceversa, restituisce 422.
- Rose: solo per varianti a squadre; nome 1–60 caratteri, numero di maglia 0–99 opzionale, massimo da `max_roster`, duplicati 409. Le rose restano modificabili dopo la generazione.
- Da 2 a 32 partecipanti per generazione. Gironi multifase di uguale dimensione, almeno 2 partecipanti ciascuno; 1 o 2 promossi per girone. Le qualificazioni attendono tutti i gironi.
- Incontri: `waiting` → `ready` → `completed`; `bye` è un passaggio automatico senza punteggio. Le correzioni possono riportare incontri dipendenti a `waiting`/`ready`.
- Classifiche: ricalcolate dai risultati validi. A parità di punti il criterio è `tie_breaker` (`goal_difference`, `head_to_head`, `goals_for`, `wins`), poi nome e ID. Con `head_to_head` si confrontano solo gli incontri tra le squadre appaiate. Nei tornei a set `goals_for`/`goals_against` rappresentano i set vinti e persi; in Pallavolo 6v6 una vittoria al quinto set vale 2/1 invece di 3/0.
- Tornei: `draft`, `active`, `completed`, derivati dai dati, non impostati manualmente dal browser.
- Nomi ripuliti e limitati; campi extra rifiutati. Punteggi interi 0–999; booleani, decimali e stringhe numeriche non accettati.
- 404 per risorse mancanti o incontro di un altro torneo; 409 per versioni obsolete, duplicati, sovrapposizioni, tornei archiviati e dipendenze da confermare; 422 per input/regole non validi; 401 per scritture senza sessione quando l'autenticazione è attiva; 429 per troppi tentativi di accesso; 403 per scritture da Origin diverso; 400 per Host non consentito.
- Generazione ripetuta: 409 senza duplicati. Caricamento esempi ripetuto: stessi ID e risultati preservati. Le scritture su più tabelle sono atomiche. Paginazione e ruoli amministrativi aggiuntivi restano da implementare.
