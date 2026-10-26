# Backend: avvio, backup e futura pubblicazione

26 ottobre 2026. Nessun deploy, modifica DNS, push o acquisto effettuato.
Il servizio del professore su Aruba non è stato identificato. Prima di scegliere
un ambiente chiedere il nome esatto del prodotto acquistato, accesso a processi
persistenti Python/ASGI, disco persistente, backup e responsabilità operative.

## Prova locale

Dalla cartella `torneo-lab`, usare l'ambiente esistente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Modalità predefinita `demo`: la UI esistente funziona come prima, per i tornei
dimostrativi/non assegnati. Le nuove API sono in `/docs` e `/openapi.json`.
Nessuna UI account/studenti/inviti è stata aggiunta: serve l'integrazione Team B.
Su Linux usare `.venv/bin/python`; Python minimo resta 3.10 per l'applicazione,
CI su 3.11 e 3.14. Installare `tzdata` dalla requirements anche su Windows.

Creare un professore locale, senza password nella riga di comando:

```powershell
.\.venv\Scripts\python.exe manage.py create-teacher --email docente@example.test --display-name Docente --organization "Contesto sintetico"
```

La password viene chiesta due volte con input protetto, 12–128 caratteri.
Il comando stampa l'ID. Per un altro professore nello stesso contesto usare
`--organization-id ID` al posto di `--organization`. Questi sono esempi sintetici,
non account o credenziali preinstallati.

L'email non viene verificata automaticamente: un account autenticato non prova
da solo un'identità scolastica. Il professore deve associare gli account corretti
o usare inviti con approvazione; questa è la modalità predefinita degli inviti.

Per le API in Swagger: GET `/api/v1/auth/csrf`, copiare csrf_token; POST login
con credenziali e header X-CSRF-Token; poi copiare il **nuovo** token di risposta
nelle altre scritture. Il browser conserva il cookie HttpOnly. È possibile
registrare studenti da register, ma nessuno può registrarsi come professore.
Non inserire password in URL, script versionati o comandi shell salvati.

## Conservazione e migrazioni

Il DB rimane SQLite: default `data/open_score.sqlite3`, override `TORNEO_DB_PATH`.
Schema corrente **4**, migrazioni SQL 001–004. Prima di aggiornare uno schema
esistente il programma crea una copia SQLite consistente accanto all'originale:
`open_score.pre-v4-TIMESTAMP.sqlite3`. Conservare anche un backup fuori dal server.
Nuovo schema su DB vuoto non richiede backup. DB legacy senza versione non vuoto
e DB più recente del codice vengono rifiutati, senza cancellazione.

Le migrazioni sono additive: nessun torneo/risultato viene assegnato al primo
account. Per un torneo precedente serve una scelta esplicita, dopo il backup:

```powershell
.\.venv\Scripts\python.exe manage.py claim --tournament 1 --teacher 1 --variant-id football-5
```

Preserva ID, risultati e punteggi classifica; valida gli score rispetto al preset.
Nessuna reinterpretazione di incontri numerici come set. Risultati precedenti
restano con provenienza legacy, approvatore e timestamp di approvazione null.
Dopo l'assegnazione le API demo non espongono più quel torneo, e il professore
lo legge via V1. La vecchia UI non mostra tornei V1: passaggio da coordinare col Team B.
Per autorizzare un collaboratore già nello stesso contesto:

```powershell
.\.venv\Scripts\python.exe manage.py add-collaborator --tournament 1 --teacher 2
```

I comandi amministrativi presuppongono accesso locale autorizzato al database.
Eseguire `manage.py migrate` prima di avviare il servizio aggiornato, con un solo
processo e server fermo. L'avvio applica comunque le migrazioni mancanti, ma
la procedura operativa evita migrazioni simultanee di più processi.

## Backup e ripristino verificabili

Usare percorsi di destinazione nuovi: nessun comando sovrascrive il DB esistente.

```powershell
.\.venv\Scripts\python.exe manage.py backup --output data/backup-sintetico.sqlite3
.\.venv\Scripts\python.exe manage.py --db data/backup-sintetico.sqlite3 restore --output data/ripristino-sintetico.sqlite3
```

Backup usa l'API SQLite, non la copia a caldo del file: include il contenuto
coerente anche se si usa WAL in futuro. Sorgente aperta in sola lettura, quick_check
e foreign_key_check su sorgente e destinazione. La suite riapre un'app sulla
copia ripristinata e verifica risultati e permessi. Il comando restore crea una
nuova copia; per attivarla arrestare il server, impostare TORNEO_DB_PATH su quel
file, verificare schema e health, poi riavviare. Non sovrascrivere a caldo.

Pianificazione proposta da concordare: backup giornaliero e prima di ogni
migrazione, una copia separata cifrata, retention limitata concordata con scuola.
Provare periodicamente il ripristino in ambiente isolato; registrare data, esito,
conteggi, hash del backup e tempo necessario. I backup contengono dati privati:
non versionarli, non servirli dal web e limitarne i permessi di filesystem.

## Modalità servizio e configurazione

