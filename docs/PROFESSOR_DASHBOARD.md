> Documento di consegna storico: le parti su adapter mancanti/ready:false, schema e ruoli descrivono la versione indicata. Per il comportamento integrato corrente usare [FINAL_AUDIT.md](FINAL_AUDIT.md), [ARCHITECTURE.md](ARCHITECTURE.md) e [TEAM_B_INTEGRATION_REPORT.md](TEAM_B_INTEGRATION_REPORT.md).

# Dashboard del professore — verifica e mappa

> Documento del Team B. Verifica la copertura delle pagine richieste dal master prompt rispetto alla SPA attuale, senza duplicare pagine né inventare API.
> Base: `max-develop` · App 0.8.0.

## Stato delle pagine richieste

| Pagina | Stato attuale | Azione |
| --- | --- | --- |
| Elenco tornei | Dashboard (`renderDashboard`) con filtri e card; per il prof usa `?mine=1` | Migliorata (aggiunte "Prossime partite") |
| Creazione torneo | Wizard a 3 passi (`startWizard`) | Presente |
| Dettaglio torneo | `renderTournament` con tab e breadcrumb con il nome del torneo | Presente |
| Squadre | Tab partecipanti + scheda squadra (`teamModal`) | Presente |
| Studenti | Non esiste come entità separata: solo rose giocatori per squadra | Richiede API (aggregato studenti) |
| Partite | Tab "Partite" (`matchRow`) | Presente |
| Calendario | Solo programmazione per singolo incontro; nessuna vista calendario | Futura, da definire con Team A |
| Classifiche | Tab "Classifica" per girone unico | Presente |
| Tabellone | Tab "Tabellone" (`bracket`), con navigatore turni su mobile | Presente |
| Campi | Il campo è solo testo (`location`) | Richiede API (inventario campi) |
| Regole | Tab "Regolamento" + catalogo sport | Presente |
| Risultati da verificare | Non esiste un flusso di approvazione | Richiede API/decisione (stato `pending`) |
| Condivisione | Modale "Condividi" con link, CSV e QR | Presente |
| Statistiche | Contatori aggregati in dashboard e dettaglio | Presente; individuali richiedono API |

## Navigazione

La SPA ha già un percorso prevedibile: **sidebar** (Panoramica, Crea un torneo, Sport e regole, I tuoi tornei) + **breadcrumb** nella topbar + **tab** nel dettaglio. Il breadcrumb mostra il nome del torneo aperto, quindi il professore sa sempre cosa sta gestendo.

| Esigenza del professore | Dove si soddisfa |
| --- | --- |
| 1. Quale torneo sta gestendo | Breadcrumb e intestazione del torneo |
| 2. Inserire le squadre | Tab "Partecipanti" del torneo |
| 3. Assegnare studenti | Rosa giocatori nella scheda squadra (per varianti a squadre) |
| 4. Programmare le partite | Tab "Partite" → azione di programmazione |
| 5. Approvare i risultati | Non presente: serve decisione/API del Team A |
| 6. Classifiche e tabelloni | Tab "Classifica" e "Tabellone" |
| 7. Condividere | Pulsante "Condividi" (link, CSV, QR) |

## Cosa è stato implementato (Team B, con API reali)

- **Prossime partite** nella dashboard del prof: raccoglie, dai dettagli dei tornei gestiti, gli incontri `ready` non ancora giocati, ordinati per orario, e apre il torneo al click.
- **Azioni rapide** già presenti nell'hero: "Crea il tuo torneo" e "Sport e regole".

## Cosa manca e a chi compete

- **Team A (API)**: aggregati dashboard (prossime partite, conflitti, studenti, approvazioni), inventario campi/arbitri, stato `pending` per i risultati.
- **Team B (frontend, dopo l'API)**: vista calendario, pagina "Risultati da verificare", gestione campi, statistiche individuali.

## Non duplicare

Non vanno create nuove pagine per: elenco tornei, creazione, dettaglio, squadre, partite, classifiche, tabellone, regole e condivisione: esistono già e sono raggiungibili dal percorso descritto sopra. Le uniche nuove superfici giustificate sono quelle elencate in "Cosa manca".
