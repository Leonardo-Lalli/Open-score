<p align="center">
  <img src="torneo-lab/static/mark.svg" width="84" height="84" alt="Open Score" />
</p>

<h1 align="center">Open Score</h1>

<p align="center"><strong>Il tuo campo di gioco.</strong></p>

<p align="center">
  Web app per organizzare i tornei di scienze motorie a scuola: sei sport,
  sedici varianti, squadre, partite, risultati, classifiche, calendario e
  tabellone in un unico posto. Da desktop e da smartphone, pensata per la LAN
  della scuola.
</p>

<p align="center">
  <a href="https://github.com/Leonardo-Lalli/Open-score/actions/workflows/tests.yml">
    <img src="https://github.com/Leonardo-Lalli/Open-score/actions/workflows/tests.yml/badge.svg" alt="Stato dei test" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10 o successivo" />
  <img src="https://img.shields.io/badge/versione-0.8.0-informational" alt="Versione 0.8.0" />
  <img src="https://img.shields.io/badge/licenza-da%20definire-lightgrey" alt="Licenza da definire" />
</p>

<p align="center">
  <a href="https://leonardo-lalli.github.io/Open-score/">Sito del progetto</a> ·
  <a href="torneo-lab/README.md">Guida all'app</a> ·
  <a href="docs/">Documentazione</a> ·
  <a href="https://github.com/Leonardo-Lalli/Open-score/issues">Segnalazioni</a>
</p>

> Progetto scolastico di **Leonardo Lalli** e **Maximiliam Cichello**, da
> discutere con il professore di scienze motorie. Nome e scelte di prodotto
> restano provvisori.

## In breve

| | |
| --- | --- |
| **Cos'è** | Una web app per creare e gestire tornei sportivi scolastici. |
| **A chi serve** | Professori di scienze motorie, studenti e scuole. |
| **Dove gira** | Su un computer della LAN scolastica. Il sito GitHub Pages è solo una vetrina statica. |
| **Stato** | Versione applicativa 0.8.0; interfaccia e sito in evoluzione. |
| **Demo** | La demo pubblica non è ancora disponibile. |
| **Licenza** | Da definire. |

## Origine e obiettivi

Open Score nasce come progetto scolastico per il professore di scienze motorie.
L'obiettivo è togliere dall'organizzazione quotidiana il peso di fogli di
calcolo, regolamenti ricordati a memoria e classifiche aggiornate a mano.

Il progetto punta a:

- raccogliere in un unico posto sport, varianti, squadre, studenti, partite,
  risultati e classifiche;
- rendere esplicite le regole della variante scelta, invece di lasciarle
  implicite;
- dare agli studenti una vista chiara in sola lettura, senza comandi di
  modifica;
- mantenere i dati a scuola, su un'installazione locale con account docenti
  separati;
- restare semplice da usare da telefono e da computer.

Non è un servizio cloud e non è pensato per Internet: la piattaforma operativa
vive sulla LAN della scuola. Il sito pubblico su GitHub Pages presenta il
progetto e non contiene backend, database o API.

## Funzionalità

### Disponibili oggi

