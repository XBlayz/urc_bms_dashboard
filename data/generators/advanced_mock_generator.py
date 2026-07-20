import time
from typing import Optional

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, pyqtSlot

from data.generators.state import BmsState, CommandResponse, BmsTelemetryState
from data.hardware.hardware_mapping import get_voltage_cell_mapping, get_temperature_sensor_mapping
from data.generators.telemetry import TelemetryFrame
from data.proto import messages_pb2
from data.hardware.hardware_config import SLAVE_COUNT, CELLS_PER_SLAVE, TEMP_SENSORS_PER_SLAVE


class AdvancedMockGenerator(QObject):
    telemetry_frame_updated = pyqtSignal(TelemetryFrame)
    connection_changed = pyqtSignal(bool)

    def __init__(self, volt_count=138, temp_count=175):
        super().__init__()
        self.volt_count = volt_count
        self.temp_count = temp_count

        self.start_time = time.time()
        self._is_connected = False

        self.update_rates = {
            "fast": 0.1,
            "medium": 0.2,
            "slow": 1.0
        }

        self._accumulators = {k: 0.0 for k in self.update_rates}
        self._last_tick = time.time()

        self.mock_fsm_state = BmsState.INITIALIZING.value
        self.mock_fsm_timer = 0.0
        self._charging_requested = False

        self._pending_settings_ack = False

        # UI Modifiers initialization
        self._force_initializing = False
        self._forced_error_code = 0
        self._external_sdc = True
        self._actuator_overrides: dict[str, Optional[bool]] = {
            "air_pos": None,
            "air_neg": None,
            "pre_charge": None,
            "sdc": None
        }
        #TODO: implement in DEBUG UI
        self._cmd_ignore = {
            "start_charging": False,
            "stop_charging": False,
            "charging_settings": False,
            "initial_state_request": False
        }
        #TODO: implement in DEBUG UI
        self._cmd_error = {
            "charging_settings": False,
        }

        self.mock_charging_v = 400.0
        self.mock_charging_c = 30.0

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

        self.tick_timer = QTimer()
        self.tick_timer.timeout.connect(self._tick)

        self.dpg_render_timer: Optional[QTimer] = None

    # --- UI Interactions ---
    def set_force_initializing(self, state: bool):
        self._force_initializing = state
        if state:
            self._set_fsm_state(BmsState.INITIALIZING.value)
        elif self.mock_fsm_state == BmsState.INITIALIZING.value:
            self._set_fsm_state(BmsState.STANDBY.value)

    def set_forced_error(self, error_code: int):
        self._forced_error_code = error_code
        if error_code > 0:
            self._set_fsm_state(BmsState.ERROR.value)
        elif self.mock_fsm_state == BmsState.ERROR.value:
            self._set_fsm_state(BmsState.STANDBY.value)

    def set_external_sdc(self, state: bool):
        self._external_sdc = state

    def set_charging_params(self, voltage: float, current: float):
        self.mock_charging_v = voltage
        self.mock_charging_c = current

        self._send_charging_parameters()

    def set_actuator_override(self, actuator: str, state: int):
        if state == 0:
            self._actuator_overrides[actuator] = None
        elif state == 1:
            self._actuator_overrides[actuator] = False
        elif state == 2:
            self._actuator_overrides[actuator] = True

    def set_cmd_ignore(self, cmd: str, state: bool):
        self._cmd_ignore[cmd] = state

    # --- Commands from Dashboard UI ---
    @pyqtSlot()
    def on_charging_start_requested(self):
        if self._cmd_ignore["start_charging"]:
            return

        if self.mock_fsm_state in (BmsState.STANDBY.value, BmsState.DRIVING.value):
            self._charging_requested = True
            self._set_fsm_state(BmsState.PREPARING_CHARGING.value)

    @pyqtSlot()
    def on_charging_stop_requested(self):
        if self._cmd_ignore["stop_charging"]:
            return

        if self.mock_fsm_state in (BmsState.CHARGING.value, BmsState.PREPARING_CHARGING.value):
            self._charging_requested = False
            self._set_fsm_state(BmsState.EXITING_CHARGING.value)

    @pyqtSlot(float, float)
    def on_charging_settings_updated(self, voltage: float, current: float):
        if self._cmd_ignore["charging_settings"]:
            return

        self.mock_charging_v = voltage
        self.mock_charging_c = current

        self._pending_settings_ack = True

        import dearpygui.dearpygui as dpg
        if dpg.is_dearpygui_running():
            if dpg.does_alias_exist("charge_v"):
                dpg.set_value("charge_v", voltage)
            if dpg.does_alias_exist("charge_c"):
                dpg.set_value("charge_c", current)

    @pyqtSlot()
    def on_initial_state_requested(self):
        if self._cmd_ignore["initial_state_request"]:
            return

        self._send_charging_parameters()

    # --- Core Loop ---
    def start(self):
        self._last_tick = time.time()
        self.tick_timer.start(10)

    def stop(self):
        self.tick_timer.stop()

    def connect_bms(self):
        if not self._is_connected:
            self._is_connected = True
            self._last_tick = time.time()
            self.connection_changed.emit(True)

    def disconnect_bms(self):
        if self._is_connected:
            self._is_connected = False
            self.connection_changed.emit(False)

    def set_update_rate(self, group: str, rate_hz: float):
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

        for group, interval in self.update_rates.items():
            self._accumulators[group] += dt

            if self._accumulators[group] >= interval:
                self._accumulators[group] -= interval
                self._update_group(group, current_sim_time)
                frame_needs_emit = True

        if self._pending_settings_ack:
            if self._cmd_error["charging_settings"]:
                msg_ack = messages_pb2.BmsTelemetry( # pyright: ignore[reportAttributeAccessIssue]
                    command_response=messages_pb2.CommandResponse( # pyright: ignore[reportAttributeAccessIssue]
                        message=CommandResponse.CHARGING_SETTINGS_REJECTED.value
                    )
                )
            else:
                msg_ack = messages_pb2.BmsTelemetry( # pyright: ignore[reportAttributeAccessIssue]
                    command_response=messages_pb2.CommandResponse( # pyright: ignore[reportAttributeAccessIssue]
                        message=CommandResponse.CHARGING_SETTINGS_APPLIED.value
                    )
                )
            self.current_state.update(msg_ack)

            self._pending_settings_ack = False
            frame_needs_emit = True

        if frame_needs_emit:
            frame = TelemetryFrame(timestamp=current_sim_time, state=self.current_state)
            self.telemetry_frame_updated.emit(frame)

    def _set_fsm_state(self, new_state: int):
        self.mock_fsm_state = new_state
        self.mock_fsm_timer = 0.0

    def _advance_fsm(self, dt: float):
        if self._force_initializing:
            return
        if self._forced_error_code > 0:
            return

        self.mock_fsm_timer += dt
        st = self.mock_fsm_state

        if not self._external_sdc and st in (BmsState.PRECHARGING.value, BmsState.DRIVING.value):
            self._set_fsm_state(BmsState.STANDBY.value)
            st = BmsState.STANDBY.value

        if st == BmsState.INITIALIZING.value:
            if self.mock_fsm_timer >= 2.0:
                self._set_fsm_state(BmsState.STANDBY.value)
        elif st == BmsState.PREPARING_CHARGING.value:
            if self.mock_fsm_timer >= 2.0:
                self._set_fsm_state(BmsState.CHARGING.value)
        elif st == BmsState.EXITING_CHARGING.value:
            if self.mock_fsm_timer >= 1.5:
                self._set_fsm_state(BmsState.STANDBY.value)
        elif st == BmsState.STANDBY.value:
            if self.mock_fsm_timer >= 5.0 and not self._charging_requested:
                if self._external_sdc:
                    self._set_fsm_state(BmsState.PRECHARGING.value)
        elif st == BmsState.PRECHARGING.value:
            if self.mock_fsm_timer >= 2.0 and not self._charging_requested:
                self._set_fsm_state(BmsState.DRIVING.value)
        elif st == BmsState.DRIVING.value:
            if self.mock_fsm_timer >= 10.0:
                self._set_fsm_state(BmsState.STANDBY.value)

    def _contactors_for_state(self, state, has_error):
        air_pos, air_neg, pre_charge = False, False, False
        sdc = not has_error  # Open (False) ONLY if there is an error

        if state in (BmsState.PRECHARGING.value, BmsState.PREPARING_CHARGING.value):
            air_pos = True
            pre_charge = True
            air_neg = False
        elif state in (BmsState.DRIVING.value, BmsState.CHARGING.value):
            air_pos = True
            air_neg = True
            pre_charge = False

        return air_pos, air_neg, pre_charge, sdc

    def _diagnostic_state_for(self, state, elapsed):
        if state != 3:
            return 0
        active_bits = 1 + int(elapsed) % 3
        return (1 << active_bits) - 1

    def _update_group(self, group: str, current_time: float):
        is_initializing = (self.mock_fsm_state == BmsState.INITIALIZING.value)

        if group == "fast":
            # --- VOLTAGES ---
            if not is_initializing:
                voltages = np.zeros(self.volt_count)
                volt_drift = np.sin(current_time * 0.1 + self.volt_bases) * 0.05
                voltages = self.volt_bases + volt_drift + np.random.normal(0, 0.002, self.volt_count)

                self._pack_voltages_data_for_msg(voltages)

            # --- TEMPERATURES ---
            if not is_initializing:
                temperatures = np.zeros(self.temp_count)
                temp_drift = np.sin(current_time * 0.05 + self.temp_bases) * 2.0
                temperatures = self.temp_bases + temp_drift + np.random.normal(0, 0.05, self.temp_count)

                self._pack_temperatures_data_for_msg(temperatures)

        elif group == "medium":
            # --- PACK STATE ---
            if not is_initializing:
                v = 380.0 + np.sin(current_time * 0.1) * 10.0 + np.random.normal(0, 0.5)
                pack_state = messages_pb2.PackState( # pyright: ignore[reportAttributeAccessIssue]
                    voltage=float(v),
                    current=float(50.0 + np.cos(current_time * 0.15) * 20.0 + np.random.normal(0, 0.3)),
                    post_air_voltage=float(v - 2.0 + np.random.normal(0, 0.1)),
                    soc=float(max(0.0, min(100.0, 75.0 + np.sin(current_time * 0.05) * 15.0))),
                    sop_dischg=float(200.0 + np.random.normal(0, 5.0)),
                    sop_chg=float(150.0 + np.random.normal(0, 5.0))
                )

                msg = messages_pb2.BmsTelemetry(pack_state=pack_state) # pyright: ignore[reportAttributeAccessIssue]
                self.current_state.update(msg)

        elif group == "slow":
            self._advance_fsm(self.update_rates["slow"])

            # --- BMS STATUS ---
            msg_status = messages_pb2.BmsTelemetry( # pyright: ignore[reportAttributeAccessIssue]
                status=messages_pb2.BmsStatus(state=self.mock_fsm_state) # pyright: ignore[reportAttributeAccessIssue]
            )
            self.current_state.update(msg_status)

            if is_initializing:
                contactors = messages_pb2.ActuatorState( # pyright: ignore[reportAttributeAccessIssue]
                    air_pos=False, air_neg=False, pre_charge=False, sdc=False
                )
                diagnostics = messages_pb2.Diagnostics( # pyright: ignore[reportAttributeAccessIssue]
                    diagnostic_state=0, ams_error=False
                )
            else:
                has_error = (self._forced_error_code > 0) or (self.mock_fsm_state == BmsState.ERROR.value)
                air_pos, air_neg, pre_charge, sdc = self._contactors_for_state(self.mock_fsm_state, has_error)

                contactors = messages_pb2.ActuatorState( # pyright: ignore[reportAttributeAccessIssue]
                    air_pos=bool(air_pos if self._actuator_overrides["air_pos"] is None else self._actuator_overrides["air_pos"]),
                    air_neg=bool(air_neg if self._actuator_overrides["air_neg"] is None else self._actuator_overrides["air_neg"]),
                    pre_charge=bool(pre_charge if self._actuator_overrides["pre_charge"] is None else self._actuator_overrides["pre_charge"]),
                    sdc=bool(sdc if self._actuator_overrides["sdc"] is None else self._actuator_overrides["sdc"])
                )

                diag_state = self._forced_error_code if self._forced_error_code > 0 else self._diagnostic_state_for(self.mock_fsm_state, current_time)
                diagnostics = messages_pb2.Diagnostics( # pyright: ignore[reportAttributeAccessIssue]
                    diagnostic_state=int(diag_state),
                    ams_error=bool(diag_state != 0)
                )

            self.current_state.update(messages_pb2.BmsTelemetry(contactors=contactors)) # pyright: ignore[reportAttributeAccessIssue]
            self.current_state.update(messages_pb2.BmsTelemetry(diagnostics=diagnostics)) # pyright: ignore[reportAttributeAccessIssue]

    def _pack_voltages_data_for_msg(self, voltages):
        for slave in range(SLAVE_COUNT):
            slave_voltages = []
            for cell in range(CELLS_PER_SLAVE):
                flat_idx = self.current_state._volt_mapping.flat_index(slave, cell)
                val = float(voltages[flat_idx]) if flat_idx is not None else 0.0
                slave_voltages.append(val)

            msg_v = messages_pb2.BmsTelemetry( # pyright: ignore[reportAttributeAccessIssue]
                cell_voltages=messages_pb2.CellVoltages( # pyright: ignore[reportAttributeAccessIssue]
                    device_idx=slave,
                    voltages=slave_voltages
                )
            )
            self.current_state.update(msg_v)

    def _pack_temperatures_data_for_msg(self, temperatures):
        for slave in range(SLAVE_COUNT):
            slave_temps = []
            for sensor in range(TEMP_SENSORS_PER_SLAVE):
                flat_idx = self.current_state._temp_mapping.flat_index(slave, sensor)
                val = float(temperatures[flat_idx]) if flat_idx is not None else 0.0
                slave_temps.append(val)

            msg_t = messages_pb2.BmsTelemetry( # pyright: ignore[reportAttributeAccessIssue]
                cell_temperatures=messages_pb2.CellTemperatures( # pyright: ignore[reportAttributeAccessIssue]
                    device_idx=slave,
                    temperatures=slave_temps
                )
            )
            self.current_state.update(msg_t)


    def _send_charging_parameters(self):
        msg_chg = messages_pb2.BmsTelemetry( # pyright: ignore[reportAttributeAccessIssue]
            charging=messages_pb2.ChargingSettings( # pyright: ignore[reportAttributeAccessIssue]
                set_voltage=float(self.mock_charging_v),
                set_current=float(self.mock_charging_c)
            )
        )
        self.current_state.update(msg_chg)

        current_sim_time = time.time() - self.start_time
        frame = TelemetryFrame(timestamp=current_sim_time, state=self.current_state)
        self.telemetry_frame_updated.emit(frame)
