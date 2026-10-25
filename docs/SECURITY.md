# Sicurezza e limiti della LAN scolastica

Open Score è pensato per un computer della scuola raggiungibile dalla rete
interna. È un servizio multiutente per i docenti, con consultazione pubblica
in sola lettura, e non è destinato a Internet. Questo documento descrive cosa
protegge, cosa non protegge e come gestire le credenziali.

## Modello di minaccia

**Attori considerati**

- Studenti e spettatori con un browser sulla stessa LAN: possono leggere i
  tornei e provare a modificare risultati o impostazioni.
- Un organizzatore che condivide per errore password o link pubblico.
- Un dispositivo scolastico smarrito o lasciato con la sessione aperta.
- Un attaccante sulla stessa rete che prova password comuni o invia richieste
  da un sito esterno aperto nel browser.

**Fuori ambito**

- Esposizione diretta a Internet, NAT o tunnel pubblico.
- Attacchi al sistema operativo, al filesystem o all'hardware del server.
- Isolamento fra scuole diverse o fra installazioni separate.
- Disponibilità garantita, bilanciamento di carico, protezione DDoS.

## Ruoli effettivi

| Ruolo | Come si ottiene | Cosa può fare |
| --- | --- | --- |
| Docente | Email e password personale; cookie di sessione firmato | Leggere tutto e gestire solo i tornei della propria utenza |
| Studente | Nessun accesso: scelta “Sono uno studente” | Leggere dashboard, tornei, classifiche ed esportazioni CSV; nessuna scrittura |
| Link pubblico | Token del torneo in `/public/{token}` | Leggere quel torneo, senza diario né metadati privati |

Non esistono ruoli amministrativi oltre ai docenti e non c'è
un'iscrizione autonoma: il primo account viene creato al primo avvio con
`TORNEO_ADMIN_EMAIL` e `TORNEO_ADMIN_PASSWORD`, gli altri con
`python manage.py create-teacher`. Senza sessione docente l'app è sempre in
sola lettura: non esiste più una modalità locale con scritture aperte.

## Come funziona l'accesso

- Le password sono salvate come hash PBKDF2-HMAC-SHA256 con sale casuale e
  260.000 iterazioni; la password in chiaro non viene mai memorizzata.
- `POST /api/auth/login` accetta email e password, confronta l'hash in tempo
  costante e imposta il cookie `open_score_session`.
- Il cookie è firmato con HMAC-SHA256, contiene `teacher_id`, email e scadenza,
  ed è `HttpOnly` e `SameSite=Lax`. Con `TORNEO_COOKIE_SECURE=1` diventa anche
  `Secure`.
- La durata predefinita è 12 ore (`TORNEO_SESSION_HOURS`).
- Il segreto viene letto da `TORNEO_SECRET` oppure da
  `torneo-lab/data/session.secret`, creato al primo avvio. Se il file viene
  cancellato, tutte le sessioni decadono.
- `POST /api/auth/logout` cancella il cookie nel browser. Non esiste un elenco
  server-side delle sessioni: un cookie copiato prima del logout resta valido
  fino alla scadenza. Per invalidare davvero tutti gli accessi, cambiare
  `TORNEO_SECRET` (o cancellare `data/session.secret`) e riavviare.

## Difese presenti

- **Scritture protette**: ogni metodo diverso da `GET`/`HEAD`/`OPTIONS` sotto
  `/api` richiede una sessione docente, tranne login e logout. Le letture e
  `/public` restano aperte.
- **Isolamento fra docenti**: ogni scrittura verifica che il torneo appartenga
  al docente autenticato. Un torneo altrui o storico riceve 403; la UI nasconde
  comunque i comandi non consentiti.
- **Controllo dell'host**: solo gli host in `TORNEO_ALLOWED_HOSTS` più
  `127.0.0.1`, `localhost` e `testserver` sono accettati. Questo limita il DNS
  rebinding verso il server locale.
- **Controllo dell'Origin**: una scrittura con `Origin` diverso da quello del
  server riceve 403, per fermare richieste cross-site da altri siti aperti nel
  browser.
