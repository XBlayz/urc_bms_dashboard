import logging
from enum import Enum
from typing import Optional, Any

import numpy as np


class BmsState(Enum):
    """
    Python enumeration mirroring the Protobuf SystemState.
    """
    STANDBY = 0
    DRIVING = 1
    CHARGING = 2
    ERROR = 3
    PRECHARGING = 4
    PREPARING_CHARGING = 5
    INITIALIZING = 6
    EXITING_CHARGING = 7
    OVERRIDE = 8
    COUNT = 9
    NONE = 10

#TODO: Da definire
class CommandResponse(Enum):
    CHARGING_SETTINGS_APPLIED = "charging_settings_applied"
    CHARGING_SETTINGS_REJECTED = "charging_settings_rejected"

class BmsTelemetryState:
    def __init__(self, volt_count: int, temp_count: int, volt_mapping: Any, temp_mapping: Any) -> None:
        self._volt_mapping = volt_mapping
        self._temp_mapping = temp_mapping

        # --- Real states ---
        # - Persistent states -
        #* Persistente states maintain always the last received value
        self._bms_status = None
        self.bms_status = None

        self.pack_voltage: float = 0.0
        self.post_air_voltage: float = 0.0
        self.pack_current: float = 0.0
        self.sop_dischg: float = 0.0
        self.sop_chg: float = 0.0
        self.soc: float = 0.0

        self.cell_voltages = np.zeros(volt_count, dtype=np.float64)
        self.cell_temperatures = np.zeros(temp_count, dtype=np.float64)

        self.balancing_masks: bytes = b""

        self.contactors = {
            "air_pos": False,
            "air_neg": False,
            "pre_charge": False,
            "sdc": False
        }

        self.ams_error: bool = False
        self.diagnostic_state: int = 0

        # - Transient states -
        #* Transient states are updated every time a new telemetry frame is received
        #* If the value is not received, it is set to None
        self.charging_set_voltage: Optional[float] = None
        self.charging_set_current: Optional[float] = None

        self.charging_settings_ack: Optional[bool] = None

        # --- Elaborated states ---
        # - Persistent states -
        self.is_charging_starting: bool = False
        self.is_charging_active: bool = False
        self.is_charging_stopping: bool = False

        self.is_override_active: bool = False

    @property
    def bms_status(self) -> Optional['BmsState']:
        return self._bms_status

    @bms_status.setter
    def bms_status(self, value: Optional['BmsState']) -> None:
        self._bms_status = value
        self._update_elaborated_states()

    def update(self, telemetry_msg) -> None:
        """Updates internal state based on the received telemetry payload."""
        self._reset_transient_states()

        payload_type = telemetry_msg.WhichOneof("payload")

        if payload_type == "status":
            raw_state = telemetry_msg.status.state
            try:
                self.bms_status = BmsState(raw_state)
            except ValueError:
                logging.error(f"[STATE UPDATE] Invalid state received from telemetry: {raw_state}")
                self.bms_status = None

        elif payload_type == "pack_state":
            ps = telemetry_msg.pack_state
            self.pack_voltage = ps.voltage
            self.pack_current = ps.current
            self.post_air_voltage = ps.post_air_voltage
            self.soc = ps.soc
            self.sop_dischg = ps.sop_dischg
            self.sop_chg = ps.sop_chg

        elif payload_type == "balancing":
            self.balancing_masks = telemetry_msg.balancing.balancing_masks

        elif payload_type == "contactors":
            acts = telemetry_msg.contactors
            self.contactors["air_pos"] = acts.air_pos
            self.contactors["air_neg"] = acts.air_neg
            self.contactors["pre_charge"] = acts.pre_charge
            self.contactors["sdc"] = acts.sdc

        elif payload_type == "charging":
            chg = telemetry_msg.charging
            self.charging_set_voltage = chg.set_voltage
            self.charging_set_current = chg.set_current

        elif payload_type == "diagnostics":
            diag = telemetry_msg.diagnostics
            self.ams_error = diag.ams_error
            self.diagnostic_state = diag.diagnostic_state

        elif payload_type == "cell_voltages":
            cv = telemetry_msg.cell_voltages
            device_idx = cv.device_idx
            for i, v in enumerate(cv.voltages):
                idx = self._volt_mapping.flat_index(device_idx, i)
                if idx is not None:
                    self.cell_voltages[idx] = v

        elif payload_type == "cell_temperatures":
            ct = telemetry_msg.cell_temperatures
            device_idx = ct.device_idx
            for i, t in enumerate(ct.temperatures):
                idx = self._temp_mapping.flat_index(device_idx, i)
                if idx is not None:
                    self.cell_temperatures[idx] = t

        elif payload_type == "command_response":
            self._decode_command_response(telemetry_msg.command_response.message)

        elif payload_type is None:
            logging.debug("[STATE UPDATE] Received BmsTelemetry message with no payload set.")
            return
        else:
            logging.warning(f"[STATE UPDATE] Received unknown payload type: {payload_type}")
            return

    def _decode_command_response(self, message: str):
        match message:
            case CommandResponse.CHARGING_SETTINGS_APPLIED.value:
                self.charging_settings_ack = True
            case CommandResponse.CHARGING_SETTINGS_REJECTED.value:
                self.charging_settings_ack = False


    def _update_elaborated_states(self):
        self.is_charging_starting = self._bms_status == BmsState.PREPARING_CHARGING
        self.is_charging_active = self._bms_status == BmsState.CHARGING
        self.is_charging_stopping = self._bms_status == BmsState.EXITING_CHARGING

        self.is_override_active = self._bms_status == BmsState.OVERRIDE

    def _reset_transient_states(self):
        self.charging_set_voltage = None
        self.charging_set_current = None

        self.charging_settings_ack = None
