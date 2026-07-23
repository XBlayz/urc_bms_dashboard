"""Business logic for the Override screen: enable/disable command dispatch with
FSM-state ack tracking (mirrors ChargingController's StartStopController, using
BmsStatus == OVERRIDE as the ack instead of a dedicated flag), plus actuator
command dispatch and the relay-closure voltage guardrail sequencing. Kept
separate from OverrideScreen so the screen module stays limited to layout and
widget wiring.
"""

from enum import Enum, auto
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from data.sender.bms_command_sender import AbstractBmsCommandSender
from data.generators.state import BmsTelemetryState
from ui.strings import Strings


ENABLE_TIMEOUT_MS = 3000
DISABLE_TIMEOUT_MS = 2000

# Mirrors the wire-level ActuatorOverrideMode enum (data/proto/messages.proto)
# without coupling the controller to the protobuf module.
ACTUATOR_MODE_AUTO = 0
ACTUATOR_MODE_FORCE_OFF = 1
ACTUATOR_MODE_FORCE_ON = 2

# The three main relays that must never all be simultaneously closed unless
# the post-AIR/pack voltage ratio guardrail is satisfied.
MAIN_RELAYS = ("sdc", "air_pos", "air_neg")

RELAY_SEQUENCE_STEP_MS = 400


class OverrideState(Enum):
    DISABLED = auto()
    SEND_ENABLE = auto()
    ENABLED = auto()
    SEND_DISABLE = auto()


class OverrideEnableController(QObject):
    # UI button state
    button_state_changed = pyqtSignal(str, bool, str) # (label, is_enabled, color_string)
    busy_changed = pyqtSignal(bool)

    # UI text feedback (transmission errors/timeouts only)
    feedback_changed = pyqtSignal(str, bool) # (text, is_success)

    # Notifies the screen so it can enable/disable the actuator switches.
    active_changed = pyqtSignal(bool)

    STATE_MAP = {                        # (is_enabled, label,                          color_string)
        OverrideState.DISABLED:     (True,  Strings.BTN_ENABLE_OVERRIDE,  "green"),
        OverrideState.SEND_ENABLE:  (False, "Sending enable...",          "gray"),
        OverrideState.ENABLED:      (True,  Strings.BTN_DISABLE_OVERRIDE, "red"),
        OverrideState.SEND_DISABLE: (False, "Sending disable...",         "gray"),
    }

    def __init__(self, command_sender: AbstractBmsCommandSender, parent=None):
        super().__init__(parent)
        self.command_sender = command_sender

        self._state = OverrideState.DISABLED
        self._last_send_error = None

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)

        self.command_sender.error_occurred.connect(self._on_send_error)

    def force_sync(self):
        self._update_button_ui_state()

    @property
    def is_active(self) -> bool:
        return self._state == OverrideState.ENABLED

    def handle_click(self):
        if self._state == OverrideState.DISABLED:
            self._request_enable()
        elif self._state == OverrideState.ENABLED:
            self._request_disable()

    def _request_enable(self):
        self._last_send_error = None
        self._change_state(OverrideState.SEND_ENABLE)

        if not self.command_sender.send_override_start():
            self._handle_timeout_or_error(is_error=True)
            return

        self.busy_changed.emit(True)
        self._timer.start(ENABLE_TIMEOUT_MS)

    def _request_disable(self):
        self._last_send_error = None
        self._change_state(OverrideState.SEND_DISABLE)

        if not self.command_sender.send_override_stop():
            self._handle_timeout_or_error(is_error=True)
            return

        self.busy_changed.emit(True)
        self._timer.start(DISABLE_TIMEOUT_MS)

    def on_telemetry(self, state: BmsTelemetryState):
        target_state = OverrideState.ENABLED if state.is_override_active else OverrideState.DISABLED

        if self._state == OverrideState.SEND_ENABLE:
            if target_state == OverrideState.ENABLED:
                self._timer.stop()
                self.busy_changed.emit(False)
                self._change_state(OverrideState.ENABLED)
        elif self._state == OverrideState.SEND_DISABLE:
            if target_state == OverrideState.DISABLED:
                self._timer.stop()
                self.busy_changed.emit(False)
                self._change_state(OverrideState.DISABLED)
        else:
            # Keep synced with async FSM changes (e.g. firmware-side fault exit).
            self._change_state(target_state)

    def _change_state(self, new_state: OverrideState):
        if self._state == new_state:
            return
        was_active = self.is_active
        self._state = new_state
        self._update_button_ui_state()
        if self.is_active != was_active:
            self.active_changed.emit(self.is_active)

    def _update_button_ui_state(self):
        is_enabled, label, color_string = self.STATE_MAP.get(
            self._state, self.STATE_MAP[OverrideState.DISABLED]
        )
        self.button_state_changed.emit(label, is_enabled, color_string)

    def _on_timeout(self):
        self._handle_timeout_or_error(is_error=False)

    def _handle_timeout_or_error(self, is_error=False):
        self._timer.stop()
        if self._state == OverrideState.SEND_ENABLE:
            self._change_state(OverrideState.DISABLED)
            self.busy_changed.emit(False)
            self._emit_feedback(Strings.MSG_SEND_FAILED if is_error else Strings.MSG_NO_RESPONSE, False, is_error)
        elif self._state == OverrideState.SEND_DISABLE:
            self._change_state(OverrideState.ENABLED)
            self.busy_changed.emit(False)
            self._emit_feedback(Strings.MSG_SEND_FAILED if is_error else Strings.MSG_NO_RESPONSE, False, is_error)

    def _on_send_error(self, message):
        self._last_send_error = message

    def _emit_feedback(self, base_text, is_success, include_error=False):
        text = f"{base_text}: {self._last_send_error}" if include_error and self._last_send_error else base_text
        self.feedback_changed.emit(text, is_success)


