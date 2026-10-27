# Database SQLite — schema 8

Default `torneo-lab/data/open_score.sqlite3`, override TORNEO_DB_PATH.
Nuovo DB senza tornei/studenti. Il runner integra Team A schema 4 e Team B
schema 7: le versioni numeriche originarie appartenevano a linee diverse.

| Entità | Dati e relazioni |
| --- | --- |
| organizations, users | Contesti/account, email unica, ruolo e hash password |
| teachers, teacher_user_links | Account storici, stato active e ponte fra ID distinti |
| sessions, rate_limits | Hash token, CSRF, scadenza e limiti V1 |
| sport_configs, sport_variants | Sei sport/sedici varianti |
| tournaments | Owner/contesto, teacher_id, pubblicazione, snapshot e versioni |
| teams, students, team_players | Partecipanti, alias/account per torneo, assegnazioni e rose |
| tournament_collaborators | Collaborazione esplicita V1 nello stesso contesto |
| stages, groups, matches, match_sets | Fasi/gironi, dipendenze/BYE, score/set e calendario |
| result_proposals, result_reviews, official_results | Proposte, revisioni e risultato ufficiale attribuito |
| invites, enrollments | Hash/scadenza/usi/revoca e adesioni con revisione |
| venues, fields | Risorse docente, varianti compatibili, disponibilità/archiviazione |
| team_penalties, player_performances | Penalità e prestazioni inserite dal docente |
| audit_logs, administrative_audit | Autore, azione e snapshot |

variant_id è numerico del catalogo; platform_variant_id identifica i cinque
preset V1. rules_snapshot/regulation_snapshot congelano il catalogo;
rules_json è autorevole per configurazioni V1. identity_bridge e roster_bridge
mantengono i collegamenti senza assumere ID uguali. Classifiche derivate,
nessuna cache dei risultati. L'ordine visuale è indipendente dal seed.

## Integrità e concorrenza

FK attive per connessione, timeout 10 secondi e WAL. BEGIN IMMEDIATE prima
della verifica versioni; errore = rollback integrale. Un worker e disco locale
persistente, niente copie indipendenti dietro un bilanciatore. Controlli API
su appartenenza, capienza, casefold oltre ai vincoli SQL. Gli indici effettivi
sono nei file SQL: questa revisione non ne aggiunge senza necessità misurata.

Match futuri con sorgenti, non avversari inventati; NULL non significa 0–0.
ID incontri eliminati non riciclati; invalidazione esplicita dei discendenti,
revisioni/snapshot conservati. Le proposte possono avere match_id nullo e
original_match_id storico. Date con offset/UTC e timezone IANA; intervalli
semiaperti [inizio,fine), adiacenza consentita. updated_at storico non è un
contatore universale di tutte le mutazioni V1: usare le versioni specifiche.

## Migrazione e backup

Il runner applica i passi storici mancanti e 008_team_integration.sql in una
transazione, verifica FK e imposta PRAGMA user_version=8. Prima di modificare
un DB esistente crea una copia consistente *.pre-v8-TIMESTAMP.sqlite3.
DB futuri o non vuoti senza versione rifiutati, nessun reset automatico.
Migrare con server fermo e un processo; conservare anche un backup esterno.
La revisione 0.9.2 **non introduce migrazioni**. I vecchi tornei vengono
assegnati solo con scelta esplicita/CLI, mai al primo account automaticamente.

backup.py --keep 14 usa VACUUM INTO; manage.py backup/restore usa l'API SQLite
con copie nuove verificate. Non copiare a caldo soltanto il file principale:
WAL può contenere scritture non riversate. Testare restore in nuovo percorso,
integrità/FK, conteggi, login e risultati; procedura in [DEPLOY.md](DEPLOY.md).

DB e backup sono privati; TORNEO_SECRET/data/session.secret è separato e non
è incluso nella copia SQLite. Proteggere entrambi e non pubblicarli. PostgreSQL
richiede adapter e migrazioni dedicate, non basta cambiare la URL.
