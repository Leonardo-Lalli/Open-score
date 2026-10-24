# Avvio della demo Open Score

Questa è la cartella dell'applicazione, derivata dallo starter TorneoLab. Il nome di prodotto è ancora provvisorio.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Apri [http://127.0.0.1:8000](http://127.0.0.1:8000). I quattro tornei dimostrativi sono già pronti al primo avvio. I dati si conservano in `data/open_score.sqlite3`, escluso da Git.

Se l'attivazione è bloccata, usa `.venv\Scripts\python.exe` al posto di `python`, senza attivare l'ambiente. Per i test: `python -m pip install -r requirements-dev.txt`, poi `python -m pytest -q`.

Istruzioni complete, presentazione e limiti: [README principale](../README.md). Architettura, API e verifiche: [docs](../docs/ARCHITECTURE.md).

**Demo locale senza account:** mantenere l'ascolto su `127.0.0.1`. I link spettatore mostrano i dati dello stesso server locale; non esiste ancora un servizio online o una sincronizzazione tra collaboratori.
