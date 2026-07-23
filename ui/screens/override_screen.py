import numpy as np
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy, QSlider
)
from PyQt6.QtCore import Qt, QTimer

from ui.screens.telemetry_screen import TelemetryScreen
from ui.widgets.plot_host_mixin import PlotHostMixin
from ui.screens.logic.override_controller import OverrideController
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme
from ui.fsm_state import fsm_state_labels
from ui.widgets.plot_widgets import SimpleTimeSeriesPlot, TimeSeriesPlotWidget, StackedBoolPlot
from ui.widgets.stacked_widget import CurrentPageStackedWidget
from ui.widgets.plates import EnumStatePlate, UnitPlate
from ui.widgets.percentage_bar import PercentageBar, ratio_status_color
from ui.widgets.relay_switch import RelaySwitch
from ui.widgets.responsive_grid import ResponsiveGrid
from ui.widgets.relay_circuit_diagram import RelayCircuitDiagram
from ui.screens.metrics_screen import DualVoltagesPlot
from ui.widgets.override_dialogs import GuardrailDialog, ForceConfirmDialog


MIN_THRESHOLD_PCT = 30
MAX_THRESHOLD_PCT = 95
DEFAULT_THRESHOLD_PCT = 85

# (field key in state.contactors, switch label)
RELAY_CONFIG = [
    ("sdc", Strings.STATE_SDC),
    ("air_pos", Strings.STATE_AIR_PLUS),
    ("air_neg", Strings.STATE_AIR_MINUS),
    ("pre_charge", Strings.STATE_PRECHARGE),
]

class FixedFeedbackLabel(QLabel):
    """QLabel with word-wrap but without heightForWidth propagation to ancestor layouts."""
    def hasHeightForWidth(self):
        return False

