# Bozza PR — coordinamento A0/A1

> Bozza storica dell'incremento `4e15385`, mai pubblicata. L'utente ha richiesto
> di proseguire in locale senza push. La descrizione corrente da revisionare
> è nel [report backend 0.3](../CORE_ENGINE_REPORT.md); questa non descrive il diff attuale.

Stato: **preparata localmente, non aperta su GitHub**. Il push è subordinato
all'autorizzazione esplicita prevista nel Prompt A, sezione 17. Nessun merge
autorizzato. Head: `leo-develop`; base: `main`.

## Titolo

`docs(api): define shared tournament contracts`

## Descrizione pronta per la PR

Il frontend deve poter distinguere le API della demo già disponibili dalle
funzioni del nuovo backend ancora da costruire. Questa PR documenta i contratti
effettivi `/api` e propone i contratti `/api/v1` per account, studenti, risultati
da approvare, inviti, campi, regole sportive e riepiloghi, senza cambiare le route
o il comportamento della demo.

Include audit della baseline `b541824`, matrice backend e handoff al Team B.
Lo schema OpenAPI è generato da FastAPI su un database temporaneo; un test
confronta lo snapshot con il server per intercettare divergenze. Le risposte
di successo restano generiche nell'OpenAPI attuale: i relativi JSON e i limiti
sono descritti nel contratto.

Nessuna modifica a frontend, README principale, workflow, dipendenze o schema DB.
Nessuna funzionalità pianificata è dichiarata implementata. Prima di iniziare
la migrazione multiutente servono revisione dei due sviluppatori e integrazione
di questo contratto.

Validazione: **87 test passati** su Windows/Python 3.14.3, un warning di
deprecazione Starlette/httpx. Include sincronizzazione OpenAPI e verifica che
l'esportatore lasci intatti database utente e snapshot in modalità controllo.
`python scripts/export_openapi.py --check` passato. Nessuna nuova verifica CI remota.

## Checklist di revisione congiunta

- [ ] Confermare che i contratti correnti descrivano le chiamate della UI.
- [ ] Approvare `/api/v1` e il percorso di migrazione senza rinomine silenziose.
- [ ] Concordare cookie, CSRF, recupero account e dominio UI/backend.
- [ ] Approvare owner/organizzazioni e migrazione dei tornei esistenti.
- [ ] Verificare ordine visuale distinto da seeding e membership versionate.
- [ ] Approvare semantica di proposte, revisioni e correzioni concorrenti.
- [ ] Approvare pubblicazione, whitelist e inviti con capienza/approvazione.
- [ ] Scegliere i primi preset sportivi con il professore.
- [ ] Confermare i confini dei file posseduti dal Team B.
- [ ] Entrambi gli sviluppatori hanno revisionato; integrazione in main autorizzata separatamente.

## Pubblicazione, solo dopo autorizzazione

Controllare stato e branch, effettuare push di `leo-develop`, poi aprire una PR
verso `main` usando titolo, descrizione e checklist sopra. La PR effettiva userà
un body-file temporaneo contenente solo descrizione e checklist. Non attribuire
a questa bozza un URL, una revisione o un'integrazione che non esistono.
