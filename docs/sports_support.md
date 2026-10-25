# Supporto per sport multipli

Open Score organizza sei sport, ognuno con varianti selezionabili. Le regole vivono nel database: la UI non contiene elenchi duplicati.

## Sport e varianti

| Sport | Varianti | Partecipanti | Punteggio | Durata | Rosa max |
| --- | --- | --- | --- | --- | --- |
| Calcio | a 11, a 7, a 5 | squadre | reti, pareggio ammesso | 90 / 50 / 40 min | 22 / 14 / 12 |
| Basket | 5 contro 5, 3x3 | squadre | punti, nessun pareggio | 40 / 10 min | 12 / 4 |
| Pallavolo | 6v6, 4v4, beach 2v2 | squadre | set; 6v6 al meglio dei 5 | 105 / 50 / 50 min | 14 / 8 / 2 |
| Badminton | singolare, doppio, doppio misto | individuale / squadre | set a 21, limite 30 | 45 min | 1 / 2 / 2 |
| Ping pong | singolare, doppio, doppio misto | individuale / squadre | game a 11, al meglio dei 5 | 30 min | 1 / 2 / 2 |
| Biliardino | singolare, doppio | individuale / squadre | gol a tempo o primo a 5 | 15 min | 1 / 2 |

Pallamano e Tennis non fanno più parte del catalogo. I tornei storici che li citano restano leggibili, ma `sport_id`/`variant_id` sono NULL e ogni scrittura riceve 409.

## Cosa determina una variante

- `participant_kind`: squadre o persone individuali.
- `players_on_field`, `min_lineup`, `max_roster`: composizione e limite della rosa.
- `match_duration`: durata predefinita degli incontri generati e della programmazione.
- `scoring_mode`: `goals`, `points` o `sets`.
- Parametri dei set: `sets_to_win`, `max_sets`, `points_per_set`, `tiebreak_points`, `win_by_two`, `max_points`.
- Profilo di classifica: punti vittoria/pareggio/sconfitta e bonus `win_tiebreak`/`loss_tiebreak`.
- `regulation`: testo mostrato nella scheda regolamento.

Alla creazione del torneo regole e regolamento vengono copiati in `rules_snapshot` e `regulation_snapshot`. Le modifiche future al catalogo non riscrivono i tornei già creati.

## API di accesso

- `GET /api/sports` — sport padre con varianti annidate.
- `GET /api/sports/{sport_name}` — sport, varianti e regole della variante predefinita; 404 se assente.
- `GET /api/sports/{sport_name}/variants/{slug}` — dettaglio di una variante.
- `GET /api/variants/{slug}` — scorciatoia per slug univoco.

La SPA carica il catalogo dal server all'avvio. Aggiungere una variante significa inserire una riga in `sport_variants`, senza duplicare schermate o JavaScript.

## Verifica automatica

`tests/test_sports.py` parametrizza tutte le sedici coppie sport/variante. Per ogni coppia verifica che:

- il dettaglio esponga regole e regolamento;
- la creazione del torneo usi la variante e il tipo partecipante corretti;
- il regolamento sia congelato nello snapshot del torneo;
- gli incontri generati ereditino `match_duration` dalla variante.

Questi controlli, insieme ai test di integrità del catalogo, portano la suite a 179 test.
