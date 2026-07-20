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
