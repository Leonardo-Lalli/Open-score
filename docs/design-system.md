# Design system — Open Score

> Documento del Team B. Riferimento per frontend e UX. Non introduce nuove API né modifica il backend.
> Base: `max-develop` @ `f0eedf9` · Versione app 0.8.0 · Ultimo aggiornamento: 26 ottobre 2026.

## 1. Principi

L'interfaccia deve trasmettere **chiarezza, affidabilità, semplicità, organizzazione, modernità e accessibilità**. È un prodotto scolastico, ma deve sembrare uno strumento pronto all'uso, non un prototipo.

Regole guida:

- una sola azione primaria per schermata;
- testi brevi, in italiano, con tono diretto;
- lo stato è sempre visibile (caricamento, vuoto, errore, sola lettura);
- nessuna informazione affidata solo al colore;
- nessuna identità visiva copiata da Score7 o altre piattaforme.

## 2. File e confini

| File | Ruolo |
| --- | --- |
| `torneo-lab/static/index.html` | Shell della SPA: gate, sidebar, topbar, `<main>`, `<dialog>`, toast |
| `torneo-lab/static/app.js` | Rendering, stato, routing hash, client HTTP |
| `torneo-lab/static/styles.css` | Design system e componenti |
| `torneo-lab/static/fonts/` | DM Sans locale (OFL), nessuna CDN |
| `torneo-lab/static/vendor/qrcode.js` | Encoder QR locale (qrcode-generator 1.4.4, MIT) |
| `torneo-lab/static/mark.svg` | Marchio |

`styles.css` contiene **due sezioni storiche**:

1. **righe ~35–2130** — shell e componenti attuali della SPA (fonte principale per il lavoro nuovo);
2. **righe ~2133–3799** — token e classi delle vecchie pagine di design (`.btn-primary`, `.stats-grid`, `.standings-table`, `.editorial-grid`, …). **Non è usata dalla SPA attuale** e non va estesa;
3. **righe ~3800–4217** — mobile hardening, gate e regole finali.

Regola: i nuovi componenti usano i token e le classi della sezione 1, oppure vengono aggiunti in coda prima del blocco mobile. Non introdurre un terzo `:root`.

## 3. Token

### 3.1 Colori attivi (sezione 1)

| Token | Valore | Uso |
| --- | --- | --- |
| `--bg` | `#f6f7f2` | Sfondo pagina |
| `--paper` | `#ffffff` | Card, pannelli, dialog |
| `--ink` | `#1c3028` | Testo principale, pulsante primario |
| `--muted` | `#738077` | Testo secondario |
| `--line` | `#e3e8df` | Bordi e divisori |
| `--lime` | `#d6f473` | Accento, card prof, CTA lime |
| `--dark` | `#182923` | Sidebar e superfici scure |
| `--green` | `#2d694d` | Accento verde |
| `--radius` | `17px` | Raggio di riferimento della shell |

Colori semantici aggiuntivi usati nei componenti:

- stati: `#5b7d32` (attivo), `#36644e` (concluso), `#987630` (bozza), `#5d6570` (archiviato);
- errore: `#ba1a1a`, sfondo `#ffdad6`, testo `#93000a`;
- pericolo: `#b14135` su `#fff3ee`.

### 3.2 Colori estesi (sezione 2, legacy)

La seconda sezione definisce una palette Material-like (`--primary`, `--secondary-container`, `--surface`, `--outline`, `--error`, …). **Non usarla per nuovi componenti della SPA**: serve solo alle vecchie pagine di design. Se un valore manca nella palette attiva, aggiungerlo alla sezione 1 con un nome semantico.

### 3.3 Tipografia

- Famiglia: **DM Sans**, locale, `font-display: swap`; fallback `"Segoe UI", Arial, sans-serif`.
- Pesi: 300, 400, 500, 600, 700.
- Scala legacy (sezione 2): display 32/24/20, headline 24/20/18, title 16/14/12, body 16/14/12, label 14/12/11.
- Nella shell attuale i testi usano valori puntuali: titoli 17–29px, testi 10–13px, etichette 8–10px, numero statistiche 29px.

**Gap noto:** molte etichette sono sotto i 12px. Vanno verificate su mobile e con ingrandimento del testo; per i nuovi componenti usare almeno 12px per il testo operativo e 16px per gli input su mobile.

### 3.4 Spaziature e raggi

- Spaziatura legacy: `4, 8, 12, 16, 24, 32px` (`--space-xs…2xl`).
- Nella shell attuale: padding tipici 17–28px, gap 8–25px.
- Raggi: 6–8px (controlli), 10–12px (card piccole), 14–18px (pannelli, card, dialog), 24px (gate), `999px` (pillole e chip).
- Ombre: leggere sulle card (`0 7px 20px`), marcate su dialog e gate (`0 30px 100px`).

### 3.5 Movimento

