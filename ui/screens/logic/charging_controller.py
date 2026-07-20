"""Business logic for the Charging screen: command dispatch, FSM state
tracking (sent / waiting for confirmation / timed out) and derived button
state. Kept separate from ChargingScreen so the screen module stays limited
to layout and widget wiring.
"""

from enum import Enum, auto
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from data.sender.bms_command_sender import AbstractBmsCommandSender
from data.generators.state import BmsTelemetryState
from ui.strings import Strings


START_TIMEOUT_MS    = 5000
STOP_TIMEOUT_MS     = 2000
SETTINGS_TIMEOUT_MS = 3000

SETTINGS_MATCH_TOLERANCE = 0.01

class ChargingState(Enum):
    NO_CHR = auto()
    SEND_START = auto()
    WAIT_START = auto()
    CHR = auto()
    SEND_STOP = auto()
    WAIT_STOP = auto()

class SettingsState(Enum):
    IDLE = auto()
    SENDING = auto()

class StartStopController(QObject):
    # UI button state
    button_state_changed = pyqtSignal(str, bool, str) # (label, is_enabled, color_string)
    busy_changed = pyqtSignal(str, bool)              # (kind, busy) kind in {"start", "stop"}

    # UI text feedback
    feedback_changed = pyqtSignal(str, bool) # (text, is_success)

    # UI state mapping
    STATE_MAP = {               # (is_enabled,  label,                      color_string,   is_start)
        ChargingState.NO_CHR:     (True,        Strings.BTN_START_CHARGING, "green",        True),
        ChargingState.SEND_START: (False,       "Sending start...",         "gray",         None),
        ChargingState.WAIT_START: (True,        Strings.BTN_STOP_CHARGING,  "yellow",       False),
        ChargingState.CHR:        (True,        Strings.BTN_STOP_CHARGING,  "red",          False),
        ChargingState.SEND_STOP:  (False,       "Sending stop...",          "gray",         None),
        ChargingState.WAIT_STOP:  (False,       "Stopping...",              "gray",         None),
    }

    def __init__(self, command_sender: AbstractBmsCommandSender, parent=None):
        super().__init__(parent)
        self.command_sender = command_sender
        self.is_button_start: Optional[bool] = True

        # FSM state
        self._button_state = ChargingState.NO_CHR
        self._last_telemetry = None
        self._last_send_error = None

        # Timeout timer
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)

        # Signal wiring
        self.command_sender.error_occurred.connect(self._on_send_error)

    def force_sync(self):
        self._update_button_ui_state()

    def handle_click(self):
        if self._button_state == ChargingState.NO_CHR:
            self._request_start()
        elif self._button_state in (ChargingState.WAIT_START, ChargingState.CHR):
            self._request_stop()

    def _request_start(self):
        self._last_send_error = None
        self._change_state(ChargingState.SEND_START)

        if not self.command_sender.send_charging_start():
            self._handle_timeout_or_error(is_error=True)
            return

        self.busy_changed.emit("start", True)
        self._timer.start(START_TIMEOUT_MS)

    def _request_stop(self):
        self._last_send_error = None
        self._change_state(ChargingState.SEND_STOP)

        if not self.command_sender.send_charging_stop():
            self._handle_timeout_or_error(is_error=True)
            return

        self.busy_changed.emit("stop", True)
        self._timer.start(STOP_TIMEOUT_MS)

    def on_telemetry(self, state: BmsTelemetryState):
        self._last_telemetry = state

        # FSM continues sync state with BMS state
        if getattr(state, 'is_charging_starting', False):
            target_state = ChargingState.WAIT_START
        elif getattr(state, 'is_charging_active', False):
            target_state = ChargingState.CHR
        elif getattr(state, 'is_charging_stopping', False):
            target_state = ChargingState.WAIT_STOP
        else:
            target_state = ChargingState.NO_CHR

        # Handle completed tasks state transitions
        if self._button_state == ChargingState.SEND_START:
            if target_state in (ChargingState.WAIT_START, ChargingState.CHR):
                self._timer.stop()
                self.busy_changed.emit("start", False)
                self._change_state(target_state)
        elif self._button_state == ChargingState.SEND_STOP:
            if target_state in (ChargingState.WAIT_STOP, ChargingState.NO_CHR):
                self._timer.stop()
                self.busy_changed.emit("stop", False)
                self._change_state(target_state)
        else:
            # Set state directly for async BMS state update
            self._change_state(target_state)

    def _change_state(self, new_state: ChargingState):
        if self._button_state == new_state:
            return
        self._button_state = new_state
        self._update_button_ui_state()

    def _update_button_ui_state(self):
        is_enabled, label, color_string, is_start = StartStopController.STATE_MAP.get(
            self._button_state, StartStopController.STATE_MAP[ChargingState.NO_CHR]
        )
        self.is_button_start = is_start
        self.button_state_changed.emit(label, is_enabled, color_string)

    def _on_timeout(self):
        self._handle_timeout_or_error(is_error=False)

    def _handle_timeout_or_error(self, is_error=False):
        self._timer.stop()
        if self._button_state == ChargingState.SEND_START:
            self._change_state(ChargingState.NO_CHR)
            self.busy_changed.emit("start", False)
            self._emit_feedback(Strings.MSG_SEND_FAILED if is_error else Strings.MSG_NO_RESPONSE, False, is_error)
        elif self._button_state == ChargingState.SEND_STOP:
            self.busy_changed.emit("stop", False)
            # Fallback based on last telemetry
            if self._last_telemetry and getattr(self._last_telemetry, 'is_charging_starting', False):
                self._change_state(ChargingState.WAIT_START)
            elif self._last_telemetry and getattr(self._last_telemetry, 'is_charging_active', False):
                self._change_state(ChargingState.CHR)
            else:
                self._change_state(ChargingState.NO_CHR)
            self._emit_feedback(Strings.MSG_SEND_FAILED if is_error else Strings.MSG_NO_RESPONSE, False, is_error)

    def _on_send_error(self, message):
        self._last_send_error = message

    def _emit_feedback(self, base_text, is_success, include_error=False):
        text = f"{base_text}: {self._last_send_error}" if include_error and self._last_send_error else base_text
        self.feedback_changed.emit(text, is_success)

