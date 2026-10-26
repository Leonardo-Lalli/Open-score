# Campi e calendario — Team B

> Proprietario: Team B (frontend/UX). Branch `max-develop`. Versione app 0.8.0.
> Registro cronologico: [handoffs/TEAM_B_LOG.md](handoffs/TEAM_B_LOG.md).
> Richieste backend: [handoffs/FRONTEND_TO_BACKEND.md](handoffs/FRONTEND_TO_BACKEND.md), punto 13.

## Perimetro

Solo frontend. Nessuna modifica a `app.py`, `services.py`, `schemas.py`, `db.py`, migrazioni o deploy. La programmazione delle partite continua a usare `PATCH /api/tournaments/{id}/matches/{match_id}/schedule` con `location` testuale, già esistente.

## 1. Pagina Campi (`#/fields`)

Visibile solo ai docenti (`data-teacher-only`); per gli studenti la voce è nascosta e `openFields()` riporta alla dashboard.

Contenuti:

- contatori: campi attivi, campi citati negli incontri, incontri già assegnati a una sede;
- elenco dei campi del docente (`fieldsAdapter.list`);
- stato per campo: attivo/disattivato, nome, sede, descrizione, sport supportati, disponibilità;
- azioni **Modifica** e **Disattiva**;
- sezione "Campi citati negli incontri": deduplicazione dei `location` reali presenti nei tornei leggibili, con numero di incontri programmati;
- modale di creazione/modifica con nome, sede, disponibilità, descrizione, sport (le sei discipline del catalogo) e stato.

Quando `fieldsAdapter.ready` è `false`:

- la lista API è vuota e viene mostrato un avviso esplicito con il contratto atteso;
- la modale si apre in **anteprima** e il submit blocca il salvataggio con il messaggio "Nessun dato è stato inviato";
- i campi citati negli incontri restano visibili perché derivano da dati reali.

## 2. Pagina Calendario (`#/calendar`)

Accessibile a docenti e studenti in sola lettura.

- Partite raggruppate per giorno (`Europe/Rome`), con orario, durata, squadre, torneo, girone, campo, stato e punteggio se presente.
- Sezione separata "Da programmare" per gli incontri senza data.
- Filtri: **torneo**, **squadra**, **giorno**, **campo**, **stato** (tutti, da giocare, giocate, da programmare) e azzeramento.
- Su telefono le righe diventano schede a due colonne con le azioni in basso; i filtri passano a una colonna.
- I docenti con permessi sul torneo hanno il pulsante **Programma/Modifica**, che apre il torneo e la modale di orario e campo.
- Aggiornamento manuale con **Aggiorna**; nessun dato viene salvato dalla pagina calendario.

### Fonte dei dati

`calendarAdapter.ready` è `false`. In questa modalità il frontend aggrega i dettagli dei tornei leggibili con le API esistenti (`GET /api/tournaments` + `GET /api/tournaments/{id}`) e costruisce gli eventi lato client. È lo stesso schema di `loadUpcoming`, esteso a tutti gli incontri.

### Conflitti

Due livelli, distinti e dichiarati nella UI:

1. **Server** (`calendarState.source === "server"`): quando l'API calendario restituirà `conflicts`, il pannello indica "Segnalati dal server".
2. **Anteprima client**: incrociando campo e intervallo `[inizio, inizio + durata)` vengono segnalati:
   - due partite sullo stesso campo con orari sovrapposti;
   - la stessa squadra in due partite sovrapposte (solo dentro lo stesso torneo, perché gli id squadra sono locali).

Le righe coinvolte ricevono `.has-conflict` e un messaggio leggibile con orario, campo e squadre. Il pannello chiarisce che il server resta l'unica fonte autorevole.

### Conflitti in programmazione

Nella modale di una partita:

- il campo `location` suggerisce i campi già usati (`<datalist id="known-fields">`), senza cambiare il payload esistente;
- `updateScheduleConflictHint()` mostra un avviso se un'altra partita dello stesso torneo occupa lo stesso campo nello stesso intervallo;
- il salvataggio non viene forzato: se l'API risponde `409`, `scheduleError()` mostra "Conflitto di calendario: …" dentro la modale e la modale resta aperta.

