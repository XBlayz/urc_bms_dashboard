# Changelog — ristrutturazione GUI/mock

Ambito di questa passata: solo **GUI e sistema mock** (protocollo/comandi seriali esclusi,
come da indicazione).

## Bug corretti

- `Theme.feedback_label` mancante (crash al primo click su Start/Stop/Apply in Charging).
- `on_start_stop_clicked`: `float()` non protetto da try/except → crash con input non numerico.
- `sidebar.uptime_plate` non veniva mai aggiornato.
- `StackedBoolPlot` dichiarava `sig_maximize_toggled` ma non emetteva mai nulla (nessun
  pulsante maximize nell'header) → ora eredita l'header comune ed emette correttamente.
- Colori/label attuatori non conformi a `UI_definition.md` 1.3 (AIR+, Pre-charge, SDC
  avevano tutti verde=chiuso; label "ON/OFF" invece di "Close/Open").
- `StatSummaryPlate`: tutte le label MIN/MAX/AVG/DELTA erano dello stesso colore.
- `SerialDataGenerator.on_telemetry_received`: `list.index()` O(n) per ogni singolo valore
  di ogni frame (~313 valori ogni 100ms) → sostituito con `HardwareMapping.flat_index()` O(1).
- Legenda del `time_series_plot` non scrollabile: con 138/175 serie andava in overflow.
  Ora è una `LegendPanel` scrollabile con ALL/NONE.
- `mousePressEvent`/`wheelEvent` custom su `TimeSeriesPlotWidget` erano codice morto (gli
  eventi arrivano al `pg.PlotWidget` figlio, non al `QFrame` esterno): l'autoscroll non si
  disattivava mai trascinando/zoomando. Sostituiti con `sigRangeChangedManually` di
  pyqtgraph, che disattiva l'autoscroll sia su drag che su wheel-zoom nativi (nessun
  modificatore Ctrl richiesto, click vs drag gestiti nativamente da pyqtgraph).
- `on_mouse_click` non escludeva le serie nascoste dal calcolo di prossimità (poteva
  selezionare una serie invisibile); ora usa solo gli indici visibili.
- `MetricsScreen`/`ChargingScreen.clear_selection()` non esistevano (il tasto ESC non
  faceva nulla): ora propagano `clear_selection()` a tutti i plot figli.
- `BarChartWidget` colorava le barre per outlier (>2σ rosso/verde) invece che con un vero
  gradiente heatmap come da spec 2.2.

## Architettura (OOP)

- `data/hardware_config.py` + `HardwareMapping`: unica fonte per topologia pack
  (`SLAVE_COUNT`/`CELLS_PER_SLAVE`/`TEMP_SENSORS_PER_SLAVE`), sostituisce il magic-number
  `25/6/7` ripetuto in 3 punti diversi.
- `ui/fsm_state.py`: unica fonte per label/colori FSM, sostituisce il dizionario enum
  triplicato in `sidebar.py`/`metrics_screen.py`/`charging_screen.py`.
- `ui/nav_config.py`: unica fonte per le voci di navigazione, sostituisce i due dizionari
  paralleli in `sidebar.py` e `main_window.py`.
- `ui/widgets/ring_buffer.py` (`TimeSeriesRingBuffer`): buffer hr/lr con decimazione, prima
  duplicato identico in `TimeSeriesPlotWidget` e `StackedBoolPlot`.
- `ui/widgets/plot_frame_base.py` (`PlotFrameBase`): header comune (titolo, pause, table,
  maximize, reset, stats) + `QStackedWidget`, ora ereditato da `TimeSeriesPlotWidget`,
  `StackedBoolPlot`, `BarChartWidget` (prima ciascuno ricostruiva l'header da zero).
- `ui/widgets/responsive_grid.py`: unica `ResponsiveGrid` (prima duplicata e divergente tra
  `metrics_screen.py` e `charging_screen.py`).
- `ui/widgets/plot_host_mixin.py` (`PlotHostMixin`): logica di maximize unificata (prima
  `MetricsScreen` faceva swap su grid, `ChargingScreen` nascondeva interi pannelli senza
  vincolo di viewport). Ora `ChargingScreen` usa lo stesso meccanismo.
- `ui/widgets/table_models.py`: `SignalTimeTableModel` (segnali×tempo, per `time_series_plot`),
  `TransitionTableModel` (solo transizioni, per enum/stacked-bool), `MatrixTableModel`
  (matrice spaziale con heatmap, per `bar_chart`).
- `ui/widgets/heatmap.py`: `VoltageHeatmap`/`TemperatureHeatmap`, gradiente condiviso
  (prima `get_heatmap_color` duplicato in due TableModel quasi identici).
- `ui/screens/telemetry_screen.py` (`TelemetryScreen`, ABC): contratto esplicito
  `add_point()`/`clear_selection()`, sostituisce `hasattr(screen, 'add_point')` in
  `main_window.py` con `isinstance(screen, TelemetryScreen)`.
- `ui/widgets/plates.py`: `Plate` base comune per Enum/Unit/Actuator/Time/StatSummary/
  FaultCounter plate.

## Decisioni di adattamento allo spec (`UI_definition.md`)

1. **Vista a matrice**: spostata dal `time_series_plot` al `bar_chart` (istogrammi
   voltaggi/temperature), come da indicazione. Il `time_series_plot` ora ha una vera
   tabella segnali×tempo (righe=segnali colorati come le curve, colonne=istanti,
   scroll orizzontale).
2. **Fault counter**: mostra il numero di fault correntemente attivi. `diagnostic_state`
   è trattato come bitmask (popcount) — nessun bit layout è ancora definito dal firmware,
   è un placeholder v1 (vedi commento in `plates.py`/`mock_generator.py`).
3. **Override/Logs**: placeholder `PlaceholderScreen` con testo TODO, nessuna logica.
4. **Sidebar nav**: "Export" rimosso, sostituito da "Settings" (placeholder TODO).
5. **Zoom rotellina**: nessun modificatore richiesto (comportamento nativo pyqtgraph).
6. **Drag vs click**: gestito nativamente da pyqtgraph (soglia di movimento interna);
   il drag ha sempre priorità, il click deve essere "secco".

## Limitazioni note / possibili follow-up

- `StackedBoolPlot` ha un cursore minimale (v_line + tooltip testuale) ma non il
  click-to-select/hover_point completo del `time_series_plot` base — lo spec 2.1.2 non lo
  richiede esplicitamente oltre alla label di stato sul cursore.
- Il "matrix view" del `bar_chart` supporta zoom cella via Ctrl+rotellina; non implementa
  il posizionamento arbitrario/personalizzato di celle vuote oltre a quelle già derivate da
  `PARTIAL_SLAVE_INDICES`.
- `Diagnostics.diagnostic_state` come bitmask di fault è un'assunzione: da confermare/
  aggiornare quando il firmware definirà il layout reale dei bit.
- Nessuna modifica al layer di protocollo/comandi (fuori ambito per questa passata).
