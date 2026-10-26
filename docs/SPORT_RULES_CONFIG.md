# Configurazione sport e regole — Team B

> Proprietario: Team B (frontend/UX). Branch `max-develop`. Versione app 0.8.0.
> Registro cronologico: [handoffs/TEAM_B_LOG.md](handoffs/TEAM_B_LOG.md).
> Richieste backend: [handoffs/FRONTEND_TO_BACKEND.md](handoffs/FRONTEND_TO_BACKEND.md), punto 14.

## Principio

La **variante** è la fonte autorevole. Il frontend non conosce il regolamento di uno sport: legge i metadati restituiti da `GET /api/sports` e `GET /api/sports/{sport}/variants/{slug}` e costruisce i form da lì.

- Ciò che il backend dichiara modificabile viene mostrato come input.
- Ciò che la variante definisce (durata, tempi, set, pareggio, campo, rose) viene mostrato in sola lettura.
- Un nuovo sport o una nuova variante aggiunti dal Team A compaiono automaticamente: non serve toccare i componenti.

## 1. Selettore sport

### Catalogo `#/sport/{sport}/{variante}`

- Sport e varianti arrivano da `GET /api/sports`.
- Ogni scheda mostra nome, descrizione, partecipanti, durata, punteggio e limiti della rosa.
- La scheda di dettaglio mostra:
  - statistiche della variante;
  - **regolamento** completo;
  - **Dettagli di gioco** generati da `variant.rules` (chiave → etichetta → valore);
  - **Parametri configurabili** con i limiti dichiarati dai metadati;
  - CTA per creare un torneo con quella variante.

Nessuno sport viene mostrato se il backend non lo restituisce. `schemas.py` continua a validare lo sport lato server.

### Wizard di creazione

Passo 1 («Il torneo»):

1. nome;
2. sport (`#wizard-sport`);
3. variante (`#wizard-variant`);
4. anteprima della variante;
5. percorso (eliminazione, girone unico, gironi + finali);
6. numero partecipanti;
7. **regole del torneo** (`#wizard-rule-fields`).

Cambiando sport o variante, l'anteprima e i campi regola vengono ricostruiti con i valori predefiniti della nuova variante. Cambiando formato, i campi non applicabili vengono rimossi (es. gironi in eliminazione diretta) e le validazioni si aggiornano.

## 2. Metadati accettati

La variante può includere un array `config_schema` (alias supportati: `rule_schema`, `configurable`). Se è assente, il frontend usa il **contratto condiviso** di `TournamentInput` come fallback.

```json
{
  "slug": "calcio-a-5",
  "name": "Calcio a 5",
  "participant_kind": "team",
  "rules": {
    "players_on_field": 5,
    "min_lineup": 3,
    "max_roster": 12,
    "match_duration": 40,
    "draw_allowed": true,
    "periods": 2,
    "period_minutes": 20,
    "standings": { "win": 3, "draw": 1, "loss": 0 },
    "default_tie_breaker": "goal_difference"
  },
  "config_schema": [
    {
      "key": "win_points",
      "label": "Punti vittoria",
      "type": "number",
      "min": 0,
      "max": 10,
      "step": 1,
      "default": 3,
      "required": true,
      "help": "Punti in classifica per una vittoria.",
      "scope": "tournament",
      "stages": ["round_robin", "groups"]
    },
    {
      "key": "tie_breaker",
      "label": "Criterio a parità",
      "type": "select",
      "options": [
        { "value": "goal_difference", "label": "Differenza reti" },
        { "value": "head_to_head", "label": "Scontri diretti" }
      ],
      "default": "goal_difference",
      "required": true,
      "scope": "tournament"
    }
  ]
}
```

### Campi del descrittore

