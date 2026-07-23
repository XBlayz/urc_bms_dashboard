from PyQt6.QtCore import QObject, pyqtSignal


class AbstractBmsCommandSender(QObject):
    """
    Abstract base class for BMS command senders.
    Defines the interface and signals for all concrete implementations.
    """
    command_sent = pyqtSignal(str, bool)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def send_charging_start(self) -> bool:
        raise NotImplementedError("Subclasses must implement send_charging_start")

    def send_charging_stop(self) -> bool:
        raise NotImplementedError("Subclasses must implement send_charging_stop")

    def send_charging_settings(self, voltage: float, current: float) -> bool:
        raise NotImplementedError("Subclasses must implement send_charging_settings")

    def send_initial_state_request(self) -> bool:
        raise NotImplementedError("Subclasses must implement send_initial_state_request")

    def send_override_start(self) -> bool:
        raise NotImplementedError("Subclasses must implement send_override_start")

    def send_override_stop(self) -> bool:
        raise NotImplementedError("Subclasses must implement send_override_stop")

    #TODO: Da rivedere
    def send_actuator_override(self, actuator: str, mode: int) -> bool:
        """`actuator` is one of 'air_pos'/'air_neg'/'pre_charge'/'sdc'; `mode` is
        ACTUATOR_MODE_AUTO/FORCE_OFF/FORCE_ON (see ui.screens.logic.override_controller)."""
        raise NotImplementedError("Subclasses must implement send_actuator_override")
