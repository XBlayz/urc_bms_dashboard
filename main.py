import sys
import argparse
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication

from ui.main_window import DashboardWindow
from data.generators.mock_generator import MockDataGenerator
from data.generators.serial_generator import SerialDataGenerator
from data.bms_command_sender import MockBmsCommandSender, BmsCommandSender
from data.hardware.hardware_mapping import get_voltage_cell_mapping, get_temperature_sensor_mapping


def main():
    parser = argparse.ArgumentParser(description="URC BMS Dashboard")
    parser.add_argument("--mock", action="store_true", help="Use mock data generator instead of serial")
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0", help="Serial port to use (default: /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baudrate (default: 115200)")

    args, unknown = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unknown

    app = QApplication(sys.argv)

    pg.setConfigOptions(antialias=True)
    pg.setConfigOption('background', '#121212')
    pg.setConfigOption('foreground', '#DDDDDD')

    volt_count = len(get_voltage_cell_mapping())
    temp_count = len(get_temperature_sensor_mapping())

    # Init command sender
    if args.mock:
        command_sender = MockBmsCommandSender()
    else:
        command_sender = BmsCommandSender(port=args.port, baudrate=args.baud)

    # Init main UI window
    window = DashboardWindow(command_sender=command_sender, is_mock=args.mock)
    window.show()

    # Init data generator
    if args.mock:
        generator = MockDataGenerator(volt_count=volt_count, temp_count=temp_count)
    else:
        generator = SerialDataGenerator(
            port=args.port,
            baudrate=args.baud,
            volt_count=volt_count,
            temp_count=temp_count
        )

    # Wire generator telemetry to window dispatcher
    generator.telemetry_received.connect(window.on_telemetry_received)

    generator.start(500)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
