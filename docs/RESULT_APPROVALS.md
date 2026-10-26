# Risultati proposti e approvazioni

> Documento del Team B. Le interfacce sono pronte; il backend delle proposte non esiste ancora.
> Base: `max-develop` · App 0.8.0.

## Stato

- **Interfaccia professore**: scheda **Da verificare** nel dettaglio torneo, visibile al docente proprietario. Mostra lo stato “In attesa API” finché l'adapter non è attivo.
- **Interfaccia studente**: modale “Proponi il risultato” con campi numerici o set, avviso **PROPOSTA · NON UFFICIALE** e messaggio che la classifica non cambia fino all'approvazione. Il pulsante è mostrato solo quando `resultProposalsAdapter.ready` è `true`, quindi oggi non appare.
- **Nessun salvataggio simulato**: `resultProposalsAdapter.ready` è `false`; non vengono usati localStorage o dati finti.

## Contratto proposto al Team A

### Elenco proposte

```http
GET /api/tournaments/{id}/proposals?status=pending
200 {
  "proposals": [{
    "id": 12,
    "match_id": 34,
    "tournament_name": "Coppa d'istituto",
    "home_name": "3A Falchi",
    "away_name": "3B Leoni",
    "proposed_home_score": 2,
    "proposed_away_score": 1,
    "proposed_sets": null,
    "author": "Mario Rossi",
    "created_at": "2026-10-26T10:00:00Z",
    "status": "pending",
    "conflicts": []
  }]
}
```

`author` deve arrivare solo se il richiedente è autorizzato a vederlo. `conflicts` elenca eventuali proposte alternative sulla stessa partita.

### Invio proposta (studente)

```http
POST /api/tournaments/{id}/matches/{match_id}/proposals
{"home_score": 2, "away_score": 1, "version": 3}
```

Per le varianti a set:

```json
{"sets": [{"home": 25, "away": 20}, {"home": 21, "away": 25}], "version": 3}
```

Il backend valida la partita, la variante, lo stato `ready`, i punteggi e la versione. La proposta non modifica classifica, tabellone o risultati ufficiali.

### Revisione (professore)

```http
PATCH /api/proposals/{id}
{"action": "approve"}
{"action": "reject"}
{"action": "correct", "home_score": 3, "away_score": 1}
```

Dopo `approve`, il risultato ufficiale deve essere aggiornato dal backend e restituito nel dettaglio torneo, così classifiche e tabelloni vengono riletti.

## Errori gestiti

| Codice | Messaggio previsto |
| --- | --- |
| 401 | Sessione scaduta. Accedi di nuovo. |
| 403 | Non hai i permessi per questa azione. |
| 404 | Partita o proposta non trovata. |
| 409 | Proposta già revisionata o modificata da un altro utente. |
| rete | Server non raggiungibile. |

Una risposta fallita non viene mai mostrata come salvataggio riuscito. Dopo l'approvazione la UI ricarica il torneo dal server; non aggiorna localmente classifiche o tabelloni.

## Cosa deve ancora fornire il Team A

1. Identità studente e sessione studente (oggi lo studente è anonimo in sola lettura).
2. Modello e tabelle delle proposte, con stato `pending`/`approved`/`rejected`.
3. Regole di autorizzazione: chi può proporre, chi può vedere l'autore, chi può approvare.
4. Conflitti tra proposte sulla stessa partita.
5. Cronologia delle revisioni.
6. Endpoint di elenco e revisione, con gestione della concorrenza tramite versione.

## Test

- Test statico per adapter, scheda, modali, azioni e mapping errori.
- La prova end-to-end resta bloccata finché il backend non espone le proposte.
