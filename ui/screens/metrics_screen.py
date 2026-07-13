import numpy as np
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QGridLayout, QWidget
)
from PyQt6.QtCore import Qt, QTimer

from ui.widgets.plot_widgets import EnumPlot, StackedBoolPlot, BarChartWidget, SimpleTimeSeriesPlot
from ui.widgets.voltages_plot import VoltagesPlotWidget
from ui.widgets.temperatures_plot import TemperaturesPlotWidget
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme


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
        self._items.append(widget)
        self._grid.addWidget(widget, 0, len(self._items) - 1)
        self._relayout()
        self._schedule_recalc()

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


class MetricsScreen(QFrame):
    def __init__(self, volt_mapping, temp_mapping, parent=None):
        super().__init__(parent)
        self.volt_mapping = volt_mapping
        self.temp_mapping = temp_mapping
        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        section_a = QFrame()
        section_a_layout = QVBoxLayout(section_a)
        section_a_layout.setContentsMargins(0, 0, 0, 0)
        section_a_layout.setSpacing(10)

        voltage_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)
        self.pack_voltage_plot = SimpleTimeSeriesPlot(
            title=Strings.TITLE_PACK_VOLTAGE,
            unit="V",
            label_formatter_callback=lambda i: Strings.LBL_PACK_VOLTAGE,
            empty_text="No voltage data"
        )
        self.pack_voltage_plot.setMinimumHeight(Theme.H_SIZE_S)
        self.pack_voltage_plot.setMinimumWidth(Theme.W_SIZE_S)
        self.pack_voltage_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        voltage_row.add_item(self.pack_voltage_plot)

        self.pack_voltage_post_air_plot = SimpleTimeSeriesPlot(
            title=Strings.TITLE_PACK_VOLTAGE_POST_AIR,
            unit="V",
            label_formatter_callback=lambda i: Strings.LBL_PACK_VOLTAGE_POST_AIR,
            empty_text="No post-AIR voltage data"
        )
        self.pack_voltage_post_air_plot.setMinimumHeight(Theme.H_SIZE_S)
        self.pack_voltage_post_air_plot.setMinimumWidth(Theme.W_SIZE_S)
        self.pack_voltage_post_air_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        voltage_row.add_item(self.pack_voltage_post_air_plot)

        section_a_layout.addWidget(voltage_row)

        current_soc_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)
        self.pack_current_plot = SimpleTimeSeriesPlot(
            title=Strings.TITLE_PACK_CURRENT,
            unit="A",
            label_formatter_callback=lambda i: Strings.LBL_PACK_CURRENT,
            empty_text="No current data"
        )
        self.pack_current_plot.setMinimumHeight(Theme.H_SIZE_S)
        self.pack_current_plot.setMinimumWidth(Theme.W_SIZE_S)
        self.pack_current_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        current_soc_row.add_item(self.pack_current_plot)

        self.soc_plot = SimpleTimeSeriesPlot(
            title=Strings.TITLE_SOC,
            unit="%",
            label_formatter_callback=lambda i: "SoC",
            empty_text="No SoC data"
        )
        self.soc_plot.setMinimumHeight(Theme.H_SIZE_S)
        self.soc_plot.setMinimumWidth(Theme.W_SIZE_S)
        self.soc_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
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
        temp_cell_row.add_item(self.temp_histogram)

        section_c_layout.addWidget(temp_cell_row)
        layout.addWidget(section_c)

    def add_point(self, current_time, telemetry):
        if telemetry.HasField("pack_state"):
            ps = telemetry.pack_state
            self.soc_plot.add_point(current_time, [ps.soc])
            self.pack_voltage_plot.add_point(current_time, [ps.voltage])
            self.pack_voltage_post_air_plot.add_point(current_time, [ps.post_air_voltage])
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
