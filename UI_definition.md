# Main structure
La struttura principale della UI è configurata da due zone:
- Pannello laterale
- Schermata principale

## Pannello laterale
Il pannello laterale è configurato da 4 zone posiziona verticalmente una sopra l'altra:

### Logo
Logo del progetto.

### Navigazione delle schermate principali
Bottoni di navigazione per le varie schermate principali.

### Pannello di stato
Pannello che mostra lo stato generale del sistema BMS.
- Stato degli attuatori [`actuator_state`]
- Stato della FSM (con ultimo stato precedente) [`enum_state`]
- Uptime [`time_plate`]
- Numero di faults [...]
- Tensione di pacco (sia pre che post AIR) 2x[`unit_plate`]
- Corrente di pacco [`unit_plate`]
- Stato di carica [`unit_plate`]
- Stato di potenza (sia in carica che in scarica) 2x[`unit_plate`]
- Statistiche sulle celle (min, max, avg e delta di tensioni e temperature) 2x[`stat_summary`]

### Pannello di stato della connessione
Mostra lo stato della connessione con il BMS tramite seriale (#TODO: Aggiungere eventuali statistiche di riferimento dello stato della connessione).


## Schermata principale
La schermata principale mostra una delle schermate selezionabili tramite il pannello laterale. Possibilità di inserire delle linee che separano le schemate in sezioni.

### 1. Metrics
Mostra una serie di grafici:
- SoC nel tempo [`time_series_plot`]
- Tensioni (pre e post AIR) nel tempo [`time_series_plot`]
- Corrente di pacco e limiti di carica e scarica nel tempo [`time_series_plot`]
- Stato della FSM nel tempo [`time_series_plot_enum`]
- Stato degli attuatori nel tempo [`time_series_plot_stacked_bool`]
- Statistiche delle tensioni
  - Tensioni delle varie celle nel tempo [`time_series_plot`]
  - Istogramma delle tensioni delle varie celle [`bar_chart`]
- Statistiche delle temperature
  - Temperatura delle varie celle nel tempo [`time_series_plot`]
  - Istogramma delle temperature delle varie celle [`bar_chart`]

### {Linea separatrice}

### 2. Charging
Mostra varie informazioni relative alla ricarica e alla sua configurazione.
- Stato della carica (se in carica o meno) [`enum_state`]
- Durata della carica e stima del tempo di carica rimanente 2x[`time_plate`]
- Tensione del pacco (pre AIR) [`unit_plate`]
- Corrente di pacco [`unit_plate`]
- Stato di carica [`unit_plate`]
- Grafici temporali del SoC e tensione (pre AIR) [`time_series_plot`]
- Grafico temporale della corrente di pacco [`time_series_plot`]
- Informazioni sullo stato del bilanciamento (#TODO: Da definire bene)
- Pulsante di avvio e arresto della ricarica (toggle + pop-up di conferma dell'avvio con riepilogo dei parametri di ricarica)
- Field di configurazione della tensione di ricarica
- Field di configurazione della corrente di ricarica
- Tasto di invio dei parametri di ricarica (con feedback della conferma)

### 3. Override
#TODO:

### {Linea separatrice}

### 4. Logs
#TODO:

### {Linea separatrice}

### 5. Export
#TODO:

---

# Widgets
Ogni componente istanziato viene definito come un widget.

## Plate
Le **Plate** sono delle targette che mostrano dei valori istantanei singoli.

### Enum state `enum_state`
Mostra un segnale com un enum, associando ad ogni valore una lable e un colore.

### Unit plate `unit_plate`
Mostra un valore con la sua didascalia e l'unita di misura di visualizzazione.
- Lable del segnale
- Eventuale colore opzionale (anche definibile sulla base del valore)
- Unita di misura

### Actuator state `actuator_state`
Mostra lo stato di un'attuatore mostrando lo stato booleano.
- Lable del segnale
- Lable custom per definire lo stato booleano (con valori di default)
- Colori opzionali sulla base dello stato (con valori di default)

### Statistic summory `stat_summary`
Mostra valori statistici di riassunto relativi a vari dati.
- Valore minimo
- Valore massimo
- Valore medio
- Differenza tra il valore massimo e il valore minimo

Ogni stat può avere un'unità di misura e un colore opzionale.

### Time plate `time_plate`
Mostra un valore temporale con la sua didascalia in un formato umanamente leggibile (es. `hh:mm:ss`). Se il segnale non è presente mostra come valore di default qualcosa di simile a `--:--:--` (in base al formato specificato).


## Grafici
Ogni grafico deve presentare le seguenti funzioni:
- La possibilità di massimizzare il grafico per tutta la schermata principale o tutta la finestra
- Pausa l'aggiornamento della visualizzazione dei nuovi dati ricevuti fino ad un nuovo click del pulsante

### Grafici temporali `time_series_plot`
Plotta uno o più segnali nel tempo. Deve avere le seguenti funzioni:
- Cursore che mostra il valore nell'istante di tempo identificato dalla posizione del mouse sul grafico
- Zoom in e out con la rottelina del mouse
- Spostamento del grafico cliccando e trascinando il mouse
- Autoscroll che segue l'ultimo valore ricevuto (si deve disabilitare automaticamente se il grafico viene spostato manualmente)
- Visualizzazione tabulare (istante di tempo, valori dei vari grafici) come pulsate toggle
- Pulsante di clear
- Legenda dei vari segnali con possibilità di abilitare o disabilitare la visualizzazione do ogni singolo segnale

Inolte tutti i grafici temporali raggrupapti tra loro devono poter fare (widget `plot_group`):
- Pulsate di lock del sync temporale, abilita o disabilita la vilualizzazione degli stessi intervalli temporali
- Pulsante di clear globale per il gruppo

Feature opzionali abilitabili:
- Statistiche temporali della finestra di visualizzazione (min, max, avg e delta)
- Statistiche tra vari segnali (min, max, avg e delta)
- Selezione di un singolo segnale da visualizzare con l'ultimo valore istantaneo ricevuto e valore del cursore in basso a grafico come plate

#### Variante ENUM `time_series_plot_enum`
Invece di mostrare valori continui mostra un'enumerazione di valori (ad esempio 1, 2, 3, 4, 5) con la possibilità di associare una lable e un colore ad ogni valore. Lo zoom verticale é bloccato.

#### Variante STACKED BOOL `time_series_plot_stacked_bool`
Mostra uno o più segnali booleani uno stopra l'altro, mostrano solo una line ase il valore è false, o una line più alta con la sua are sottega riempita dal colore del segnale in trasparenza se il valore é true (l'are deve fermarsi prima dell'inizio del prossimo stacked plot inferiore). Tutti i grafici condividono la stessa asse temporale e lo zoom verticale è bloccato. Non viene mostrata alcuna legenda, invece mostra direttamente sull'asse Y inserisci le lable dei vari segnali.

### Grafici a barre `bar_chart`
Mostra vari segnali in un grafico a barre che mostra l'ultimo valore istantaneo ricevuto, visualizzato anche numericamente sopra ogni barra.

Evidenzia i valori massimi e minimi e possibilità di abilitare una linea che mostra il valore medio. Se si passa sopra una barra con il cursore viene mostrata la lable del segnale.

Possibilità di abilitare tale funzione:
- Visualizzare il valore numerico del delta tra due segnali selezionati cliccando con il mouse.
- Pulsate di clear della selezione.
- Barra selezionata evidenziata lievemente.
- Cliccare su una barra già selezionata per deselezionarla.

### Grafico spaziale `spatial_plot`
#TODO:
