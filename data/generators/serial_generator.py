import time
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from data.extif_reader import ExtifUartReader
from data.proto import messages_pb2
from data.hardware.hardware_mapping import get_voltage_cell_mapping, get_temperature_sensor_mapping


class SerialDataGenerator(QObject):
    telemetry_received = pyqtSignal(messages_pb2.BmsTelemetry) # pyright: ignore[reportAttributeAccessIssue]

    def __init__(self, port="/dev/ttyUSB0", baudrate=115200, volt_count=138, temp_count=175):
        super().__init__()
        self.volt_count = volt_count
        self.temp_count = temp_count

        self.start_time = time.time()

        self.reader = ExtifUartReader(port, baudrate)
        self.reader.telemetry_received.connect(self.on_telemetry_received)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)

        self.current_volts = np.zeros(self.volt_count, dtype=np.float64)
        self.current_temps = np.zeros(self.temp_count, dtype=np.float64)

        self.volt_mapping = get_voltage_cell_mapping()
        self.temp_mapping = get_temperature_sensor_mapping()

        self._latest_telemetry = messages_pb2.BmsTelemetry() # pyright: ignore[reportAttributeAccessIssue]

    def start(self, interval_ms=100):
        self.reader.start()
        self.timer.start(interval_ms)

    def stop(self):
        self.timer.stop()
        self.reader.stop()

    def on_telemetry_received(self, telemetry):
        if telemetry.HasField("cell_voltages"):
            device_idx = telemetry.cell_voltages.device_idx
            for i, v in enumerate(telemetry.cell_voltages.voltages):
                idx = self.volt_mapping.flat_index(device_idx, i)
                if idx is not None:
                    self.current_volts[idx] = v

        if telemetry.HasField("cell_temperatures"):
            device_idx = telemetry.cell_temperatures.device_idx
            for i, t in enumerate(telemetry.cell_temperatures.temperatures):
                idx = self.temp_mapping.flat_index(device_idx, i)
                if idx is not None:
                    self.current_temps[idx] = t

        # Accumulate non-slice fields into the latest telemetry snapshot
        if telemetry.HasField("status"):
            self._latest_telemetry.status.CopyFrom(telemetry.status)

        if telemetry.HasField("pack_state"):
            self._latest_telemetry.pack_state.CopyFrom(telemetry.pack_state)

        if telemetry.HasField("contactors"):
            self._latest_telemetry.contactors.CopyFrom(telemetry.contactors)

        if telemetry.HasField("charging"):
            self._latest_telemetry.charging.CopyFrom(telemetry.charging)

        if telemetry.HasField("balancing"):
            self._latest_telemetry.balancing.CopyFrom(telemetry.balancing)

        if telemetry.HasField("diagnostics"):
            self._latest_telemetry.diagnostics.CopyFrom(telemetry.diagnostics)

    def update(self):
        # Build accumulated snapshot
        snapshot = messages_pb2.BmsTelemetry() # pyright: ignore[reportAttributeAccessIssue]
        snapshot.CopyFrom(self._latest_telemetry)

        if not snapshot.HasField("cell_voltages"):
            snapshot.cell_voltages.device_idx = 0
            snapshot.cell_voltages.voltages.extend(self.current_volts.tolist())

        if not snapshot.HasField("cell_temperatures"):
            snapshot.cell_temperatures.device_idx = 0
            snapshot.cell_temperatures.temperatures.extend(self.current_temps.tolist())

        self.telemetry_received.emit(snapshot)