class SettingsController(QObject):
    # UI button state
    button_state_changed = pyqtSignal(str, bool, str) # (label, is_enabled, color_string)
    busy_changed = pyqtSignal(str, bool)              # (kind, busy) kind in {"settings"}

    # UI text feedback
    feedback_changed = pyqtSignal(str, bool) # (text, is_success)

    # UI state mapping
    STATE_MAP = {            # (is_enabled, label,                          color_string)
        SettingsState.IDLE:    (True,       Strings.BTN_SETTINGS_SUBMIT,    "blue"),
        SettingsState.SENDING: (False,      Strings.BTN_WAITING_SETTINGS,   "gray")
    }

    def __init__(self, command_sender: AbstractBmsCommandSender, parent=None):
        super().__init__(parent)
        self.command_sender = command_sender

        # FSM state
        self._button_state = SettingsState.IDLE
        self._last_send_error = None

        # Timeout timer
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)

        # Signal wiring
        self.command_sender.error_occurred.connect(self._on_send_error)

    def force_sync(self):
        self._update_button_ui_state()

    def handle_click(self, voltage, current):
        if self._button_state != SettingsState.IDLE:
            return

        self._last_send_error = None
        self._change_state(SettingsState.SENDING)

        if not self.command_sender.send_charging_settings(voltage, current):
            self._handle_timeout_or_error(is_error=True)
            return

        self.busy_changed.emit("settings", True)
        self.feedback_changed.emit(Strings.MSG_WAITING_RESPONSE, True)
        self._timer.start(SETTINGS_TIMEOUT_MS)

    def on_telemetry(self, state: BmsTelemetryState):
        charging_settings_ack = state.charging_settings_ack
        if self._button_state == SettingsState.SENDING and charging_settings_ack is not None:
            self._timer.stop()
            self._change_state(SettingsState.IDLE)
            self.busy_changed.emit("settings", False)
            self._emit_feedback(Strings.MSG_SETTINGS_APPLIED if charging_settings_ack else Strings.MSG_SETTINGS_REGECTED, charging_settings_ack)

    def _change_state(self, new_state: SettingsState):
        if self._button_state == new_state:
            return
        self._button_state = new_state
        self._update_button_ui_state()

    def _update_button_ui_state(self):
        is_enabled, label, color_string = SettingsController.STATE_MAP.get(
            self._button_state, SettingsController.STATE_MAP[SettingsState.IDLE]
        )
        self.button_state_changed.emit(label, is_enabled, color_string)

    def _on_timeout(self):
        self._handle_timeout_or_error(is_error=False)

    def _handle_timeout_or_error(self, is_error=False):
        self._timer.stop()
        self._change_state(SettingsState.IDLE)
        self.busy_changed.emit("settings", False)
        self._emit_feedback(Strings.MSG_SEND_FAILED if is_error else Strings.MSG_NO_RESPONSE, False, is_error)

    def _on_send_error(self, message):
        self._last_send_error = message

    def _emit_feedback(self, base_text, is_success, include_error=False):
        text = f"{base_text}: {self._last_send_error}" if include_error and self._last_send_error else base_text
        self.feedback_changed.emit(text, is_success)


class ChargingController(QObject):
    # UI button state
    charging_button_state_changed = pyqtSignal(str, bool, str) # (label, is_enabled, color_string)
    settings_button_state_changed = pyqtSignal(str, bool, str) # (label, is_enabled, color_string)
    busy_changed = pyqtSignal(str, bool)                       # (kind, busy) kind in {"start", "stop", "settings"}

    # UI text feedback
    feedback_changed = pyqtSignal(str, bool) # (text, is_success)

    def __init__(self, command_sender: AbstractBmsCommandSender, parent=None):
        super().__init__(parent)

        # Sub-controller instantiation
        self.start_stop_controller = StartStopController(command_sender, self)
        self.settings_controller = SettingsController(command_sender, self)

        # Signal wiring
        self.start_stop_controller.button_state_changed.connect(self.charging_button_state_changed)
        self.start_stop_controller.busy_changed.connect(self.busy_changed)
        self.start_stop_controller.feedback_changed.connect(self.feedback_changed)

        self.settings_controller.button_state_changed.connect(self.settings_button_state_changed)
        self.settings_controller.busy_changed.connect(self.busy_changed)
        self.settings_controller.feedback_changed.connect(self.feedback_changed)

    @property
    def is_button_start(self):
        return self.start_stop_controller.is_button_start

    def force_sync(self):
        """Forces the emission of the current UI state to synchronize the view after the widgets have been created and wired."""
        self.start_stop_controller.force_sync()
        self.settings_controller.force_sync()

    def handle_charging_button_click(self):
        self.start_stop_controller.handle_click()

    def handle_settings_button_click(self, voltage, current):
        self.settings_controller.handle_click(voltage, current)

    def on_telemetry(self, state: BmsTelemetryState):
        self.start_stop_controller.on_telemetry(state)
        self.settings_controller.on_telemetry(state)
