# Dominio del professore e GitHub Pages

> **Stato: predisposizione, nessuna configurazione reale.** Nessun record DNS è
> stato modificato, nessun dominio è stato aggiunto a GitHub e nessuna
> credenziale Aruba è nel repository. Il nome del dominio, il piano Aruba e la
> scelta tra apex e `www` non sono ancora noti.

## 1. Divisione delle responsabilità

| Nome (esempio) | Cosa ospita | Responsabile | Stato |
| --- | --- | --- | --- |
| `www.DOMINIO.IT` | sito statico di presentazione, GitHub Pages | Team B | da configurare |
| `DOMINIO.IT` (apex) | redirect verso `www` (consigliato) | Team B | da configurare |
| `app.DOMINIO.IT` | web app FastAPI + database | Team A | da definire |
| `api.DOMINIO.IT` | eventuale API separata | Team A | da definire |

I nomi sono **esempi**: non sono valori da configurare. GitHub Pages serve solo
file statici e **non esegue Python/FastAPI**: `app` e `api` non vanno mai
puntati a Pages. Il sito pubblico non chiama oggi le API dell'app.

## 2. Cosa è già pronto nel repository

- `website/` è statico e usa percorsi relativi per CSS, JS, font e immagini.
- `website/site.config.json` contiene i tre valori di pubblicazione:
  `base`, `url`, `custom_domain`. Oggi `custom_domain` è `null` e il sito vive
  sul percorso di progetto `/Open-score/`.
- `website/404.html` usa `<base href="__SITE_BASE__" />`: sulla radice di un
  dominio personalizzato il segnaposto diventa `/`.
- `website/index.html` usa `__SITE_URL__` per `canonical` e `og:url`.
- `.github/scripts/build_site.py` genera `_site/` risolvendo i due segnaposto e
  verificando la coerenza della configurazione. Non copia `site.config.json`
  né i file `.md`.
- `.github/workflows/pages.yml` esegue `verify` e poi `deploy`, solo su `main`.
- `torneo-lab/tests/test_website.py` controlla configurazione, build, link,
  asset, tema, accessibilità statica e workflow.

## 3. Quando il dominio sarà noto

1. Decidere il nome pubblico: `www.DOMINIO.IT` (consigliato) oppure l'apex
   `DOMINIO.IT`.
2. Aggiornare `website/site.config.json`. Esempio con un dominio fittizio, da
   sostituire con quello reale:

   ```json
   {
     "base": "/",
     "url": "https://www.DOMINIO.IT/",
     "custom_domain": "www.DOMINIO.IT"
   }
   ```

3. Provare in locale:

   ```bash
   python .github/scripts/build_site.py
   cd _site && python -m http.server 8080
   ```

   Controllare home, link, tema chiaro/scuro e una pagina inesistente (404).

4. Fare merge su `main` e attendere il deploy del workflow.
5. In **Settings → Pages → Custom domain** inserire `www.DOMINIO.IT` e salvare.
   Con il workflow Actions GitHub **non crea un file `CNAME`** e ignora quelli
   esistenti: la configurazione vive nelle impostazioni del repository.
6. Verificare il dominio (consigliato prima di toccare il DNS): **Settings del
   profilo → Pages → Add a domain**, poi creare il record TXT indicato da GitHub
   (`_github-pages-challenge-<utente>.<dominio>`) e conservarlo.
7. Configurare il DNS come nella sezione 4.
8. Attendere la propagazione (fino a 24 ore) e attivare **Enforce HTTPS**
   quando diventa disponibile (può richiedere fino a 24 ore).

## 4. DNS, a livello alto

Fonte: documentazione ufficiale GitHub, consultata il 26 ottobre 2026:
[Managing a custom domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
e [Verifying your custom domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages).

| Scenario | Tipo | Nome | Valore |
| --- | --- | --- | --- |
| Apex | `A` | `@` | `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` |
| Apex (IPv6) | `AAAA` | `@` | `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153` |
| Apex (alternativa) | `ALIAS`/`ANAME` | `@` | `leonardo-lalli.github.io` |
| Sottodominio `www` | `CNAME` | `www` | `leonardo-lalli.github.io` |
| Verifica dominio | `TXT` | `_github-pages-challenge-<utente>` | valore fornito da GitHub |

Note operative:

- Il `CNAME` punta a `leonardo-lalli.github.io` **senza** `/Open-score/`.
  Se il repository cambia proprietario o nome, il valore va aggiornato.
- Non puntare il `CNAME` al dominio `*.pages.github.io` mostrato nelle
  impostazioni.
- Se si configurano sia apex sia `www`, GitHub crea automaticamente il redirect
  tra i due. Scegliere quale dei due è il dominio principale.
- **Non usare record wildcard** `*.DOMINIO.IT`: espongono al takeover.
- La propagazione DNS può richiedere fino a 24 ore.
- Verifica da terminale: `dig www.DOMINIO.IT` oppure
  `Resolve-DnsName www.DOMINIO.IT` su Windows.
- Il vecchio URL `leonardo-lalli.github.io/Open-score/` va ricontrollato dopo il
  cambio: il comportamento di redirect dipende dalla configurazione di Pages.

## 5. Aruba, a livello alto

- I record si creano nella **zona DNS del dominio** dal pannello di gestione
  Aruba. I nomi esatti dei menu possono cambiare: seguire la guida Aruba
  aggiornata, senza copiare istruzioni vecchie.
- Non è necessario spostare i nameserver se la zona DNS resta gestita da Aruba.
- **Non cancellare** record esistenti di posta (`MX`), verifica o altri servizi:
  aggiungere solo i record web necessari. Se l'apex punta già a un sito Aruba,
  sostituirlo è un cambio visibile e va autorizzato dal professore.
- Le credenziali Aruba non vanno mai nel repository, in file `.env` versionati,
  nelle issue, nei log o nelle schermate.
- `app` e `api` restano al Team A: non creare per quei nomi record verso
  GitHub Pages.

## 6. Separazione tra sito e applicazione

| Elemento | GitHub Pages | Hosting Team A (Aruba o altro) |
| --- | --- | --- |
| HTML/CSS/JS statici | Sì | possibile ma non necessario |
| FastAPI/Python | **No** | Sì |
| Database SQLite | **No** | Sì, con backup |
| Login e sessioni | **No** | Sì |
| HTTPS | certificato gestito da GitHub | certificato del provider o reverse proxy |

Il sito è una vetrina: non contiene dati, account o API. L'applicazione resta
sulla LAN scolastica finché il Team A non definirà hosting, dominio e
protezioni. Se in futuro il sito chiamerà `api.DOMINIO.IT`, il Team A dovrà
autorizzare l'origine del sito (CORS) e documentare il contratto.

## 7. Rollback

1. Rimuovere il dominio personalizzato da **Settings → Pages**.
2. Ripristinare i record DNS precedenti (annotarli **prima** del cambio).
3. In `website/site.config.json` riportare
   `base: "/Open-score/"`, `url: "https://leonardo-lalli.github.io/Open-score/"`,
   `custom_domain: null`.
4. Rieseguire la build e il deploy.

Il sito torna così sul percorso GitHub Pages senza dipendere dal dominio.

## 8. Informazioni ancora mancanti

- nome reale del dominio e scelta tra apex e `www`;
- piano Aruba e chi ha accesso al pannello DNS;
- se la zona DNS è gestita da Aruba o da terzi;
- se sull'apex esiste già un sito o una casella di posta da preservare;
- hosting scelto dal Team A per `app` e `api`.
