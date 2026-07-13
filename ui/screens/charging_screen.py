from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt

from ui.widgets.plot_widgets import SimpleTimeSeriesPlot
from ui.widgets.plates import EnumStatePlate, UnitPlate, TimePlate
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme


class ChargingScreen(QFrame):
    def __init__(self, command_sender, parent=None):
        super().__init__(parent)
        self.command_sender = command_sender
        self.charge_start_time = None
        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Info panel (left)
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

        # SoC history
        self.soc_plot = SimpleTimeSeriesPlot(
            title=Strings.LBL_SOC_HISTORY,
            unit="%",
            label_formatter_callback=lambda i: "SoC",
            empty_text="No SoC history"
        )
        self.soc_plot.setMinimumHeight(150)
        self.soc_plot.setMinimumWidth(250)
        self.soc_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        info_layout.addWidget(self.soc_plot, stretch=1)

        # Voltage history
        self.voltage_plot = SimpleTimeSeriesPlot(
            title=Strings.LBL_VOLTAGE_HISTORY,
            unit="V",
            label_formatter_callback=lambda i: Strings.LBL_CHARGE_VOLTAGE,
            empty_text="No voltage history"
        )
        self.voltage_plot.setMinimumHeight(150)
        self.voltage_plot.setMinimumWidth(250)
        self.voltage_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        info_layout.addWidget(self.voltage_plot, stretch=1)

        # Current history
        self.current_plot = SimpleTimeSeriesPlot(
            title=Strings.LBL_CURRENT_HISTORY,
            unit="A",
            label_formatter_callback=lambda i: Strings.LBL_CHARGE_CURRENT,
            empty_text="No current history"
        )
        self.current_plot.setMinimumHeight(150)
        self.current_plot.setMinimumWidth(250)
        self.current_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        info_layout.addWidget(self.current_plot, stretch=1)

        # Balancing placeholder
        balancing_lbl = QLabel(Strings.LBL_BALANCING + ": --")
        balancing_lbl.setStyleSheet("color: #888888; font-size: 12px;")
        info_layout.addWidget(balancing_lbl)

        layout.addWidget(info_panel, stretch=2)

        # Controls panel (right)
        controls_panel = QFrame()
        controls_panel.setStyleSheet(Theme.charging_control())
        controls_panel.setMinimumWidth(280)
        controls_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
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
        layout.addWidget(controls_panel, stretch=1)

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