```powershell
$env:TORNEO_MODE = 'service'
$env:TORNEO_DB_PATH = 'C:\percorso-persistente\open_score.sqlite3'
$env:TORNEO_PUBLIC_ORIGIN = 'https://tornei.example.test'
$env:TORNEO_ALLOWED_HOSTS = 'tornei.example.test'
$env:TORNEO_ALLOW_REGISTRATION = 'true'
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Esempio di configurazione, non un ambiente pubblicato. In service l'avvio fallisce
senza origin HTTPS e host coerenti espliciti; niente wildcard. Cookie Secure,
Origin e CSRF controllati; API demo escluse e nessun esempio creato automaticamente.
TORNEO_ALLOW_REGISTRATION false disabilita la registrazione pubblica degli studenti.
La proprietà mode non è cambiabile via richiesta HTTP.

TLS termina su un reverse proxy o sul servizio di hosting. Esporre solo HTTPS,
inoltrare Host correttamente, limitare gli header proxy fidati agli indirizzi
del proxy reale; non accettare X-Forwarded-* da Internet. Nessuna CORS generica.
Il frontend V1 va sullo stesso origin o dietro un proxy coordinato con Team B.
La UI legacy non è ancora un client multiutente utilizzabile in service.

## Scelta dell'ambiente

| Ambiente candidato | Valutazione per questo codice | Verifica prima dell'acquisto |
| --- | --- | --- |
| PC locale, solo loopback | Demo e prova sintetica | Backup del file locale, niente accesso pubblico anonimo |
| VPS/VM Linux con ASGI persistente | Candidato semplice, SQLite su disco locale persistente, un'istanza | Gestione patch, TLS, firewall, backup e monitoraggio a carico del gestore |
| Hosting applicativo gestito | Candidato se supporta Python/ASGI e volume persistente | Evitare filesystem effimero, conoscere restart, quote e backup |
| Hosting Aruba condiviso | Compatibilità ASGI non dimostrata | Supporto Python CGI non implica Uvicorn persistente o gestione processi |
| GitHub Pages | Solo sito/frontend statico | Non esegue FastAPI o SQLite server-side |

Aruba distingue servizi e pacchetti; la documentazione Linux cita Python in
`cgi-bin`, che **non prova** la compatibilità con il nostro processo ASGI.
Questa è un'inferenza architetturale, non una verifica del contratto del professore.
Fonti ufficiali consultate: [linguaggi Linux Aruba](https://guide.aruba.it/faq/hosting-e-domini/linguaggi-e-spazio-web-linux),
[servizi hosting e domini](https://guide.aruba.it/hosting-e-domini/gestione-domini/acquisto-e-rinnovo/acquisto-registrazione/hosting-domini-caratteristiche-e-utilizzo),
[GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

Nessun preventivo scelto. Confrontare canone e rinnovo, disco persistente, backup,
traffico, TLS, assistenza e tempo di amministrazione; non assumere che un dominio
includa un VPS. Sottodomini e DNS restano da concordare. I concetti operativi sono
coerenti con [deployment FastAPI](https://fastapi.tiangolo.com/deployment/concepts/)
e [HTTPS FastAPI](https://fastapi.tiangolo.com/deployment/https/).

## Database di produzione e limiti

SQLite è mantenuto, adatto alla prima istanza con carico contenuto. Scritture
serializzate, timeout 10 secondi; niente repliche del file su filesystem di rete,
container multipli con copie diverse o bilanciamento su database indipendenti.
Monitorare lock/latency e spazio disco prima di aumentare le istanze.

PostgreSQL non è ancora supportato: servizi e migrazioni usano sqlite3, placeholder
`?`, PRAGMA e AUTOINCREMENT. Occorrono adapter/migrazioni dedicate, import con
conservazione ID e storia, verifica FK/unicità/JSON, test di rollback/concorrenza,
backup e confronto dei conteggi. Non basta impostare una connection string.

## Rilascio, monitoraggio e rollback

Prima di un deploy autorizzato: revisione Team B, test/contratto sincronizzato,
UI V1 integrata, backup verificato e prova in staging. Usare versione/commit
identificabile, dipendenze runtime fissate, utente sistema senza privilegi,
directory dati fuori dal document root e processo supervisionato con riavvio.

Health: GET `/api/health`, versione 0.3.0/mode service. Affiancare controllo
read-only del DB e verifica backup, non dedurre l'integrità dei dati dal solo
health HTTP. Monitorare 5xx, 401/429 anomali, tempi, lock SQLite, spazio disco,
riavvii e scadenza TLS. Limitare access log e retention; niente body contenenti
password, token o dati studenti. URL invito usa frammento proprio per non passare
il token negli access log. L'audit applicativo registra autore e operazioni importanti.

Rollback: arrestare il processo; conservare sia DB attuale sia backup precedente;
se lo schema resta compatibile tornare al codice precedente. Un codice schema 2
non può aprire schema 4: ripristinare il relativo backup in un **nuovo percorso**,
selezionarlo con TORNEO_DB_PATH e accettare esplicitamente le scritture successive
al backup che andrebbero perse. Nessuna down-migration distruttiva automatica.

Privacy: usare alias minimi; consentire accesso solo a professore e partecipanti
autorizzati; pubblicare solo dati selezionati, senza rose o email. Prima di usare
dati reali concordare con scuola gestione account, conservazione/cancellazione,
pubblicazione e gestione degli incidenti. Il recupero email automatico e una
valutazione operativa indipendente della sicurezza restano da completare.
Scelta hashing documentata in [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).
