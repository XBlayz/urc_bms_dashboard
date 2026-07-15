---
lang: it
---

# Contesto & Terminologia
Questa app è relativa a un **sistema di diagnostica** per un _sistema BMS (Battery Management System)_ custom.

## Contesto dell'applicazione
Esso è costruito per interfacciarsi con il _microcontrollore_ (STM32) tramite _porta seriale_ (USB UART).
L'applicazione legge i **segnali** che il microcontrollore produce e li visualizza nell'**interfaccia grafica**, gestendo inoltre **comandi** da parte dell'utente.

## Terminologia
- I vari **segnali** sono identificati con i _loro nomi_ tra ``...``
- Le scritte tra `[...]` indicano i **widget** da usare per visualizzare i **segnali** scritti prima (separati da virgole). Eventuali `(...)` danno _informazioni aggiuntive_ per il **widget**. Se il nome del widget è tra ``...`` (es. `[`widget_name`]`), indica un **widget custom**, altrimenti è solo un nome che si riferisce ad un **widget** predefinito generalmente identificato con un nome _generico_ (devi trovare tu un **widget** che consideri più adatto). La scritta `(arr)` dopo il nome di un **segnale** indica che esso è costituito da un **array di valori**.
- I _layout_ sono strutturati con liste (`- ...`) in caso dell'_ordine verticale_ e tramite `|` in caso dell'_ordine orizzontale_.

---

# Struttura principale della UI
La struttura principale della UI è suddivisa in _2 zone_:
1. **Pannello laterale**
2. **Schermata principale**

La finestra deve essere **ridimensionabile** con dei limiti minimi dettati dalle **dimensioni minime** delle _2 zone_.

## 1. Pannello laterale
Il **pannello laterale** è configurato da _4 zone_ posiziona _verticalmente una sopra l'altra_:
1. **Logo**
2. **Navigazione delle schermate principali**
3. **Pannello di stato del BMS**
4. **Pannello di stato della connessione**

Esso **non deve essere scrollabile**, ne in _verticale_ ne in _orizzontale_. I vari componenti devono avere **dimensione fissata** e alla _scalatura della finestra_ lo spazio extra deve essere _distribuito uniformemente_ nel **padding delle varie zone**.

### 1.1. Logo
Icona dell'applicazione (#TODO: Attualmente _placeholder_).

### 1.2. Navigazione delle schermate principali
_Colonna di bottoni_ che permettono di **cambiare la schermata principale**.

I bottoni devono essere suddivisi in _4 sezioni_, separati da una _linea_:
1. `Metrics`
2. `Charging` e `Override`
3. `Logs`
4. `Settings`

### 1.3. Pannello di stato del BMS
Pannello che mostra lo _stato generale_ del sistema **BMS**.

Esso deve mostrare i seguenti **segnali** nel seguente _layout_:
- `SoC` [`unit_plate`](Unità %) | `Pack current` [`unit_plate`](Unità A)
- "Pack voltage" [box]
  - `DC Link Voltage` [`unit_plate`](Unità V) | `Post AIR Voltage` [`unit_plate`](Unità V)
- "SoP" [box]
  - `SoP Discharge` [`unit_plate`](Unità A) | `SoP Charge` [`unit_plate`](Unità A)
- "Cells stats" [box]
  - `Cells Voltages`(arr) [`stat_summary`](Min celeste, Max rosso, Avg giallo, Delta default, Unità V) | `Cells Temperatures`(arr) [`stat_summary`](Min celeste, Max rosso, Avg giallo, Delta default, Unità °C)
- `FSM state` [`enum_state`](Ogni stato deve avere il suo colore associato)
- "Actuator states" [box]
  - `SDC` [`actuator_state`](True "Close" rosso, False "Open" verde) | `Pre-charge` [`actuator_state`](True "Close" giallo, False "Open" grigio)
  - `AIR+` [`actuator_state`](True "Close" rosso, False "Open" grigio) | `AIR-` [`actuator_state`](True "Close" rosso, False "Open" grigio)
