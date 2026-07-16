import logging
import serial
from PyQt6.QtCore import QObject, pyqtSignal
from cobs import cobs

from data.extif_reader import extif_calculate_crc16
from data.proto import messages_pb2


class BmsCommandSender(QObject):
    command_sent = pyqtSignal(str, bool)
    error_occurred = pyqtSignal(str)

    def __init__(self, port="/dev/ttyUSB0", baudrate=115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self._serial = None

    def _open(self):
        if self._serial is None or not self._serial.is_open:
            try:
                self._serial = serial.Serial(self.port, self.baudrate, timeout=0.1)
            except Exception as e:
                self.error_occurred.emit(f"Failed to open serial port: {e}")
                return False
        return True

    def _close(self):
        if self._serial and self._serial.is_open:
            self._serial.close()
            self._serial = None

    def _send_protobuf(self, payload_bytes, command_name):
        if not self._open():
            return False

        try:
            crc = extif_calculate_crc16(payload_bytes)
            frame = bytearray(payload_bytes)
            frame.append((crc >> 8) & 0xFF)
            frame.append(crc & 0xFF)

            encoded = cobs.encode(bytes(frame))
            encoded.append(0x00) # pyright: ignore[reportAttributeAccessIssue]

            self._serial.write(encoded) # pyright: ignore[reportOptionalMemberAccess]
            self.command_sent.emit(command_name, True)
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to send {command_name}: {e}")
            return False

    def send_charging_start(self, voltage, current):
        #TODO: Configurare messaggio di invio dei comandi
        charging = messages_pb2.ChargingSettings() # pyright: ignore[reportAttributeAccessIssue]
        charging.set_voltage = float(voltage)
        charging.set_current = float(current)
        payload = charging.SerializeToString()
        return self._send_protobuf(payload, "charging_start")

    def send_charging_stop(self):
        #TODO: Configurare messaggio di invio dei comandi
        empty = messages_pb2.BmsTelemetry() # pyright: ignore[reportAttributeAccessIssue]
        payload = empty.SerializeToString()
        return self._send_protobuf(payload, "charging_stop")

    def send_charging_settings(self, voltage, current):
        #TODO: Configurare messaggio di invio dei comandi
        charging = messages_pb2.ChargingSettings() # pyright: ignore[reportAttributeAccessIssue]
        charging.set_voltage = float(voltage)
        charging.set_current = float(current)
        payload = charging.SerializeToString()
        return self._send_protobuf(payload, "charging_settings")


class MockBmsCommandSender(QObject):
    command_sent = pyqtSignal(str, bool)
    error_occurred = pyqtSignal(str)

    def send_charging_start(self, voltage, current):
        logging.info(f"[MOCK] charging_start: voltage={voltage}, current={current}")
        self.command_sent.emit("charging_start", True)

    def send_charging_stop(self):
        logging.info("[MOCK] charging_stop")
        self.command_sent.emit("charging_stop", True)

    def send_charging_settings(self, voltage, current):
        logging.info(f"[MOCK] charging_settings: voltage={voltage}, current={current}")
        self.command_sent.emit("charging_settings", True)
