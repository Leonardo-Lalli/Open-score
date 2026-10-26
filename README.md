# Open Score

**Il tuo campo di gioco.**

Open Score è una web app per organizzare i tornei di scienze motorie a scuola: calcio, basket, pallavolo, badminton, ping pong e biliardino, ognuno con le proprie varianti e regole. Funziona da desktop e da smartphone e gestisce partecipanti, gironi, eliminazione diretta, risultati, calendario e classifica.

Progetto di **Leonardo Lalli e Maximiliam Cichello**, da discutere con il professore di scienze motorie. Nome e scelte di prodotto restano provvisori.

## Avvio rapido

### Windows

Requisiti: Python 3.10 o successivo.

```powershell
git clone https://github.com/Leonardo-Lalli/Open-score.git
cd Open-score\torneo-lab
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Apri [http://127.0.0.1:8000](http://127.0.0.1:8000). Per fermare il server: **Ctrl+C**.

### Linux

Requisiti: Python 3.10 o successivo.

```bash
git clone https://github.com/Leonardo-Lalli/Open-score.git
cd Open-score/torneo-lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### Docker

Requisiti: Docker con il plugin Compose.

```bash
git clone https://github.com/Leonardo-Lalli/Open-score.git
cd Open-score
cp deploy/open-score.env.example deploy/open-score.env
# Modifica deploy/open-score.env: password del primo prof e IP della LAN.
docker compose up -d --build
```

Apri [http://127.0.0.1:8000](http://127.0.0.1:8000). I dati restano in `torneo-lab/data/`; per fermare il servizio usa `docker compose down`.

Al primo avvio serve un account docente: imposta `TORNEO_ADMIN_EMAIL` e `TORNEO_ADMIN_PASSWORD` in `deploy/open-score.env` (oppure crea un docente con `python manage.py create-teacher`). Chi non accede resta in sola lettura.

Funzioni complete, hosting sulla LAN e documentazione tecnica: [torneo-lab/README.md](torneo-lab/README.md).
