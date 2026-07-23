import numpy as np
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QScrollArea, QSizePolicy
from PyQt6.QtCore import Qt, QTimer

from ui.sidebar import Sidebar
from ui.screens.telemetry_screen import TelemetryScreen
from ui.screens.metrics_screen import MetricsScreen
from ui.screens.charging_screen import ChargingScreen
from ui.screens.override_screen import OverrideScreen
from ui.screens.logs_screen import LogsScreen
from ui.screens.settings_screen import SettingsScreen
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme
from ui.nav_config import NAV_ENTRIES
from ui.widgets.stacked_widget import CurrentPageStackedWidget
from ui.widgets.plot_frame_base import PlotFrameBase
from data.hardware.hardware_mapping import get_voltage_cell_mapping, get_temperature_sensor_mapping


class DashboardWindow(QMainWindow):
    def __init__(self, command_sender=None, is_mock=False):
        super().__init__()
        self.setWindowTitle(Strings.WINDOW_TITLE)
        sidebar_min = 240
        padding = 40
        self.resize(sidebar_min + Theme.W_SIZE_S + padding, Theme.H_SIZE_S + 400)
        self.setMinimumWidth(sidebar_min + Theme.W_SIZE_S + padding)
        self.setMinimumHeight(Theme.H_SIZE_S + 450)
        self.setStyleSheet(Theme.main_window())

        self.volt_mapping = get_voltage_cell_mapping()
        self.temp_mapping = get_temperature_sensor_mapping()

        self.command_sender = command_sender
        self.is_mock = is_mock

        # --- Asynchronous Rendering State ---
        self._latest_frame = None
        self._last_rendered_timestamp = -1.0
        self._is_connected = False

        self.init_ui()

        # Configura il timer di rendering UI a ~30fps (33ms)
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self._render_loop)
        self.render_timer.start(33)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.nav_clicked.connect(self.on_nav_clicked)
        main_layout.addWidget(self.sidebar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Sizes to the current page only, so pages smaller than the largest
        # screen don't force an unnecessary scrollbar (see CurrentPageStackedWidget).
        self.stack = CurrentPageStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.scroll_area.setWidget(self.stack)

        self.stack.currentChanged.connect(self._on_screen_changed)
        main_layout.addWidget(self.scroll_area, stretch=1)

        screen_factories = {
            "metrics": lambda: MetricsScreen(self.volt_mapping, self.temp_mapping),
            "charging": lambda: ChargingScreen(self.command_sender),
            "override": lambda: OverrideScreen(self.command_sender),
            "logs": LogsScreen,
            "settings": SettingsScreen,
        }

        self._nav_index_map = {}
        for i, entry in enumerate(NAV_ENTRIES):
            screen = screen_factories[entry.key]()
            self.stack.addWidget(screen)
            self._nav_index_map[entry.key] = i

            # While any plot on this screen is maximized, the main scroll area
            # must not scroll (the maximized plot already fills the viewport).
            for plot in screen.findChildren(PlotFrameBase):
                plot.sig_maximize_toggled.connect(self._on_plot_maximize_state_changed)

        self.metrics_screen = self.stack.widget(self._nav_index_map["metrics"])
        self.charging_screen = self.stack.widget(self._nav_index_map["charging"])
        self.override_screen = self.stack.widget(self._nav_index_map["override"])

        self.stack.setCurrentIndex(0)

    def _on_plot_maximize_state_changed(self, maximized):
        policy = (
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff if maximized
            else Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setVerticalScrollBarPolicy(policy)

    def set_connection_status(self, connected: bool):
        """Da chiamare esternamente (es. da main.py) quando lo stato seriale cambia."""
        if self._is_connected and not connected:
            self._inject_nan_gap()

        self._is_connected = connected
        self.sidebar.update_connection_status(connected=connected, is_mock=self.is_mock)

    def _inject_nan_gap(self):
        """Inietta un salto temporale se la connessione cade."""
        if self._last_rendered_timestamp < 0:
            return

        gap_time = self._last_rendered_timestamp + 0.001
        for i in range(self.stack.count()):
            widget = self.stack.widget(i)
            if isinstance(widget, TelemetryScreen):
                widget.inject_gap(gap_time)

    def on_telemetry_received(self, frame):
        """
        O(1) Receiver. Salva solo il frame (Envelope) senza bloccare la UI.
        Assumiamo che 'frame' abbia .timestamp e .state
        """
        self._latest_frame = frame

    def on_nav_clicked(self, key):
        if key in self._nav_index_map:
            self.stack.setCurrentIndex(self._nav_index_map[key])

    def _on_screen_changed(self, index):
        if index >= 0:
            widget = self.stack.widget(index)
            widget.updateGeometry() # pyright: ignore[reportOptionalMemberAccess]
            self.stack.updateGeometry()
            self.scroll_area.updateGeometry()
            self.scroll_area.viewport().updateGeometry() # pyright: ignore[reportOptionalMemberAccess]

    def keyPressEvent(self, event): # pyright: ignore[reportIncompatibleMethodOverride]
        if event.key() == Qt.Key.Key_Escape:
            active = self.stack.currentWidget()
            if isinstance(active, TelemetryScreen):
                active.clear_selection()
        super().keyPressEvent(event)

    def _render_loop(self):
        """Eseguito a 30Hz dal QTimer. Applica i dati alla UI."""
        if not self._is_connected or self._latest_frame is None:
            return

        frame = self._latest_frame
        if frame.timestamp <= self._last_rendered_timestamp:
            return

        self._last_rendered_timestamp = frame.timestamp
        state = frame.state

        # --- Sidebar Updates ---
        self.sidebar.uptime_plate.update_value(frame.timestamp)

        if state.bms_status is not None:
            self.sidebar.fsm_plate.update_value(state.bms_status.value)

        self.sidebar.pack_voltage_plate.update_value(f"{state.pack_voltage:.1f}")
        self.sidebar.pack_voltage_post_air_plate.update_value(f"{state.post_air_voltage:.1f}")
        self.sidebar.pack_current_plate.update_value(f"{state.pack_current:.1f}")
        self.sidebar.soc_plate.update_value(f"{state.soc:.1f}")
        self.sidebar.sop_dischg_plate.update_value(f"{state.sop_dischg:.1f}")
        self.sidebar.sop_chg_plate.update_value(f"{state.sop_chg:.1f}")

        c = state.contactors
        self.sidebar.actuator_plates["air_pos"].update_value(c["air_pos"])
        self.sidebar.actuator_plates["air_neg"].update_value(c["air_neg"])
        self.sidebar.actuator_plates["pre_charge"].update_value(c["pre_charge"])
        self.sidebar.actuator_plates["sdc"].update_value(c["sdc"])

        self.sidebar.fault_plate.update_value(state.diagnostic_state)

        volts = state.cell_voltages
        if volts.size > 0:
            v_min, v_max, v_avg = float(np.min(volts)), float(np.max(volts)), float(np.mean(volts))
            self.sidebar.voltage_stats_plate.update_stats(v_min, v_max, v_avg, v_max - v_min)

        temps = state.cell_temperatures
        if temps.size > 0:
            t_min, t_max, t_avg = float(np.min(temps)), float(np.max(temps)), float(np.mean(temps))
            self.sidebar.temp_stats_plate.update_stats(t_min, t_max, t_avg, t_max - t_min)

        # --- Forward to every screen, not just the visible one, so plots stay
        # populated with the latest data even while their screen is hidden. ---
        for i in range(self.stack.count()):
            widget = self.stack.widget(i)
            if isinstance(widget, TelemetryScreen):
                widget.add_point(frame.timestamp, state)