- **Limite ai tentativi**: 5 password errate in 5 minuti dallo stesso IP
  bloccano il login per 60 secondi (429). Il conteggio è in memoria e si azzera
  al riavvio; non protegge da tentativi distribuiti su più IP.
- **Intestazioni di risposta**: `X-Content-Type-Options: nosniff`,
  `Referrer-Policy: same-origin`, CSP con `frame-ancestors 'none'`, HSTS solo
  con `TORNEO_COOKIE_SECURE=1`.
- **Segreti fuori da Git**: `torneo-lab/data/`, `torneo-lab/backup/` e i file
  `.env` sono esclusi. Il database e i backup contengono tutti i dati: vanno
  protetti come documenti scolastici.

## HTTP nella LAN: cosa comporta

L'installazione predefinita usa HTTP. Sulla rete scolastica questo significa
che password, cookie e dati passano in chiaro e possono essere letti da chi ha
accesso alla rete o al Wi-Fi. È accettabile solo se la LAN è considerata
affidabile e il server non è raggiungibile da Internet.

Se serve riservatezza sul filo, mettere il server dietro un reverse proxy HTTPS
(per esempio Caddy, nginx o IIS) sullo stesso computer o su un altro computer
della LAN, e impostare:

```text
TORNEO_COOKIE_SECURE=1
```

In questa configurazione il proxy termina TLS e inoltra a
`http://127.0.0.1:8000`; aprire solo la porta HTTPS nel firewall. Verificare che
il proxy conservi l'intestazione `Host` corretta o aggiungere l'host del proxy a
`TORNEO_ALLOWED_HOSTS`.

Non esporre il server a Internet nemmeno con HTTPS: mancano revoca centralizzata
delle sessioni, protezione da abusi su larga scala e monitoraggio.

## Link pubblico

`/public/{token}` è una capacità, non un permesso verificabile: chiunque abbia
l'URL può leggere il torneo. Non contiene il diario delle modifiche né i
metadati privati, e non accetta scritture. Non pubblicare il link su canali
aperti se il torneo contiene nomi che non devono uscire dalla scuola.

## Password e segreti

- Usare una password lunga e diversa da quelle personali per ogni docente.
- Non inserire password in `opencode.json`, nel README o in un commit.
- Su Windows limitare i permessi di `deploy/open-score.env` al gruppo degli
  amministratori; su Linux `chmod 600` e proprietario `openscore`.
- Dopo un cambio della password bootstrap riavviare il server; per gli altri
  docenti usare `python manage.py reset-password`.
- Conservare una copia del segreto insieme ai backup solo se i backup sono
  protetti; senza segreto le sessioni semplicemente decadono, i dati restano.

## Cosa non è protetto

- Gli audit registrano l'azione ma non ancora l'autore della modifica.
- Manca una disattivazione account dalla UI: un docente che lascia la scuola va
  gestito sul database o con un futuro comando dedicato.
- Nessuna cifratura del database SQLite: chi legge il file legge i dati.
- Nessuna protezione dalla modifica diretta del database sul server.
- Nessun limite alle letture: un client può scaricare ripetutamente i dati.
- Nessuna gestione automatica dei certificati: l'HTTPS richiede un proxy
  esterno.
- Nessun controllo di sicurezza applicativo contro un server compromesso.

## Igiene operativa

1. Accedere solo dal computer degli organizzatori; uscire dopo l'uso su un
   dispositivo condiviso.
2. Controllare periodicamente i backup e la loro integrità.
3. Aggiornare Python e le dipendenze durante le vacanze o prima di un torneo,
   non durante l'evento.
4. Non installare estensioni o software non necessario sul server.
5. Se un dispositivo con la sessione aperta viene perso, cambiare
   `TORNEO_SECRET` e riavviare.
6. Tenere il server spento o non raggiungibile quando non serve.

Per installazione, firewall, backup e ripristino vedere [DEPLOY.md](DEPLOY.md).
