# Drag and drop per l'ordine delle squadre

> Documento del Team B. Descrive la vista tabellare, l'accessibilità e l'adapter di salvataggio in attesa dell'API del Team A.
> Base: `max-develop` · App 0.8.0.

## Cosa è implementato

Nella scheda **Partecipanti** di un torneo a squadre, per il docente proprietario, compare il pannello **Ordine delle squadre**:

- tabella con una riga per squadra: posizione, maniglia, nome, girone, rosa, comandi;
- trascinamento con mouse, dito o penna tramite **Pointer Events**;
- feedback visivo: riga trascinata (`.dragging`), destinazione (`.drag-target`), posizione aggiornata;
- riordino anche con **Sposta su / Sposta giù** e con la tastiera sull'handle (frecce, Home/End);
- annunci per screen reader tramite live region dedicata;
- messaggio di stato sotto la tabella.

**L'ordine è solo di visualizzazione.** Non modifica classifica, risultati, accoppiamenti o seeding. La tabella lo dichiara esplicitamente.

## Salvataggio e rollback

L'adapter è `teamOrderAdapter` in `static/app.js`.

- Oggi `ready: false`: l'ordine resta in **anteprima locale** e al reload torna quello del server.
- Contratto proposto al Team A:

```http
PATCH /api/tournaments/{id}/teams/order
{"team_ids": [3, 1, 2]}

200 {"ok": true, "team_ids": [3, 1, 2]}
```

- Quando l'endpoint sarà disponibile, impostare `ready: true`.
- In caso di rifiuto del backend, il frontend ricarica il torneo dal server e mostra l'errore; se anche il reload fallisce, ripristina l'ordine precedente catturato prima del trascinamento.
- Al reload la tabella mostra sempre l'ordine restituito dal server.

## Accessibilità

- Maniglia con `aria-label`, istruzioni collegate e `aria-keyshortcuts`.
- Frecce su/giù sull'handle e pulsanti visibili **Sposta su / Sposta giù**; Home/End portano agli estremi.
- Touch target ≥44px e `touch-action: none` solo sulla maniglia.
- Live region `#team-order-live` per annunciare posizione e risultato.
- La tabella è dentro `.table-wrap`, quindi scrollabile in orizzontale su mobile.

## Perché nessuna libreria

Il progetto è una SPA senza build step, con CSP `script-src 'self'`. Per riordinare al massimo 32 righe non serve una libreria esterna: Pointer Events nativi + gestione tastiera coprono mouse, touch e accessibilità senza dipendenze, senza peso aggiuntivo e senza rischi di manutenzione. La utility `enableReorder` è già usata anche dal wizard.

## Spostamento studenti

Non è implementato in questa iterazione. Servono API per archivio studenti, assegnazione e spostamento atomico tra squadre. Rimuovere e riaggiungere con due chiamate non è sicuro (perdita dello studente se la seconda fallisce). Dettagli in [`STUDENT_MANAGEMENT.md`](STUDENT_MANAGEMENT.md) e nel handoff (punto 10).

## Test

- Test statico in `tests/test_static_ui.py` per tabella, adapter, stato, live region e stili.
- `moveItem` già verificata in Node.
- Non è disponibile una prova browser automatizzata: verificare manualmente mouse, touch e tastiera.
