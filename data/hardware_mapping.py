def get_voltage_cell_mapping():
    """
    Returns a list of tuples (slave_index, cell_index) for all valid voltage cells.
    Based on the BMS firmware logic where partial slaves skip cells 2 and 3.
    Indices returned are 0-based to match the firmware.
    """
    mapping = []
    for slave_index in range(25):
        is_partial = (slave_index > 0 and (slave_index + 1) % 5 == 0) or slave_index == 18
        for cell_index in range(6):
            if is_partial and (cell_index == 2 or cell_index == 3):
                continue
            mapping.append((slave_index, cell_index))
    return mapping

def get_temperature_sensor_mapping():
    """
    Returns a list of tuples (slave_index, sensor_index) for all valid temp sensors.
    Indices returned are 0-based to match the firmware.
    """
    mapping = []
    for slave_index in range(25):
        for reading_index in range(7):
            mapping.append((slave_index, reading_index))
    return mapping
