"""Bidirectional mapping between flat sensor arrays and (slave, local_index) positions."""

from data.hardware.hardware_config import (
    SLAVE_COUNT,
    CELLS_PER_SLAVE,
    TEMP_SENSORS_PER_SLAVE,
    PARTIAL_SLAVE_INDICES,
    PARTIAL_SLAVE_SKIPPED_CELLS,
)


class HardwareMapping:
    """Maps a flat sensor index to its (slave, local_index) position and back in O(1).

    Iterable and sized like the plain list of tuples it replaces, so existing
    call sites using len(mapping) / for slave, idx in mapping keep working.
    """

    def __init__(self, positions):
        self.positions = positions
        self._position_to_flat = {pos: i for i, pos in enumerate(positions)}

    def __len__(self):
        return len(self.positions)

    def __iter__(self):
        return iter(self.positions)

    def __getitem__(self, flat_index):
        return self.positions[flat_index]

    def flat_index(self, slave, local_index):
        """Returns the flat array index for a (slave, local_index) position, or None if invalid."""
        return self._position_to_flat.get((slave, local_index))


def _build_voltage_positions():
    positions = []
    for slave in range(SLAVE_COUNT):
        is_partial = slave in PARTIAL_SLAVE_INDICES
        for cell in range(CELLS_PER_SLAVE):
            if is_partial and cell in PARTIAL_SLAVE_SKIPPED_CELLS:
                continue
            positions.append((slave, cell))
    return positions


def _build_temperature_positions():
    return [
        (slave, sensor)
        for slave in range(SLAVE_COUNT)
        for sensor in range(TEMP_SENSORS_PER_SLAVE)
    ]


def get_voltage_cell_mapping():
    """Returns the HardwareMapping for all valid voltage cells (0-based, matches firmware)."""
    return HardwareMapping(_build_voltage_positions())


def get_temperature_sensor_mapping():
    """Returns the HardwareMapping for all valid temperature sensors (0-based, matches firmware)."""
    return HardwareMapping(_build_temperature_positions())
