FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TORNEO_DB_PATH=/app/torneo-lab/data/open_score.sqlite3

WORKDIR /app

COPY torneo-lab/requirements.txt torneo-lab/requirements.txt
RUN python -m pip install --no-cache-dir -r torneo-lab/requirements.txt

COPY torneo-lab torneo-lab

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"

CMD ["python", "-m", "uvicorn", "app:app", "--app-dir", "torneo-lab", "--host", "0.0.0.0", "--port", "8000"]
