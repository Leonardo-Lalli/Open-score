# Mettere Open Score sulla LAN della scuola

Questa guida descrive un'installazione reale su un solo computer della scuola,
raggiungibile dagli altri dispositivi della stessa rete. Non è una guida per
pubblicare l'app su Internet.

Un solo processo `uvicorn` gestisce il database SQLite. Non usare più worker
(`--workers` maggiore di 1) con questo database: le scritture sono già
serializzate da `BEGIN IMMEDIATE` e più processi non porterebbero vantaggi.

## 1. Prerequisiti

- Windows 10/11 o una distribuzione Linux con systemd.
- Python 3.10 o successivo.
- Un indirizzo IP fisso per il computer server (prenotazione DHCP nel router).
- Accesso amministratore al computer, solo per aprire la porta e installare
  l'attività pianificata o il servizio.
- La repository del progetto copiata sul computer, per esempio in
  `C:\OpenScore` (Windows) o `/opt/open-score` (Linux).

Sul server:

```powershell
cd C:\OpenScore\torneo-lab
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Su Linux:

```bash
cd /opt/open-score/torneo-lab
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## 2. Configurazione

Copiare `deploy/open-score.env.example` in `deploy/open-score.env` e compilare
almeno l'account bootstrap del primo docente:

```powershell
Copy-Item C:\OpenScore\deploy\open-score.env.example C:\OpenScore\deploy\open-score.env
notepad C:\OpenScore\deploy\open-score.env
```

| Variabile | Effetto |
| --- | --- |
| `TORNEO_ADMIN_EMAIL` | Email del primo docente, creata al primo avvio se non esiste. Predefinita `admin@open-score.local` se si imposta solo la password. |
| `TORNEO_ADMIN_PASSWORD` | Password del primo docente. Almeno 8 caratteri. Gli altri docenti si creano con `manage.py`. |
| `TORNEO_ALLOWED_HOSTS` | Elenco separato da virgole di IP e nomi con cui si raggiunge il server, per esempio `192.168.1.50,open-score.local`. `127.0.0.1`, `localhost` e `testserver` sono sempre ammessi. Se l'indirizzo non è in elenco il server risponde 400. |
| `TORNEO_SECRET` | Segreto di firma dei cookie. Se assente viene creato `torneo-lab/data/session.secret` al primo avvio. |
| `TORNEO_SESSION_HOURS` | Durata della sessione in ore. Predefinito `12`. |
| `TORNEO_COOKIE_SECURE` | `1` solo dietro HTTPS: aggiunge `Secure` al cookie e abilita HSTS. |
| `TORNEO_DB_PATH` | Percorso del database. Predefinito `torneo-lab/data/open_score.sqlite3`. |

Il file `open-score.env` contiene segreti: non va versionato né condiviso. La
cartella `torneo-lab/data/` e `torneo-lab/backup/` sono escluse da Git.

### Trovare l'indirizzo IP

Windows:

```powershell
Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -ne 'WellKnown' } |
  Select-Object IPAddress, InterfaceAlias
```

Linux: `ip -4 addr show scope global`.

Aggiungere quell'indirizzo (e il nome del computer, se usato) a
`TORNEO_ALLOWED_HOSTS`. Il nome del computer si trova con `hostname`.

## 3. Aprire la porta nel firewall

Windows, PowerShell come amministratore:

```powershell
New-NetFirewallRule -DisplayName "Open Score" -Direction Inbound `
  -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private
```

Linux con `ufw`: `sudo ufw allow 8000/tcp`. Aprire la porta solo sulla rete
interna, non su quella ospiti o su Internet.

## 4. Primo avvio manuale

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File C:\OpenScore\deploy\start-open-score.ps1
```

Linux (in primo piano, per prova):

```bash
cd /opt/open-score/torneo-lab
set -a; . /etc/open-score/open-score.env; set +a
.venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1
```

