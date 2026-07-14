from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QWidget, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt

from ui.widgets.plot_widgets import SimpleTimeSeriesPlot
from ui.widgets.plates import EnumStatePlate, UnitPlate, TimePlate
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme


class ResponsiveGrid(QWidget):
    def __init__(self, min_item_width=400, parent=None):
        super().__init__(parent)
        self._items = []
        self._min_item_width = min_item_width
        self._cols = 1
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(10)

    def add_item(self, widget):
        self._items.append(widget)
        self._grid.addWidget(widget, 0, len(self._items) - 1)
        self._relayout()
        self._update_cols(self.width())

    def resizeEvent(self, event): # pyright: ignore[reportIncompatibleMethodOverride]
        super().resizeEvent(event)
        self._update_cols(self.width())

    def _update_cols(self, width):
        if width <= 0:
            if self._cols != 1:
                self._cols = 1
                self._relayout()
            return
        new_cols = max(1, width // self._min_item_width)
        if new_cols != self._cols:
            self._cols = new_cols
            self._relayout()

    def _relayout(self):
        for i, widget in enumerate(self._items):
            row = i // self._cols
            col = i % self._cols
            self._grid.addWidget(widget, row, col)


class ChargingScreen(QFrame):
    def __init__(self, command_sender, parent=None):
        super().__init__(parent)
        self.command_sender = command_sender
        self.charge_start_time = None
        self._maximized_widget = None
        self._normal_widgets = []
        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Top row: info panel | controls panel
        top_row = QHBoxLayout()
        top_row.setSpacing(15)

        info_panel = QFrame()
        info_panel.setStyleSheet(Theme.charging_control())
        info_panel.setMinimumWidth(320)
        info_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(10)

        # Charging state
        fsm_enum_map = {
            0: Strings.STATE_STANDBY,
            1: Strings.STATE_DRIVING,
            2: Strings.STATE_CHARGING,
            3: Strings.STATE_ERROR,
            4: Strings.STATE_PRECHARGING,
            5: Strings.STATE_PREPARING_CHARGING,
            6: Strings.STATE_INITIALIZING,
            7: Strings.STATE_EXITING_CHARGING,
            8: Strings.STATE_OVERRIDE,
            10: Strings.STATE_NONE,
        }
        self.charging_state_plate = EnumStatePlate(
            Strings.LBL_CHARGING_STATE,
            fsm_enum_map,
            value_key="state"
        )
        info_layout.addWidget(self.charging_state_plate)

        # Charge duration
        self.charge_duration_plate = TimePlate(Strings.LBL_CHARGE_DURATION)
        info_layout.addWidget(self.charge_duration_plate)

        # Estimated remaining
        self.estimated_remaining_plate = TimePlate(Strings.LBL_ESTIMATED_REMAINING)
        info_layout.addWidget(self.estimated_remaining_plate)

        info_layout.addSpacing(10)

        # Pack voltage (pre AIR)
        self.pack_voltage_plate = UnitPlate(Strings.LBL_CHARGE_VOLTAGE, unit="V")
        info_layout.addWidget(self.pack_voltage_plate)

        # Pack current
        self.pack_current_plate = UnitPlate(Strings.LBL_CHARGE_CURRENT, unit="A")
        info_layout.addWidget(self.pack_current_plate)

        # SoC
        self.soc_plate = UnitPlate(Strings.LBL_SOC, unit="%")
        info_layout.addWidget(self.soc_plate)

        info_layout.addSpacing(10)

        history_row = ResponsiveGrid(min_item_width=350)
        self.soc_plot = SimpleTimeSeriesPlot(
            title=Strings.LBL_SOC_HISTORY,
            unit="%",
            label_formatter_callback=lambda i: "SoC",
            empty_text="No SoC history",
            colors=[Theme.SIGNAL_COLORS["soc"]]
        )
        self.soc_plot.setMinimumHeight(200)
        self.soc_plot.setMinimumWidth(300)
        self.soc_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.soc_plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        history_row.add_item(self.soc_plot)

        # Voltage history
        self.voltage_plot = SimpleTimeSeriesPlot(
            title=Strings.LBL_VOLTAGE_HISTORY,
            unit="V",
            label_formatter_callback=lambda i: Strings.LBL_CHARGE_VOLTAGE,
            empty_text="No voltage history",
            colors=[Theme.SIGNAL_COLORS["pack_voltage_pre_air"]]
        )
        self.voltage_plot.setMinimumHeight(200)
        self.voltage_plot.setMinimumWidth(300)
        self.voltage_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.voltage_plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        history_row.add_item(self.voltage_plot)

        # Current history
        self.current_plot = SimpleTimeSeriesPlot(
            title=Strings.LBL_CURRENT_HISTORY,
            unit="A",
            label_formatter_callback=lambda i: Strings.LBL_CHARGE_CURRENT,
            empty_text="No current history",
            colors=[Theme.SIGNAL_COLORS["pack_current"]]
        )
        self.current_plot.setMinimumHeight(200)
        self.current_plot.setMinimumWidth(300)
        self.current_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.current_plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        history_row.add_item(self.current_plot)

        info_layout.addWidget(history_row, stretch=1)

        # Balancing placeholder
        balancing_lbl = QLabel(Strings.LBL_BALANCING + ": --")
        balancing_lbl.setStyleSheet("color: #888888; font-size: 12px;")
        info_layout.addWidget(balancing_lbl)

        top_row.addWidget(info_panel, stretch=2)

        # Controls panel (right)
        controls_panel = QFrame()
        controls_panel.setStyleSheet(Theme.charging_control())
        controls_panel.setMinimumWidth(280)
        controls_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        controls_layout = QVBoxLayout(controls_panel)
        controls_layout.setContentsMargins(15, 15, 15, 15)
        controls_layout.setSpacing(15)

        title = QLabel("CHARGING CONTROLS")
        title.setStyleSheet(Theme.plate_title())
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(title)

        controls_layout.addSpacing(20)

        # Start/Stop toggle
        self.start_stop_btn = QPushButton(Strings.BTN_START_CHARGING)
        self.start_stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_stop_btn.setStyleSheet(Theme.button_primary())
        self.start_stop_btn.clicked.connect(self.on_start_stop_clicked)
        controls_layout.addWidget(self.start_stop_btn)

        controls_layout.addSpacing(20)

        # Voltage input
        voltage_lbl = QLabel(Strings.LBL_SET_VOLTAGE)
        voltage_lbl.setStyleSheet("color: #DDDDDD; font-size: 12px;")
        controls_layout.addWidget(voltage_lbl)

        self.voltage_input = QLineEdit("400.0")
        self.voltage_input.setStyleSheet(Theme.line_edit())
        controls_layout.addWidget(self.voltage_input)

        # Current input
        current_lbl = QLabel(Strings.LBL_SET_CURRENT)
        current_lbl.setStyleSheet("color: #DDDDDD; font-size: 12px;")
        controls_layout.addWidget(current_lbl)

        self.current_input = QLineEdit("30.0")
        self.current_input.setStyleSheet(Theme.line_edit())
        controls_layout.addWidget(self.current_input)

        controls_layout.addSpacing(10)

        # Submit settings
        self.submit_btn = QPushButton(Strings.BTN_SETTINGS_SUBMIT)
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.setStyleSheet(Theme.button_primary())
        self.submit_btn.clicked.connect(self.on_submit_settings)
        controls_layout.addWidget(self.submit_btn)

        controls_layout.addSpacing(20)

        # Feedback label
        self.feedback_lbl = QLabel("")
        self.feedback_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(self.feedback_lbl)

        controls_layout.addStretch()
        top_row.addWidget(controls_panel, stretch=1)

        layout.addLayout(top_row, stretch=1)

        # Store references for maximize/restore
        self._normal_widgets = [info_panel, controls_panel]
        self._max_page = None
        self._max_layout = None

    def _on_plot_maximize(self, checked):
        sender = self.sender()
        if not sender:
            return
        if checked:
            self._maximize_plot(sender)
        else:
            self._restore_normal()

    def _maximize_plot(self, plot_widget):
        self._maximized_widget = plot_widget
        for w in self._normal_widgets:
            w.hide()
        if self._max_page is None:
            self._max_page = QWidget()
            self._max_layout = QVBoxLayout(self._max_page)
            self._max_layout.setContentsMargins(0, 0, 0, 0)
            self.layout().addWidget(self._max_page)
        self._max_layout.addWidget(plot_widget)
        self._max_page.show()

    def _restore_normal(self):
        if self._maximized_widget and self._max_layout is not None:
            self._max_layout.removeWidget(self._maximized_widget)
            self._maximized_widget = None
        if self._max_page is not None:
            self._max_page.hide()
        for w in self._normal_widgets:
            w.show()

    def on_start_stop_clicked(self):
        if self.start_stop_btn.text() == Strings.BTN_START_CHARGING:
            voltage = self.voltage_input.text()
            current = self.current_input.text()
            reply = QMessageBox.question(
                self,
                Strings.TITLE_CHARGING_SUMMARY,
                Strings.MSG_CONFIRM_START.format(voltage=voltage, current=current),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.command_sender.send_charging_start(float(voltage), float(current))
                self.start_stop_btn.setText(Strings.BTN_STOP_CHARGING)
                self.start_stop_btn.setStyleSheet(Theme.button_danger())
                self.feedback_lbl.setStyleSheet(Theme.feedback_label(is_success=True)) # pyright: ignore[reportAttributeAccessIssue]
                self.feedback_lbl.setText(Strings.MSG_CHARGING_STARTED)
        else:
            self.command_sender.send_charging_stop()
            self.start_stop_btn.setText(Strings.BTN_START_CHARGING)
            self.start_stop_btn.setStyleSheet(Theme.button_primary())
            self.feedback_lbl.setStyleSheet(Theme.feedback_label(is_success=True)) # pyright: ignore[reportAttributeAccessIssue]
            self.feedback_lbl.setText(Strings.MSG_CHARGING_STOPPED)

    def on_submit_settings(self):
        try:
            voltage = float(self.voltage_input.text())
            current = float(self.current_input.text())
            self.command_sender.send_charging_settings(voltage, current)
            self.feedback_lbl.setStyleSheet(Theme.feedback_label(is_success=True)) # pyright: ignore[reportAttributeAccessIssue]
            self.feedback_lbl.setText(Strings.MSG_SETTINGS_APPLIED)
        except ValueError:
            self.feedback_lbl.setStyleSheet(Theme.feedback_label(is_success=False)) # pyright: ignore[reportAttributeAccessIssue]
            self.feedback_lbl.setText("Invalid input")

    def update_telemetry(self, telemetry):
        if telemetry.HasField("status"):
            self.charging_state_plate.update_value(telemetry.status.state)

        if telemetry.HasField("pack_state"):
            ps = telemetry.pack_state
            self.pack_voltage_plate.update_value(f"{ps.voltage:.1f}")
            self.pack_current_plate.update_value(f"{ps.current:.1f}")
            self.soc_plate.update_value(f"{ps.soc:.1f}")

    def add_point(self, current_time, telemetry):
        self.update_telemetry(telemetry)

        if telemetry.HasField("pack_state"):
            ps = telemetry.pack_state
            self.soc_plot.add_point(current_time, [ps.soc])
            self.voltage_plot.add_point(current_time, [ps.voltage])
            self.current_plot.add_point(current_time, [ps.current])

        # Update charge duration if in charging state
        if telemetry.HasField("status") and telemetry.status.state == 2:
            if self.charge_start_time is None:
                self.charge_start_time = current_time
            duration = current_time - self.charge_start_time
            self.charge_duration_plate.update_value(duration)
        else:
            self.charge_start_time = None
            self.charge_duration_plate.update_value(None)
