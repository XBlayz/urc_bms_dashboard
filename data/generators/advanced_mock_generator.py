import time
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from data.generators.state import BmsState, BmsTelemetryState
from data.hardware.hardware_mapping import get_voltage_cell_mapping, get_temperature_sensor_mapping
from dataclasses import dataclass # Assumendo che tu abbia definito TelemetryFrame qui

@dataclass
class TelemetryFrame:
    timestamp: float
    state: BmsTelemetryState

class AdvancedMockGenerator(QObject):
    # Segnali per la UI
    telemetry_frame_updated = pyqtSignal(TelemetryFrame)
    connection_changed = pyqtSignal(bool)

    def __init__(self, volt_count=138, temp_count=175):
        super().__init__()
        self.volt_count = volt_count
        self.temp_count = temp_count

        self.start_time = time.time()
        self._is_connected = False

        # Frequenze di aggiornamento indipendenti (in secondi)
        self.update_rates = {
            "fast": 0.05,   # 20Hz: Celle e Temperature
            "medium": 0.2,  # 5Hz: Pack State (Tensioni e correnti totali)
            "slow": 1.0     # 1Hz: FSM, Contattori, Diagnostica
        }

        # Accumulatori di tempo per ogni gruppo
        self._accumulators = {k: 0.0 for k in self.update_rates}
        self._last_tick = time.time()

        # Stato mock interno per simulare la macchina a stati
        self.mock_fsm_state = 0
        self.mock_fsm_timer = 0.0

        self.volt_bases = np.linspace(3.7, 4.1, self.volt_count)
        self.temp_bases = np.linspace(25.0, 45.0, self.temp_count)

        volt_mapping = get_voltage_cell_mapping()
        temp_mapping = get_temperature_sensor_mapping()
        self.current_state = BmsTelemetryState(
            volt_count=self.volt_count,
            temp_count=self.temp_count,
            volt_mapping=volt_mapping,
            temp_mapping=temp_mapping
        )

        # Il timer principale gira molto velocemente (es. 10ms = 100Hz)
        self.tick_timer = QTimer()
        self.tick_timer.timeout.connect(self._tick)

    def start(self):
        """Avvia il motore di simulazione, ma non connette il BMS."""
        self._last_tick = time.time()
        self.tick_timer.start(10)

    def stop(self):
        """Ferma completamente il motore."""
        self.tick_timer.stop()

    def connect_bms(self):
        """Simula l'inserimento del cavo o l'avvio della connessione."""
        if not self._is_connected:
            self._is_connected = True
            # Resettiamo il tempo per evitare che il delta_time crei salti enormi
            self._last_tick = time.time()
            self.connection_changed.emit(True)

    def disconnect_bms(self):
        """Simula la perdita di connessione."""
        if self._is_connected:
            self._is_connected = False
            self.connection_changed.emit(False)

    def set_update_rate(self, group: str, rate_hz: float):
        """Permette di modificare i rate in tempo reale dalla UI."""
        if group in self.update_rates and rate_hz > 0:
            self.update_rates[group] = 1.0 / rate_hz

    def _tick(self):
        if not self._is_connected:
            self._last_tick = time.time()
            return

        now = time.time()
        dt = now - self._last_tick
        self._last_tick = now

        current_sim_time = now - self.start_time
        frame_needs_emit = False

        # Valuta quali gruppi devono essere aggiornati
        for group, interval in self.update_rates.items():
            self._accumulators[group] += dt

            if self._accumulators[group] >= interval:
                # Evita la deriva temporale sottraendo l'intervallo esatto
                self._accumulators[group] -= interval
                self._update_group(group, current_sim_time)
                frame_needs_emit = True

        # Emette il frame solo se almeno un gruppo è stato modificato
        if frame_needs_emit:
            frame = TelemetryFrame(
                timestamp=current_sim_time,
                state=self.current_state
            )
            self.telemetry_frame_updated.emit(frame)

    def _update_group(self, group: str, current_time: float):
        """Indirizza l'aggiornamento in base al gruppo temporale."""
        s = self.current_state

        if group == "fast":
            # Aggiornamento matrici ad alta frequenza
            volt_drift = np.sin(current_time * 0.1 + self.volt_bases) * 0.05
            s.cell_voltages[:] = self.volt_bases + volt_drift + np.random.normal(0, 0.002, self.volt_count)

            temp_drift = np.sin(current_time * 0.05 + self.temp_bases) * 2.0
            s.cell_temperatures[:] = self.temp_bases + temp_drift + np.random.normal(0, 0.05, self.temp_count)

        elif group == "medium":
            # Aggiornamento macro-grandezze
            s.pack_voltage = 380.0 + np.sin(current_time * 0.1) * 10.0 + np.random.normal(0, 0.5)
            s.pack_current = 50.0 + np.cos(current_time * 0.15) * 20.0 + np.random.normal(0, 0.3)
            s.post_air_voltage = s.pack_voltage - 2.0 + np.random.normal(0, 0.1)
            s.soc = max(0.0, min(100.0, 75.0 + np.sin(current_time * 0.05) * 15.0))
            s.sop_dischg = 200.0 + np.random.normal(0, 5.0)
            s.sop_chg = 150.0 + np.random.normal(0, 5.0)

        elif group == "slow":
            # Aggiornamento logico (FSM, Contattori, Diagnostica)
            self._advance_fsm(current_time)
            s.bms_status = BmsState(self.mock_fsm_state)

            # Qui andrebbe la logica per mappare lo stato FSM ai contattori
            # s.contactors["air_pos"] = ...

            s.diagnostic_state = 0 if self.mock_fsm_state != 3 else 1
            s.ams_error = s.diagnostic_state != 0

    def _advance_fsm(self, current_time):
        """Logica semplificata per avanzare gli stati nel mock."""
        # Puoi reinserire qui la tua lista STATE_SEQUENCE originale
        pass
