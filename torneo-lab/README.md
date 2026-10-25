# Avvio della demo Open Score

Questa è la cartella dell'applicazione, derivata dallo starter TorneoLab. Il nome di prodotto è ancora provvisorio.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Apri [http://127.0.0.1:8000](http://127.0.0.1:8000). I quattro tornei dimostrativi sono già pronti al primo avvio. Per entrare come prof serve un account: imposta `TORNEO_ADMIN_EMAIL`/`TORNEO_ADMIN_PASSWORD` oppure crea un docente con `python manage.py create-teacher email@scuola.it`. I dati si conservano in `data/open_score.sqlite3`, escluso da Git.

Se l'attivazione è bloccata, usa `.venv\Scripts\python.exe` al posto di `python`, senza attivare l'ambiente. Per i test: `python -m pip install -r requirements-dev.txt`, poi `python -m pytest -q`.

Istruzioni complete, presentazione e limiti: [README principale](../README.md). Architettura, API e verifiche: [docs](../docs/ARCHITECTURE.md).

**Prof e studenti:** all'ingresso si sceglie **Sono un prof** (login email/password) o **Sono uno studente** (sola lettura). Ogni docente gestisce solo i propri tornei. I link spettatore mostrano i dati dello stesso server locale; non esiste ancora un servizio online o una sincronizzazione tra collaboratori.
