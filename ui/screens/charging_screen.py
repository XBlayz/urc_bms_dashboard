from typing import Optional

import numpy as np
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer

from ui.widgets.plot_widgets import SimpleTimeSeriesPlot, TimeSeriesPlotWidget
from ui.widgets.plates import EnumStatePlate, UnitPlate, TimePlate
from ui.widgets.responsive_grid import ResponsiveGrid
from ui.widgets.plot_host_mixin import PlotHostMixin
from ui.widgets.stacked_widget import CurrentPageStackedWidget
from ui.screens.telemetry_screen import TelemetryScreen
from ui.screens.logic.charging_controller import ChargingController, SETTINGS_MATCH_TOLERANCE
from ui.fsm_state import fsm_state_labels
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme


class FixedFeedbackLabel(QLabel):
    """QLabel with word-wrap but without heightForWidth propagation to ancestor layouts."""
    def hasHeightForWidth(self):
        return False

class ChargingScreen(TelemetryScreen, PlotHostMixin):
    FEEDBACK_CLEAR_DELAY_MS = 5000

    def __init__(self, command_sender, parent=None):
        super().__init__(parent)
        self.command_sender = command_sender
        self.controller = ChargingController(command_sender)
        self.controller.feedback_changed.connect(self._on_feedback_changed)
        self.controller.charging_button_state_changed.connect(self._on_button_state_changed)
        self.controller.settings_button_state_changed.connect(self._on_settings_button_state_changed)
        self.controller.busy_changed.connect(self._on_busy_changed)

        self.charge_start_time = None

        self.feedback_clear_timer = QTimer(self)
        self.feedback_clear_timer.setSingleShot(True)
        self.feedback_clear_timer.timeout.connect(self._clear_feedback)

        self._voltage_settings_on_bms: Optional[float] = None
        self._current_settings_on_bms: Optional[float] = None

        self._settings_request_timer = QTimer(self)
        self._settings_request_timer.timeout.connect(self._resend_initial_state_request)

        # Create UI
        self.init_ui()

        # Force initial sync for the controller
        self.controller.force_sync()

        if self._voltage_settings_on_bms is None or self._current_settings_on_bms is None:
            self._settings_request_timer.start(3000)
            self._resend_initial_state_request()

    def _resend_initial_state_request(self):
        self.command_sender.send_initial_state_request()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        stack = CurrentPageStackedWidget()
        outer_layout.addWidget(stack)

        normal_page = QWidget()
        layout = QVBoxLayout(normal_page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Row 1: Plates | Controls ---
        top_row = QHBoxLayout()
        top_row.setSpacing(15)

        plates_panel = QWidget()
        plates_panel.setStyleSheet(Theme.charging_control())
        plates_panel.setMinimumWidth(320)
        plates_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        plates_layout = QVBoxLayout(plates_panel)
        plates_layout.setContentsMargins(15, 15, 7, 15)
        plates_layout.setSpacing(10)

        self.charging_state_plate = EnumStatePlate(Strings.LBL_CHARGING_STATE, fsm_state_labels())
        plates_layout.addWidget(self.charging_state_plate)

        self.charge_duration_plate = TimePlate(Strings.LBL_CHARGE_DURATION)
        plates_layout.addWidget(self.charge_duration_plate)

        self.estimated_remaining_plate = TimePlate(Strings.LBL_ESTIMATED_REMAINING)
        plates_layout.addWidget(self.estimated_remaining_plate)

        plates_layout.addSpacing(10)

        self.pack_voltage_plate = UnitPlate(Strings.LBL_CHARGE_VOLTAGE, unit="V")
        plates_layout.addWidget(self.pack_voltage_plate)

        self.pack_current_plate = UnitPlate(Strings.LBL_CHARGE_CURRENT, unit="A")
        plates_layout.addWidget(self.pack_current_plate)

        self.soc_plate = UnitPlate(Strings.LBL_SOC, unit="%")
        plates_layout.addWidget(self.soc_plate)

        plates_layout.addSpacing(10)

        balancing_lbl = QLabel(Strings.LBL_BALANCING + ": --")
        balancing_lbl.setStyleSheet("color: #888888; font-size: 12px;")
        plates_layout.addWidget(balancing_lbl)

        plates_layout.addStretch()

        top_row.addWidget(plates_panel, stretch=2)

        controls_panel = QWidget()
        controls_panel.setStyleSheet(Theme.charging_control())
        controls_panel.setMinimumWidth(280)
        controls_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        controls_layout = QVBoxLayout(controls_panel)
        controls_layout.setContentsMargins(7, 15, 15, 15)
        controls_layout.setSpacing(15)

        title = QLabel("CHARGING CONTROLS")
        title.setStyleSheet(Theme.plate_title())
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(title)

        self.start_stop_btn = QPushButton(Strings.BTN_START_CHARGING)
        self.start_stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_stop_btn.clicked.connect(self.on_start_stop_clicked)
        controls_layout.addWidget(self.start_stop_btn)

        voltage_lbl = QLabel(Strings.LBL_SET_VOLTAGE)
        voltage_lbl.setStyleSheet("color: #DDDDDD; font-size: 12px;")
        controls_layout.addWidget(voltage_lbl)

        self.voltage_input = QLineEdit("400")
        self.voltage_input.setStyleSheet(Theme.line_edit())
        controls_layout.addWidget(self.voltage_input)

        current_lbl = QLabel(Strings.LBL_SET_CURRENT)
        current_lbl.setStyleSheet("color: #DDDDDD; font-size: 12px;")
        controls_layout.addWidget(current_lbl)

        self.current_input = QLineEdit("30")
        self.current_input.setStyleSheet(Theme.line_edit())
        controls_layout.addWidget(self.current_input)

        self.voltage_input.textChanged.connect(self._validate_styles)
        self.current_input.textChanged.connect(self._validate_styles)

        self.submit_btn = QPushButton(Strings.BTN_SETTINGS_SUBMIT)
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.clicked.connect(self.on_submit_settings)
        controls_layout.addWidget(self.submit_btn)

        self.feedback_lbl = FixedFeedbackLabel("")
        self.feedback_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_lbl.setWordWrap(True)
        self.feedback_lbl.setFixedHeight(25)
        self.feedback_lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        controls_layout.addWidget(self.feedback_lbl)

        controls_layout.addStretch()
        top_row.addWidget(controls_panel, stretch=1)

        layout.addLayout(top_row)

        # --- Plots, one per row, full width (Plot(SoC), Plot(Voltage), Plot(Current)) ---
        soc_row = ResponsiveGrid(min_item_width=350)
        self.soc_plot = self._build_history_plot(
            Strings.LBL_SOC_HISTORY, "%", "SoC", "No SoC history", Theme.SIGNAL_COLORS["soc"]
        )
        self.soc_plot.setMinimumHeight(Theme.H_SIZE_S)
        soc_row.add_item(self.soc_plot)
        layout.addWidget(soc_row, stretch=1)

        voltage_row = ResponsiveGrid(min_item_width=350)
        self.voltage_plot = self._build_history_plot_with_target(
            Strings.LBL_VOLTAGE_HISTORY, "V", [Strings.LBL_CHARGE_VOLTAGE, "Target Voltage"], "No voltage history",
            Theme.SIGNAL_COLORS["pack_voltage_pre_air"]
        )
        self.voltage_plot.setMinimumHeight(Theme.H_SIZE_S)
        voltage_row.add_item(self.voltage_plot)
        layout.addWidget(voltage_row, stretch=1)

        current_row = ResponsiveGrid(min_item_width=350)
        self.current_plot = self._build_history_plot_with_target(
            Strings.LBL_CURRENT_HISTORY, "A", [Strings.LBL_CHARGE_CURRENT, "Target Current"], "No current history",
            Theme.SIGNAL_COLORS["pack_current"]
        )
        self.current_plot.setMinimumHeight(Theme.H_SIZE_S)
        current_row.add_item(self.current_plot)
        layout.addWidget(current_row, stretch=1)

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

    def _build_history_plot_with_target(self, title, unit, label, empty_text, color):
        plot = TimeSeriesPlotWidget(
            title=title, unit=unit, label_formatter_callback=lambda i: label[i],
            series_count=2,
            empty_text=empty_text, colors=[color], dashed=[False, True]
        )
        plot.setMinimumHeight(200)
        plot.setMinimumWidth(300)
        plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        return plot

    # --- user actions: parse/validate input and confirm, then delegate to the controller ---

    def on_start_stop_clicked(self):
        if self.controller.is_button_start is None:
            return
        elif not self.controller.is_button_start:
            # STOP
            self.controller.handle_charging_button_click()
            return

        try:
            voltage = float(self.voltage_input.text())
            current = float(self.current_input.text())
        except ValueError:
            self.feedback_lbl.setStyleSheet(Theme.feedback_label(is_success=False))
            self.feedback_lbl.setText(Strings.MSG_INVALID_INPUT)
            return

        reply = QMessageBox.question(
            self, Strings.TITLE_CHARGING_SUMMARY,
            Strings.MSG_CONFIRM_START.format(voltage=voltage, current=current),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # START
            self.controller.handle_charging_button_click()

    def on_submit_settings(self):
        try:
            voltage = float(self.voltage_input.text())
            current = float(self.current_input.text())
        except ValueError:
            self.feedback_lbl.setStyleSheet(Theme.feedback_label(is_success=False))
            self.feedback_lbl.setText(Strings.MSG_INVALID_INPUT)
            return

        self.controller.handle_settings_button_click(voltage, current)

    # --- controller signal reflection ---

    def _on_feedback_changed(self, text, is_success):
        self.feedback_lbl.setStyleSheet(Theme.feedback_label(is_success=is_success))
        self.feedback_lbl.setText(text)

        if text:
            self.feedback_clear_timer.start(self.FEEDBACK_CLEAR_DELAY_MS)
        else:
            self.feedback_clear_timer.stop()

    def _clear_feedback(self):
        self.feedback_lbl.setText("")

    def _on_button_state_changed(self, label, is_active, color_string):
        self.start_stop_btn.setText(label)
        self.start_stop_btn.setStyleSheet(Theme.charging_button(is_active, color_string))

    def _on_settings_button_state_changed(self, label, is_active, color_string):
        self.submit_btn.setText(label)
        self.submit_btn.setStyleSheet(Theme.charging_button(is_active, color_string))
        self.submit_btn.setEnabled(is_active)

        self._resend_initial_state_request()
        self._validate_styles()

    def _on_busy_changed(self, kind, busy):
        button = self.start_stop_btn if kind in ("start", "stop") else self.submit_btn
        button.setEnabled(not busy)

    def _validate_styles(self):
        """
        Compares current input text with the applied values and updates stylesheets.
        Uses float conversion with error handling for incomplete typing.
        """
        # Validate Voltage
        try:
            current_v = float(self.voltage_input.text())
            if self._voltage_settings_on_bms is None:
                # BMS value not yet received
                is_v_applied = None
            else:
                is_v_applied = abs(current_v - self._voltage_settings_on_bms) < SETTINGS_MATCH_TOLERANCE
        except ValueError:
            is_v_applied = False
        except AttributeError:
            # Screen not yet initialized
            return

        self.voltage_input.setStyleSheet(Theme.line_edit(applied=is_v_applied))

        # Validate Current
        try:
            current_c = float(self.current_input.text())
            if self._current_settings_on_bms is None:
                # BMS value not yet received
                is_c_applied = None
            else:
                is_c_applied = abs(current_c - self._current_settings_on_bms) < SETTINGS_MATCH_TOLERANCE
        except ValueError:
            is_c_applied = False
        except AttributeError:
            # Screen not yet initialized
            return

        self.current_input.setStyleSheet(Theme.line_edit(applied=is_c_applied))

    # --- telemetry ---

    def update_telemetry(self, state):
        self.controller.on_telemetry(state)

        if state.bms_status is not None:
            self.charging_state_plate.update_value(state.bms_status.value)

        if state.charging_set_voltage is not None:
            self._voltage_settings_on_bms = round(state.charging_set_voltage, 1)
            self.voltage_input.setText(f"{state.charging_set_voltage:.1f}")
        if state.charging_set_current is not None:
            self._current_settings_on_bms = round(state.charging_set_current, 1)
            self.current_input.setText(f"{state.charging_set_current:.1f}")

        if self._voltage_settings_on_bms is not None and self._current_settings_on_bms is not None:
            self._settings_request_timer.stop()

        self._validate_styles()

        self.pack_voltage_plate.update_value(f"{state.pack_voltage:.1f}")
        self.pack_current_plate.update_value(f"{state.pack_current:.1f}")
        self.soc_plate.update_value(f"{state.soc:.1f}")

    def add_point(self, current_time, state):
        self.update_telemetry(state)

        self.soc_plot.add_point(current_time, [state.soc])
        self.voltage_plot.add_point(current_time, [state.pack_voltage, state.charging_set_voltage])
        self.current_plot.add_point(current_time, [state.pack_current, state.charging_set_current])

        # Update charge duration while in CHARGING state (value = 2)
        if state.bms_status is not None and state.bms_status.value == 2:
            if self.charge_start_time is None:
                self.charge_start_time = current_time
            duration = current_time - self.charge_start_time
            self.charge_duration_plate.update_value(duration)
        else:
            self.charge_start_time = None
            self.charge_duration_plate.update_value(None)

    def inject_gap(self, timestamp):
        """Inserisce dei valori NaN per spezzare le linee temporali alla disconnessione."""
        self.soc_plot.add_point(timestamp, [np.nan])
        self.voltage_plot.add_point(timestamp, [np.nan])
        self.current_plot.add_point(timestamp, [np.nan])

    def clear_selection(self):
        for plot in (self.soc_plot, self.voltage_plot, self.current_plot):
            plot.clear_selection()