| Area | Cosa c'è |
| --- | --- |
| **Sport e regole** | Calcio, Basket, Pallavolo, Badminton, Ping pong e Biliardino con 16 varianti standard. Ogni variante porta con sé durata, composizione, punteggio e regolamento. |
| **Tornei** | Wizard di creazione, girone unico anche con numero dispari, andata/ritorno, eliminazione diretta da 2 a 32, gironi uguali con fase finale. BYE e qualificazioni calcolati dal motore. |
| **Persone** | Squadre e partecipanti individuali, rose con limiti della variante, numero di maglia, ricerca, aggiunta e rimozione degli studenti. |
| **Risultati** | Punteggi numerici o set per set, correzioni con controllo versione, invalidazione controllata degli incontri dipendenti, criteri a parità e classifica. |
| **Tabellone** | Collegamenti reali tra gli incontri, BYE, risultati ufficiali, colonna Campione e navigazione per turni su telefono. |
| **Calendario** | Partite per giorno, filtri per torneo, squadra, giorno, campo e stato. Programmazione manuale di data, ora, campo e durata, con anteprima dei conflitti visibili. |
| **Ruoli e sicurezza** | Ingresso come prof o studente, account docenti separati, isolamento dei tornei per proprietario e scritture bloccate lato API per gli studenti. |
| **Condivisione** | Link spettatore in sola lettura con aggiornamento automatico, QR generato nel browser, stampa e infografica esportabile in SVG o PNG. |
| **Statistiche** | KPI del torneo, podio/classifica, qualificati, campione e QR. I file SVG e PNG sono reali; il PDF si ottiene dalla stampa del browser. |
| **Dati e deploy** | SQLite persistente con schema versionato, nessun dato dimostrativo preinstallato, backup, avvio in LAN, systemd/Windows Task Scheduler e Docker. |
| **Mobile** | Interfaccia responsive, safe area, drawer, modali full-screen e touch target da 44 px. La verifica sistematica su dispositivi reali è ancora in corso. |

### In sviluppo

Queste parti hanno già una base nell'interfaccia, ma aspettano un'integrazione
backend o una verifica sul campo. Non vanno considerate complete.

- **Proposte di risultato**: gli studenti potranno proporre un risultato; il
  professore approva, respinge o corregge. La scheda è pronta, manca l'API.
- **Campi come risorsa**: nome, sede, sport supportati e disponibilità. Oggi il
  campo è un testo; la schermata attende la persistenza lato server.
- **Calendario e conflitti lato server**: oggi il client aggrega i tornei
  leggibili e mostra un'anteprima dei conflitti; l'API dedicata porterà il
  calcolo definitivo.
- **Import massivo studenti**: anteprima da elenco o CSV già presente, ma il
  salvataggio è sequenziale; manca l'operazione atomica e l'import Excel.
- **Statistiche individuali**: marcatori e dettagli giocatore.
- **Persistenza del riordino squadre nel torneo già creato** con drag & drop:
  il wizard salva già l'ordine in `team_names`, mentre la tabella del torneo è
  un'anteprima locale in attesa dell'API dedicata.
- **Verifica su iPhone e Android reali** e test browser automatizzati.
- **Export PDF nativo** dell'infografica: oggi si usa la stampa del browser.

### Prospettive future

- Doppia eliminazione, formato Swiss e Cup & Consolation.
- Scheduler automatico con campi, arbitri e disponibilità.
- Forfait, ritiri, rigori e penalità.
- Più istituti, società sportive e hosting oltre la LAN, quando il progetto
  sarà pronto e i regolamenti condivisi.
- Nuovi sport e varianti quando il backend li esporrà nel catalogo.

## Screenshot

Al momento **non sono inclusi screenshot reali** in questa repository. Per non
mostrare immagini finte, la sezione del sito usa segnaposto dichiarati e la
cartella [`website/assets/screenshots/`](website/assets/screenshots/README.md)
è pronta per le immagini definitive.

| Anteprima | Contenuto previsto | Stato |
| --- | --- | --- |
| Dashboard del professore | Tornei, prossime partite e avanzamento | Da aggiungere |
| Tabellone | Quarti → semifinali → finale → campione, con BYE | Da aggiungere |
| Statistiche | KPI, podio, qualificati e infografica | Da aggiungere |

Quando saranno disponibili, gli screenshot useranno dati di prova e non
mostreranno nomi reali di studenti.

## Stack tecnologico

| Area | Tecnologia verificata |
| --- | --- |
| **Backend** | Python 3.10+, FastAPI 0.162.0, Uvicorn 0.54.0, Pydantic 2.14.1 |
| **Dati** | SQLite, schema versionato con migrazioni (ultima: `007_teachers.sql`) |
| **Autenticazione** | Password con PBKDF2-SHA256 (260.000 iterazioni), sessioni firmate HMAC-SHA256, ruoli prof/studente |
| **Frontend** | HTML, CSS e JavaScript vanilla; SPA senza build step; DM Sans locale (OFL); qrcode-generator 1.4.4 (MIT) |
| **Test e qualità** | pytest, httpx TestClient, ruff |
| **Deploy** | Uvicorn in LAN, systemd/Windows Task Scheduler, Docker Compose, backup |
| **CI/CD** | GitHub Actions per i test; GitHub Pages per il sito statico |

