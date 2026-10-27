> Documento di consegna storico: le parti su adapter mancanti/ready:false, schema e ruoli descrivono la versione indicata. Per il comportamento integrato corrente usare [FINAL_AUDIT.md](FINAL_AUDIT.md), [ARCHITECTURE.md](ARCHITECTURE.md) e [TEAM_B_INTEGRATION_REPORT.md](TEAM_B_INTEGRATION_REPORT.md).

# Dashboard degli studenti — verifica e mappa

> Documento del Team B. Rende esplicito cosa lo studente può già vedere e cosa richiede il Team A.
> Base: `max-develop` · App 0.8.0.

## Principi rispettati nel frontend

- La modalità studente è **sola lettura**: nessun pulsante di creazione, modifica o eliminazione viene mostrato.
- La dashboard studente è **distinta** da quella del professore (non è una dashboard amministrativa).
- Il diario degli eventi (`audit`) del torneo è nascosto a chi non è un docente (`!publicToken && canEdit()`).
- La sicurezza resta server-side: la UI nasconde solo i comandi, non sostituisce i 401/403 del backend.

## Informazioni richieste → stato attuale

| Informazione | Oggi | Azione |
| --- | --- | --- |
| Torneo | Sì, nell'elenco | Presente |
| Sport | Sì, nell'elenco e nella card | Presente |
| Squadra | No: non esiste associazione studente→squadra | Richiede API |
| Professore/organizzatore | No: il backend espone `teacher_id` ma non il nome, con visibilità da definire | Richiede API |
| Prossima partita / avversario / data / ora / campo / sede | No in forma personalizzata | Richiede API |
| Risultati | Sì, aprendo il torneo (tab Partite) | Presente |
| Classifica | Sì, aprendo il torneo (tab Classifica) | Presente |
| Tabellone | Sì, aprendo il torneo (tab Tabellone) | Presente |
| Stato delle proposte di risultato | No: non esiste un flusso di proposta | Richiede API |

## Cosa ho implementato (Team B, con API esistenti)

- **Dashboard studente dedicata** (`renderStudentDashboard`): intestazione "Segui i tornei", tre contatori in sola lettura (Tornei, In corso, Conclusi), filtri e card torneo senza azioni amministrative.
- La card torneo resta una card di sola lettura: solo "Apri", nessun "Modifica/Ripristina/Archivia".
- CTA finale "Accedi come prof" per chi vuole organizzare.
- Diario del torneo nascosto ai non docenti.

## Cosa serve dal Team A (API)

1. **Identità studente e appartenenza a una squadra**: per mostrare "la mia squadra", "la mia prossima partita" e "i miei avversari".
2. **Organizzatore con visibilità appropriata**: nome del professore del torneo, con livello di esposizione deciso dal backend.
3. **Prossima partita personalizzata**: data, ora, campo, sede e avversario dello studente.
4. **Proposte di risultato**: eventuale stato (`pending`/`accepted`/`rejected`) se si introduce un flusso di proposta.
5. **Visibilità**: oggi `GET /api/tournaments` e `GET /api/tournaments/{id}` restituiscono a utenti anonimi `teacher_id`, `public_token` e (nel dettaglio) `audit`. Il frontend nasconde l'`audit` ai non docenti, ma il backend dovrebbe non esporre questi campi ai non proprietari (o servire una vista "studente" dedicata).

## Da non fare

- Non creare una dashboard amministrativa per lo studente.
- Non mostrare pulsanti che lo studente non può usare.
- Non mostrare automaticamente dati personali di altri studenti: rispettare il livello di visibilità restituito dal backend.
