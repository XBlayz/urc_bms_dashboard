import logging
from PyQt6.QtCore import pyqtSignal
from data.sender.bms_command_sender import AbstractBmsCommandSender

class AdvancedMockBmsCommandSender(AbstractBmsCommandSender):
    """
    Concrete implementation of AbstractBmsCommandSender for testing purposes.
    Transmit signals to the AdvancedMockGenerator.
    """
    sig_charging_start_requested = pyqtSignal()
    sig_charging_stop_requested = pyqtSignal()
    sig_charging_settings_updated = pyqtSignal(float, float)
    sig_initial_state_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._is_connected = False

    def send_charging_start(self) -> bool:
        if not self._is_connected:
            return False

        logging.info("[ADV-MOCK SENDER] Start charging requested...")
        self.sig_charging_start_requested.emit()
        self.command_sent.emit("charging_start", True) #? TODO: Perché c'è questo?
        return True

    def send_charging_stop(self) -> bool:
        if not self._is_connected:
            return False

        logging.info("[ADV-MOCK SENDER] Stop charging requested...")
        self.sig_charging_stop_requested.emit()
        self.command_sent.emit("charging_stop", True) #? TODO: Perché c'è questo?
        return True

    def send_charging_settings(self, voltage: float, current: float) -> bool:
        if not self._is_connected:
            return False

        logging.info(f"[ADV-MOCK SENDER] Charging settings: {voltage} V, {current} A")
        self.sig_charging_settings_updated.emit(voltage, current)
        self.command_sent.emit("charging_settings", True) #? TODO: Perché c'è questo?
        return True

    def on_connection_changed(self, is_connected: bool) -> None:
        self._is_connected = is_connected

    def send_initial_state_request(self) -> bool:
        if not self._is_connected:
            return False

        logging.info("[ADV-MOCK SENDER] Initiali state request...")
        self.sig_initial_state_requested.emit()
        self.command_sent.emit("initial_state_request", True) #? TODO: Perché c'è questo?
        return True
