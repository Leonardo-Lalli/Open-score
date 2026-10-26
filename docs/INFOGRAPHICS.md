# Statistiche e infografica — Team B

> Proprietario: Team B (frontend/UX). Branch `max-develop`. Versione app 0.8.0.
> Registro cronologico: [handoffs/TEAM_B_LOG.md](handoffs/TEAM_B_LOG.md).

## 1. Perimetro e dati

La scheda **Statistiche** è una vista del torneo (`tab === "stats"`). Non introduce nuove API: legge il dettaglio già restituito da `GET /api/tournaments/{id}`.

| Dato | Fonte |
| --- | --- |
| Squadre | `data.teams.length` |
| Studenti | somma di `team.player_count` (nessun nome) |
| Partite totali / completate / rimanenti | `data.matches`, esclusi i BYE |
| Avanzamento | `completate / totali` |
| Risultati da verificare | `resultProposalsAdapter` + `approvalsCache`; `—` finché l'API non è attiva |
| Classifica / podio | `data.standings` oppure finale knockout |
| Qualificati | `data.groups[].standings` solo a gironi completati |
| Campione | `data.champion_team_id`; per il girone unico il primo in classifica a torneo concluso |
| Periodo | minimo/massimo `scheduled_at`; altrimenti `created_at` |
| QR | `public_token` (docente/studente) o token pubblico corrente (vista spettatore) |

Nessun valore è scritto a mano nell'infografica: il generatore riceve un payload e produce solo etichette e forma.

## 2. Dashboard statistica

In cima alla scheda:

- 8 riquadri: squadre, studenti, partite, completate, rimanenti, avanzamento, da verificare, qualificate;
- barra di avanzamento con `role="progressbar"`;
- podio/classifica con i primi tre;
- elenco qualificati per girone, quando disponibili.

Comportamenti onesti:

- **Qualificati** compaiono solo quando tutte le partite dei gironi hanno un risultato. Prima l'ordine è provvisorio e non viene presentato come qualificazione.
- **Podio** è etichettato «Classifica attuale» nel girone unico non concluso, «Podio» quando il torneo è concluso o c'è un campione.
- **Risultati da verificare** mostra `—` con la nota «API proposte in attesa» finché `resultProposalsAdapter.ready` è `false`.
- **Campione** per il girone unico è il primo della classifica solo a torneo concluso; non viene anticipato.

## 3. Infografica condivisibile

`static/infographic.js` è un modulo puro (UMD) che genera un SVG 1080×1350:

- intestazione: brand, titolo, sport/variante, stato, periodo;
- quattro KPI: squadre, studenti, partite, avanzamento;
- barra di avanzamento con completate/rimanenti;
- banner campione (o primo posto);
- podio/classifica con tre card;
- qualificati per girone (massimo sei, poi «e altri N»);
- QR pubblico con URL;
- footer con data di generazione.

Il file non contiene nomi di squadre o studenti: riceve tutto dal payload. I test verificano che non ci siano dati hardcoded e che il testo sia escapato.

### Formati

| Formato | Stato | Come |
| --- | --- | --- |
| **SVG** | Implementato | `Infographic.buildSvg(payload, {xmlDeclaration:true})` → download `infografica-{id}.svg`; XML valido con `xmlns`, `viewBox`, testo escapato |
| **PNG** | Implementato | L'SVG viene caricato in un `<img>`, disegnato su canvas 2160×2700 (2×) e salvato con `canvas.toBlob`; nessuna risorsa esterna, quindi il canvas non è contaminato |
| **PDF** | Non generato | Il pulsante **Stampa** apre la stampa del browser con solo l'infografica; da lì si può scegliere «Salva come PDF». Non esiste un file PDF prodotto dall'app e la UI non lo dichiara |
| Stampa | Implementata | Foglio `#print-sheet.infographic-sheet`, A4 verticale, SVG a larghezza piena |

Errori: se il canvas o la conversione non sono disponibili, l'export PNG mostra un errore e suggerisce l'SVG; non viene mai mostrato un successo falso.

## 4. Anteprima

L'anteprima nella scheda è lo **stesso SVG** dell'export (senza dichiarazione XML), scalato via CSS. Questo evita differenze tra ciò che si vede e il file scaricato.

- `.infographic-preview svg { width: 100%; height: auto; }`
- Su schermi sotto 1100px la griglia statistiche/infografica passa a una colonna.
- Il podio passa a una colonna sotto 560px.
- Nella stampa viene nascosto tutto tranne `#print-sheet.infographic-sheet`.

## 5. Privacy

- Nessun nome di studente nell'infografica né nelle statistiche: solo conteggi aggregati.
- Nessun `teacher_id`, `public_token` o audit nel testo dell'infografica.
- Il QR contiene soltanto l'URL pubblico in sola lettura; nessuna credenziale.
- Nella vista spettatore il QR usa il token già presente nell'URL, quindi non espone nulla di nuovo.
- Se il link pubblico non esiste, l'infografica mostra «Link pubblico non disponibile» invece di inventarlo.

## 6. Test

`torneo-lab/tests/test_infographic.py` + `tests/infographic_probe.js`:

- l'SVG (con e senza dichiarazione XML) è XML valido, con namespace, `viewBox` e dimensioni corrette;
- titolo con `<`, `>` e `&` viene escapato;
- KPI, podio, campione, qualificati, QR e footer sono presenti;
- la matrice QR produce centinaia di `<rect>` reali;
- senza QR/campione/podio compaiono gli stati espliciti, non dati inventati;
- il modulo non contiene nomi di squadre hardcoded.

Test statici in `test_static_ui.py` verificano script versionato, marker delle azioni, selettori CSS e bilancio delle graffe.

## 7. Limiti noti

- Non ci sono test browser automatizzati: la validità dell'SVG è testata, mentre la resa cromatica e il download PNG vanno verificati a mano su Chrome/Safari/Firefox.
- Il PNG dipende dal rendering SVG del browser; se un font di sistema manca, il testo usa il fallback `Arial, sans-serif`.
- Senza API proposte il conteggio «da verificare» resta `—`.
- Il PDF non è un export nativo: è la stampa del browser.
- Il numero di studenti dipende da `player_count` già presente nel dettaglio; se il Team A cambia la forma delle rose, il calcolo va allineato.
