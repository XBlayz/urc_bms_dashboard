import time
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from data.generators.state import BmsState, BmsTelemetryState
from data.hardware.hardware_mapping import get_voltage_cell_mapping, get_temperature_sensor_mapping


# Realistic-ish state sequence: (state, duration_seconds)
STATE_SEQUENCE = [
    (0, 4.0),   # STANDBY
    (6, 1.5),   # INITIALIZING
    (4, 2.0),   # PRECHARGING
    (1, 6.0),   # DRIVING
    (5, 2.0),   # PREPARING_CHARGING
    (2, 8.0),   # CHARGING
    (7, 1.5),   # EXITING_CHARGING
    (1, 5.0),   # DRIVING
    (8, 3.0),   # OVERRIDE
    (3, 2.0),   # ERROR
    (0, 3.0),   # STANDBY
]

class MockDataGenerator(QObject):
    bms_state_updated = pyqtSignal(BmsTelemetryState)

    def __init__(self, volt_count=138, temp_count=175):
        super().__init__()
        self.volt_count = volt_count
        self.temp_count = temp_count

        self.start_time = time.time()
        self.state_index = 0
        self.state_timer = 0.0

        self.volt_bases = np.linspace(3.7, 4.1, self.volt_count)
        self.temp_bases = np.linspace(25.0, 45.0, self.temp_count)

        self.timer = QTimer()
        self.timer.timeout.connect(self.emit_state)

        # Retrieve mappings and initialize the state object directly
        volt_mapping = get_voltage_cell_mapping()
        temp_mapping = get_temperature_sensor_mapping()
        self.current_state = BmsTelemetryState(
            volt_count=self.volt_count,
            temp_count=self.temp_count,
            volt_mapping=volt_mapping,
            temp_mapping=temp_mapping
        )

    def start(self, interval_ms=100):
        self.timer.start(interval_ms)

    def stop(self):
        self.timer.stop()

    def _current_state(self, elapsed):
        remaining = elapsed - self.state_timer
        state, duration = STATE_SEQUENCE[self.state_index]
        if remaining >= duration:
            self.state_timer += duration
            self.state_index = (self.state_index + 1) % len(STATE_SEQUENCE)
            state, _ = STATE_SEQUENCE[self.state_index]
        return state

    def _contactors_for_state(self, state):
        if state == 1:  # DRIVING
            return True, True, False, True
        elif state == 4:  # PRECHARGING
            return False, False, True, True
        elif state == 2:  # CHARGING
            return True, True, False, True
        elif state == 5:  # PREPARING_CHARGING
            return False, False, True, True
        elif state == 7:  # EXITING_CHARGING
            return True, True, False, True
        elif state == 8:  # OVERRIDE
            return True, True, False, True
        elif state == 3:  # ERROR
            return False, False, False, False
        else:  # STANDBY, INITIALIZING, NONE
            return False, False, False, False

    def _diagnostic_state_for(self, state, elapsed):
        if state != 3:
            return 0
        active_bits = 1 + int(elapsed) % 3
        return (1 << active_bits) - 1

    def emit_state(self):
        current_time = time.time() - self.start_time
        state_val = self._current_state(current_time)
        air_pos, air_neg, pre_charge, sdc = self._contactors_for_state(state_val)

        # Use a short reference for cleaner code
        s = self.current_state

        # BmsStatus
        try:
            s.bms_status = BmsState(state_val)
        except ValueError:
            s.bms_status = BmsState.NONE

        # PackState
        s.pack_voltage = 380.0 + np.sin(current_time * 0.1) * 10.0 + np.random.normal(0, 0.5)
        s.pack_current = 50.0 + np.cos(current_time * 0.15) * 20.0 + np.random.normal(0, 0.3)
        s.post_air_voltage = s.pack_voltage - 2.0 + np.random.normal(0, 0.1)
        s.soc = max(0.0, min(100.0, 75.0 + np.sin(current_time * 0.05) * 15.0))
        s.sop_dischg = 200.0 + np.random.normal(0, 5.0)
        s.sop_chg = 150.0 + np.random.normal(0, 5.0)

        # ActuatorState
        s.contactors["air_pos"] = air_pos
        s.contactors["air_neg"] = air_neg
        s.contactors["pre_charge"] = pre_charge
        s.contactors["sdc"] = sdc

        # ChargingSettings
        s.charging_set_voltage = 400.0
        s.charging_set_current = 30.0

        # Diagnostics
        s.diagnostic_state = self._diagnostic_state_for(state_val, current_time)
        s.ams_error = s.diagnostic_state != 0

        # CellVoltages & CellTemperatures
        # Aggiorniamo gli array numpy in-place usando [:] per mantenere intatte
        # le reference in memoria (utile per tool di plot come pyqtgraph)
        volt_drift = np.sin(current_time * 0.1 + self.volt_bases) * 0.05
        s.cell_voltages[:] = self.volt_bases + volt_drift + np.random.normal(0, 0.002, self.volt_count)

        temp_drift = np.sin(current_time * 0.05 + self.temp_bases) * 2.0
        s.cell_temperatures[:] = self.temp_bases + temp_drift + np.random.normal(0, 0.05, self.temp_count)

        # Emit the fully updated state object
        self.bms_state_updated.emit(s)