- Transizioni brevi (0.15s) su hover delle card.
- Focus visibile: `outline: 3px solid #77a82c; outline-offset: 4px`.
- Esiste `@media (prefers-reduced-motion: reduce)`; ogni nuova animazione deve rispettarlo.

## 4. Componenti attivi

Classi realmente usate da `app.js`; i nomi corrispondono al CSS.

### 4.1 Azioni

| Componente | Classi | Varianti / stati |
| --- | --- | --- |
| Pulsante | `.button` | `.primary`, `.lime`, `.ghost`, `.danger`, `.compact`, `:disabled` |
| Pulsante icona | `.icon-button` | usato per menu, chiusura modale |
| Azione testuale | `.text-button` | link-like dentro card e pannelli |
| Link pulsante | `.button` su `<a>` | condivisione/export |

Regole: una sola `.primary` per vista; `.danger` solo per azioni distruttive; testo al presente (“Crea”, “Archivia”, “Ripristina”).

### 4.2 Form

| Componente | Classi | Note |
| --- | --- | --- |
| Campo | `label > input / select / textarea` | label sempre visibile, non solo placeholder |
| Griglia form | `.form-grid`, `.full` | due colonne su desktop, una su mobile |
| Aiuto | `.field-help` | sotto il campo, 10px |
| Opzioni formato | `.format-options`, `.format-option`, `.format-fieldset` | selezione con `:has(input:checked)` |
| Errore modale | `.modal-error` | `role="alert"` |
| Ricerca/filtri | `.filters`, `.filter`, `.filter.active` | filtri dashboard |

Input su mobile: `font-size: 16px` per evitare lo zoom iOS; touch target ≥44px.

### 4.3 Superfici

| Componente | Classi | Uso |
| --- | --- | --- |
| Pannello | `.panel`, `.panel-label` | sezioni del dettaglio torneo |
| Card torneo | `.event-card`, `.event-card-top/footer`, `.event-format`, `.event-meta` | dashboard |
| Statistica | `.stat`, `.stat-top`, `.stat-number`, `.stat-foot`, `.stat-grid` | contatori |
| Card catalogo | `.catalog-card`, `.catalog-chips`, `.catalog-cta` | sport e varianti |
| Card squadra | `.team-summary`, `.roster`, `.roster-item` | scheda partecipante |
| Card partita | `.match-row`, `.match-round`, `.match-note`, `.result-inputs` | incontri |
| Card campione | `.champion-banner` | torneo concluso |

### 4.4 Navigazione

| Componente | Classi | Note |
| --- | --- | --- |
| Sidebar | `.sidebar`, `.brand`, `.workspace`, `.nav-item`, `.event-nav` | drawer su mobile |
| Topbar | `.topbar`, `.breadcrumb`, `.top-actions`, `.context-label` | sticky su mobile |
| Tab | `.tabs`, `.tab`, `.tab.active` | `role="tablist"`, `aria-selected` |
| Filtri | `.filters`, `.filter` | dashboard |
| Wizard | `.wizard-steps`, `.wizard-step`, `.wizard-step.active` | 3 passi |
| Passi torneo | `.steps`, `.step`, `.step.done` | panoramica |

### 4.5 Feedback e stati

| Componente | Classi | Note |
| --- | --- | --- |
| Badge stato | `.tag` + `.active`, `.completed`, `.draft`, `.archived` | colore + testo |
| Toast | `#toast`, `#toast.error` | `role="status"`, `aria-live="polite"` |
| Vuoto | `.empty`, `.empty h2`, `.empty .button` | sempre con azione successiva |
| Caricamento | `.loading`, `.spinner` | dentro `<main aria-busy>` |
| Errore pagina | `.error-page` | server irraggiungibile |
| Progresso | `.progress-track > span`, `.progress-copy` | con `role="progressbar"` |
| Avviso | `.note-banner` | informazione non bloccante |

### 4.6 Dialog e sovrapposizioni

- `<dialog id="modal">` nativo; apertura con `showModal()`, chiusura con `close()`.
- `.modal-header`, `.modal-body`, `.modal-footer`; scroll nel body.
- `dialog::backdrop` con blur; su mobile il dialog diventa full-screen.
- Focus: il dialog nativo gestisce il focus iniziale; verificare il ritorno del focus all’elemento che ha aperto.
- Gate iniziale: `.role-gate`, `.role-gate-panel`, `.role-choice` (`.role-teacher`, `.role-student`), `.role-login`, `.role-login-actions`, `.role-switch`.
- QR di condivisione: `.share-qr`; SVG generato nel browser da `static/vendor/qrcode.js`, con `title`/`description` accessibili.

### 4.7 Dati e rappresentazioni

