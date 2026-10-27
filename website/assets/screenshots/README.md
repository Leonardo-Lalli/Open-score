Schermata presente: bracket.png, acquisita nel browser il 27 ottobre 2026
su app 0.9.2 e DB sintetico isolato. Nessun dato reale, credenziale o token.
Dashboard e statistiche restano segnaposto dichiarati.

# Screenshot del sito

Questa cartella è pronta per le immagini reali dell'applicazione. Finché è vuota, il sito mostra segnaposto dichiarati nella sezione `#screenshot`.

## Nomi consigliati

| File | Contenuto | Formato |
| --- | --- | --- |
| `dashboard-prof.png` | Dashboard del professore con tornei e prossime partite | 1600×900 |
| `bracket.png` | Tabellone a eliminazione con campione | 1600×900 |
| `statistiche.png` | Scheda Statistiche e infografica | 1600×900 |
| `mobile.png` (opzionale) | Vista studente o calendario su telefono | 390×844 |

PNG o WebP, peso indicativo sotto 500 KB per immagine. Usa `loading="lazy"` e `width`/`height` espliciti nell'HTML.

Se le immagini mostrano l'interfaccia dell'app, valuta una coppia chiaro/scuro oppure un'immagine neutra: il tema del sito non ricolora le fotografie. I grafici e i segnaposto costruiti in CSS usano già i token del tema.

## Privacy

- Non inserire nomi, foto o dati reali di studenti.
- Usa un torneo di prova con nomi neutri (es. «Squadra A», «Squadra B»).
- Se uno screenshot contiene dati reali, sfoca nomi e dettagli prima di salvarlo.
- Non includere password, cookie, token, URL con `public_token` reali o indirizzi IP interni.

## Come inserirli

Sostituisci il riquadro `.screenshot-frame` corrispondente in `website/index.html` con un `<img>` che punta a `assets/screenshots/<file>` e mantieni la `<figcaption>`. Aggiorna l'`alt` con una descrizione concreta.
