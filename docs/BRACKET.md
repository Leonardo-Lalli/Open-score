# Tabellone a eliminazione — Team B

> Proprietario: Team B (frontend/UX). Branch `max-develop`. Versione app 0.8.0.
> Registro cronologico: [handoffs/TEAM_B_LOG.md](handoffs/TEAM_B_LOG.md).

## 1. Audit iniziale

Il bracket grafico esisteva già nella scheda **Tabellone** (`tab === "bracket"`):

- leggeva `data.matches` filtrando `kind === "knockout"`;
- usava `round_no`, `position`, `source_home`, `source_away`;
- disegnava le linee con SVG e posizionava le card in un contenitore con scroll orizzontale;
- aveva già i chip dei turni su mobile e la regione focusabile.

Punti migliorati in questo intervento:

- layout estratto in un modulo puro e testabile;
- colonna **Campione** alla fine dell'albero;
- etichette delle partite future basate sui turni reali, non su ID;
- stati più espliciti e `aria-label` per ogni card;
- nota che chiarisce il rapporto con le proposte di risultato;
- tipografia mobile più leggibile e chip "Campione";
- test automatici per 4, 8 e 16 squadre, BYE e incontri incompleti.

## 2. Fonte dei dati

Il tabellone usa **solo dati ufficiali** restituiti da `GET /api/tournaments/{id}`:

| Campo | Uso |
| --- | --- |
| `round_no`, `position` | posizione della card nel turno |
| `source_home`, `source_away` | relazioni reali tra gli incontri e origine delle linee |
| `home_team_id`, `away_team_id` | squadre già qualificate |
| `home_score`, `away_score` | risultato ufficiale |
| `winner_team_id` | squadra evidenziata come vincente |
| `is_bye` | passaggio automatico |
| `status` | `waiting`, `ready`, `completed`, `bye` |
| `champion_team_id` | campione mostrato nella colonna finale |

La progressione **non** viene dedotta dall'ordine dell'array: ogni linea nasce da `source_home`/`source_away`. Il layout accetta anche fixture in ordine diverso e produce le stesse coordinate (test dedicato).

### Proposte di risultato

Il tabellone legge `data.matches`, che contiene solo risultati ufficiali. Le proposte vivono nel flusso separato `resultProposalsAdapter` e non modificano `matches` finché un docente non approva. Per questo una proposta in attesa non fa avanzare nessuno. La UI lo dichiara sotto il tabellone.

## 3. Modulo di layout

`static/bracket-layout.js` è un modulo UMD senza dipendenze:

- nel browser espone `BracketLayout`;
- in Node esporta lo stesso oggetto (`module.exports`) per i test.

API:

```js
BracketLayout.layout(fixtures)
```

Restituisce:

```json
{
  "rounds": 3,
  "roundNumbers": [1, 2, 3],
  "labels": ["Quarti di finale", "Semifinali", "Finale"],
  "first": 4,
  "width": 1132,
  "height": 572,
  "coords": { "12": { "x": 0, "y": 104, "roundIndex": 0 } },
  "paths": [{ "fromMatch": "12", "toMatch": "16", "d": "M246,104H270V296H295" }],
  "champion": { "x": 885, "y": 296, "d": "M541,296H885" },
  "lines": "M246,104H270V296H295…"
}
```

Costanti geometriche: colonna 295px, card 246×84px, riga 128px, offset titoli 40px, connettore 24px. Le card e i titoli sono posizionati in assoluto dentro `.bracket-tree`; l'SVG dei collegamenti è `aria-hidden`.

### Etichette dei turni

`roundLabels` deriva i nomi dal numero di turni:

- 1 turno → Finale;
- 2 → Semifinali, Finale;
- 3 → Quarti di finale, Semifinali, Finale;
- 4 → Ottavi di finale, Quarti di finale, Semifinali, Finale;
- oltre → `Turno N`.

## 4. Interfaccia

- **Card partita**: due squadre, punteggio ufficiale, stato, vincente in evidenza. Le card modificabili sono `<button>`; le altre sono `<div role="group">` con `aria-label` completo.
- **Partite future**: mostrano `Vincente {turno} {posizione}` invece dell'ID grezzo.
- **BYE**: lato mancante "Riposo · BYE", stato "Passaggio automatico".
- **Colonna Campione**: card con trofeo e nome del campione; se la finale non è conclusa mostra "Da decidere / La finale decide".
- **Collegamenti**: linee SVG dalle sorgenti reali; la finale è collegata alla colonna Campione.
- **Chip turni**: su mobile permettono di saltare a un turno; c'è anche il chip "Campione".
- **Nota finale**: "Il tabellone usa solo i risultati confermati: le proposte non approvate non fanno avanzare nessuno."

## 5. Responsive e accessibilità

- Desktop: albero completo e centrato, scroll orizzontale se non entra.
- Mobile (≤800px): scroll orizzontale con `-webkit-overflow-scrolling: touch`, chip dei turni, testo delle squadre a 11px e stato a 8px.
- `.bracket-scroll` è `tabindex="0"` e `role="region"` con etichetta; i chip hanno `aria-pressed`; le card hanno `aria-label`; i movimenti rispettano `prefers-reduced-motion` nello scroll dei turni.
- Il tabellone non usa zoom/pan: è consultabile con scroll e chip.

## 6. Test

`torneo-lab/tests/test_bracket_layout.py` esegue `tests/bracket_layout_probe.js` con Node (skip se Node non è disponibile) e verifica:

- 4 squadre: 2 turni, Semifinali/Finale, 2 partite iniziali;
- 8 squadre: 3 turni, Quarti/Semifinali/Finale, 4 partite iniziali;
- 16 squadre: 4 turni, Ottavi/Quarti/Semifinali/Finale, 8 partite iniziali;
- 6 e 5 squadre: BYE presenti, albero completo, 7 collegamenti;
- collegamenti coerenti con `source_home`/`source_away` e colonna Campione agganciata alla finale;
- punteggi e stato non spostano le card;
- ordine dell'array irrilevante.

Test statici in `test_static_ui.py` verificano script versionato, marker del modulo, `champion-card` e CSS.

## 7. Limiti noti

- Il tabellone assume un solo stage a eliminazione per torneo (il modello attuale). Più stage richiederebbero un selettore dedicato.
- Non ci sono test browser automatizzati (Playwright non disponibile): la geometria è testata, il rendering visivo resta da verificare a mano.
- Su schermi molto stretti il bracket resta a scorrimento orizzontale: è una scelta coerente con la struttura a turni.
- Il campione arriva da `champion_team_id`: se il backend non lo espone per la vista pubblica, la colonna mostra "Da decidere" e la UI non inventa nulla.