Nessun framework frontend, nessun bundler, nessuna CDN a runtime. Il QR e
l'infografica sono generati nel browser.

## Requisiti

- **Python 3.10 o successivo** (la CI copre 3.11 e 3.14; l'immagine Docker usa
  Python 3.12).
- Un browser moderno.
- **Docker con Compose** solo se si sceglie quella modalità.
- **Node.js** non serve per eseguire l'app: è usato solo da alcuni test
  opzionali di geometria del tabellone, validazione SVG e controllo del sito.
  Se manca, quei test vengono saltati.
- Per la LAN: indirizzo IP fisso o prenotato, porta `8000` accessibile nel
  firewall e host ammessi configurati.

## Setup e avvio

### Windows

```powershell
git clone https://github.com/Leonardo-Lalli/Open-score.git
cd Open-score\torneo-lab
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Apri <http://127.0.0.1:8000>. Per fermare il server: **Ctrl+C**.

### Linux e macOS

```bash
git clone https://github.com/Leonardo-Lalli/Open-score.git
cd Open-score/torneo-lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### Docker

```bash
git clone https://github.com/Leonardo-Lalli/Open-score.git
cd Open-score
cp deploy/open-score.env.example deploy/open-score.env
# Modifica deploy/open-score.env: password del primo prof e IP della LAN.
docker compose up -d --build
```

Il database resta in `torneo-lab/data/`. `docker compose down` ferma il servizio
senza cancellare i dati. Il file `deploy/open-score.env` contiene segreti ed è
ignorato da Git.

### Primo account docente

Il database parte vuoto. Il primo docente può essere creato in due modi
documentati:

- impostando `TORNEO_ADMIN_EMAIL` e `TORNEO_ADMIN_PASSWORD` prima dell'avvio;
- dalla cartella `torneo-lab`:

```bash
python manage.py create-teacher prof@scuola.it --name "Nome Cognome"
```

Chi non accede resta in sola lettura, come gli studenti. La guida completa per
LAN, firewall, avvio automatico, backup e ripristino è in
[`torneo-lab/README.md`](torneo-lab/README.md) e in
[`docs/DEPLOY.md`](docs/DEPLOY.md).

## Test

