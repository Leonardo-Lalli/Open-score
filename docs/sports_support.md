# Supporto per Sport Multipli

Open Score ora supporta una vasta gamma di sport con configurazioni personalizzate per ogni tipo.

## Sport Supportati

### Sport di Squadra

| Sport | Dimensione Squadra | Campo | Palla | Note |
|-------|-------------------|-------|-------|------|
| Calcio | 7-11 giocatori | Erba | Standard | Sport principale |
| Calcio a 5 | 5 giocatori | Erba | Piccola | Campo ridotto |
| Basket | 5 giocatori | Interno | Basket | |
| Pallamano | 7 giocatori | Interno | Pallamano | |
| Volley | 6 giocatori | Interno | Volley | |
| Pallavolo | 6 giocatori | Interno | Pallavolo | |
| Pallacanestro | 5 giocatori | Interno | Basket | Versione specifica |

### Sport Individuali o a Coppia

| Sport | Dimensione Squadra | Campo | Palla | Note |
|-------|-------------------|-------|-------|------|
| Badminton | 1-2 giocatori | Interno | Volano | |
| Tennis | 1-2 giocatori | Esterno | Palla | |

## Configurazioni Sportive

Ogni sport può avere configurazioni specifiche che influenzano:
- Dimensioni delle squadre
- Tipo di campo o campo da gioco
- Tipo di palla o oggetto di gioco
- Sistema di punteggio (punti, set, tempo)

## Esempi di Utilizzo

### Creazione di un Torneo di Basket

Quando si crea un torneo di basket:
- Il sistema verificherà che le squadre abbiano tra 5 e 5 giocatori
- Le partite avverranno su un campo da basket
- Il sistema utilizzerà il punteggio standard

### Creazione di un Torneo di Badminton

Quando si crea un torneo di badminton:
- Il sistema verificherà che le squadre abbiano tra 1 e 2 giocatori
- La partite saranno giocate su un campo da badminton
- Potrebbero essere supportati i punti a set

## Estendibilità

La struttura è progettata per essere estesa facilmente. Per aggiungere un nuovo sport:

1. Aggiungere le configurazioni nello schema `sport_configs` del database
2. Definire le regole specifiche per l' sport
3. Implementare le validazioni appropriate
4. Aggiornare l'interfaccia utente

## API di Accesso

Gli endpoint dell'API per le configurazioni sportive:
- `GET /api/sports` - Elenco di tutti gli sport
- `GET /api/sports/{sport_name}` - Dettagli di uno sport specifico