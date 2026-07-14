import numpy as np
import time
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QScrollArea, QSizePolicy
from PyQt6.QtCore import Qt

from ui.sidebar import Sidebar
from ui.screens.metrics_screen import MetricsScreen
from ui.screens.charging_screen import ChargingScreen
from ui.screens.override_screen import OverrideScreen
from ui.screens.logs_screen import LogsScreen
from ui.screens.export_screen import ExportScreen
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme
from data.hardware_mapping import get_voltage_cell_mapping, get_temperature_sensor_mapping


class DashboardWindow(QMainWindow):
    def __init__(self, command_sender=None, is_mock=False):
        super().__init__()
        self.setWindowTitle(Strings.WINDOW_TITLE)
        sidebar_min = 240
        padding = 40
        self.resize(sidebar_min + Theme.W_SIZE_S + padding, Theme.H_SIZE_S + 400)
        self.setMinimumWidth(sidebar_min + Theme.W_SIZE_S + padding)
        self.setMinimumHeight(Theme.H_SIZE_S + 400)
        self.setStyleSheet(Theme.main_window())

        self.volt_mapping = get_voltage_cell_mapping()
        self.temp_mapping = get_temperature_sensor_mapping()

        self.command_sender = command_sender
        self.is_mock = is_mock
        self._start_time = None

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.nav_clicked.connect(self.on_nav_clicked)
        main_layout.addWidget(self.sidebar)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Content Area with QStackedWidget
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        scroll.setWidget(self.stack)

        self.stack.currentChanged.connect(self._on_screen_changed)
        main_layout.addWidget(scroll, stretch=1)

        # Metrics Screen
        self.metrics_screen = MetricsScreen(self.volt_mapping, self.temp_mapping)
        self.stack.addWidget(self.metrics_screen)

        # Charging Screen
        self.charging_screen = ChargingScreen(self.command_sender)
        self.stack.addWidget(self.charging_screen)

        # Override Screen
        self.override_screen = OverrideScreen()
        self.stack.addWidget(self.override_screen)

        # Logs Screen
        self.logs_screen = LogsScreen()
        self.stack.addWidget(self.logs_screen)

        # Export Screen
        self.export_screen = ExportScreen()
        self.stack.addWidget(self.export_screen)

        # Show metrics screen by default
        self.stack.setCurrentIndex(0)

    def on_telemetry_received(self, telemetry):
        if self._start_time is None:
            self._start_time = time.time()
        current_time = time.time() - self._start_time

        # Update sidebar state panels
        self.sidebar.update_connection_status(connected=True, is_mock=self.is_mock)

        if telemetry.HasField("status"):
            self.sidebar.fsm_plate.update_value(telemetry.status.state)

        if telemetry.HasField("pack_state"):
            ps = telemetry.pack_state
            self.sidebar.pack_voltage_plate.update_value(f"{ps.voltage:.1f}")
            self.sidebar.pack_voltage_post_air_plate.update_value(f"{ps.post_air_voltage:.1f}")
            self.sidebar.pack_current_plate.update_value(f"{ps.current:.1f}")
            self.sidebar.soc_plate.update_value(f"{ps.soc:.1f}")
            self.sidebar.sop_dischg_plate.update_value(f"{ps.sop_dischg:.1f}")
            self.sidebar.sop_chg_plate.update_value(f"{ps.sop_chg:.1f}")

        if telemetry.HasField("contactors"):
            c = telemetry.contactors
            self.sidebar.actuator_plates["air_pos"].update_value(c.air_pos)
            self.sidebar.actuator_plates["air_neg"].update_value(c.air_neg)
            self.sidebar.actuator_plates["pre_charge"].update_value(c.pre_charge)
            self.sidebar.actuator_plates["sdc"].update_value(c.sdc)

        if telemetry.HasField("cell_voltages") and telemetry.HasField("cell_temperatures"):
            volts = np.array(telemetry.cell_voltages.voltages, dtype=np.float64)
            temps = np.array(telemetry.cell_temperatures.temperatures, dtype=np.float64)

            v_min = float(np.min(volts))
            v_max = float(np.max(volts))
            v_avg = float(np.mean(volts))
            v_delta = float(v_max - v_min)
            self.sidebar.voltage_stats_plate.update_stats(v_min, v_max, v_avg, v_delta)

            t_min = float(np.min(temps))
            t_max = float(np.max(temps))
            t_avg = float(np.mean(temps))
            t_delta = float(t_max - t_min)
            self.sidebar.temp_stats_plate.update_stats(t_min, t_max, t_avg, t_delta)

        # Forward to active screen
        active_screen = self.stack.currentWidget()
        if hasattr(active_screen, 'add_point'):
            active_screen.add_point(current_time, telemetry) # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]

    def on_nav_clicked(self, key):
        index_map = {
            "metrics": 0,
            "charging": 1,
            "override": 2,
            "logs": 3,
            "export": 4,
        }
        if key in index_map:
            self.stack.setCurrentIndex(index_map[key])

    def _on_screen_changed(self, index):
        if index >= 0:
            widget = self.stack.widget(index)
            widget.updateGeometry() # pyright: ignore[reportOptionalMemberAccess]
            scroll = self.stack.parent()
            while scroll and not isinstance(scroll, QScrollArea):
                scroll = scroll.parent()
            if scroll:
                scroll.updateGeometry()
                scroll.viewport().updateGeometry() # pyright: ignore[reportOptionalMemberAccess]

    def keyPressEvent(self, event): # pyright: ignore[reportIncompatibleMethodOverride]
        if event.key() == Qt.Key.Key_Escape:
            active = self.stack.currentWidget()
            if hasattr(active, 'clear_selection'):
                active.clear_selection() # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
        super().keyPressEvent(event)
