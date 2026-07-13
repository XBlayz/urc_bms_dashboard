import time
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from data.extif_reader import ExtifUartReader
from data.hardware_mapping import get_voltage_cell_mapping, get_temperature_sensor_mapping

class SerialDataGenerator(QObject):
    voltages_updated = pyqtSignal(float, np.ndarray)
    temperatures_updated = pyqtSignal(float, np.ndarray)
    
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200, volt_count=138, temp_count=175):
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
                try:
                    idx = self.volt_mapping.index((device_idx, i))
                    self.current_volts[idx] = v
                except ValueError:
                    pass
        elif telemetry.HasField("cell_temperatures"):
            device_idx = telemetry.cell_temperatures.device_idx
            for i, t in enumerate(telemetry.cell_temperatures.temperatures):
                try:
                    idx = self.temp_mapping.index((device_idx, i))
                    self.current_temps[idx] = t
                except ValueError:
                    pass

    def update(self):
        current_time = time.time() - self.start_time
        self.voltages_updated.emit(current_time, self.current_volts)
        self.temperatures_updated.emit(current_time, self.current_temps)
