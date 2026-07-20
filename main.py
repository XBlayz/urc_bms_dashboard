import sys
import argparse
import logging
import pyqtgraph as pg
import dearpygui.dearpygui as dpg

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from ui.main_window import DashboardWindow
from data.extif_reader import ExtifUartReader
from data.generators.serial_generator import SerialDataGenerator
from data.generators.mock_generator import MockDataGenerator
from data.generators.advanced_mock_generator import AdvancedMockGenerator
from data.sender.serial_cmd_sender import SerialBmsCommandSender
from data.sender.mock_cmd_sender import MockBmsCommandSender
from data.sender.advanced_mock_cmd_sender import AdvancedMockBmsCommandSender
from data.hardware.hardware_mapping import get_voltage_cell_mapping, get_temperature_sensor_mapping

from debug.debug_gui import setup_dpg_mock_controller


def logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d(%H:%M:%S)'
    )


def ui_app(args: argparse.Namespace, command_sender):
    app = QApplication(sys.argv)

    pg.setConfigOptions(antialias=True)
    pg.setConfigOption('background', '#121212')
    pg.setConfigOption('foreground', '#DDDDDD')

    window = DashboardWindow(command_sender=command_sender, is_mock=args.mock or args.advanced_mock)
    window.show()

    return (app, window)


def serial_setup(args: argparse.Namespace):
    if not (args.mock or args.advanced_mock):
        return ExtifUartReader(port=args.port, baudrate=args.baud)

    return None

def sender_setup(args: argparse.Namespace, uart_reader):
    if args.advanced_mock:
        return AdvancedMockBmsCommandSender()

    elif args.mock:
        return MockBmsCommandSender()

    else:
        if not uart_reader:
            raise RuntimeError("Cannot create SerialBmsCommandSender without ExtifUartReader")

        return SerialBmsCommandSender(extif_reader=uart_reader)

def generator_setup(args: argparse.Namespace, window, uart_reader, command_sender):
    volt_count = len(get_voltage_cell_mapping())
    temp_count = len(get_temperature_sensor_mapping())

    if args.advanced_mock:
        generator = AdvancedMockGenerator(volt_count=volt_count, temp_count=temp_count)
        generator.connection_changed.connect(window.set_connection_status)
        generator.connection_changed.connect(command_sender.on_connection_changed)

        command_sender.sig_charging_start_requested.connect(generator.on_charging_start_requested)
        command_sender.sig_charging_stop_requested.connect(generator.on_charging_stop_requested)
        command_sender.sig_charging_settings_updated.connect(generator.on_charging_settings_updated)
        command_sender.sig_initial_state_requested.connect(generator.on_initial_state_requested)

        setup_dpg_mock_controller(generator)

        # Create a Qt Timer to manually pump the DearPyGui render loop at ~60fps
        generator.dpg_render_timer = QTimer()
        generator.dpg_render_timer.timeout.connect(
            lambda: dpg.render_dearpygui_frame() if dpg.is_dearpygui_running() else None
        )
        generator.dpg_render_timer.start(16)

        generator.start()

    elif args.mock:
        generator = MockDataGenerator(volt_count=volt_count, temp_count=temp_count)
        generator.start(500)
        window.set_connection_status(True)

    else:
        if not uart_reader:
            raise RuntimeError("Cannot create SerialDataGenerator without ExtifUartReader")

        generator = SerialDataGenerator(extif_reader=uart_reader, volt_count=volt_count, temp_count=temp_count)
        generator.connection_changed.connect(window.set_connection_status)
        generator.start()

    generator.telemetry_frame_updated.connect(window.on_telemetry_received)

    return generator


def main():
    # --- Args Parsing ---
    parser = argparse.ArgumentParser(description="URC BMS Dashboard")
    parser.add_argument("--mock", action="store_true", help="Use standard mock generator")
    parser.add_argument("--advanced-mock", action="store_true", help="Use advanced mock with DPG control UI")
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0", help="Serial port to use (default: /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baudrate (default: 115200)")

    args, unknown = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unknown

    # --- Init ---
    logger()

    uart_reader = serial_setup(args)
    command_sender = sender_setup(args, uart_reader)
    app, window = ui_app(args, command_sender)
    generator = generator_setup(args, window, uart_reader, command_sender)

    # --- Execute Main Event Loop ---
    exit_code = app.exec()

    # --- Cleanup ---
    generator.stop()
    if args.advanced_mock:
        dpg.destroy_context()

    sys.exit(exit_code)

if __name__ == '__main__':
    main()
