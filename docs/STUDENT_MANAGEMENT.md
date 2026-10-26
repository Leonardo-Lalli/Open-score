# Gestione studenti nelle squadre

> Documento del Team B. Distingue ciò che è implementato con le API esistenti da ciò che richiede il Team A.
> Base: `max-develop` · App 0.8.0.

## Schermata implementata: tab “Studenti”

Disponibile nel dettaglio torneo per i tornei a squadre, agli utenti con sessione docente. È una vista distinta da “Partecipanti”, che resta la gestione delle squadre.

Contiene:

- **Elenco squadre** con numero di studenti e limite della variante.
- **Ricerca squadra** lato client, senza chiamate aggiuntive.
- **Squadra selezionata** con roster, numero di studenti, minimo per la lineup e stato “Rosa completa / Spazio disponibile”.
- **Aggiunta singola** di uno studente con nome e numero di maglia.
- **Rimozione** di uno studente.
- **Limiti**: `max_roster` e `min_lineup` dalla variante; il pulsante di aggiunta si disabilita a rosa piena e il backend resta comunque l’autorità con 422.
- **Messaggi di validazione**: nome obbligatorio e massimo 60 caratteri, numero 0–99, duplicati non ammessi, limite rosa.
- **Inserimento rapido**:
  - incolla un nome per riga;
  - carica un CSV con colonne `nome` e, facoltativamente, `numero`;
  - anteprima con stato per riga (Pronto / Già presente / Nome non valido / Numero non valido / Rosa completa);
  - salvataggio dei soli elementi validi.

## Come viene salvato l’inserimento rapido

Usa l’**API esistente di aggiunta singola** (`POST /api/tournaments/{id}/teams/{team_id}/players`) una volta per ogni studente valido. Non è un’operazione atomica: se una riga fallisce, le precedenti restano salvate e il riepilogo indica quante sono andate a buon fine. L’interfaccia lo dichiara esplicitamente.

## Cosa manca e richiede il Team A

| Funzione | Stato | Serve |
| --- | --- | --- |
| Studenti non assegnati | Non disponibile | Archivio studenti separato dalle squadre e relativo endpoint |
| Spostamento tra squadre | Non disponibile | Endpoint atomico di assegnazione/spostamento |
| Import massivo atomico | Solo sequenziale lato client | Endpoint bulk con esito per riga |
| Import Excel (.xlsx) | Non supportato | Conversione lato backend o libreria dedicata; per ora CSV |
| Identità studente | Non disponibile | Account/identità studente e appartenenza alla squadra |

La schermata mostra un pannello “Studenti non assegnati” marcato **In attesa API**: non vengono inventati dati.

## Privacy e permessi

- La tab è visibile solo agli utenti con sessione docente; gli studenti non vedono comandi di gestione.
- Le rose mostrano solo nome e numero di maglia, senza altri dati personali.
- La sicurezza è server-side: nascondere i pulsanti non sostituisce i controlli 401/403/422 del backend.

## Test

- Test statici in `tests/test_static_ui.py` per la presenza della schermata, del parser, dei limiti e della form.
- `parseStudentList` verificata in Node con: intestazione CSV, riga valida, duplicato, nome vuoto, numero fuori range.
