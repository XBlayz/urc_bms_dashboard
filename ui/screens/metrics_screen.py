import numpy as np
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QGridLayout, QWidget,
    QHeaderView, QStackedWidget, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QAbstractTableModel, QSize

from ui.widgets.time_series_plot import TimeSeriesPlotWidget
from ui.widgets.plot_widgets import EnumPlot, StackedBoolPlot, BarChartWidget, SimpleTimeSeriesPlot
from ui.widgets.voltages_plot import VoltagesPlotWidget
from ui.widgets.temperatures_plot import TemperaturesPlotWidget
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme
from data.hardware_mapping import get_voltage_cell_mapping, get_temperature_sensor_mapping


class ResponsiveGrid(QWidget):
    def __init__(self, min_item_width=Theme.W_SIZE_S, parent=None):
        super().__init__(parent)
        self._items = []
        self._min_item_width = min_item_width
        self._cols = 1
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(10)
        self._pending_recalc = False

    def add_item(self, widget):
        widget._original_grid = self
        self._items.append(widget)
        self._grid.addWidget(widget, 0, len(self._items) - 1)
        self._relayout()
        self._schedule_recalc()

    def remove_item(self, widget):
        if widget in self._items:
            self._items.remove(widget)
            self._grid.removeWidget(widget)
            self._relayout()

    def resizeEvent(self, event): # pyright: ignore[reportIncompatibleMethodOverride]
        super().resizeEvent(event)
        self._schedule_recalc()

    def showEvent(self, event): # pyright: ignore[reportIncompatibleMethodOverride]
        super().showEvent(event)
        self._schedule_recalc()

    def _schedule_recalc(self):
        if not self._pending_recalc:
            self._pending_recalc = True
            QTimer.singleShot(0, self._recalc_columns)

    def _recalc_columns(self):
        self._pending_recalc = False
        width = self.width()
        if width <= 0:
            if self._cols != 1:
                self._cols = 1
                self._relayout()
            return
        new_cols = max(1, width // self._min_item_width)
        if new_cols != self._cols:
            self._cols = new_cols
            self._relayout()

    def _relayout(self):
        for i, widget in enumerate(self._items):
            row = i // self._cols
            col = i % self._cols
            self._grid.addWidget(widget, row, col)


class DualVoltagesTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = 1
        self.cols = 2
        self.latest_matrix = [["--", "--"]]

    def update_data(self, x_data, y_data):
        if len(x_data) > 0:
            latest = y_data[-1]
            self.latest_matrix[0][0] = f"{latest[0]:.2f} V" if len(latest) > 0 else "--"
            self.latest_matrix[0][1] = f"{latest[1]:.2f} V" if len(latest) > 1 else "--"
            self.layoutChanged.emit()

    def rowCount(self, parent=None):
        return self.rows

    def columnCount(self, parent=None):
        return self.cols

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        r, c = index.row(), index.column()
        val = self.latest_matrix[r][c]
        if role == Qt.ItemDataRole.DisplayRole:
            return val
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return ["Pre AIR", "Post AIR"][section]
        return None


class DualVoltagesPlot(TimeSeriesPlotWidget):
    def __init__(self, parent=None):
        super().__init__(
            title=Strings.TITLE_PACK_VOLTAGE,
            unit="V",
            series_count=2,
            label_formatter_callback=lambda i: ["Pre AIR", "Post AIR"][i],
            empty_text="No voltage data",
            colors=[Theme.SIGNAL_COLORS["pack_voltage_pre_air"], Theme.SIGNAL_COLORS["pack_voltage_post_air"]]
        )
        self.setMinimumHeight(Theme.H_SIZE_S)
        self.setMinimumWidth(Theme.W_SIZE_S)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.stats_lbl.hide()

    def _create_table_model(self):
        return DualVoltagesTableModel()


class MetricsScreen(QFrame):
    def __init__(self, volt_mapping, temp_mapping, parent=None):
        super().__init__(parent)
        self.volt_mapping = volt_mapping
        self.temp_mapping = temp_mapping
        self._maximized_widget = None
        self._original_grid = None
        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self._maximized_widget = None

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.setSpacing(10)

        self._stack = QStackedWidget()
        outer_layout.addWidget(self._stack)

        # Normal page
        normal_page = QWidget()
        layout = QVBoxLayout(normal_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        section_a = QFrame()
        section_a_layout = QVBoxLayout(section_a)
        section_a_layout.setContentsMargins(0, 0, 0, 0)
        section_a_layout.setSpacing(10)

        voltage_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)
        self.pack_voltage_plot = DualVoltagesPlot()
        self.pack_voltage_plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        voltage_row.add_item(self.pack_voltage_plot)
        section_a_layout.addWidget(voltage_row)

        current_soc_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)
        self.pack_current_plot = SimpleTimeSeriesPlot(
            title=Strings.TITLE_PACK_CURRENT,
            unit="A",
            label_formatter_callback=lambda i: Strings.LBL_PACK_CURRENT,
            empty_text="No current data",
            colors=[Theme.SIGNAL_COLORS["pack_current"]]
        )
        self.pack_current_plot.setMinimumHeight(Theme.H_SIZE_S)
        self.pack_current_plot.setMinimumWidth(Theme.W_SIZE_S)
        self.pack_current_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.pack_current_plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        current_soc_row.add_item(self.pack_current_plot)

        self.soc_plot = SimpleTimeSeriesPlot(
            title=Strings.TITLE_SOC,
            unit="%",
            label_formatter_callback=lambda i: "SoC",
            empty_text="No SoC data",
            colors=[Theme.SIGNAL_COLORS["soc"]]
        )
        self.soc_plot.setMinimumHeight(Theme.H_SIZE_S)
        self.soc_plot.setMinimumWidth(Theme.W_SIZE_S)
        self.soc_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.soc_plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        current_soc_row.add_item(self.soc_plot)
        section_a_layout.addWidget(current_soc_row)
        layout.addWidget(section_a)

        section_b = QFrame()
        section_b_layout = QVBoxLayout(section_b)
        section_b_layout.setContentsMargins(0, 0, 0, 0)
        section_b_layout.setSpacing(10)

        state_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)

        fsm_enum_map = {
            0: Strings.STATE_STANDBY,
            1: Strings.STATE_DRIVING,
            2: Strings.STATE_CHARGING,
            3: Strings.STATE_ERROR,
            4: Strings.STATE_PRECHARGING,
            5: Strings.STATE_PREPARING_CHARGING,
            6: Strings.STATE_INITIALIZING,
            7: Strings.STATE_EXITING_CHARGING,
            8: Strings.STATE_OVERRIDE,
            10: Strings.STATE_NONE,
        }
        self.fsm_plot = EnumPlot(
            title=Strings.TITLE_FSM_STATE,
            enum_map=fsm_enum_map,
            label_formatter_callback=lambda i: "FSM",
            empty_text="No FSM data"
        )
        self.fsm_plot.setMinimumHeight(Theme.H_SIZE_S)
        self.fsm_plot.setMinimumWidth(Theme.W_SIZE_S)
        self.fsm_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.fsm_plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        state_row.add_item(self.fsm_plot)

        actuator_labels = [
            Strings.STATE_AIR_PLUS,
            Strings.STATE_AIR_MINUS,
            Strings.STATE_PRECHARGE,
            Strings.STATE_SDC,
        ]
        self.actuator_plot = StackedBoolPlot(
            title=Strings.TITLE_ACTUATOR_STATE,
            series_labels=actuator_labels,
            empty_text="No actuator data"
        )
        self.actuator_plot.setMinimumHeight(Theme.H_SIZE_S)
        self.actuator_plot.setMinimumWidth(Theme.W_SIZE_S)
        self.actuator_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.actuator_plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        state_row.add_item(self.actuator_plot)

        section_b_layout.addWidget(state_row)
        layout.addWidget(section_b)

        section_c = QFrame()
        section_c_layout = QVBoxLayout(section_c)
        section_c_layout.setContentsMargins(0, 0, 0, 0)
        section_c_layout.setSpacing(10)

        voltage_cell_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)
        self.cell_voltages_plot = VoltagesPlotWidget(
            mapping=self.volt_mapping,
            label_formatter_callback=lambda i: f"Cell {i+1}"
        )
        self.cell_voltages_plot.setMinimumHeight(Theme.H_SIZE_S)
        self.cell_voltages_plot.setMinimumWidth(Theme.W_SIZE_S)
        self.cell_voltages_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.cell_voltages_plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        voltage_cell_row.add_item(self.cell_voltages_plot)

        self.voltage_histogram = BarChartWidget(
            title=Strings.TITLE_VOLTAGE_HISTOGRAM,
            unit=Strings.UNIT_VOLTAGE,
            bar_count=len(self.volt_mapping),
            label_formatter_callback=lambda i: f"Cell {i+1}",
            empty_text="No voltage data"
        )
        self.voltage_histogram.setMinimumHeight(Theme.H_SIZE_S)
        self.voltage_histogram.setMinimumWidth(Theme.W_SIZE_S)
        self.voltage_histogram.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.voltage_histogram.sig_maximize_toggled.connect(self._on_plot_maximize)
        voltage_cell_row.add_item(self.voltage_histogram)
        section_c_layout.addWidget(voltage_cell_row)

        temp_cell_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)
        self.cell_temps_plot = TemperaturesPlotWidget(
            mapping=self.temp_mapping,
            label_formatter_callback=lambda i: f"Sensor {i+1}"
        )
        self.cell_temps_plot.setMinimumHeight(Theme.H_SIZE_S)
        self.cell_temps_plot.setMinimumWidth(Theme.W_SIZE_S)
        self.cell_temps_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.cell_temps_plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        temp_cell_row.add_item(self.cell_temps_plot)

        self.temp_histogram = BarChartWidget(
            title=Strings.TITLE_TEMP_HISTOGRAM,
            unit=Strings.UNIT_TEMP,
            bar_count=len(self.temp_mapping),
            label_formatter_callback=lambda i: f"Sensor {i+1}",
            empty_text="No temperature data"
        )
        self.temp_histogram.setMinimumHeight(Theme.H_SIZE_S)
        self.temp_histogram.setMinimumWidth(Theme.W_SIZE_S)
        self.temp_histogram.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.temp_histogram.sig_maximize_toggled.connect(self._on_plot_maximize)
        temp_cell_row.add_item(self.temp_histogram)
        section_c_layout.addWidget(temp_cell_row)
        layout.addWidget(section_c)

        self._stack.addWidget(normal_page)

        # Maximized page
        self._max_page = QWidget()
        self._max_layout = QVBoxLayout(self._max_page)
        self._max_layout.setContentsMargins(0, 0, 0, 0)
        self._stack.addWidget(self._max_page)

    def _on_plot_maximize(self, checked):
        sender = self.sender()
        if not sender:
            return
        if checked:
            self._maximize_plot(sender)
        else:
            self._restore_normal()

    def _maximize_plot(self, plot_widget):
        self._maximized_widget = plot_widget
        self._original_grid = getattr(plot_widget, '_original_grid', None)
        if self._original_grid:
            self._original_grid.remove_item(plot_widget)
        self._max_layout.addWidget(plot_widget)
        self._stack.setCurrentIndex(1)
        QTimer.singleShot(0, self._constrain_max_page)

    def _constrain_max_page(self):
        scroll_area = None
        parent = self.parent()
        while parent:
            if isinstance(parent, QScrollArea):
                scroll_area = parent
                break
            parent = parent.parent()
        if scroll_area and scroll_area.viewport():
            self._max_page.setMaximumSize(scroll_area.viewport().size())
            self._max_page.setMinimumSize(scroll_area.viewport().size())

    def _restore_normal(self):
        if self._maximized_widget:
            self._max_layout.removeWidget(self._maximized_widget)
            if self._original_grid:
                self._original_grid.add_item(self._maximized_widget)
                self._maximized_widget.show()
            self._maximized_widget = None
            self._original_grid = None
        self._max_page.setMaximumSize(16777215, 16777215)
        self._max_page.setMinimumSize(0, 0)
        self._stack.setCurrentIndex(0)

    def add_point(self, current_time, telemetry):
        if telemetry.HasField("pack_state"):
            ps = telemetry.pack_state
            self.soc_plot.add_point(current_time, [ps.soc])
            self.pack_voltage_plot.add_point(current_time, [ps.voltage, ps.post_air_voltage])
            self.pack_current_plot.add_point(current_time, [ps.current])

        if telemetry.HasField("status"):
            self.fsm_plot.add_point(current_time, [telemetry.status.state])

        if telemetry.HasField("contactors"):
            c = telemetry.contactors
            self.actuator_plot.add_point(current_time, [c.air_pos, c.air_neg, c.pre_charge, c.sdc])

        if telemetry.HasField("cell_voltages"):
            volts = list(telemetry.cell_voltages.voltages)
            self.cell_voltages_plot.add_point(current_time, volts)
            self.voltage_histogram.update_data(volts)

        if telemetry.HasField("cell_temperatures"):
            temps = list(telemetry.cell_temperatures.temperatures)
            self.cell_temps_plot.add_point(current_time, temps)
            self.temp_histogram.update_data(temps)
