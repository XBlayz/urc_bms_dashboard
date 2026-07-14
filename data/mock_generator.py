import time
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from data import messages_pb2


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
    telemetry_received = pyqtSignal(messages_pb2.BmsTelemetry) # pyright: ignore[reportAttributeAccessIssue]

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
        self.timer.timeout.connect(self.update)

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

    def update(self):
        current_time = time.time() - self.start_time
        state = self._current_state(current_time)
        air_pos, air_neg, pre_charge, sdc = self._contactors_for_state(state)

        telemetry = messages_pb2.BmsTelemetry() # pyright: ignore[reportAttributeAccessIssue]

        # PackState
        pack = telemetry.pack_state
        pack.voltage = 380.0 + np.sin(current_time * 0.1) * 10.0 + np.random.normal(0, 0.5)
        pack.current = 50.0 + np.cos(current_time * 0.15) * 20.0 + np.random.normal(0, 0.3)
        pack.post_air_voltage = pack.voltage - 2.0 + np.random.normal(0, 0.1)
        pack.soc = max(0.0, min(100.0, 75.0 + np.sin(current_time * 0.05) * 15.0))
        pack.sop_dischg = 200.0 + np.random.normal(0, 5.0)
        pack.sop_chg = 150.0 + np.random.normal(0, 5.0)

        # BmsStatus
        status = telemetry.status
        status.state = state

        # ActuatorState
        contactors = telemetry.contactors
        contactors.air_pos = air_pos
        contactors.air_neg = air_neg
        contactors.pre_charge = pre_charge
        contactors.sdc = sdc

        # ChargingSettings
        charging = telemetry.charging
        charging.set_voltage = 400.0
        charging.set_current = 30.0

        # Diagnostics
        diag = telemetry.diagnostics
        diag.ams_error = False
        diag.diagnostic_state = 0

        # CellVoltages
        cell_voltages = telemetry.cell_voltages
        cell_voltages.device_idx = 0
        volt_drift = np.sin(current_time * 0.1 + self.volt_bases) * 0.05
        current_volts = self.volt_bases + volt_drift + np.random.normal(0, 0.002, self.volt_count)
        cell_voltages.voltages.extend(current_volts.tolist())

        # CellTemperatures
        cell_temps = telemetry.cell_temperatures
        cell_temps.device_idx = 0
        temp_drift = np.sin(current_time * 0.05 + self.temp_bases) * 2.0
        current_temps = self.temp_bases + temp_drift + np.random.normal(0, 0.05, self.temp_count)
        cell_temps.temperatures.extend(current_temps.tolist())

        self.telemetry_received.emit(telemetry)