## 3. Contratto richiesto al Team A

### Campi

```http
GET    /api/fields
POST   /api/fields
PATCH  /api/fields/{id}
DELETE /api/fields/{id}
```

```json
{
  "fields": [
    {
      "id": 1,
      "name": "Palestra A",
      "description": "Parquet, canestri regolamentari",
      "venue": "Plesso centrale",
      "sports": ["Basket", "Pallavolo"],
      "availability": "Lun–Ven 8:00–13:00",
      "active": true
    }
  ]
}
```

- Ambito: solo i campi del docente autenticato.
- `DELETE` = disattivazione soft (`active: false`), non cancellazione dei dati storici.
- Errori: `401` accesso richiesto, `403` campo di un altro docente, `404` inesistente, `409` nome duplicato, `422` dati non validi.
- Quando l'API esiste: impostare `fieldsAdapter.ready = true`. La UI abilita subito creazione, modifica e disattivazione.

### Calendario

```http
GET /api/calendar?tournament=&team=&day=&field=&status=
```

```json
{
  "events": [
    {
      "id": "12-34",
      "tournament_id": 12,
      "tournament_name": "Coppa d'istituto",
      "match_id": 34,
      "home": "5A",
      "away": "5B",
      "home_team_id": 7,
      "away_team_id": 9,
      "round_no": 2,
      "kind": "round_robin",
      "scheduled_at": "2026-11-03T10:00:00+01:00",
      "field": "Palestra A",
      "field_id": 1,
      "duration": 20,
      "status": "ready",
      "score": null,
      "group": "Girone A"
    }
  ],
  "teams": [{ "tournament_id": 12, "id": 7, "name": "5A" }],
  "fields": ["Palestra A", "Palestra B"],
  "conflicts": [
    {
      "kind": "field",
      "match_id": 34,
      "other_match_id": 35,
      "message": "Palestra A occupata due volte alle 10:00"
    }
  ]
}
```

- `status`: `ready`, `waiting`, `completed`.
- `conflicts` calcolati dal server: campo occupato, squadra in doppio impegno, docente in doppio impegno.
- Errori: `401`, `403`, `422` filtri non validi.
- Quando l'API esiste: impostare `calendarAdapter.ready = true`. Il frontend userà gli eventi e i conflitti del server senza modificare la UI.

### Campi nella programmazione partita

Il contratto attuale accetta `location` testuale. Se in futuro si aggiunge `field_id` a `PATCH /matches/{id}/schedule`, il frontend può inviarlo senza rompere il testo: la modale continuerà a mostrare il nome del campo.

## 4. Accessibilità e mobile

- I filtri sono `<label>` con controllo associato, non solo testo.
- Le righe del calendario espongono stato e conflitto a parole, non solo con il colore.
- Il pulsante di azione è un `<button type="button">` con etichetta esplicita.
- Sotto 560px: filtri a una colonna, eventi a due colonne con azioni in basso, campi a una colonna.
- `min-height: 40px` per i controlli dei filtri, in linea con i target touch del progetto.

## 5. Test

In `torneo-lab/tests/test_static_ui.py`:

- `test_fields_and_calendar_interfaces_are_prepared` — adapter, funzioni, azioni, selettori CSS, voci di navigazione e bilancio delle graffe;
- `test_fields_and_calendar_do_not_fake_saves_or_conflicts` — blocco del salvataggio senza API, aggregazione dai tornei reali e gestione dei conflitti `409`.

## 6. Limiti noti

- Il calendario carica un dettaglio per torneo (N+1): accettabile in LAN, da sostituire con `GET /api/calendar` quando disponibile.
- I conflitti lato client sono un'anteprima: non conoscono vincoli che il server applicherà (arbitri, capienza, disponibilità dei campi).
- La disponibilità dei campi è un testo libero finché il backend non definirà una struttura (giorni/fasce).
- Nessun salvataggio viene simulato: senza API la modale campo resta in anteprima e il calendario è in sola lettura.
