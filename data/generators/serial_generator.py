import time

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from data.generators.state import BmsTelemetryState
from data.generators.telemetry import TelemetryFrame
from data.extif_reader import ExtifUartReader
from data.hardware.hardware_mapping import get_voltage_cell_mapping, get_temperature_sensor_mapping


class SerialDataGenerator(QObject):
    telemetry_frame_updated = pyqtSignal(TelemetryFrame)

    def __init__(self, port="/dev/ttyUSB0", baudrate=115200, volt_count=138, temp_count=175):
        super().__init__()
        self.start_time = time.time()

        self.reader = ExtifUartReader(port, baudrate)
        self.reader.telemetry_received.connect(self.on_telemetry_received)

        self.timer = QTimer()
        self.timer.timeout.connect(self.emit_state)

        # Retrieve hardware mappings
        volt_mapping = get_voltage_cell_mapping()
        temp_mapping = get_temperature_sensor_mapping()

        # Inject mappings and dimensions into the state object
        self.current_state = BmsTelemetryState(
            volt_count=volt_count,
            temp_count=temp_count,
            volt_mapping=volt_mapping,
            temp_mapping=temp_mapping
        )

    def start(self, interval_ms=100):
        self.reader.start()
        self.timer.start(interval_ms)

    def stop(self):
        self.timer.stop()
        self.reader.stop()

    def on_telemetry_received(self, telemetry):
        self.current_state.update(telemetry)

    def emit_state(self):
        current_time = time.time() - self.start_time

        frame = TelemetryFrame(
            timestamp=current_time,
            state=self.current_state
        )
        self.telemetry_frame_updated.emit(frame)