class OverrideScreen(TelemetryScreen, PlotHostMixin):
    FEEDBACK_CLEAR_DELAY_MS = 5000

    def __init__(self, command_sender, parent=None):
        super().__init__(parent)
        self.command_sender = command_sender
        self.controller = OverrideController(command_sender)
        self.controller.feedback_changed.connect(self._on_feedback_changed)
        self.controller.enable_button_state_changed.connect(self._on_enable_button_state_changed)
        self.controller.override_active_changed.connect(self._on_override_active_changed)
        self.controller.busy_changed.connect(self._on_busy_changed)

        self.feedback_clear_timer = QTimer(self)
        self.feedback_clear_timer.setSingleShot(True)
        self.feedback_clear_timer.timeout.connect(self._clear_feedback)

        self._threshold_pct = DEFAULT_THRESHOLD_PCT
        self._last_state = None
        self._override_active = False

        # Create UI
        self.init_ui()

        # Force initial sync for the controller
        self.controller.force_sync()

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

        self.override_state_plate = EnumStatePlate(Strings.LBL_OVERRIDE_STATE, fsm_state_labels())
        plates_layout.addWidget(self.override_state_plate)

        plates_layout.addSpacing(10)

        voltage_plates_row = QHBoxLayout()
        voltage_plates_row.setSpacing(2)
        self.pack_voltage_plate = UnitPlate(Strings.LBL_PACK_VOLTAGE_POST_AIR, unit="V")
        voltage_plates_row.addWidget(self.pack_voltage_plate, stretch=1)
        self.pack_voltage_post_air_plate = UnitPlate(Strings.LBL_PACK_VOLTAGE_POST_AIR, unit="V")
        voltage_plates_row.addWidget(self.pack_voltage_post_air_plate, stretch=1)
        plates_layout.addLayout(voltage_plates_row)

        self.ratio_bar = PercentageBar()
        plates_layout.addWidget(self.ratio_bar)

        self.ratio_plate = UnitPlate(Strings.LBL_VOLTAGE_RATIO, unit="%")
        plates_layout.addWidget(self.ratio_plate)

        self.pack_current_plate = UnitPlate(Strings.LBL_PACK_CURRENT, unit="A")
        plates_layout.addWidget(self.pack_current_plate)

        plates_layout.addStretch()
        top_row.addWidget(plates_panel, stretch=2)

        controls_panel = QWidget()
        controls_panel.setStyleSheet(Theme.charging_control())
        controls_panel.setMinimumWidth(280)
        controls_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        controls_layout = QVBoxLayout(controls_panel)
        controls_layout.setContentsMargins(7, 15, 15, 15)
        controls_layout.setSpacing(15)

        override_title = QLabel("OVERRIDE CONTROLS")
        override_title.setStyleSheet(Theme.plate_title())
        override_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(override_title)

        self.enable_btn = QPushButton(Strings.BTN_ENABLE_OVERRIDE)
        self.enable_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.enable_btn.clicked.connect(self.on_enable_clicked)
        controls_layout.addWidget(self.enable_btn)

        threshold_lbl = QLabel(Strings.LBL_VOLTAGE_THRESHOLD)
        threshold_lbl.setStyleSheet("color: #DDDDDD; font-size: 12px;")
        controls_layout.addWidget(threshold_lbl)

        threshold_row = QHBoxLayout()
        threshold_row.setSpacing(6)
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(MIN_THRESHOLD_PCT)
        self.threshold_slider.setMaximum(MAX_THRESHOLD_PCT)
        self.threshold_slider.setValue(DEFAULT_THRESHOLD_PCT)
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)
        threshold_row.addWidget(self.threshold_slider, stretch=1)

        self.threshold_value_lbl = QLabel(f"{DEFAULT_THRESHOLD_PCT}%")
        self.threshold_value_lbl.setStyleSheet("color: #FFFFFF; font-size: 12px; font-family: monospace;")
        self.threshold_value_lbl.setFixedWidth(40)
        threshold_row.addWidget(self.threshold_value_lbl)
        controls_layout.addLayout(threshold_row)

        self.feedback_lbl = FixedFeedbackLabel("")
        self.feedback_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_lbl.setWordWrap(True)
        controls_layout.addWidget(self.feedback_lbl)

        hint_lbl = FixedFeedbackLabel(Strings.MSG_OVERRIDE_DISABLED_HINT)
        hint_lbl.setWordWrap(True)
        hint_lbl.setStyleSheet("color: #888888; font-size: 11px;")
        controls_layout.addWidget(hint_lbl)

        controls_layout.addStretch()
        top_row.addWidget(controls_panel, stretch=1)

        layout.addLayout(top_row)

        # --- Row 2: Manual control panel ---
        manual_control_panel = QWidget()
        manual_control_panel.setStyleSheet(Theme.charging_control())
        manual_control_layout = QVBoxLayout(manual_control_panel)
        manual_control_layout.setContentsMargins(15, 12, 15, 12)
        manual_control_layout.setSpacing(10)

        manual_control_title = QLabel(Strings.TITLE_MANUAL_CONTROL)
        manual_control_title.setStyleSheet(Theme.plate_title())
        manual_control_layout.addWidget(manual_control_title)

        switches_row = QHBoxLayout()
        switches_row.setSpacing(10)

        self.relay_switches = {}
        for actuator, label in RELAY_CONFIG:
            switch = RelaySwitch(label)
            switch.sig_user_toggled.connect(lambda closed, a=actuator: self._on_switch_toggled(a, closed))
            self.relay_switches[actuator] = switch
            switches_row.addWidget(switch, stretch=1)

        manual_control_layout.addLayout(switches_row)

        layout.addWidget(manual_control_panel)

        # --- Row 3: Circuit panel ---
        circuit_panel = QWidget()
        circuit_panel.setStyleSheet(Theme.charging_control())
        circuit_layout = QVBoxLayout(circuit_panel)
        circuit_layout.setContentsMargins(15, 12, 15, 12)
        circuit_layout.setSpacing(10)

        title = QLabel(Strings.TITLE_CIRCUIT_DIAGRAM)
        title.setStyleSheet(Theme.plate_title())
        circuit_layout.addWidget(title)

        self.circuit_diagram = RelayCircuitDiagram()
        circuit_layout.addWidget(self.circuit_diagram)

        layout.addWidget(circuit_panel)

        # --- Plots, one per row, full width (Plot(Actuator), Plot(Voltage), Plot(Ratio), Plot(Current)) ---
        actuator_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)
        actuator_labels = [
            Strings.STATE_AIR_PLUS,
            Strings.STATE_AIR_MINUS,
            Strings.STATE_PRECHARGE,
            Strings.STATE_SDC,
        ]
        self.actuator_plot = StackedBoolPlot(
            title=Strings.TITLE_ACTUATOR_STATE,
            series_labels=actuator_labels,
            empty_text="No actuator data"
        )
        self.actuator_plot.setMinimumHeight(400)
        self.actuator_plot.setMinimumWidth(300)
        self.actuator_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.actuator_plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        actuator_row.add_item(self.actuator_plot)
        layout.addWidget(actuator_row, stretch=1)

        voltage_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)
        self.pack_voltage_plot = DualVoltagesPlot()
        self.pack_voltage_plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        self.pack_voltage_plot.setMinimumHeight(Theme.H_SIZE_S)
        voltage_row.add_item(self.pack_voltage_plot)
        layout.addWidget(voltage_row, stretch=1)

        ratio_raw = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)
        self.ratio_plot = self._build_history_plot_with_target(
            Strings.TITLE_VOLTAGE_RATIO_HISTORY, "%", ["Ratio", "Threshold"],
            "No ratio history", "#00AAFF"
        )
        self.ratio_plot.setMinimumHeight(Theme.H_SIZE_S)
        ratio_raw.add_item(self.ratio_plot)
        layout.addWidget(ratio_raw, stretch=1)

        current_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)
        self.current_plot = self._build_history_plot(
            Strings.LBL_CURRENT_HISTORY, "A", Strings.LBL_CHARGE_CURRENT, "No current history",
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
            empty_text=empty_text, colors=[color, "#EEEEEE"], dashed=[False, True]
        )
        plot.setMinimumHeight(200)
        plot.setMinimumWidth(300)
        plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        return plot

    # --- user actions ---

    def on_enable_clicked(self):
        self.controller.handle_enable_toggle()

    def _on_threshold_changed(self, value):
        self._threshold_pct = value
        self.threshold_value_lbl.setText(f"{value}%")
        self._refresh_ratio_display(self.controller.voltage_ratio_pct())

    def _on_switch_toggled(self, actuator, desired_closed):
        if not self._override_active:
            return

        if not desired_closed:
            self.controller.request_actuator_open(actuator)
            return

        needs_guardrail = self.controller.request_actuator_close(actuator, self._threshold_pct)
        if needs_guardrail:
            self._show_guardrail_dialog(actuator)

    def _show_guardrail_dialog(self, actuator):
        dialog = GuardrailDialog(self.controller.voltage_ratio_pct(), self._threshold_pct, parent=self)
        dialog.exec()
        if dialog.choice == GuardrailDialog.PRE_CHARGE:
            self.controller.resolve_guardrail_precharge(actuator)
        elif dialog.choice == GuardrailDialog.FORCE:
            self._show_force_confirm(actuator)
        # CANCEL: no-op, the switch keeps reflecting the real (unchanged) state.

    def _show_force_confirm(self, actuator):
        dialog = ForceConfirmDialog(parent=self)
        dialog.exec()
        if dialog.confirmed:
            self.controller.resolve_guardrail_force(actuator)

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

    def _on_enable_button_state_changed(self, label, is_active, color_string):
        self.enable_btn.setText(label)
        self.enable_btn.setStyleSheet(Theme.charging_button(is_active, color_string))

    def _on_busy_changed(self, busy):
        self.enable_btn.setEnabled(not busy)

    def _on_override_active_changed(self, active):
        self._override_active = active
        for switch in self.relay_switches.values():
            switch.set_control_enabled(active)

    def _refresh_ratio_display(self, ratio):
        self.ratio_bar.set_values(ratio, self._threshold_pct)
        self.ratio_plate.update_value(f"{ratio:.1f}")
        color = ratio_status_color(ratio, self._threshold_pct)
        self.ratio_plate.value_lbl.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; font-family: monospace;")

    # --- telemetry ---

    def add_point(self, current_time, state):
        self._last_state = state
        self.controller.on_telemetry(state)

        if state.bms_status is not None:
            self.override_state_plate.update_value(state.bms_status.value)

        self.pack_voltage_plate.update_value(f"{state.pack_voltage:.1f}")
        self.pack_voltage_post_air_plate.update_value(f"{state.post_air_voltage:.1f}")
        self.pack_current_plate.update_value(f"{state.pack_current:.1f}")

        ratio = self.controller.voltage_ratio_pct()
        self._refresh_ratio_display(ratio)

        for actuator, switch in self.relay_switches.items():
            switch.set_actual_state(state.contactors.get(actuator, False))

        self.circuit_diagram.update_values(state.contactors, state.pack_voltage, state.post_air_voltage, state.pack_current)

        self.pack_voltage_plot.add_point(current_time, [state.pack_voltage, state.post_air_voltage])
        self.current_plot.add_point(current_time, [state.pack_current])
        self.ratio_plot.add_point(current_time, [ratio, self._threshold_pct])

        c = state.contactors
        self.actuator_plot.add_point(current_time, [
            int(c["air_pos"]), int(c["air_neg"]), int(c["pre_charge"]), int(c["sdc"])
        ])

    def inject_gap(self, timestamp):
        """Inserisce dei valori NaN per spezzare le linee temporali alla disconnessione."""
        self.pack_voltage_plot.add_point(timestamp, [np.nan, np.nan])
        self.current_plot.add_point(timestamp, [np.nan])
        self.ratio_plot.add_point(timestamp, [np.nan])
        self.actuator_plot.add_point(timestamp, [np.nan, np.nan, np.nan, np.nan])

    def clear_selection(self):
        for plot in (self.pack_voltage_plot, self.current_plot, self.ratio_plot, self.actuator_plot):
            plot.clear_selection()
