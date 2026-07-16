import sys
import argparse
import pyqtgraph as pg
import dearpygui.dearpygui as dpg

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from ui.main_window import DashboardWindow
from data.generators.mock_generator import MockDataGenerator
from data.generators.advanced_mock_generator import AdvancedMockGenerator
from data.generators.serial_generator import SerialDataGenerator
from data.bms_command_sender import MockBmsCommandSender, BmsCommandSender
from data.hardware.hardware_mapping import get_voltage_cell_mapping, get_temperature_sensor_mapping

from debug.debug_gui import setup_dpg_mock_controller


def main():
    parser = argparse.ArgumentParser(description="URC BMS Dashboard")
    parser.add_argument("--mock", action="store_true", help="Use standard mock generator")
    parser.add_argument("--advanced-mock", action="store_true", help="Use advanced mock with DPG control UI")
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0", help="Serial port to use (default: /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baudrate (default: 115200)")

    args, unknown = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unknown

    is_any_mock = args.mock or args.advanced_mock

    app = QApplication(sys.argv)

    pg.setConfigOptions(antialias=True)
    pg.setConfigOption('background', '#121212')
    pg.setConfigOption('foreground', '#DDDDDD')

    volt_count = len(get_voltage_cell_mapping())
    temp_count = len(get_temperature_sensor_mapping())

    # Init command sender
    if is_any_mock:
        command_sender = MockBmsCommandSender()
    else:
        command_sender = BmsCommandSender(port=args.port, baudrate=args.baud)

    # Init main UI window
    window = DashboardWindow(command_sender=command_sender, is_mock=is_any_mock)
    window.show()

    # --- Generator Initialization ---
    dpg_render_timer = None

    if args.advanced_mock:
        generator = AdvancedMockGenerator(volt_count=volt_count, temp_count=temp_count)
        generator.connection_changed.connect(window.set_connection_status)

        # Pass the object reference directly to DPG
        setup_dpg_mock_controller(generator)

        # Create a Qt Timer to manually pump the DearPyGui render loop at ~60fps
        dpg_render_timer = QTimer()
        dpg_render_timer.timeout.connect(
            lambda: dpg.render_dearpygui_frame() if dpg.is_dearpygui_running() else None
        )
        dpg_render_timer.start(16)

        generator.start()

    elif args.mock:
        generator = MockDataGenerator(volt_count=volt_count, temp_count=temp_count)
        generator.start(500)
        window.set_connection_status(True)

    else:
        generator = SerialDataGenerator(port=args.port, baudrate=args.baud, volt_count=volt_count, temp_count=temp_count)
        generator.start()
        window.set_connection_status(True)

    generator.telemetry_frame_updated.connect(window.on_telemetry_received)

    # --- Execute Main Event Loop ---
    exit_code = app.exec()

    # --- Cleanup ---
    generator.stop()
    if args.advanced_mock:
        dpg.destroy_context()

    sys.exit(exit_code)

if __name__ == '__main__':
    main()
