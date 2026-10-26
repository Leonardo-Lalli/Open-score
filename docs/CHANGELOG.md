# Changelog

## 0.3.0 — 26 ottobre 2026 — backend locale

- API V1 con sessioni, CSRF, password salate, ruoli, ownership e isolamento;
  confine esplicito fra demo anonima e modalità servizio.
- Migrazioni additive schema 3/4 con backup preventivo; CLI professori,
  assegnazione conservativa dei tornei legacy e copie backup/restore verificate.
- Studenti, squadre, capienza, riordino indipendente dal seeding e iscrizioni.
- Proposte distinte, revisione professore, risultati ufficiali e storico attribuibile,
  correzioni/avanzamenti/calendario nella stessa transazione.
- Inviti a uso limitato con hash, scadenza e revoca; pubblicazione con whitelist.
- Campi/sedi, disponibilità e conflitti del campo tra tornei dello stesso contesto.
- Preset scolastici calcio 11/7/5, basket e pallavolo indoor, set e regole custom,
  tavolino esplicito e penalità; next slot bracket e statistiche ufficiali.
- Risposte V1 tipizzate e OpenAPI generato; test di integrazione su SQLite reale.
- Frontend e README principale invariati. Nessun push, PR remota o deploy.

Esito finale delle verifiche e limiti nel [report backend](CORE_ENGINE_REPORT.md).

## 0.2.0 — 24 ottobre 2026

- Audit dello starter ZIP e baseline dei sei test originali.
- Backend separato in entry point, servizi, validazioni, database, fixture e motore.
- Dashboard e wizard originali, viste partecipanti/partite/classifiche, tabellone collegato e adattamento responsive.
- Knockout da 2 a 32 partecipanti anche dispari, BYE, seeding riproducibile via API, avanzamento per incontro e gestione delle correzioni con audit.
- Gironi andata/ritorno e percorso a più fasi con qualificazioni automatiche e controllate.
- Programmazione manuale con UTC, conflitti di campo/partecipanti conosciuti e versioni per evitare salvataggi obsoleti.
- Quattro esempi locali, incluso il JSON fornito; vista spettatore di sola lettura ed export CSV.
- Test degli algoritmi/API e documentazione concreta del perimetro. Formati avanzati, set e account restano da implementare.
