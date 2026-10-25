# Schede funzionali

Perimetro: demo 0.5 e funzioni future chiaramente distinte. Le regole della demo sono scelte originali, non una ricostruzione certa del backend di Score7. Fonti e link completi in [REFERENCE_ANALYSIS.md](REFERENCE_ANALYSIS.md); stato di copertura in [FEATURE_MATRIX.md](FEATURE_MATRIX.md). P0 = nucleo della demo, P1 = passo vicino o prerequisito per uso pubblico, P2 = evoluzione.

## 01. Creazione, elenco e gestione tornei

| Campo | Specifica |
| --- | --- |
| Descrizione | Impostare una competizione persistente. |
| Input | Nome, sport, variante, formato, partecipanti, descrizione. |
| Regole di business | Scelta originale: 2–32 partecipanti alla generazione; nomi validati; la variante determina tipo partecipante, durata e regole; nessuna modifica della struttura dopo la generazione. |
| Output | Torneo con ID e token di consultazione. |
| Entità database | tournaments, teams, audit_logs |
| Stati | draft → active → completed |
| Errori e casi limite | Nomi vuoti, duplicati; formato non supportato. |
| Dipendenze | Validazione, database. |
| Priorità | P0 |
| Fonte | Screenshot utente; indice KB |
| Grado di certezza | UI e API della demo verificate; CRUD torneo incompleto. |

## 02. Impostazioni e personalizzazione

| Campo | Specifica |
| --- | --- |
| Descrizione | Definire regole iniziali leggibili. |
| Input | Variante, punti V/N/P, andata/ritorno, gruppi, promossi, tipo partecipante. |
| Regole di business | Scelta demo: regole fissate alla creazione e congelate in snapshot; nome/descrizione iniziali, niente temi o loghi. La variante propone i valori, che restano modificabili in bozza. |
| Output | Configurazione usata da motore, durata e interfaccia; regolamento consultabile. |
| Entità database | tournaments |
| Stati | Configurata; poi usata durante la competizione. |
| Errori e casi limite | Numero di gironi incompatibile; knockout con andata/ritorno. |
| Dipendenze | Creazione. |
| Priorità | P0 |
| Fonte | Screenshot utente; pagina campionati |
| Grado di certezza | Regole demo testate; personalizzazione avanzata solo individuata nell’indice. |

## 03. Partecipanti individuali e squadre

| Campo | Specifica |
| --- | --- |
| Descrizione | Iscrivere i soggetti che disputano gli incontri. |
| Input | Nome e tipo sul torneo. |
| Regole di business | Stesso tipo per torneo; aggiunta/rimozione solo in bozza, rinomina anche dopo. |
| Output | Elenco partecipanti e nomi nelle partite. |
| Entità database | teams, tournaments |
| Stati | Iscritto; bloccato strutturalmente dopo generazione. |
| Errori e casi limite | Omonimi, partecipante inesistente, oltre 32. |
| Dipendenze | Torneo. |
| Priorità | P0 |
| Fonte | Screenshot utente; indice KB |
| Grado di certezza | Implementazione originale testata; non riproduce tutto il modello Score7. |

## 04. Giocatori nelle squadre

| Campo | Specifica |
| --- | --- |
| Descrizione | Gestire le rose delle squadre. |
| Input | Squadra, nome del giocatore e numero di maglia opzionale. |
| Regole di business | Solo per varianti a squadre; nome unico per squadra; massimo da `max_roster` della variante; il minimo in campo è mostrato ma non blocca la creazione della rosa. |
| Output | Rosa ordinata, conteggio giocatori e scheda squadra. |
| Entità database | team_players, teams |
| Stati | Modificabile anche a torneo generato; bloccata solo per tornei archiviati o storici. |
| Errori e casi limite | Duplicati (409), superamento del massimo o variante individuale (422). |
| Dipendenze | Partecipanti e variante. |
| Priorità | P1 |
| Fonte | Indice KB: gestione giocatori; richiesta del committente |
| Grado di certezza | Implementata e testata; statistiche individuali restano future. |

## 05. Girone all’italiana

| Campo | Specifica |
| --- | --- |
| Descrizione | Generare incontri tra ogni coppia. |
| Input | Partecipanti ordinati e legs 1/2. |
| Regole di business | Metodo del cerchio originale; n(n−1)/2 per andata; dispari con riposo, nessuna partita fittizia. |
| Output | Turni e incontri senza duplicati indesiderati. |
| Entità database | stages, matches; groups per multifase |
| Stati | Generato → parzialmente giocato → completo. |
| Errori e casi limite | Meno di 2, duplicati, parametro legs errato. |
| Dipendenze | Partecipanti e motore. |
| Priorità | P0 |
| Fonte | Pagina campionati Score7 |
| Grado di certezza | Regola generale documentata; algoritmo originale testato per 2,3,4,5,8,16,32. |

