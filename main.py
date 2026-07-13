import sys
import argparse
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication

from ui.main_window import DashboardWindow
from data.mock_generator import MockDataGenerator
from data.serial_generator import SerialDataGenerator

def main():
    parser = argparse.ArgumentParser(description="URC BMS Dashboard")
    parser.add_argument("--mock", action="store_true", help="Use mock data generator instead of serial")
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0", help="Serial port to use (default: /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baudrate (default: 115200)")
    
    # Parse args, removing them from sys.argv so QApplication doesn't complain about unknown options
    args, unknown = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unknown

    app = QApplication(sys.argv)
    
    # Configure pyqtgraph globally
    pg.setConfigOptions(antialias=True)
    pg.setConfigOption('background', '#121212')
    pg.setConfigOption('foreground', '#DDDDDD')
    
    # Init main UI window
    window = DashboardWindow()
    window.show()
    
    # Init data generator
    if args.mock:
        generator = MockDataGenerator(
            volt_count=len(window.volt_mapping),
            temp_count=len(window.temp_mapping)
        )
    else:
        generator = SerialDataGenerator(
            port=args.port,
            baudrate=args.baud,
            volt_count=len(window.volt_mapping),
            temp_count=len(window.temp_mapping)
        )
    
    # Wire the generator signals to the UI slots
    generator.voltages_updated.connect(window.on_voltages_updated)
    generator.temperatures_updated.connect(window.on_temperatures_updated)
    
    # Start simulating incoming data at 2Hz
    generator.start(500)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