Dal computer server aprire `http://127.0.0.1:8000`, da un altro dispositivo
della LAN `http://192.168.1.50:8000` (con l'IP reale). Verificare:

1. Compare il gate **Sono un prof** / **Sono uno studente**.
2. **Sono uno studente** apre la dashboard in sola lettura: **Nuovo torneo** ed
   eventuali comandi di modifica sono nascosti.
3. **Sono un prof** apre il login email/password; dopo l'accesso compaiono il
   nome del docente, **Esci** e **Nuovo torneo**, ma solo i propri tornei sono
   modificabili.
4. Un altro dispositivo vede il torneo e il link **Condividi** in sola lettura.

Per creare altri docenti, dalla cartella `torneo-lab`:

```powershell
.\.venv\Scripts\python.exe manage.py create-teacher altro.prof@scuola.it --name "Nome Cognome"
.\.venv\Scripts\python.exe manage.py list-teachers
```

Se l'app risponde 400 `Invalid host header`, l'indirizzo usato non è in
`TORNEO_ALLOWED_HOSTS`. Se risponde 401 su una scrittura, la sessione è scaduta:
accedere di nuovo.

## 5. Avvio automatico

### Windows: attività pianificata (consigliato)

PowerShell come amministratore:

```powershell
powershell -ExecutionPolicy Bypass -File C:\OpenScore\deploy\install-windows-task.ps1
```

Lo script registra due attività con account `SYSTEM`:

- **Open Score**: avvio del server all'accensione del computer.
- **Open Score backup**: backup giornaliero alle 18:30 (modificabile con
  `-BackupTime 19:00`).

Comandi di controllo:

```powershell
Get-ScheduledTask -TaskName 'Open Score' | Get-ScheduledTaskInfo
Start-ScheduledTask -TaskName 'Open Score'
Stop-ScheduledTask -TaskName 'Open Score'
powershell -ExecutionPolicy Bypass -File C:\OpenScore\deploy\install-windows-task.ps1 -Remove
```

L'attività non mostra una finestra: per vedere il log usare il Visualizzatore
eventi (Registro attività pianificate) o avviare manualmente lo script.

### Windows: servizio con NSSM (alternativa)

Se serve un vero servizio Windows, installare [NSSM](https://nssm.cc/) e
puntarlo a `C:\OpenScore\torneo-lab\.venv\Scripts\python.exe` con argomenti
`-m uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1`, directory
`C:\OpenScore\torneo-lab`, e le variabili di `open-score.env` impostate
nell'ambiente del servizio. Non usare NSSM e l'attività pianificata insieme.

### Linux: systemd

```bash
sudo useradd --system --home /opt/open-score --shell /usr/sbin/nologin openscore
sudo install -d -o openscore -g openscore /opt/open-score/torneo-lab/data /opt/open-score/torneo-lab/backup
sudo chown -R openscore:openscore /opt/open-score/torneo-lab/data /opt/open-score/torneo-lab/backup
sudo mkdir -p /etc/open-score
sudo install -m 600 deploy/open-score.env.example /etc/open-score/open-score.env
sudo nano /etc/open-score/open-score.env
sudo cp deploy/open-score.service /etc/systemd/system/open-score.service
sudo systemctl daemon-reload
sudo systemctl enable --now open-score
systemctl status open-score
```

Il file `open-score.service` presuppone l'installazione in `/opt/open-score`.
Se il percorso è diverso, aggiornare `WorkingDirectory`, `ExecStart` e
`ReadWritePaths`.

## 6. Backup

Il backup usa `VACUUM INTO`, quindi è consistente anche con il server in
esecuzione. Non copiare a caldo solo `open_score.sqlite3`: con WAL il file
principale può essere incompleto.

Manuale:

```powershell
powershell -ExecutionPolicy Bypass -File C:\OpenScore\deploy\backup-open-score.ps1
```

Linux:

```bash
cd /opt/open-score/torneo-lab
.venv/bin/python backup.py --keep 14
```

I file finiscono in `torneo-lab/backup/` con nome
`open_score-AAAAMMGG-HHMMSS-microsecondi.sqlite3`. `--keep` conserva i più
recenti; il valore predefinito è 14. Copiare periodicamente i backup su un
secondo disco o su una cartella di rete, altrimenti un guasto al computer
porta via anche le copie.

### Verificare un backup

```powershell
cd C:\OpenScore\torneo-lab
.venv\Scripts\python.exe -c "import sqlite3,sys; db=sqlite3.connect(sys.argv[1]); print(db.execute('PRAGMA integrity_check').fetchone()[0], db.execute('PRAGMA user_version').fetchone()[0], db.execute('SELECT count(*) FROM tournaments').fetchone()[0])" C:\OpenScore\torneo-lab\backup\open_score-....sqlite3
```

Deve stampare `ok`, la versione dello schema (6) e il numero di tornei
atteso.

### Ripristinare un backup

1. Fermare il server (`Stop-ScheduledTask` oppure `sudo systemctl stop open-score`).
2. Spostare il database attuale: `open_score.sqlite3` e gli eventuali
   `open_score.sqlite3-wal` e `open_score.sqlite3-shm` in una cartella di
   sicurezza.
3. Copiare il backup scelto come `torneo-lab/data/open_score.sqlite3`.
4. Riavviare il server e controllare dashboard, tornei e login.

Non ripristinare un database con una versione dello schema più recente del
programma installato: il server lo rifiuta. Aggiornare prima il codice.

## 7. Aggiornare l'applicazione

1. Eseguire un backup manuale.
2. Fermare il server.
3. Aggiornare il codice (`git pull` oppure sostituire i file).
4. Reinstallare le dipendenze se `requirements.txt` è cambiato.
5. Avviare i test: `.venv\Scripts\python.exe -m pytest -q` (serve
   `requirements-dev.txt`).
6. Riavviare il server. Le migrazioni mancanti vengono applicate all'avvio.

Se l'avvio segnala un database più recente del programma, il codice è vecchio:
non forzare la versione, aggiornare l'applicazione.

## 8. Log e diagnostica

- **Avvio manuale**: il log di `uvicorn` è la console.
- **Attività pianificata**: Visualizzatore eventi → Registro attività
  pianificate → `Open Score`; il backup scrive anche
  `torneo-lab/backup/backup.log`.
- **systemd**: `journalctl -u open-score -f`.
- **NSSM**: configurare un file di log nelle impostazioni del servizio.
- **Stato**: `GET /api/health` restituisce versione, modalità `school-lan` e
  `auth: teacher-login`.

## 9. Lista di controllo prima dell'uso

- [ ] `TORNEO_ADMIN_EMAIL` e `TORNEO_ADMIN_PASSWORD` impostati e diversi da quelli di esempio.
- [ ] Account docenti creati solo per le persone autorizzate, password non scritte nella repository.
- [ ] IP del server prenotato nel router e presente in `TORNEO_ALLOWED_HOSTS`.
- [ ] Porta 8000 aperta solo sul profilo di rete privato.
- [ ] Accesso verificato da un secondo dispositivo della LAN.
- [ ] Uno studente non vede i pulsanti di modifica e riceve 401 se tenta una scrittura.
- [ ] Un secondo docente non può modificare i tornei del primo (403).
- [ ] Backup manuale riuscito e integrità verificata.
- [ ] Backup giornaliero attivo e copia esterna configurata.
- [ ] `torneo-lab/data/`, `torneo-lab/backup/` e `open-score.env` fuori da Git.
- [ ] Riavvio del computer provato: il server torna disponibile da solo.

Per il modello di minacce e i limiti di questa configurazione vedere
[SECURITY.md](SECURITY.md).