## 06. Eliminazione diretta

| Campo | Specifica |
| --- | --- |
| Descrizione | Seguire il percorso fino al campione. |
| Input | Partecipanti ordinati; seed casuale opzionale via API. |
| Regole di business | Albero alla prossima potenza di due, BYE alle teste di serie; un vincitore per incontro; più gare/rigori non presenti. |
| Output | Bracket completo, dipendenze e campione. |
| Entità database | stages, matches |
| Stati | waiting, ready, completed, bye |
| Errori e casi limite | Pareggio, avversari mancanti, richiesta obsoleta. |
| Dipendenze | Partecipanti, risultati. |
| Priorità | P0 |
| Fonte | Screenshot e JSON utente |
| Grado di certezza | Campione certo; albero e seeding scelte originali, test e browser. |

## 07. BYE, seeding e sorteggio

| Campo | Specifica |
| --- | --- |
| Descrizione | Gestire quantità arbitrarie e ordine iniziale. |
| Input | Da 2 a 32 ID distinti; random_seed opzionale. |
| Regole di business | Seeding standard ricorsivo; seed pseudo-casuale riproducibile; BYE senza risultato. |
| Output | Avanzamenti automatici e incontri realmente giocabili. |
| Entità database | matches.is_bye, source_home, source_away |
| Stati | BYE immediato; avversario futuro in attesa. |
| Errori e casi limite | ID ripetuti, seed non intero. |
| Dipendenze | Knockout. |
| Priorità | P0 |
| Fonte | Nome byes negli screenshot; scelta originale |
| Grado di certezza | Semantica endpoint byes ignota; comportamento demo testato. |

## 08. Risultati, correzioni e storico

| Campo | Specifica |
| --- | --- |
| Descrizione | Salvare e correggere senza incoerenze. |
| Input | Punteggi numerici oppure elenco di set, versione e conferma invalidate. |
| Regole di business | Interi rigorosi; varianti a set con numero massimo, punti minimi, scarto e limite; nulla prima di giocare; cambio vincitore azzera discendenti, con conferma se si perdono risultati. |
| Output | Classifica/tabellone aggiornati, set salvati e storico prima/dopo. |
| Entità database | matches, match_sets, audit_logs |
| Stati | ready → completed; correzioni possono riaprire la competizione. |
| Errori e casi limite | 409 per versione/confirme; 422 per risultato o set invalido; rollback atomico. |
| Dipendenze | Incontri e dipendenze. |
| Priorità | P0 |
| Fonte | Indice KB; scelta originale per l’invalidazione |
| Grado di certezza | Test API e prova browser di blocco/conferma. |

## 09. Classifiche e spareggi

| Campo | Specifica |
| --- | --- |
| Descrizione | Derivare una graduatoria dai risultati. |
| Input | Risultati validi, regole V/N/P e profilo della variante. |
| Regole di business | Demo: punti, differenza, fatti, nome, ID; 0–0 conta, punteggi NULL no. Nei tornei a set i gol sono i set vinti/persi; in Pallavolo 6v6 il 3-2 vale 2/1. Scontri diretti opzionali. |
| Output | Giocate/V/N/P/fatti/subiti/differenza/punti. |
| Entità database | Calcolata da teams, matches e match_sets; nessuna copia salvata. |
| Stati | Provvisoria; definitiva quando tutti gli incontri sono completi. |
| Errori e casi limite | Risultati mancanti e parità residue. |
| Dipendenze | Gironi, risultati e regole della variante. |
| Priorità | P0 |
| Fonte | Pagina campionati e calcolo classifiche KB |
| Grado di certezza | Criteri Score7 più ampi; criteri demo espliciti, test e browser. |

## 10. Tornei multifase