| Componente | Classi | Note |
| --- | --- | --- |
| Tabella | `.table-wrap`, `.table-note` | scroll orizzontale su mobile |
| Elenco dettagli | `.details-list` | coppie dt/dd |
| Classifica | tabella dentro `.panel` | posizione, punti, differenza |
| Bracket | `.bracket-scroll`, `.bracket-tree`, `.round-title`, `.tree-help` | scroll orizzontale; su mobile `.bracket-mobile-nav`, `.bracket-rounds`, `.bracket-round-chip` | 
| Regolamento | `.regulation-copy`, `.rule-list`, `.rule-pills`, `.rules-preview` | testo + pillole |
| Punteggio a set | `.set-inputs`, `.set-row` | input per set |
| Diario | `.timeline-item` | storico modifiche |
| Icone | `.icon` | SVG inline, 20px, stroke 1.7, `aria-hidden` |

## 5. Responsive

Breakpoint presenti:

| Larghezza | Comportamento |
| --- | --- |
| `min-width: 1550px` | griglie più ampie |
| `max-width: 1150px` | riduzione colonne |
| `max-width: 1100px` / `900px` | layout torneo e catalogo |
| `max-width: 800px` | **mobile shell**: drawer, topbar sticky, modali full-screen, touch 44px, input 16px |
| `max-width: 768px` | form e pagine legacy |
| `max-width: 680px` | catalogo |
| `max-width: 560px` | griglie a una colonna |
| `max-width: 380px` | azioni login in colonna |

Regole mobile già attive:

- `100dvh`, `env(safe-area-inset-*)`, `viewport-fit=cover`;
- drawer con scrim, blocco scroll (`menu-open`), chiusura con tap/Escape/resize;
- tabelle e bracket con scroll orizzontale e `overscroll-behavior: contain`;
- `touch-action: manipulation`, `-webkit-tap-highlight-color: transparent`.

**Da migliorare:** la dashboard su telefono non deve solo restringersi. Le card e le statistiche vanno ripensate (es. 2 colonne → 1, gerarchia diversa, azioni in basso).

### Dashboard e bracket su telefono (implementato)

- hero a una colonna sotto 560px, artwork decorativo nascosto, CTA a larghezza piena;
- griglia tornei a una colonna sotto 560px e card con padding ridotto;
- statistiche 2×2 fino a 380px, poi una colonna;
- intestazioni di sezione con filtri a capo e filtrabili in orizzontale;
- bracket con hint “scorri o scegli un turno” e chip dei turni che portano il tabellone alla colonna scelta;
- `.bracket-scroll` focusabile da tastiera (`tabindex="0"`, `role="region"`).

**Da migliorare ancora:** valutare uno zoom/pan esplicito e un drag & drop per il seeding.

## 6. Accessibilità

Già presente:

- skip-link verso `#content`;
- `:focus-visible` su pulsanti e link;
- gate, tab e dialog con `aria-*` e ruoli;
- toast con `role="status"` e `aria-live="polite"`;
- `aria-busy` su `<main>`;
- touch target ≥44px e input 16px su mobile.

Da verificare o completare:

- contrasto di `--muted` e delle etichette 8–10px (puntare a WCAG AA, 4.5:1 per il testo normale);
- associazione esplicita errore-campo (`aria-describedby`, `aria-invalid`) nei form;
- gestione del focus nel passaggio gate → app e dialog → pagina;
- `prefers-reduced-motion` per ogni nuova transizione;
- test da tastiera dell’intero wizard e del tabellone.

## 7. Regole per nuovi componenti

1. Usa i token della sezione 1; non aggiungere un nuovo `:root`.
2. Usa `<button type="button">` per azioni non di submit; `<a>` solo per navigazione.
3. Etichette sempre visibili; placeholder solo come esempio.
4. Ogni stato deve avere un testo, non solo un colore.
5. Usa `h()` per interpolare dati utente nell’HTML.
6. Non introdurre librerie UI o framework CSS: il progetto resta senza build step.
7. Aggiungi le regole prima del blocco mobile; aggiorna i breakpoint solo se necessario.
8. Alza `?v=` in `index.html` quando cambi `app.js` o `styles.css`.
9. Le librerie di utilità vanno in `static/vendor/` con licenza e provenienza documentate; nessuna CDN a runtime.
10. Aggiungi o aggiorna un test in `torneo-lab/tests/test_static_ui.py` per le regole strutturali (gate, cache, classi chiave, assenza di contenuti demo).
11. Verifica con `node --check static/app.js` e con la suite `pytest`.

## 8. Debito tecnico noto

- Due `:root` e due linguaggi visivi nello stesso file; consolidamento consigliato in un refactor dedicato.
- Sezione legacy non usata dalla SPA: candidata alla rimozione dopo verifica dei redirect e delle pagine statiche.
- Molte dimensioni tipografiche piccole (8–10px) e valori hardcoded fuori dai token di spaziatura.
- Nessun dark mode / `prefers-color-scheme`.
- Bracket senza zoom/pan e senza drag & drop (previsto nel piano Team B); il navigatore dei turni su mobile è già presente.
- Statistiche individuali non ancora presenti; il QR spettatore è implementato lato client.
