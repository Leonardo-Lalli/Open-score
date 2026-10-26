# Sito di presentazione — Open Score

Questa cartella contiene **solo** il sito statico pubblico pubblicato con GitHub Pages. Non è una seconda applicazione e non contiene backend, database o API: la piattaforma operativa vive in `torneo-lab/` e va pubblicata separatamente.

- URL previsto: <https://leonardo-lalli.github.io/Open-score/>
- Repository: <https://github.com/Leonardo-Lalli/Open-score>
- Workflow: `.github/workflows/pages.yml`

## Struttura

```text
website/
├── index.html                 pagina unica di presentazione
├── 404.html                   pagina di errore statica
├── styles.css                 design system del sito, font inclusi
├── script.js                  menu mobile e anno nel footer
├── .nojekyll                  evita l'elaborazione Jekyll
├── assets/
│   ├── mark.svg               marchio Open Score
│   ├── fonts/                 DM Sans (OFL) + licenza
│   └── screenshots/           cartella pronta per le immagini reali
└── README.md
```

Nessun framework, nessun build step, nessuna CDN: si apre direttamente con un server statico.

## Pubblicazione su GitHub Pages

1. Unisci le modifiche su `main`.
2. Nel repository: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Il workflow `Open Score website` parte a ogni push su `main` (o manualmente da **Actions → Open Score website → Run workflow**).
4. Attendi la fine del job `deploy` e apri l'URL indicato nell'ambiente `github-pages`.

Il workflow carica la cartella `website/` come artifact, quindi tutto ciò che deve essere pubblico va messo qui dentro. Non pubblicare `torneo-lab/`, database, `.env` o screenshot con nomi reali.

Se il repository o il dominio cambiano, aggiorna `canonical`, `og:url` e i link GitHub in `index.html`, oltre al `<base href="/Open-score/">` in `404.html`.

## Anteprima locale

Dalla cartella `website/`:

```bash
python -m http.server 8080
```

Poi apri <http://localhost:8080>. In alternativa, apri `index.html` con un browser moderno: i percorsi sono relativi e funzionano anche senza server.

## Contenuti: regole di onestà

- **Disponibili**: solo funzionalità presenti nel codice attuale.
- **In sviluppo**: interfacce già pronte ma in attesa di API, integrazione o verifica. Non vanno presentate come complete.
- **Future**: prospettive da discutere con il professore, senza date promesse.
- **Demo**: il pulsante non esiste perché non esiste una demo pubblica. L'app è pensata per la LAN scolastica.
- **Licenza**: non è ancora assegnata; il footer dice «Licenza da definire». Non aggiungere «MIT», «Apache» o altre licenze senza una decisione degli autori.
- **Nomi**: usare solo i nomi già presenti nella repository (Leonardo Lalli e Maximiliam Cichello). Non inventare ruoli personali, contatti o account.
- **Privacy**: nessun nome reale di studente, nessun dato personale, nessun token.

## Tema chiaro e scuro

Il sito supporta tre scelte: **Chiaro**, **Scuro** e **Sistema**. Il selettore è nel header (`#theme-toggle` + `#theme-menu`) ed è utilizzabile anche su telefono.

- Preferenza salvata in `localStorage` con chiave `openScoreSiteTheme` (`light`, `dark` o `system`).
- Default: `system`, che segue `prefers-color-scheme` e si aggiorna se il dispositivo cambia tema.
- Lo script inline nel `<head>` applica il tema **prima** del foglio di stile per evitare il flash della palette sbagliata; imposta anche `color-scheme` e il colore di sfondo iniziale.
- I token vivono in `:root` (chiaro) e `[data-theme="dark"]` (scuro). Il tema scuro non è un'inversione: superfici, bordi, lime, verde e stati hanno valori propri.
- Senza JavaScript il sito segue comunque il tema di sistema tramite `@media (prefers-color-scheme: dark)`; il selettore viene nascosto con `<noscript>`.
- Il pulsante del tema è 44×44 px su mobile; le etichette e i controlli restano leggibili.
- I test calcolano il contrasto dei token principali e richiedono almeno 4.5:1 per il testo normale e 7:1 per il testo primario.

## Screenshot

La sezione `#screenshot` contiene tre segnaposto. Per inserire le immagini reali:

1. Salva i file in `assets/screenshots/` (vedi il README della cartella).
2. Sostituisci il `<div class="screenshot-frame">…</div>` corrispondente con:

```html
<img
  src="assets/screenshots/dashboard-prof.png"
  alt="Dashboard del professore con i tornei e le prossime partite"
  width="1600"
  height="900"
  loading="lazy"
/>
```

3. Mantieni la `<figcaption>` con titolo e descrizione.
4. Verifica che i dati mostrati siano di prova e che nomi e foto siano autorizzati.

## Verifica

Dalla cartella `torneo-lab/`:

```bash
python -m pytest -q tests/test_website.py
```

I test controllano sezioni e link, assenza di demo/licenze inventate, asset locali esistenti, font, workflow Pages, tema chiaro/scuro (selettore, persistenza, contrasto AA) e validità di base di CSS/JS.

## Design

Il sito riusa i token dell'app: sfondo `#f6f7f2`, inchiostro `#182923`, verde `#2d694d`, lime `#d6f473`, raggi generosi e DM Sans locale. Non introdurre una nuova identità visiva: il marchio è `assets/mark.svg`.