- `Fault counter` [#TODO: Da definire componente]
- `Uptime` [`time_plate`](Formato `hh:mm:ss`)

### 1.4. Pannello di stato della connessione
Mostra lo **stato della connessione** con il BMS _tramite seriale_ (#TODO: Aggiungere eventuali statistiche di riferimento dello stato della connessione).

Inoltre mostra se si è in modalità di _debug_ ("Mock") o meno.


## 2. Schermata principale
La schermata principale mostra una delle _schermate selezionabili_ tramite il **pannello laterale**.

Questo deve poter essere **scrollabile** solo in _verticale_ e non in _orizzontale_.

### 2.1. Metrics
Mostra una **serie di grafici** nel seguente _layout_:
- `SoC` [`time_series_plot`] | `DC Link Voltage`, `Post AIR Voltage` [`time_series_plot`]
- `Pack current`, `SoP Discharge`, `SoP Charge` [`time_series_plot`]
- `FSM state` [`time_series_plot_enum`]
- `SDC`, `Pre-charge`, `AIR+`, `AIR-` [`time_series_stacked_plot_bool`]
- `Cells Voltages`(arr) [`time_series_plot`] | `Cells Temperatures`(arr) [`time_series_plot`]
- `Cells Voltages`(arr) [`bar_chart`] | `Cells Temperatures`(arr) [`bar_chart`]

Ogni grafico deve avere una **dimensione minima**, sia in _larghezza_ che in _altezza_.

### 2.2. Charging
#TODO: Da definire

### 2.3. Override
#TODO: Da definire

### 2.4. Logs
#TODO: Da definire

### 2.5. Export
#TODO: Da definire

---

# Widgets
Ci sono vari **componenti custom** che compongono la i vari elementi della _UI_. Essi sono suddivisi nelle seguenti categorie:
1. **Plates**
2. **Plots**

## 1. Plates
Le **plates** sono delle _targette_ che mostrano dei valori _istantanei_.

Ogni tipologia di **plate** ha un _titolo_.

### 1.1. Enum state [`enum_state`]
Interpreta un **segnale** come un **enum**, associando a ogni valore una _label_ e un _colore_ (default #FFFFFF).

### 1.2. Unit plate [`unit_plate`]
Mostra un **segnale** con un'_unita di misura_, una _formattazione specifica_ (default `:.2f`) e un _colore_ (default #FFFFFF).

### 1.3. Actuator state [`actuator_state`]
Mostra lo un **segnale** come un **valore booleano**, associando a ogni valore una _label_ (default "True" e "False") e un _colore_ (default #FFFFFF e #808080).

### 1.4. Time plate [`time_plate`]
Mostra un **segnale** come un **valore temporale** con una _formattazione specifica_ (default `hh:mm:ss`) e un _colore_ (default #FFFFFF).

### 1.5. Stat summary [`stat_summary`]
Mostra delle _statistiche istantanee_ relative a una **serie di segnali**, esse sono:
- Valore **minimo** (MIN)
- Valore **massimo** (MAX)
- Valore **medio** (AVG)
- **Differenza** tra il valore _massimo_ e il valore _minimo_ (DELTA)

Ogni **statistica** ha un'_unita di misura_, una _formattazione specifica_ (default `:.2f`) e un _colore_ (default #FFFFFF).

## 2. Plots
I **plots** sono dei _grafi_ che mostrano segnali con visualizzazioni specifiche.

Ogni tipologia di **plots** ha un _titolo_.

Ogni tipologia di **plots** deve presentare almeno le seguenti funzioni:
- Un _tasto toggle_ che permettere di **massimizzare** il grafico per l'intera porzione di **Schermata principale** _visibile dalla finestra_.
- Un _tasto toggle_ che permetta di **mettere in pausa** l'aggiornamento della visualizzazione dei nuovi dati ricevuti.

### 2.1. Time series plot [`time_series_plot`]
Esso _plotta_ **uno o più segnali** nel tempo.

Inoltre presenta le seguenti _caratteristiche_:
- **Autoscroll**: esso **scrolla automaticamente** una _finestra temporale_ con **scalatura automatica** dell'_asse Y_.
  - La **dimensione** della _finestra temporale_ può essere modificabile tramite uno **slider** a _scomparsa_.
  - Lo _scroll temporale_ è **globale** per tutti i grafici _temporali_.
- **Manual move**: _selezionando_ il grafico e _trascinando_ il mouse (stato **sinistro** _mantenuto premuto_) si può **spostare** il grafico
  - L'**autoscroll** viene **disattivato** _automaticamente_.
- **Zoom**: _selezionando_ il grafico e _muovendo la rottelina_ del mouse si può **zoomare** il grafico (disattivando automaticamente l'**autoscroll**).
  - L'**autoscroll** viene **disattivato** _automaticamente_.
- **Fitting automatico**: 3 tasti che permettono di **fittare automaticamente** i valori massimi e minimi.
  - _Fitting asse Y_ permette di **fittare** l'asse Y.
  - _Fitting asse X_ permette di **fittare** l'asse X.
  - _Fitting asse X e Y_ permette di **fittare** entrambi gli assi.
- **Legenda dei segnali**: permette di **visualizzare** e **nascondere** i vari segnali cliccando sulle loro _label_.
  - Le **label** dei segnali hanno lo stesso _colore_ dei relativi grafici.
  - Tasto per **selezionare** _tutti i segnali_.
  - Tasto per **deselezionare** _tutti i segnali_.
- **Pulsante di clear**: permette di **svuotare** il grafico.
- **Visualizzazione tabulare**: permette di **visualizzare** i valori nella _finestra temporale selezionata_ in formato **tabulare**.
  - I vari **segnali** sono mostrati sulle righe, mentre l'**istante di tempo** sulle colonne.
  - Possibilità di **scrollare** la _finestra temporale_ orizzontalmente.
  - Le **label** dei segnali hanno lo stesso _colore_ dei relativi grafici.
- **Cursor**: _hovering_ con il mouse su un **plot** mostra un _cursore_, linea verticale tratteggiata grigio chiara semi trasparente.
  - Mostra il **valore** dei **segnali** _visibili_ nell'istante di tempo identificato dalla posizione del cursore, con una piccola _box_ posizionata all'**intersezione tra il cursore e il grafico relativo**.
  - Il cursore **scompare** se il mouse non è in _hovering_ sul **plot**.
  - #TODO: Misurazioni delta e intervalli
- **Signal Highlighting**: _cliccando_ sul **grafico relativo a un segnale** esso viene evidenziato, rendendo gli altri grafici _semi trasparenti_.
  - La _label_ del segnale evidenziato viene _evidenziata_ anche nella **legenda**.

Sono presenti anche _funzioni opzionali_ (abilitate solo se esplicitamente richieste):
- **Temporal statistics**: mostra **statistiche temporali** dei vari **segnali** _visibili_.
  - Minimo, Massimo, Media, Delta.
  - In caso di _segnali multipli_ visibili esse vengono visualizzate solo se un segnale è **selezionato** (Signal Highlighting).
- **Signal statistics**: mostra **statistiche** tra i vari **segnali** _visibili_.
  - Minimo, Massimo, Media, Delta.

#### 2.1.1. Time series plot enum [`time_series_plot_enum`]
Variante di `time_series_plot` dove si mostra un'**enumerazione** di valori con la possibilità di associare una _label_ e un _colore_ a ogni valore.

Esso eredita le funzionalità di `time_series_plot` con le seguenti _modifiche_:
- Supporta un solo **segnale** (nessuna legenda di conseguenza).
- Le _label degli stati_ vengono mostrare sull'**asse Y** colorando del _colore specifico_ lo stato **correntemente attivo**, mentre il resto vengono mostrati di colore _grigio semi trasparente_.
- Il _colore del grafico_ cambia in base al **valore assunto in quella porzione** di tempo.
- Lo **zoom verticale** è _bloccato_.
- Pressente solo il tasto di _Fitting asse X_ (_Fitting asse Y_ bloccato).
- La **visualizzazione tabulare** mostra solo i _punti di transizione_ di stato, ignorando i valori duplicati consecutivi.
- Il cursore mostra la _label degli stati_ relativo al valore.
- #TODO: Misurazione cursore intervalli e numeri di transizioni per stato

#### 2.1.2. Time series stacked plot boolean [`time_series_stacked_plot_bool`]
Variante di `time_series_plot` dove si mostrano **segnali booleani** come una serie di grafici a _onda quadra_ uno sopra l'altro nello stesso plot.

Ogni segnale prende una _porzione dell'asse Y_ del plot con i **due stati** (alto true, basso false) distinti dalla _colorazione dell'aria sottesa_ dal grafico in semi trasparente. I vari grafici presentano del _padding_ tra di loro.

Esso eredita le funzionalità di `time_series_plot` con le seguenti _modifiche_:
- La legenda viene inserita direttamente sull'**asse Y**, di fianco a ogni relativo grafico.
- Lo **zoom verticale** è _bloccato_.
- Pressente solo il tasto di _Fitting asse X_ (_Fitting asse Y_ bloccato).
- La **visualizzazione tabulare** mostra solo i _punti di transizione_ di stato, ignorando i valori duplicati consecutivi.
- Il cursore mostra la _label associata ai due stati_ relativo al valore (default: `True`, `False`) _colorata_ (default #FFFFFF e #808080).
    > NOTA: Il colore in base al valore è solo per la label del cursore, il colore del grafico è fissato come in `time_series_plot`.
- #TODO: Misurazione cursore intervalli e numeri di transizioni per stato

### 2.2. Bar chart [`bar_chart`]
Esso _plotta_ **una serie di segnali** come **barre** verticali, mostrando l'_ultimo valore istantaneo ricevuto_.

Inoltre presenta le seguenti _caratteristiche_:
- **Legenda dei segnali**: permette di **visualizzare** e **nascondere** i vari segnali cliccando sulle loro _label_.
  - Tasto per **selezionare** _tutti i segnali_.
  - Tasto per **deselezionare** _tutti i segnali_.
- **Heatmap colors**: le varie barre vengono **colorate** in base al **valore assunto** tramite dei gradienti di colore _heatmap_.
- **Visualizzazione matriciale**: permette di **visualizzare** i valori dei vari segnali in un formato **matriciale** _customizzabile_.
  - Possibilità di definire la _dimensione_ della matrice.
  - Possibilità di definire la _posizione_ sulla matrice dei vari segnali.
  - Possibilità di avere posizioni _vuote_ nella matrice.
  - Possibilità di **zoomare** e **scrollare** (sia verticalmente che orizzontalmente).
  - Le varie posizioni della matrice sono contrassegnate da un _label_ di **riga** e di **colonna** _customizzabili_.
  - Ogni cella ha il _colore_ relativo alla **heatmap colors**.
- **Signal statistics**: mostra **statistiche** tra i vari **segnali** _visibili_.
  - Minimo, Massimo, Media, Delta.
  - Mostra le statistiche anche sull'istogramma:
    - _Min_ e _Max_ **evidenziando i bordi** della barra relativa con i colori celeste (min) e rosso (max).
    - _Avg_ crea una **riga tratteggiata** gialla al _valore della media_.
    - _Delta_ crea una **barretta esterna al grafico** (a sinistra) di colore grigio che _inizia da valore minimo_ e _finisce al valore massimo_.

---

# Struttura delle cartelle
- `data\`: Gestione della lettura dei dati da serial port o mock per debugging.
  - ...
- `ui\`: Gestione dell'interfaccia utente.
  - `screens\`: Schermate principali.
  - `widgets\`: Elementi custom dell'interfaccia grafica.
  - ...