| Campo | Specifica |
| --- | --- |
| Descrizione | Collegare gironi e knockout. |
| Input | Gironi uguali, prime 1/2 per gruppo. |
| Regole di business | Demo: attendere tutti gli incontri; qualificazione automatica per fasce di posizione; correggere un girone ricostruisce la fase finale con conferma. |
| Output | Qualificate, fase finale e campione. |
| Entità database | stages, groups, teams, matches, audit_logs |
| Stati | Gruppi attivi → qualificazione → knockout → completo. |
| Errori e casi limite | Qualificazione prematura, gruppi disuguali o troppo piccoli. |
| Dipendenze | Gironi, classifiche, knockout. |
| Priorità | P0 |
| Fonte | KB multi-stage-tournament |
| Grado di certezza | Test completo 16→4 gruppi→8→campione; niente migliori terzi o Swiss nella demo. |

## 11. Doppia eliminazione

| Campo | Specifica |
| --- | --- |
| Descrizione | Dare una seconda possibilità in tabelloni collegati. |
| Input | Futuri: partecipanti, routing vincitori/sconfitti e variante finale. |
| Regole di business | Documentazione: upper/lower collegati, un campione; Score7 descrive una grand final senza reset. Nessun motore qui. |
| Output | Futuro bracket collegato. |
| Entità database | Candidati: nodi e dipendenze winner/loser; da progettare. |
| Stati | Due sconfitte salvo regola speciale della grand final. |
| Errori e casi limite | BYE e percorsi incompatibili da testare in futuro. |
| Dipendenze | Motore a dipendenze. |
| Priorità | P2 |
| Fonte | KB double-elimination |
| Grado di certezza | Documentato dalla pagina dedicata; non provato direttamente o implementato. |

## 12. Swiss Classic

| Campo | Specifica |
| --- | --- |
| Descrizione | Accoppiare per risultati dopo ogni turno. |
| Input | Futuri: partecipanti, numero turni, risultati, criteri. |
| Regole di business | Documentazione: accoppiamenti dinamici a punteggio vicino, rematch evitati quando possibile. Proposta futura: errori espliciti sui vincoli impossibili. |
| Output | Turno seguente e classifica. |
| Entità database | Candidati: rounds, incontri, criteri. |
| Stati | Turno aperto → completo → nuovo turno. |
| Errori e casi limite | Turno incompleto, rematch inevitabili e dispari da specificare. |
| Dipendenze | Risultati e graduatoria. |
| Priorità | P2 |
| Fonte | KB swiss-format |
| Grado di certezza | Documentato, nessun algoritmo demo né garanzia di conformità a regolamenti Swiss. |

## 13. Swiss with Pots

| Campo | Specifica |
| --- | --- |
| Descrizione | Predisporre incontri per fasce. |
| Input | Futuri: fasce, partecipanti e vincoli dentro/fuori fascia. |
| Regole di business | Documentazione: distinto dal Classic, calendario predisposto; vincoli del nostro futuro motore ancora da progettare. |
| Output | Futuro calendario a vincoli verificati. |
| Entità database | Candidati: pots, memberships, matches. |
| Stati | Configurazione → soluzione o errore. |
| Errori e casi limite | Suddivisione impossibile, vincoli senza soluzione. |
| Dipendenze | Seeding e generatore a vincoli. |
| Priorità | P2 |
| Fonte | KB swiss-format |
| Grado di certezza | Documentato, non implementato. |

## 14. Buchholz, Sonneborn-Berger ed ELO

| Campo | Specifica |
| --- | --- |
| Descrizione | Supportare criteri dedicati. |
| Input | Futuri: risultati, punti avversari e rating. |
| Regole di business | La pagina Swiss descrive questi criteri; convenzioni su BYE, ritiri e aggiornamento ELO da decidere prima del codice. |
| Output | Futuri valori spiegabili nella graduatoria. |
| Entità database | Candidati: ranking_rules, ratings. |
| Stati | Da specificare. |
| Errori e casi limite | Avversari ritirati, dati rating assenti. |
| Dipendenze | Swiss e regole esplicite. |
| Priorità | P2 |
| Fonte | KB swiss-format |
| Grado di certezza | Nomi e significato generale documentati; formule applicative non verificate. |

## 15. Cup & Consolation

| Campo | Specifica |
| --- | --- |
| Descrizione | Due percorsi con due campioni. |
| Input | Futuri: classifica iniziale e dimensioni delle due coppe. |
| Regole di business | Pagina dedicata: tabelloni indipendenti alimentati da una fase precedente; nessun percorso tra i due. |
| Output | Due campioni distinti. |
| Entità database | Candidati: fasi, qualificazioni e due bracket. |
| Stati | Qualificazione → due knockout indipendenti. |
| Errori e casi limite | Partecipanti sovrapposti o contingenti non validi. |
| Dipendenze | Multifase e knockout. |
| Priorità | P2 |
| Fonte | KB cup-and-consolation |
| Grado di certezza | Documentato, non implementato. |

## 16. Calendario manuale

| Campo | Specifica |
| --- | --- |
| Descrizione | Collocare un incontro in un orario e campo. |
| Input | Data con fuso, campo testuale, durata facoltativa, versione. |
| Regole di business | UTC in archivio; durata predefinita dalla variante; no sovrapposizioni note per campo o avversari; ordine tra dipendenze già programmate. |
| Output | Programmazione persistente visibile. |
| Entità database | matches |
| Stati | Senza orario → pianificato → ripianificato. |
| Errori e casi limite | Fuso assente, durata errata, conflitti, versione obsoleta. |
| Dipendenze | Incontri. |
| Priorità | P1 |
| Fonte | Screenshot timestamp/location; KB scheduler |
| Grado di certezza | API testata; non equivale a pianificazione globale. |

## 17. Scheduler, sedi, campi e arbitri

| Campo | Specifica |
| --- | --- |
| Descrizione | Organizzare capacità e disponibilità. |
| Input | Futuri: slot, sedi/campi, arbitri, riposi e dipendenze. |
| Regole di business | Proposta: separare accoppiamenti e collocazione; mai restituire come valido un calendario incompatibile. |
| Output | Futuro calendario o spiegazione dei vincoli impossibili. |
| Entità database | Candidati: venues, fields, referees, assignments, constraints. |
| Stati | Da pianificare → pianificato/parzialmente bloccato. |
| Errori e casi limite | Capacità insufficiente e risorse non disponibili. |
| Dipendenze | Calendario e dipendenze. |
| Priorità | P2 |
| Fonte | KB auto-generate-schedule |
| Grado di certezza | Documentato, non implementato; campi demo sono solo testo. |

## 18. Tabellone

| Campo | Specifica |
| --- | --- |
| Descrizione | Mostrare incontri e collegamenti reali. |
| Input | Albero e stato ottenuti dall’API. |
| Regole di business | Posizioni calcolate da turno e ordine; nodi futuri mostrano dipendenze; scorrimento orizzontale. |
| Output | Visualizzazione interattiva e inserimento risultati. |
| Entità database | Lettura di stages e matches. |
| Stati | In attesa, pronto, confermato, BYE. |
| Errori e casi limite | Nessun bracket prima della qualificazione. |
| Dipendenze | Knockout e UI. |
| Priorità | P0 |
| Fonte | Screenshot utente |
| Grado di certezza | Implementazione originale verificata nel browser. |

## 19. Statistiche

| Campo | Specifica |
| --- | --- |
| Descrizione | Mostrare quanto è stato giocato. |
| Input | Tornei, iscritti, risultati e stato. |
| Regole di business | Demo: contatori aggregati derivati; nessuna statistica individuale di marcatori o cartellini. |
| Output | Contatori dashboard e panoramica. |
| Entità database | tournaments, teams, matches |
| Stati | Aggiornati dopo il commit. |
| Errori e casi limite | Non contare BYE come partite. |
| Dipendenze | Risultati. |
| Priorità | P1 |
| Fonte | Indice KB per statistiche; scelta demo per contatori |
| Grado di certezza | Aggregati implementati; statistiche individuali non analizzate in dettaglio. |

## 20. Pagine spettatore e condivisione

| Campo | Specifica |
| --- | --- |
| Descrizione | Consultare lo stesso torneo da un link. |
| Input | Token locale di consultazione. |
| Regole di business | Endpoint GET senza scritture; vista senza controlli organizzatore; non è un sistema generale di permessi. |
| Output | Calendario, classifica e bracket di sola lettura. |
| Entità database | public_token su tournaments. |
| Stati | Link valido o 404; aggiornamento manuale. |
| Errori e casi limite | Server locale irraggiungibile da altri computer. |
| Dipendenze | Torneo e UI. |
| Priorità | P1 |
| Fonte | Indice KB; scelta originale |
| Grado di certezza | API e browser verificati; nessuna pubblicazione del backend. |

## 21. Importazione ed esportazione

| Campo | Specifica |
| --- | --- |
| Descrizione | Spostare dati in formati utilizzabili. |
| Input | Demo: ID torneo per export. Futuro: CSV validato. |
| Regole di business | CSV incontri con zero conservato, dettaglio dei set e testi formula neutralizzati; import non presente. |
| Output | Download CSV effettivo; nessun PDF implementato. |
| Entità database | Lettura matches e teams. |
| Stati | Esportato; import da progettare. |
| Errori e casi limite | Campi CSV malevoli; import duplicati futuro. |
| Dipendenze | Incontri. |
| Priorità | P1 |
| Fonte | Indice KB |
| Grado di certezza | Export testato; non dichiarato importatore del JSON Score7. |

