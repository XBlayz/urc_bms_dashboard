from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QWidget, QSizePolicy, QStackedWidget
)
from PyQt6.QtCore import Qt

from ui.widgets.plot_widgets import SimpleTimeSeriesPlot
from ui.widgets.plates import EnumStatePlate, UnitPlate, TimePlate
from ui.widgets.responsive_grid import ResponsiveGrid
from ui.widgets.plot_host_mixin import PlotHostMixin
from ui.screens.telemetry_screen import TelemetryScreen
from ui.fsm_state import fsm_state_labels
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme


class ChargingScreen(TelemetryScreen, PlotHostMixin):
    def __init__(self, command_sender, parent=None):
        super().__init__(parent)
        self.command_sender = command_sender
        self.charge_start_time = None
        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        stack = QStackedWidget()
        outer_layout.addWidget(stack)

        normal_page = QWidget()
        layout = QVBoxLayout(normal_page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        top_row = QHBoxLayout()
        top_row.setSpacing(15)

        info_panel = QWidget()
        info_panel.setStyleSheet(Theme.charging_control())
        info_panel.setMinimumWidth(320)
        info_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(10)

        self.charging_state_plate = EnumStatePlate(Strings.LBL_CHARGING_STATE, fsm_state_labels())
        info_layout.addWidget(self.charging_state_plate)

        self.charge_duration_plate = TimePlate(Strings.LBL_CHARGE_DURATION)
        info_layout.addWidget(self.charge_duration_plate)

        self.estimated_remaining_plate = TimePlate(Strings.LBL_ESTIMATED_REMAINING)
        info_layout.addWidget(self.estimated_remaining_plate)

        info_layout.addSpacing(10)

        self.pack_voltage_plate = UnitPlate(Strings.LBL_CHARGE_VOLTAGE, unit="V")
        info_layout.addWidget(self.pack_voltage_plate)

        self.pack_current_plate = UnitPlate(Strings.LBL_CHARGE_CURRENT, unit="A")
        info_layout.addWidget(self.pack_current_plate)

        self.soc_plate = UnitPlate(Strings.LBL_SOC, unit="%")
        info_layout.addWidget(self.soc_plate)

        info_layout.addSpacing(10)

        history_row = ResponsiveGrid(min_item_width=350)
        self.soc_plot = self._build_history_plot(
            Strings.LBL_SOC_HISTORY, "%", "SoC", "No SoC history", Theme.SIGNAL_COLORS["soc"]
        )
        history_row.add_item(self.soc_plot)

        self.voltage_plot = self._build_history_plot(
            Strings.LBL_VOLTAGE_HISTORY, "V", Strings.LBL_CHARGE_VOLTAGE, "No voltage history",
            Theme.SIGNAL_COLORS["pack_voltage_pre_air"]
        )
        history_row.add_item(self.voltage_plot)

        self.current_plot = self._build_history_plot(
            Strings.LBL_CURRENT_HISTORY, "A", Strings.LBL_CHARGE_CURRENT, "No current history",
            Theme.SIGNAL_COLORS["pack_current"]
        )
        history_row.add_item(self.current_plot)

        info_layout.addWidget(history_row, stretch=1)

        balancing_lbl = QLabel(Strings.LBL_BALANCING + ": --")
        balancing_lbl.setStyleSheet("color: #888888; font-size: 12px;")
        info_layout.addWidget(balancing_lbl)

        top_row.addWidget(info_panel, stretch=2)

        controls_panel = QWidget()
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

        self.start_stop_btn = QPushButton(Strings.BTN_START_CHARGING)
        self.start_stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_stop_btn.setStyleSheet(Theme.button_primary())
        self.start_stop_btn.clicked.connect(self.on_start_stop_clicked)
        controls_layout.addWidget(self.start_stop_btn)

        controls_layout.addSpacing(20)

        voltage_lbl = QLabel(Strings.LBL_SET_VOLTAGE)
        voltage_lbl.setStyleSheet("color: #DDDDDD; font-size: 12px;")
        controls_layout.addWidget(voltage_lbl)

        self.voltage_input = QLineEdit("400.0")
        self.voltage_input.setStyleSheet(Theme.line_edit())
        controls_layout.addWidget(self.voltage_input)

        current_lbl = QLabel(Strings.LBL_SET_CURRENT)
        current_lbl.setStyleSheet("color: #DDDDDD; font-size: 12px;")
        controls_layout.addWidget(current_lbl)

        self.current_input = QLineEdit("30.0")
        self.current_input.setStyleSheet(Theme.line_edit())
        controls_layout.addWidget(self.current_input)

        controls_layout.addSpacing(10)

        self.submit_btn = QPushButton(Strings.BTN_SETTINGS_SUBMIT)
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.setStyleSheet(Theme.button_primary())
        self.submit_btn.clicked.connect(self.on_submit_settings)
        controls_layout.addWidget(self.submit_btn)

        controls_layout.addSpacing(20)

        self.feedback_lbl = QLabel("")
        self.feedback_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(self.feedback_lbl)

        controls_layout.addStretch()
        top_row.addWidget(controls_panel, stretch=1)

        layout.addLayout(top_row, stretch=1)

        stack.addWidget(normal_page)
        self._init_plot_host(stack)

    def _build_history_plot(self, title, unit, label, empty_text, color):
        plot = SimpleTimeSeriesPlot(
            title=title, unit=unit, label_formatter_callback=lambda i: label,
            empty_text=empty_text, colors=[color]
        )
        plot.setMinimumHeight(200)
        plot.setMinimumWidth(300)
        plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        return plot

    def on_start_stop_clicked(self):
        if self.start_stop_btn.text() == Strings.BTN_START_CHARGING:
            voltage_text = self.voltage_input.text()
            current_text = self.current_input.text()
            try:
                voltage = float(voltage_text)
                current = float(current_text)
            except ValueError:
                self.feedback_lbl.setStyleSheet(Theme.feedback_label(is_success=False))
                self.feedback_lbl.setText(Strings.MSG_INVALID_INPUT)
                return

            reply = QMessageBox.question(
                self,
                Strings.TITLE_CHARGING_SUMMARY,
                Strings.MSG_CONFIRM_START.format(voltage=voltage, current=current),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.command_sender.send_charging_start(voltage, current)
                self.start_stop_btn.setText(Strings.BTN_STOP_CHARGING)
                self.start_stop_btn.setStyleSheet(Theme.button_danger())
                self.feedback_lbl.setStyleSheet(Theme.feedback_label(is_success=True))
                self.feedback_lbl.setText(Strings.MSG_CHARGING_STARTED)
        else:
            self.command_sender.send_charging_stop()
            self.start_stop_btn.setText(Strings.BTN_START_CHARGING)
            self.start_stop_btn.setStyleSheet(Theme.button_primary())
            self.feedback_lbl.setStyleSheet(Theme.feedback_label(is_success=True))
            self.feedback_lbl.setText(Strings.MSG_CHARGING_STOPPED)

    def on_submit_settings(self):
        try:
            voltage = float(self.voltage_input.text())
            current = float(self.current_input.text())
            self.command_sender.send_charging_settings(voltage, current)
            self.feedback_lbl.setStyleSheet(Theme.feedback_label(is_success=True))
            self.feedback_lbl.setText(Strings.MSG_SETTINGS_APPLIED)
        except ValueError:
            self.feedback_lbl.setStyleSheet(Theme.feedback_label(is_success=False))
            self.feedback_lbl.setText(Strings.MSG_INVALID_INPUT)

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

        # Update charge duration while in CHARGING state
        if telemetry.HasField("status") and telemetry.status.state == 2:
            if self.charge_start_time is None:
                self.charge_start_time = current_time
            duration = current_time - self.charge_start_time
            self.charge_duration_plate.update_value(duration)
        else:
            self.charge_start_time = None
            self.charge_duration_plate.update_value(None)

    def clear_selection(self):
        for plot in (self.soc_plot, self.voltage_plot, self.current_plot):
            plot.clear_selection()