| Campo | Tipo | Uso |
| --- | --- | --- |
| `key` | string | chiave inviata nel payload del torneo |
| `label` | string | etichetta visibile |
| `type` | `number`, `select`, `checkbox`, `text` | controllo da renderizzare |
| `min`, `max`, `step` | number | vincoli HTML del controllo numerico |
| `options` | array di `{value,label}` o stringhe | opzioni del select |
| `required` | bool | campo obbligatorio (default `true`) |
| `default` | any | valore iniziale |
| `help` | string | testo di supporto e valori ammessi |
| `scope` | `tournament` o `variant` | solo `tournament` è modificabile |
| `stages` | array di formati | mostra il campo solo per quei formati |
| `disabled` | bool | controllo visibile ma bloccato (es. pareggio non ammesso) |

### Fallback attuale

Senza `config_schema`, i campi modificabili sono quelli realmente accettati da `TournamentInput`/`TournamentUpdate`:

- `win_points`, `draw_points`, `loss_points` (0–10);
- `tie_breaker` (opzioni da `variant.tie_breakers` se presente, altrimenti ai quattro criteri supportati dal backend);
- `legs` (1 o 2) per girone unico e gironi;
- `group_count` (2, 4, 8) e `qualifiers` (1, 2) per i gironi.

Tutto il resto è **derivato** da `variant.rules` e mostrato in sola lettura. Il frontend non invia mai chiavi che il contratto non prevede: per il fallback il payload è limitato a quelle sopra.

## 3. Validazione

Tre livelli, coerenti con il backend:

1. **HTML**: `required`, `min`, `max`, `step` generati dal descrittore. Il browser blocca il submit con messaggi standard e focus sul campo.
2. **Avvisi in tempo reale** (`role="alert"`, `#rule-fields-warnings`):
   - campo obbligatorio vuoto;
   - numero fuori dall'intervallo dichiarato;
   - eliminazione diretta con andata e ritorno;
   - gironi non divisibili o con meno di due partecipanti per girone.
3. **Backend**: unica autorità. Se la richiesta fallisce, il messaggio di `detail` viene mostrato in `#form-error` e la modale resta aperta. Nessun salvataggio viene forzato o ritentato ignorando l'errore.

Il pulsante di salvataggio non viene disabilitato dagli avvisi: l'utente vede il problema, ma la decisione finale resta del server. Gli avvisi bloccano solo le combinazioni che il contratto dichiara impossibili (es. knockout + `legs=2`).

## 4. Tornei già iniziati

Se `data.matches.length > 0`:

- la modale di modifica mostra un banner **«Torneo già iniziato»** e non rende modificabili sport, variante, formato e regole;
- il payload contiene solo nome e descrizione, quindi non si tenta di aggirare il blocco `409` del backend;
- la scheda Regolamento mostra lo stesso avviso e nasconde il pulsante «Modifica regole»;
- le regole applicate restano consultabili.

## 5. File e funzioni

- `app.js`: `variantRuleSchema`, `fallbackRuleSchema`, `ruleInputHtml`, `ruleFieldsetHtml`, `ruleWarnings`, `derivedRuleItems`, `updateRuleWarnings`, `renderEditRules`, `readEditRules`.
- `styles.css`: `.rule-fieldset`, `.rule-warnings`, `.rule-warning-banner`, `.rule-config-list`, `.rule-config-row`, `.rule-derived`.
- Test: `tests/test_static_ui.py`, `test_sport_rule_forms_are_metadata_driven` e `test_sport_rule_forms_do_not_override_backend_metadata`.

## 6. Limiti noti

- Finché il backend non espone `config_schema`, i campi modificabili sono quelli del contratto condiviso; durata, tempi e set restano derivati dalla variante.
- Le opzioni di `tie_breaker` sono un fallback: se il Team A aggiunge criteri, deve esporli in `variant.tie_breakers` (o in `config_schema`).
- I metadati non descrivono ancora dipendenze condizionali complesse (es. «se il pareggio non è ammesso, `draw_points` deve essere 0»): il fallback gestisce i casi noti, il backend resta l'autorità.
- La modifica delle regole su un torneo avviato resta bloccata dal backend; il frontend lo dichiara e non prova a forzare.