## 22. Ritiri e forfait

| Campo | Specifica |
| --- | --- |
| Descrizione | Distinguere un esito amministrativo da una partita normale. |
| Input | Futuri: partecipante, motivazione, politica di punteggio. |
| Regole di business | Da concordare: trattamento partite precedenti e future; nessuna simulazione con punteggi fittizi nella demo. |
| Output | Futuri esiti espliciti e classifica coerente. |
| Entità database | Candidati: participant_status, match_outcome e audit. |
| Stati | Da definire. |
| Errori e casi limite | Ritiro dopo qualificazione e parità amministrative. |
| Dipendenze | Regolamento e risultati. |
| Priorità | P2 |
| Fonte | Indice KB |
| Grado di certezza | Funzione individuata; comportamento dettagliato non verificato. |

## 23. Account e autorizzazioni

| Campo | Specifica |
| --- | --- |
| Descrizione | Proteggere le scritture sulla LAN e consentire la consultazione senza accesso. |
| Input | Password unica dell'organizzatore (`TORNEO_ADMIN_PASSWORD`) oppure Bearer token (`TORNEO_API_TOKEN`). |
| Regole di business | Con autenticazione attiva ogni scrittura `/api` richiede sessione o token; letture e vista pubblica restano aperte. Limite di 5 errori in 5 minuti per IP, blocco di 60 secondi. |
| Output | Cookie firmato `open_score_session`, ruolo `admin`, `401` per scritture anonime, `429` per troppi tentativi. |
| Entità database | Nessuna tabella utenti o sessioni: segreto HMAC su file o variabile d'ambiente. |
| Stati | `local-demo` senza password; `school-lan` con autenticazione attiva; sessione valida o scaduta. |
| Errori e casi limite | Password errata, sessione scaduta, host non ammesso (400), Origin diverso (403), logout che non revoca un cookie già copiato. |
| Dipendenze | Configurazione del server e rete interna. |
| Priorità | P1 |
| Fonte | Master prompt; indice KB; scelta originale |
| Grado di certezza | Implementato e testato; account individuali, ruoli per torneo e revoca centralizzata restano da progettare. |

## 24. Persistenza e migrazioni

| Campo | Specifica |
| --- | --- |
| Descrizione | Ritrovare i dati dopo il riavvio. |
| Input | SQLite locale o TORNEO_DB_PATH. |
| Regole di business | Transazioni atomiche, FK attive, versioni schema 1→6; ID incontri mai riciclati; niente conversione legacy implicita; sport rimossi conservati in sola lettura. |
| Output | Dati e audit persistenti. |
| Entità database | Tutte le tabelle; PRAGMA user_version. |
| Stati | Schema aggiornato o errore esplicito. |
| Errori e casi limite | Schema sconosciuto, backup mancante, database più recente. |
| Dipendenze | File system locale. |
| Priorità | P0 |
| Fonte | Starter e scelte originali |
| Grado di certezza | Riavvio e migrazione testati; PostgreSQL futuro. |

## 25. Catalogo sport, varianti e schermate dedicate

| Campo | Specifica |
| --- | --- |
| Descrizione | Scegliere uno dei sei sport e la variante che porta con sé regole, durata e composizione. |
| Input | Sport padre e variante; nella UI anche un deep link `#/sport/{sport}/{variante}`. |
| Regole di business | Sei sport e sedici varianti lette dal database; la variante determina `participant_kind`, durata, punteggio, classifica, rosa e regolamento. Sport e variante sono bloccati dopo la generazione. |
| Output | Catalogo navigabile, scheda regolamento, wizard precompilato, tab Regolamento nel torneo e URL condivisibile. |
| Entità database | sport_configs, sport_variants, tournaments.rules_snapshot/regulation_snapshot |
| Stati | Catalogo letto dal server; tornei esistenti adottano la variante predefinita in migrazione. |
| Errori e casi limite | Variante di un altro sport, variante incompatibile con il tipo partecipante, sport storico rimosso (sola lettura). |
| Dipendenze | Database, servizi e SPA. |
| Priorità | P0 |
| Fonte | Richiesta del committente; catalogo scolastico |
| Grado di certezza | Implementato, testato e verificato nel browser; regolamenti da confermare con il professore. |
