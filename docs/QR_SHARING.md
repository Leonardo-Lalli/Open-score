> Documento di consegna storico: le parti su adapter mancanti/ready:false, schema e ruoli descrivono la versione indicata. Per il comportamento integrato corrente usare [FINAL_AUDIT.md](FINAL_AUDIT.md), [ARCHITECTURE.md](ARCHITECTURE.md) e [TEAM_B_INTEGRATION_REPORT.md](TEAM_B_INTEGRATION_REPORT.md).

# QR e condivisione — Team B

> Proprietario: Team B (frontend/UX). Branch `max-develop`. Versione app 0.8.0.
> Registro cronologico: [handoffs/TEAM_B_LOG.md](handoffs/TEAM_B_LOG.md).
> Richieste backend: [handoffs/FRONTEND_TO_BACKEND.md](handoffs/FRONTEND_TO_BACKEND.md), punto 12.

## Perimetro

Questa parte è **solo frontend**: nessuna modifica a `app.py`, `services.py`, `schemas.py`, `db.py` o alle migrazioni. Il QR viene generato nel browser con `static/vendor/qrcode.js` (qrcode-generator 1.4.4, MIT, copia locale compatibile con la CSP `script-src 'self'`).

## 1. Modale di condivisione del torneo

Aperta dalla scheda di condivisione di un torneo (`actions.share` → `share()`).

Contenuti:

- QR SVG del link spettatore (`/public/{public_token}`);
- campo con il link e pulsante **Copia link**;
- **Scarica QR**: serializza l'SVG con `XMLSerializer`, crea un `Blob` `image/svg+xml` e lo scarica come `qr-{public_token}.svg`;
- **Stampa**: crea un foglio `#print-sheet` con nome torneo, QR e URL; `window.print()` stampa solo quel nodo grazie alle regole `@media print` e alla classe `body.printing`;
- **Condividi**: usa `navigator.share` se disponibile, altrimenti copia il link e lo segnala nel toast;
- nota esplicita su localhost: il QR contiene `location.origin`, quindi da `localhost` il telefono non lo raggiunge. Per la LAN usare l'IP del server.

Nessun download o stampa viene simulato: se il QR non è nell'HTML (libreria assente o errore), l'azione mostra un errore e suggerisce il link.

## 2. Pagina di accettazione invito

La pagina è client-only e si apre con:

- `/?invite=<token>` (forma consigliata per i QR);
- `#/join/<token>` (alias, utile se in futuro il backend serve un path dedicato).

All'avvio `init()` riconosce il token, nasconde la navigazione e mostra una vista focalizzata (`showInviteShell` + `openInvite` + `renderInvite`). Contenuti:

- nome del torneo e sport/variante (quando il catalogo è caricato);
- formato, numero di partecipanti e organizzatore **solo se il backend lo rende pubblico**;
- per gli inviti squadra: nome squadra, posti disponibili e se serve approvazione;
- stato dell'invito (attivo, scaduto, revocato, non valido, già iscritto, squadra completa, in attesa, confermato, respinto);
- azione disponibile, con nota chiara che l'adesione è confermata solo dopo la risposta del server.

### Stati e messaggi

`inviteStatusCopy` e `inviteMessage` mappano ogni stato su un testo esplicito; nessuno stato è rappresentato solo dal colore. In caso di rete assente si mostra "Riprova" (`invite-retry`).

### Login e ripresa del flusso

Se l'adesione richiede un account, la CTA è `invite-login`: salva il token in `pendingInviteToken`, apre il gate di login e, dopo `loginTeacher`, riapre la stessa pagina invito. Anche la scelta "Sono uno studente" riporta alla pagina invito.

### Anteprima quando l'API inviti non esiste

`inviteAdapter.ready` è `false`. In questo caso `resolve(token)` usa **solo** l'endpoint pubblico già esistente `GET /api/public/{token}` per mostrare i dati reali del torneo, e restituisce lo stato `unverified`. La UI:

- mostra il badge "Anteprima dell'invito";
- disabilita "Adesione non ancora disponibile";
- offre il link alla vista spettatore.

Nessun dato finto, nessun salvataggio locale, nessuna iscrizione simulata.

## 3. Contratto richiesto al Team A

Quando il backend sarà pronto basta impostare `inviteAdapter.ready = true`.

### `GET /api/invites/{token}`

```json
{
  "status": "active | expired | revoked | already-member | full | pending | accepted | rejected",
  "kind": "tournament | team",
  "tournament": {
    "name": "Coppa d'istituto",
    "sport": "Calcio",
    "variant": "calcio-a-5",
    "format": "groups",
    "participant_kind": "team"
  },
  "organizer": { "display_name": "Prof. Rossi" },
  "team": { "name": "5A" },
  "available_slots": 3,
  "requires_approval": true
}
```

- `organizer` va incluso solo se pubblicabile.
- Il token è opaco: non deve contenere email, password, cookie o token di sessione.
- `404` = invito inesistente/revocato, `410` = scaduto.

### `POST /api/invites/{token}/join`

- Autenticazione: sessione studente/docente secondo il modello del Team A.
- Risposta: `{ "status": "pending" | "accepted" | "already-member" | "full", "message": "..." }`.
- Errori: `401` accesso richiesto, `403` invito non tuo, `404` invito inesistente, `409` già iscritto/squadra completa, `410` scaduto.
- L'adesione con approvazione resta `pending` finché un docente non la accetta.

### Link server-side (opzionale)

Oggi `/?invite=<token>` funziona senza modifiche al backend. Se si preferisce un path pulito, il Team A può aggiungere `GET /join/{token}`, che deve restituire `static/index.html` come già fa `GET /public/{token}`. Il frontend riconosce anche `#/join/<token>`.

## 4. Sicurezza e privacy

- I QR contengono solo l'URL pubblico/invito, mai credenziali o token amministrativi.
- La pagina invito non legge `localStorage` per i token e non scrive dati dell'invito in locale.
- L'organizzatore è mostrato solo se il payload lo espone; nessun elenco di studenti altrui.
- Gli errori usano messaggi generici, senza dettagli interni.
- La vista resta in sola lettura: nessuna azione di gestione è disponibile.

## 5. Test

In `torneo-lab/tests/test_static_ui.py`:

- `test_share_modal_has_client_side_qr` — vendor, QR e messaggio localhost;
- `test_share_actions_and_invite_landing_are_prepared` — azioni `download-qr`/`print-qr`/`share-qr`, adapter inviti, selettori CSS e bilancio delle graffe;
- `test_invite_landing_only_uses_real_server_data` — fallback a `GET /api/public/{token}`, CTA disabilitata e nessuna persistenza locale.

## 6. Limiti noti

- Il QR della vista spettatore da `localhost` non è raggiungibile dal telefono: serve l'IP LAN.
- `navigator.share` richiede HTTPS o localhost; su HTTP in LAN il fallback copia il link.
- Stampa: alcuni browser mobili non supportano `window.print()`; in quel caso restano "Scarica QR" e "Copia link".
- Inviti e adesioni restano in attesa dell'API del Team A: la UI è pronta ma non simula nulla.
