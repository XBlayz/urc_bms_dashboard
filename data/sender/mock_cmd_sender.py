import logging

from data.sender.bms_command_sender import AbstractBmsCommandSender


class MockBmsCommandSender(AbstractBmsCommandSender):
    """
    Concrete implementation of AbstractBmsCommandSender for testing purposes.
    Logs commands instead of sending them over a physical interface.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    def send_charging_start(self) -> bool:
        logging.info("[MOCK SENDER] charging_start")
        self.command_sent.emit("charging_start", True)
        return True

    def send_charging_stop(self) -> bool:
        logging.info("[MOCK SENDER] charging_stop")
        self.command_sent.emit("charging_stop", True)
        return True

    def send_charging_settings(self, voltage: float, current: float) -> bool:
        logging.info(f"[MOCK SENDER] charging_settings: voltage={voltage}, current={current}")
        self.command_sent.emit("charging_settings", True)
        return True

    def send_initial_state_request(self) -> bool:
        logging.info(f"[MOCK SENDER] initial state request")
        self.command_sent.emit("initial_state_request", True)
        return True