Dalla cartella `torneo-lab`:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m ruff check --select I,C4,UP,F .
```

Stato al 26 ottobre 2026: **236 test superati localmente**, con 1 warning noto
di Starlette/httpx nel TestClient. La CI esegue `pytest` su Python 3.11 e 3.14.
Il badge in alto riflette l'ultima esecuzione della CI, non un risultato
statico.

La suite copre API, motori dei tornei, avanzamenti, correzioni, autenticazione,
persistenza, backup, UI statica, geometria del tabellone, infografica SVG e
sito. Alcuni test usano Node.js e vengono saltati se non è disponibile. Il
report storico è in [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md); lo stato
corrente del lavoro frontend è nel
[registro Team B](docs/handoffs/TEAM_B_LOG.md).

## Struttura del progetto

```text
Open-score/
├── torneo-lab/            applicazione FastAPI, SPA, test e migrazioni
│   ├── static/            frontend vanilla: HTML, CSS, JS, font e QR
│   ├── tests/             pytest, test statici, geometria e infografica
│   ├── migrations/        schema SQLite versionato
│   ├── app.py             API, sicurezza, file statici
│   ├── services.py        operazioni sui tornei
│   ├── engine.py          algoritmi girone/knockout
│   ├── sport_rules.py     catalogo sport e varianti
│   ├── auth.py            account docenti e sessioni
│   └── db.py              connessione e inizializzazione SQLite
├── website/               sito statico per GitHub Pages
├── docs/                  documentazione tecnica, specifiche e handoff
├── deploy/                env di esempio, systemd, script Windows, backup
├── .github/workflows/     test e deploy GitHub Pages
├── Dockerfile
└── docker-compose.yml
```

| Percorso | Contenuto |
| --- | --- |
| `torneo-lab/README.md` | Guida completa all'app, LAN, account, backup e Docker |
| `torneo-lab/static/` | SPA unica, senza build step |
| `torneo-lab/migrations/` | Schema versionato, dalla 001 alla 007 |
| `website/` | Vetrina statica, tema chiaro/scuro e workflow Pages |
| `docs/` | Architettura, API, database, deploy, sicurezza, specifiche e design |
| `deploy/` | Configurazione LAN e script di manutenzione |

## Sito e documentazione

| Risorsa | Link |
| --- | --- |
| **Sito del progetto** | <https://leonardo-lalli.github.io/Open-score/> |
| Guida all'app | [`torneo-lab/README.md`](torneo-lab/README.md) |
| Architettura | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| API | [`docs/API.md`](docs/API.md) · `/docs` quando il server è avviato |
| Database | [`docs/DATABASE.md`](docs/DATABASE.md) |
| Deploy in LAN | [`docs/DEPLOY.md`](docs/DEPLOY.md) |
| Sicurezza | [`docs/SECURITY.md`](docs/SECURITY.md) |
| Matrice funzionale | [`docs/FEATURE_MATRIX.md`](docs/FEATURE_MATRIX.md) |
| Design system | [`docs/design-system.md`](docs/design-system.md) |
| Registro Team B | [`docs/handoffs/TEAM_B_LOG.md`](docs/handoffs/TEAM_B_LOG.md) |

Il sito è una vetrina statica: non contiene il backend e non chiama le API
dell'app. Per pubblicarlo o aggiornarlo, vedi
[`website/README.md`](website/README.md). Il workflow
`.github/workflows/pages.yml` pubblica la cartella `website/` su `main` dopo
l'attivazione di **Settings → Pages → Source: GitHub Actions**.

## Roadmap

| Stato | Contenuto |
| --- | --- |
| **Fatto** | Versione 0.8.0: catalogo sport, tornei, risultati, classifiche, tabellone, ruoli prof/studente, mobile, link spettatore, statistiche, sito pubblico. |
| **In corso** | API per proposte di risultato, campi, calendario aggregato; import massivo studenti; statistiche individuali; verifica su dispositivi reali. |
| **Prossimo** | Formati avanzati (doppia eliminazione, Swiss, Cup & Consolation) e scheduler automatico. |
| **Prospettiva** | Più scuole e società sportive, hosting oltre la LAN. |

Le date non sono promesse: il percorso dipende dal confronto con il professore e
dalla disponibilità dei due studenti. Dettagli in
[`docs/DEVELOPMENT_PLAN.md`](docs/DEVELOPMENT_PLAN.md) e
[`docs/FEATURE_MATRIX.md`](docs/FEATURE_MATRIX.md).

## Contributori

- **Leonardo Lalli**
- **Maximiliam Cichello**

Il progetto è realizzato da due studenti per il professore di scienze motorie.
Il lavoro è diviso in due aree che si incontrano nello stesso repository:
motore/API/dati e interfaccia/esperienza/sito. Revisioni, regole e prove restano
condivise.

Non sono pubblicati contatti personali non autorizzati. Per segnalazioni o
domande usare le [issue del repository](https://github.com/Leonardo-Lalli/Open-score/issues).

## Licenza

**Licenza da definire.** Il repository è pubblico, ma non è ancora stata
assegnata una licenza di riuso. La scelta spetta agli autori; fino a quel
momento non presumere diritti di utilizzo, modifica o ridistribuzione oltre a
quelli previsti dalla legge.

## Nota sullo stato

La piattaforma operativa è pensata per la **LAN scolastica** e non è esposta
pubblicamente. Il sito GitHub Pages è una presentazione statica e non contiene
dati, account o API. La demo pubblica non è disponibile.

Alcune funzioni hanno già l'interfaccia ma attendono le API del backend: sono
elencate in [In sviluppo](#in-sviluppo) e non vanno considerate complete. Nome e
scelte di prodotto restano provvisori.
