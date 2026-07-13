import time
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

class MockDataGenerator(QObject):
    voltages_updated = pyqtSignal(float, np.ndarray)
    temperatures_updated = pyqtSignal(float, np.ndarray)
    
    def __init__(self, volt_count=138, temp_count=175):
        super().__init__()
        self.volt_count = volt_count
        self.temp_count = temp_count
        
        self.start_time = time.time()
        
        self.volt_bases = np.linspace(3.7, 4.1, self.volt_count)
        self.temp_bases = np.linspace(25.0, 45.0, self.temp_count)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        
    def start(self, interval_ms=100):
        self.timer.start(interval_ms)
        
    def stop(self):
        self.timer.stop()
        
    def update(self):
        current_time = time.time() - self.start_time
        
        # Volts
        volt_drift = np.sin(current_time * 0.1 + self.volt_bases) * 0.05
        current_volts = self.volt_bases + volt_drift + np.random.normal(0, 0.002, self.volt_count)
        self.voltages_updated.emit(current_time, current_volts)
        
        # Temps
        temp_drift = np.sin(current_time * 0.05 + self.temp_bases) * 2.0
        current_temps = self.temp_bases + temp_drift + np.random.normal(0, 0.05, self.temp_count)
        self.temperatures_updated.emit(current_time, current_temps)
