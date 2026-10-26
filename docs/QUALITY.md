# Regole di qualità — audit e guardie

> Audit del 26 ottobre 2026 sul branch `max-develop`. Suite: **252 test**.
> Questo documento elenca cosa è stato corretto, come viene impedita la
> regressione e quali limiti restano dichiarati.

## 1. Correzioni di questo passaggio

### CSS duplicato eliminato

`torneo-lab/static/styles.css` conteneva due design system completi: la shell
attuale e un blocco legacy di 1.512 righe (secondo `:root`, `.btn-primary`,
`.create-steps`, `.display-large`, pagine editoriali, vecchi form). Il blocco
legacy non era usato dalla SPA: l'unica regola ancora referenziata,
`.subsection-title`, è stata spostata nella sezione attiva. Il font DM Sans,
che il blocco legacy applicava al `body`, ora è nel `:root` attivo.

- Da **5.225 a 3.732 righe** (-29%).
- Un solo `:root`, un solo linguaggio visivo.
- Aggiunti i due wrapper che non avevano regole: `.calendar-main` e
  `.infographic-panel`.

### Un solo client HTTP

`app.js` contiene **una sola chiamata `fetch(`**, dentro `api()`. Gli adapter
di proposte, ordine squadre, inviti, campi e calendario usano
`apiWithMessages()`, che conserva i messaggi d'errore per stato senza
duplicare trasporto e parsing.

### Pulsanti e azioni

Tutte le azioni letterali (`data-action="..."` e `button(..., "azione")`)
hanno un handler nella mappa `actions`. Le azioni dinamiche (`calendar`,
`fields`, …) restano coperte dalla stessa mappa.

### Classifiche dal backend

Il frontend mostra `data.standings` e `g.standings` restituiti dal server. Non
esiste alcuna funzione `buildStandings`/`computeStandings` nel client.

### QR e link pubblico

L'URL è costruito da `location.origin + "/public/" + token`; il pulsante
«Condividi» compare solo a chi gestisce il torneo; senza token o senza SVG
compare un messaggio, non un link `/undefined`.

## 2. Checklist del prompt 26

### Cosa non deve esistere

| Regola | Stato | Guardia |
| --- | --- | --- |
| Due implementazioni dello stesso componente | Nessuna funzione duplicata; un solo client HTTP; un solo design system | `test_single_http_client`, `test_stylesheet_has_a_single_design_system` |
| CSS duplicato incontrollato | Blocco legacy rimosso; 3.732 righe | `test_stylesheet_has_a_single_design_system` (< 4.000 righe) |
| Mock spacciati per API reali | Adapter con `ready: false` e messaggi espliciti; nessun salvataggio simulato | `test_no_demo_dataset_or_private_metadata_in_the_shell` |
| Interfacce inutilizzabili | Ogni azione ha un handler; gli adapter bloccano il salvataggio | `test_every_literal_action_has_a_handler` |
| Bottoni senza funzione | Verificato su 40 azioni letterali | `test_every_literal_action_has_a_handler` |
| Sport solo di nome | 6 sport e 16 varianti nel DB; regole usate da rose, durata e regolamento | test backend `test_sports.py`, `test_players.py` |
| QR che non aprono URL validi | URL pubblico da token; gating docente; fallback esplicito | `test_share_link_uses_the_public_token...`, `test_static_ui.py` |
| Tabelloni scollegati dal backend | `source_home`/`source_away`, `winner_team_id`, `champion_team_id` | `test_bracket_layout.py`, `test_api.py` |
| Classifiche calcolate a caso | Solo dati del backend | `test_standings_are_provided_by_the_backend` |
| Dashboard con dati hardcoded | Contatori da `/tournaments`, dettagli e aggregazioni reali | `test_no_demo_dataset_or_private_metadata_in_the_shell` |
| Traduzioni incomplete | UI e sito in italiano; sito `lang="it"`; nessuna i18n promessa | `test_website.py::test_site_declares_italian` |
| Tema scuro con contrasto insufficiente | Tema del sito con token e contrasto AA calcolato | `test_website.py::test_theme_tokens_have_sufficient_contrast` |
| README con informazioni inventate | Link locali verificati, licenza «da definire», demo dichiarata assente | `test_website.py`, `test_site_readme_and_root_link` |
| Build di produzione non funzionante | Build `_site/` testata con config di progetto e dominio | `test_build_renders_the_site_without_placeholders` |
| Modifiche al backend fuori perimetro | In questo passaggio: nessuna. Le tre correzioni precedenti sono autorizzate e documentate nella sezione 8 dell'handoff | revisione manuale |

### Cosa deve esistere

| Regola | Come è soddisfatta |
| --- | --- |
| Componenti riutilizzabili | Helper `h()`, `icon()`, `button()`, `modal()`, `stat()`, `avatar()`, form e tabelle condivise |
| Stato coerente | Un solo `auth`, `list`, `data`, `sports`; aggiornamenti dopo ogni scrittura |
| Interfacce accessibili | Skip link, focus visibile, `aria-*`, `aria-live`, touch target 44px, input 16px |
| Responsive reale | Breakpoint 1150/1100/900/800/680/560/380, safe-area, drawer, tabelle scrollabili |
| Contratti rispettati | Adapter isolati con endpoint documentati; nessuna API inventata |
| Codice leggibile | Client unico, messaggi d'errore centralizzati, nessun blocco CSS morto |
| Test | 252 test, incluse 6 guardie di qualità |
| Design coerente | Token unici, DM Sans locale, stati con testo oltre al colore |
| Documentazione | `docs/design-system.md`, handoff e questo documento |
| Integrazione semplice | Adapter pronti da attivare (`ready`), docs/handoffs/FRONTEND_TO_BACKEND.md |

## 3. Limiti dichiarati

- **Nessun browser automatizzato**: la verifica è statica e via API. Il
  rendering reale va provato su iPhone e Android; dopo la rimozione del CSS
  legacy è consigliata una prova visiva di dashboard, torneo, calendario,
  catalogo e gate.
- **Adapter `ready: false`**: non sono API reali e non salvano nulla. Quando il
  Team A espone gli endpoint si imposta il flag e si integra il contratto.
- **Rose pubbliche**: decisione aperta, documentata nell'handoff.
- **Versioni asset**: il server invalida `app.js`/`styles.css` con `no-cache`;
  `?v=` si alza al rilascio, non a ogni modifica locale.

## 4. Come rieseguire

Dalla cartella `torneo-lab/`:

```bash
python -m pytest -q
python -m ruff check --select I,C4,UP,F,E9 .
node --check static/app.js
```

Solo le guardie di qualità:

```bash
python -m pytest -q tests/test_quality.py
```
