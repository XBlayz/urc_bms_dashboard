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

class BmsTelemetryState:
    def __init__(self, volt_count: int, temp_count: int, volt_mapping: Any, temp_mapping: Any) -> None:
        self.bms_status: Optional['BmsState'] = None

        self.pack_voltage: float = 0.0
        self.pack_current: float = 0.0
        self.post_air_voltage: float = 0.0
        self.soc: float = 0.0
        self.sop_dischg: float = 0.0
        self.sop_chg: float = 0.0

        self.cell_voltages = np.zeros(volt_count, dtype=np.float64)
        self.cell_temperatures = np.zeros(temp_count, dtype=np.float64)

        # Hardware mapping instances injected via constructor
        self._volt_mapping = volt_mapping
        self._temp_mapping = temp_mapping

        self.balancing_masks: bytes = b""

        self.contactors = {
            "air_pos": False,
            "air_neg": False,
            "pre_charge": False,
            "sdc": False
        }

        self.charging_set_voltage: float = 0.0
        self.charging_set_current: float = 0.0

        self.ams_error: bool = False
        self.diagnostic_state: int = 0

    def update(self, telemetry_msg) -> None:
        """Updates internal state based on the received telemetry payload."""
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

        elif payload_type is None:
            logging.debug("[STATE UPDATE] Received BmsTelemetry message with no payload set.")
        else:
            logging.warning(f"[STATE UPDATE] Received unknown payload type: {payload_type}")