class OverrideController(QObject):
    # UI button state
    enable_button_state_changed = pyqtSignal(str, bool, str)
    busy_changed = pyqtSignal(bool)
    override_active_changed = pyqtSignal(bool)

    # UI text feedback: transmission errors only, per spec (actuator confirmations
    # are reflected by the relay switches themselves, driven by telemetry).
    feedback_changed = pyqtSignal(str, bool)

    def __init__(self, command_sender: AbstractBmsCommandSender, parent=None):
        super().__init__(parent)
        self.command_sender = command_sender

        self.enable_controller = OverrideEnableController(command_sender, self)
        self.enable_controller.button_state_changed.connect(self.enable_button_state_changed)
        self.enable_controller.busy_changed.connect(self.busy_changed)
        self.enable_controller.feedback_changed.connect(self.feedback_changed)
        self.enable_controller.active_changed.connect(self.override_active_changed)

        self.command_sender.error_occurred.connect(self._on_transmit_error)

        self._last_state: Optional[BmsTelemetryState] = None

        self._sequence_steps: list[tuple[str, int]] = []
        self._sequence_timer = QTimer(self)
        self._sequence_timer.setSingleShot(True)
        self._sequence_timer.timeout.connect(self._run_next_sequence_step)

    def force_sync(self):
        self.enable_controller.force_sync()

    def on_telemetry(self, state: BmsTelemetryState):
        self._last_state = state
        self.enable_controller.on_telemetry(state)

    def handle_enable_toggle(self):
        self.enable_controller.handle_click()

    # --- actuator dispatch / guardrail ---

    def voltage_ratio_pct(self) -> float:
        if self._last_state is None or self._last_state.pack_voltage <= 0:
            return 0.0
        return (self._last_state.post_air_voltage / self._last_state.pack_voltage) * 100.0

    def request_actuator_open(self, actuator: str):
        self._send_actuator(actuator, ACTUATOR_MODE_FORCE_OFF)

    def request_actuator_close(self, actuator: str, threshold_pct: float) -> bool:
        """Attempts to close `actuator`. Returns True if the guardrail popup must
        be shown by the screen (main relay closure would leave all three main
        relays closed below the voltage threshold); False if already dispatched."""
        if actuator == "pre_charge":
            self._send_actuator(actuator, ACTUATOR_MODE_FORCE_ON)
            return False

        if actuator not in MAIN_RELAYS:
            self._send_actuator(actuator, ACTUATOR_MODE_FORCE_ON)
            return False

        resulting_closed = {r: (True if r == actuator else self._current_relay_state(r)) for r in MAIN_RELAYS}
        if not all(resulting_closed.values()):
            self._send_actuator(actuator, ACTUATOR_MODE_FORCE_ON)
            return False

        if self.voltage_ratio_pct() >= threshold_pct:
            self._send_actuator(actuator, ACTUATOR_MODE_FORCE_ON)
            return False

        return True

    def resolve_guardrail_precharge(self, original_actuator: str):
        if original_actuator == "air_neg":
            self._enqueue_sequence([("pre_charge", ACTUATOR_MODE_FORCE_ON)])
            return

        # Open everything first, then re-close SDC -> AIR+ -> Pre-Charge in order,
        # leaving AIR- open (standard precharge sequence).
        self._enqueue_sequence([
            ("sdc", ACTUATOR_MODE_FORCE_OFF),
            ("air_pos", ACTUATOR_MODE_FORCE_OFF),
            ("air_neg", ACTUATOR_MODE_FORCE_OFF),
            ("pre_charge", ACTUATOR_MODE_FORCE_OFF),
            ("sdc", ACTUATOR_MODE_FORCE_ON),
            ("air_pos", ACTUATOR_MODE_FORCE_ON),
            ("pre_charge", ACTUATOR_MODE_FORCE_ON),
        ])

    def resolve_guardrail_force(self, original_actuator: str):
        self._send_actuator(original_actuator, ACTUATOR_MODE_FORCE_ON)

    def _current_relay_state(self, actuator: str) -> bool:
        if self._last_state is None:
            return False
        return bool(self._last_state.contactors.get(actuator, False))

    def _send_actuator(self, actuator: str, mode: int):
        if not self.command_sender.send_actuator_override(actuator, mode):
            self.feedback_changed.emit(Strings.MSG_SEND_FAILED, False)

    def _enqueue_sequence(self, steps):
        self._sequence_steps = list(steps)
        self._run_next_sequence_step()

    def _run_next_sequence_step(self):
        if not self._sequence_steps:
            return
        actuator, mode = self._sequence_steps.pop(0)
        self._send_actuator(actuator, mode)
        if self._sequence_steps:
            self._sequence_timer.start(RELAY_SEQUENCE_STEP_MS)

    def _on_transmit_error(self, message):
        self.feedback_changed.emit(message, False)
