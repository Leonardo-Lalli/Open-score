# Sicurezza — comportamento verificato in 0.9.2

Il database e i backup rimangono sul server scelto dalla scuola. Pages non
riceve account o rose. Le difese applicative non sostituiscono TLS, aggiornamenti
del server, permessi filesystem, backup esterni e decisioni sui dati degli studenti.

## Ruoli e visibilità

| Attore | Accesso effettivo |
| --- | --- |
| Visitatore | Tornei pubblicati e proiezioni pubbliche, nessuna modifica |
| Studente autenticato | Tornei di cui è membro, proprie richieste e proposte per la propria squadra; nessuna approvazione o modifica strutturale |
| Docente | Propri tornei; collaborazione esplicita nello stesso contesto attraverso V1 |
| Amministratore locale | CLI con accesso al DB/filesystem; nessun superadmin web |

La scelta «Sono uno studente» consente anche consultazione anonima: non crea
un'identità. Registrazione/login studente esistono; la registrazione crea solo
studenti, senza iscrizione né ruolo docente. `TORNEO_ALLOW_REGISTRATION=true`
(default) la apre, false la disabilita del tutto. **Registrazione esclusivamente
tramite QR non implementata.** L'invito autorizza una richiesta/iscrizione,
non la creazione di professori. Email non verificata: il docente deve controllare
l'associazione scolastica; preferire inviti con approvazione.

V1 usa 404 fuori ambito, le route storiche possono usare 403. Le verifiche sono
server-side. Pubblicazione sola non apre le liste private V1. Tornei archiviati
rifiutano scritture, nuove proposte e nuove adesioni. Rose mai pubbliche.

## Password, sessioni e richieste

- PBKDF2-HMAC-SHA256 con sale casuale: 260.000 iterazioni storiche, 600.000 V1.
  CLI V1: 12–128 caratteri; CLI storica/bootstrap almeno 8. Preferire CLI V1
  e password personali lunghe, senza credenziali negli script versionati.
- Cookie `open_score_session` firmato (default 12 ore) e
  `open_score_platform_session` opaco (8 ore, pre-sessione 30 minuti),
  HttpOnly/SameSite=Lax, Secure in service. Anche il cookie storico è verificato
  contro `sessions`: logout/reset/disattivazione revocano entrambe le modalità.
  Nel DB solo hash dei token. Segreto storico: TORNEO_SECRET o data/session.secret.
  Proteggere le ACL: chmod su Windows non dimostra permessi corretti.
- V1 usa CSRF anche per login/register. Il client acquisisce e aggiorna il token.
  Scritture browser storiche verificano Origin e CSRF; niente CORS generica.
  Host limitati da TORNEO_ALLOWED_HOSTS.
- Login storico: 5 errori/5 minuti, blocco 60 secondi in memoria. V1: limiti
  persistenti per IP/azione e account. Nessuna protezione DDoS o globale
  distribuita: il proxy deve completarla.
- Query parametrizzate, input rigorosi, limiti a batch/CSV, escape HTML,
  CSV anti-formule, CSP/nosniff/Referrer-Policy. CSP tollera stili inline:
  non equivale a una prova di assenza di XSS. Errori senza input sensibili.
  Import CSV come testo validato, nessun upload arbitrario eseguibile.

## Inviti, risultati e log

Inviti casuali da 32 byte, hash, scadenza entro 90 giorni, revoca, usi e capienza
verificati nella transazione. Retry idempotenti senza nuovi consumi; pending
e approvazione distinti. Proposte separate dai risultati ufficiali: nessun
avanzamento prima della revisione. Versioni di proposta/match verificate;
tavolino riservato al professore. Audit privato attribuibile.

Link nuovi `/#/join/TOKEN`, ma il client chiama anche API con token nel percorso:
il frammento da solo non protegge tutti i log. `access_logging.py` elimina query
string e oscura token di inviti/spettatore nei log Uvicorn preservando metodo/status.
Applicare la stessa minimizzazione al reverse proxy: il filtro Python non controlla
i suoi log. Non registrare body, cookie o credenziali. Limitare accessi/retention
anche di audit e backup, che contengono dati privati.

## Preparazione operativa e limiti

Service richiede HTTPS/origin/host coerenti e abilita Secure/HSTS. Fidarsi degli
header proxy solo dagli indirizzi effettivi del proxy. Un dominio Aruba può
puntare al server: il DB resta sul disco dove gira il processo. Il prodotto
hosting non è stato verificato. LAN HTTP è una configurazione di prova:
per credenziali/dati reali usare TLS anche nella rete interna.

La scuola deve decidere finalità, base giuridica, informativa, alias minimi,
retention/cancellazione, pubblicazione e risposta agli incidenti. Nessuna
conformità GDPR o sicurezza garantita è attestata. Recupero email, cancellazione
definitiva e amministrazione web incompleti; non trattare l'installazione come
SaaS multi-scuola senza revisione dell'isolamento.

Audit dipendenze/prove/rischi in [FINAL_AUDIT.md](FINAL_AUDIT.md); non include
automaticamente immagine OS, proxy o dispositivi. Procedure in
[DEPLOY.md](DEPLOY.md) e [DEPLOYMENT_BACKEND.md](DEPLOYMENT_BACKEND.md).
