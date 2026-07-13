from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt

from ui.sidebar import Sidebar
from ui.voltages_plot import VoltagesPlotWidget
from ui.temperatures_plot import TemperaturesPlotWidget
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme
from data.hardware_mapping import get_voltage_cell_mapping, get_temperature_sensor_mapping

class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Strings.WINDOW_TITLE)
        self.resize(1400, 900)
        self.setStyleSheet(Theme.main_window())
        
        self.volt_mapping = get_voltage_cell_mapping()
        self.temp_mapping = get_temperature_sensor_mapping()
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Content Area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Voltage        
        self.volt_plot = VoltagesPlotWidget(
            mapping=self.volt_mapping,
            label_formatter_callback=self.format_volt_label
        )
        content_layout.addWidget(self.volt_plot, stretch=1)
        
        self.temp_plot = TemperaturesPlotWidget(
            mapping=self.temp_mapping,
            label_formatter_callback=self.format_temp_label
        )
        content_layout.addWidget(self.temp_plot, stretch=1)
        main_layout.addWidget(content_widget, stretch=1)
        
        # Connect Maximize Signals
        self.volt_plot.sig_maximize_toggled.connect(lambda checked: self.on_plot_maximized(self.volt_plot, checked))
        self.temp_plot.sig_maximize_toggled.connect(lambda checked: self.on_plot_maximized(self.temp_plot, checked))
        
    def on_plot_maximized(self, sender_plot, is_maximized):
        plots = [self.volt_plot, self.temp_plot]
        for plot in plots:
            if plot != sender_plot:
                if is_maximized:
                    plot.hide()
                else:
                    plot.show()
                    
    def format_volt_label(self, index):
        slave, cell = self.volt_mapping[index]
        return Strings.FMT_CELL_LABEL.format(slave=slave + 1, cell=cell + 1)
        
    def format_temp_label(self, index):
        slave, sensor = self.temp_mapping[index]
        return Strings.FMT_SENSOR_LABEL.format(slave=slave + 1, sensor=sensor + 1)
        
    def on_voltages_updated(self, current_time, volt_data):
        self.volt_plot.add_point(current_time, volt_data)
        
    def on_temperatures_updated(self, current_time, temp_data):
        self.temp_plot.add_point(current_time, temp_data)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.volt_plot.underMouse():
                self.volt_plot.clear_selection()
            elif self.temp_plot.underMouse():
                self.temp_plot.clear_selection()
        super().keyPressEvent(event)
