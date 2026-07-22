from cobs import cobs
from data.sender.bms_command_sender import AbstractBmsCommandSender
from data.extif_reader import extif_calculate_crc16, ExtifUartReader
from data.proto import messages_pb2

class SerialBmsCommandSender(AbstractBmsCommandSender):
    """
    Concrete implementation of AbstractBmsCommandSender using a shared ExtifUartReader,
    Protobuf serialization, and COBS encoding.
    """
    def __init__(self, extif_reader: ExtifUartReader, parent=None):
        super().__init__(parent)
        self._extif_reader = extif_reader

    def _send_protobuf(self, payload_bytes: bytes, command_name: str) -> bool:
        try:
            # Calculate CRC and append it to the payload
            crc = extif_calculate_crc16(payload_bytes)
            frame = bytearray(payload_bytes)
            frame.append((crc >> 8) & 0xFF)
            frame.append(crc & 0xFF)

            # Encode payload using COBS and append the 0x00 delimiter
            encoded = bytearray(cobs.encode(bytes(frame)))
            encoded.append(0x00)

            # Delegate transmission to the shared reader instance
            success = self._extif_reader.write_data(bytes(encoded))

            if success:
                self.command_sent.emit(command_name, True)
            else:
                self.error_occurred.emit(f"Failed to send {command_name}: Shared serial port closed or error.")

            return success

        except Exception as e:
            self.error_occurred.emit(f"Failed to send {command_name}: {e}")
            return False

    def send_charging_start(self) -> bool:
        telemetry = messages_pb2.BmsTelemetry() # pyright: ignore[reportAttributeAccessIssue]
        telemetry.charging_start.SetInParent()
        payload = telemetry.SerializeToString()
        return self._send_protobuf(payload, "charging_start")

    def send_charging_stop(self) -> bool:
        telemetry = messages_pb2.BmsTelemetry() # pyright: ignore[reportAttributeAccessIssue]
        telemetry.charging_stop.SetInParent()
        payload = telemetry.SerializeToString()
        return self._send_protobuf(payload, "charging_stop")

    def send_charging_settings(self, voltage: float, current: float) -> bool:
        telemetry = messages_pb2.BmsTelemetry() # pyright: ignore[reportAttributeAccessIssue]
        telemetry.charging.set_voltage = float(voltage)
        telemetry.charging.set_current = float(current)
        payload = telemetry.SerializeToString()
        return self._send_protobuf(payload, "charging_settings")

    def send_initial_state_request(self) -> bool:
        telemetry = messages_pb2.BmsTelemetry() # pyright: ignore[reportAttributeAccessIssue]
        telemetry.initial_state_request.SetInParent()
        payload = telemetry.SerializeToString()
        return self._send_protobuf(payload, "initial_state_request")