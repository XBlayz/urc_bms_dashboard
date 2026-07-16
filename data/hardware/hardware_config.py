"""Hardware topology constants for the battery pack.

Single source of truth for slave/cell/sensor counts, consumed by
hardware_mapping.py and by any widget that needs matrix dimensions
(e.g. the bar_chart matrix view). Update here only if the pack topology
changes; do not hardcode these numbers elsewhere.
"""

SLAVE_COUNT = 25
CELLS_PER_SLAVE = 6
TEMP_SENSORS_PER_SLAVE = 7

# Slaves wired with fewer cells than the rest of the pack (2 cells skipped).
PARTIAL_SLAVE_INDICES = frozenset(
    slave for slave in range(SLAVE_COUNT)
    if (slave > 0 and (slave + 1) % 5 == 0) or slave == 18
)
PARTIAL_SLAVE_SKIPPED_CELLS = frozenset({2, 3})
