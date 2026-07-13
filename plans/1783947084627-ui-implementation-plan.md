# BMS Dashboard UI Implementation Plan

## Context
Implement the full UI defined in UI_definition.md while preserving existing conventions, tech stack (PyQt6 + pyqtgraph + numpy + protobuf), and code style. Skip all #TODO items. Write all code and comments in English.

## Key Decisions
- **Data flow**: Extend existing generators. Replace voltages_updated/temperatures_updated signals with a single telemetry_received: BmsTelemetry. DashboardWindow dispatches internally.
- **Command path**: Add a separate BmsCommandSender class for TX (charging start/stop, charging settings). Keeps concerns separated from the read path.
- **Navigation**: Implement real screen switching in DashboardWindow via a stacked layout; sidebar buttons toggle active state and switch visible screen.
- **Scope**: Do NOT implement spatial_plot (marked #TODO in UI definition).

## Task List

### 1. Update data generators
- **data/mock_generator.py**:
  - Add telemetry_received = pyqtSignal(messages_pb2.BmsTelemetry).
  - In update(), build a BmsTelemetry protobuf each tick:
    - PackState with evolving voltage, current, post_air_voltage, soc, sop_dischg, sop_chg
    - BmsStatus with cycling SystemState
    - ActuatorState with mock booleans
    - ChargingSettings with mock values
    - CellVoltages (device_idx + voltages list)
    - CellTemperatures (device_idx + temperatures list)
  - Remove old voltages_updated/temperatures_updated signals.
- **data/serial_generator.py**:
  - Replace signals with single telemetry_received = pyqtSignal(messages_pb2.BmsTelemetry).
  - In on_telemetry_received(), accumulate received payloads into a single BmsTelemetry and re-emit it.
  - Keep parsing for all protobuf fields already present in BmsTelemetry.

### 2. Add BMS command sender
- **data/bms_command_sender.py** (new):
  - Class BmsCommandSender(QObject) with signals:
    - command_sent = pyqtSignal(str, bool) -- (command_name, success)
    - error_occurred = pyqtSignal(str) -- error message
  - Methods:
    - __init__(port, baudrate) -- opens same serial port parameters
    - send_charging_start(voltage, current) -- writes frame, emits result
    - send_charging_stop() -- writes frame, emits result
    - send_charging_settings(voltage, current) -- writes frame, emits result
  - Reuse existing COBS + CRC16 encoding from extif_reader.py to build TX frames.
  - Emit feedback strings for UI confirmation dialogs.

### 3. Extend strings and theme
- **ui/strings.py**:
  - Add labels for: SoC, pack voltage (pre/post AIR), pack current, FSM states, actuator labels, charging start/stop, charging voltage/current fields, logs/export placeholders, connection status strings.
  - Add format strings for plates, plots, dialogs.
- **ui/theme.py**:
  - Add styles for: plate widgets (unit_plate, time_plate, enum_state, stat_summary, actuator_state), connection status panel, charging controls, sidebar nav active styling, separators, plot enum/stacked-bool variants.

### 4. Refactor sidebar
- **ui/sidebar.py**:
  - Convert nav buttons to store references and emit nav_clicked(str) with screen key (metrics, charging, override, logs, export).
  - Replace hardcoded LED actuator list with data-driven actuator_state widget rows bound to ActuatorState fields (AIR+, AIR-, PRE-CHARGE, M.AIR+, M.AIR-, M.PRE-CHARGE, SDC).
  - Add real-time widgets inside the state panel:
    - enum_state plate for FSM
    - time_plate for uptime
    - Fault counter label
    - 2x unit_plate for pack voltage (pre/post AIR)
    - unit_plate for pack current
    - unit_plate for SoC
    - 2x unit_plate for power (discharge/charge)
    - 2x stat_summary for cell voltage stats (min/max/avg/delta)
    - 2x stat_summary for temperature stats (min/max/avg/delta)
  - Add connection status panel at bottom with LED + label and optional latency/throughput stats.

### 5. Create reusable plate widgets
- **ui/plates.py** (new):
  - EnumStatePlate(label, enum_map) -- colored label based on value
  - UnitPlate(label, value, unit, color_hex=None)
  - ActuatorStatePlate(label, value, true_label, false_label, true_color, false_color)
  - StatSummaryPlate(label, min, max, avg, delta, unit)
  - TimePlate(label, seconds) -- formats as hh:mm:ss or --:--:--
  - All plates use existing theme conventions.

### 6. Implement main screen switching
- **ui/main_window.py**:
  - Replace single content layout with QStackedWidget for main screens.
  - Create screen widgets: MetricsScreen, ChargingScreen, OverrideScreen, LogsScreen, ExportScreen.
  - Connect sidebar nav_clicked to stack index changes.
  - Wire single telemetry_received signal from the generator to an internal on_telemetry_received(BmsTelemetry) dispatcher.
  - Dispatcher updates sidebar state panels and forwards data to the active screen.

### 7. Implement Metrics screen
- **ui/screens/metrics_screen.py** (new):
  - Layout: vertical with separator lines between sections.
  - **Section A** -- System metrics plots:
    - SoC vs time (time_series_plot)
    - Pack voltage (pre AIR) vs time
    - Pack post AIR voltage vs time
    - Pack current vs time
    - FSM state vs time (time_series_plot_enum)
    - Actuator states vs time (time_series_plot_stacked_bool)
  - **Section B** -- Cell statistics:
    - All cell voltages vs time
    - Cell voltage histogram (bar_chart)
    - All cell temperatures vs time
    - Cell temperature histogram (bar_chart)
  - Each plot inherits from TimeSeriesPlotWidget or new specialized base.
  - bar_chart widget: custom pyqtgraph bar plot with value labels, min/max highlighting, average line, hover tooltip, click-to-select delta mode.
  - time_series_plot_enum: subclass TimeSeriesPlotWidget locking Y zoom, mapping enum values to colors/labels.
  - time_series_plot_stacked_bool: custom widget stacking boolean series with filled areas, Y-axis labels, shared time axis, locked Y zoom.

### 8. Implement Charging screen
- **ui/screens/charging_screen.py** (new):
  - Layout: split into info panel (left) and controls (right), or stacked sections.
  - Info panel:
    - enum_state plate for charging state
    - 2x time_plate for charge duration / estimated remaining time
    - unit_plate for pack voltage (pre AIR)
    - unit_plate for pack current
    - unit_plate for SoC
    - 2x time_series_plot for SoC and voltage history
    - 1x time_series_plot for pack current history
    - Balancing state placeholder (label + minimal indicator until defined)
  - Controls panel:
    - Start/stop charging toggle button
    - Confirmation dialog on start: summary of target voltage/current/SOC estimate
    - Line edits for charge voltage and charge current
    - Submit button -> calls BmsCommandSender.send_charging_settings()
    - Success/error feedback label after each command

### 9. Implement remaining screens
- **ui/screens/override_screen.py**, **logs_screen.py**, **export_screen.py**:
  - Basic placeholder frames with title and minimal content (since UI definition leaves them as #TODO).
  - Match existing theme and layout conventions.

### 10. Update main.py wiring
- **main.py**:
  - Connect generator's telemetry_received to window.on_telemetry_received(telemetry).
  - Instantiate BmsCommandSender when not in mock mode, or a mock sender for mock mode, and pass it to DashboardWindow.
  - Remove old voltages_updated/temperatures_updated connections.

### 11. Validation
- Run the app with --mock and verify:
  - Sidebar navigation switches screens.
  - All plots update in real time.
  - Sidebar status values reflect incoming telemetry.
  - Charging screen controls emit commands via BmsCommandSender (mock sender should log commands).
  - No crashes on empty data.

## Risks
- Serial TX protocol undefined: command sender will be built with placeholders if wire format is unknown; confirm format before hardware test.
- Performance with ~313 concurrent series (138 voltages + 175 temps): existing decimation logic in TimeSeriesPlotWidget should handle it, but monitor FPS in full dashboard view.
- Protobuf enum names must match SystemState exactly in time_series_plot_enum mapping.

## Out of Scope
- spatial_plot widget
- Balancing state detailed UI
- Logs and Export screens detailed content
- Connection statistics (latency, packet loss) beyond basic LED status
