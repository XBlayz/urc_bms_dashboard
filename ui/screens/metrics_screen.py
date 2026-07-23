from PyQt6.QtWidgets import (
    QVBoxLayout, QSizePolicy, QWidget
)

from ui.widgets.time_series_plot import TimeSeriesPlotWidget
from ui.widgets.plot_widgets import EnumPlot, StackedBoolPlot, BarChartWidget, SimpleTimeSeriesPlot
from ui.widgets.voltages_plot import VoltagesPlotWidget
from ui.widgets.temperatures_plot import TemperaturesPlotWidget
from ui.widgets.responsive_grid import ResponsiveGrid
from ui.widgets.plot_host_mixin import PlotHostMixin
from ui.widgets.heatmap import VoltageHeatmap, TemperatureHeatmap
from ui.widgets.stacked_widget import CurrentPageStackedWidget
from ui.screens.telemetry_screen import TelemetryScreen
from ui.fsm_state import fsm_state_labels
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme
from data.hardware.hardware_config import SLAVE_COUNT, CELLS_PER_SLAVE, TEMP_SENSORS_PER_SLAVE


class DualVoltagesPlot(TimeSeriesPlotWidget):
    def __init__(self, parent=None):
        super().__init__(
            title=Strings.TITLE_PACK_VOLTAGE,
            unit="V",
            series_count=2,
            label_formatter_callback=lambda i: ["PACK (Pre-AIR)", "DC LINK (Post-AIR)"][i],
            empty_text="No voltage data",
            colors=[Theme.SIGNAL_COLORS["pack_voltage_pre_air"], Theme.SIGNAL_COLORS["pack_voltage_post_air"]],
            stats_mode="window",
            show_stats_label=False
        )
        self.setMinimumHeight(Theme.H_SIZE_S)
        self.setMinimumWidth(Theme.W_SIZE_S)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

class CurrentWithSopPlot(TimeSeriesPlotWidget):
    def __init__(self, parent=None):
        super().__init__(
            title=Strings.TITLE_PACK_CURRENT,
            unit="A",
            series_count=3,
            label_formatter_callback=lambda i: ["Current", "SOP (dis.)", "SOP (chg.)"][i],
            empty_text="No current data",
            colors=[Theme.SIGNAL_COLORS["pack_current"], Theme.SIGNAL_COLORS["sop_dischg"], Theme.SIGNAL_COLORS["sop_chg"]],
            dashed=[False, True, True],
            stats_mode="window",
            show_stats_label=False
        )
        self.setMinimumHeight(Theme.H_SIZE_S)
        self.setMinimumWidth(Theme.W_SIZE_S)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)


class MetricsScreen(TelemetryScreen, PlotHostMixin):
    def __init__(self, volt_mapping, temp_mapping, parent=None):
        super().__init__(parent)
        self.volt_mapping = volt_mapping
        self.temp_mapping = temp_mapping
        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        stack = CurrentPageStackedWidget()
        outer_layout.addWidget(stack)

        normal_page = QWidget()
        layout = QVBoxLayout(normal_page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # --- Section A: pack voltage / current / SoC ---
        voltage_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)
        self.pack_voltage_plot = DualVoltagesPlot()
        self.pack_voltage_plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        voltage_row.add_item(self.pack_voltage_plot)
        layout.addWidget(voltage_row)

        current_soc_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)
        self.pack_current_plot = CurrentWithSopPlot()
        self.pack_current_plot.sig_maximize_toggled.connect(self._on_plot_maximize)
        current_soc_row.add_item(self.pack_current_plot)

        self.soc_plot = self._build_simple_plot(
            Strings.TITLE_SOC, "%", "SoC", "No SoC data", Theme.SIGNAL_COLORS["soc"]
        )
        current_soc_row.add_item(self.soc_plot)
        layout.addWidget(current_soc_row)

        # --- Section B: FSM state / actuator states ---
        state_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)

        self.fsm_plot = EnumPlot(
            title=Strings.TITLE_FSM_STATE,
            label_formatter_callback=lambda i: "FSM",
            enum_map=fsm_state_labels(),
            empty_text="No FSM data"
        )
        self._configure_plot(self.fsm_plot)
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
        self._configure_plot(self.actuator_plot)
        state_row.add_item(self.actuator_plot)

        layout.addWidget(state_row)

        # --- Section C: cell voltages / temperatures (time series + histogram/matrix) ---
        voltage_cell_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)
        self.cell_voltages_plot = VoltagesPlotWidget(
            mapping=self.volt_mapping,
            label_formatter_callback=lambda i: f"Cell {i + 1}"
        )
        self._configure_plot(self.cell_voltages_plot)
        voltage_cell_row.add_item(self.cell_voltages_plot)

        self.voltage_histogram = BarChartWidget(
            title=Strings.TITLE_VOLTAGE_HISTOGRAM,
            unit=Strings.UNIT_VOLTAGE,
            bar_count=len(self.volt_mapping),
            label_formatter_callback=lambda i: f"Cell {i + 1}",
            empty_text="No voltage data",
            heatmap=VoltageHeatmap(Theme.VOLTAGE_MIN, Theme.VOLTAGE_OPT, Theme.VOLTAGE_MAX),
            matrix_mapping=self.volt_mapping,
            matrix_rows=SLAVE_COUNT,
            matrix_cols=CELLS_PER_SLAVE,
            matrix_row_label=lambda i: f"Slave {i + 1}",
            matrix_col_label=lambda i: f"Cell {i + 1}",
        )
        self._configure_plot(self.voltage_histogram)
        voltage_cell_row.add_item(self.voltage_histogram)
        layout.addWidget(voltage_cell_row)

        temp_cell_row = ResponsiveGrid(min_item_width=Theme.W_SIZE_S + 20)
        self.cell_temps_plot = TemperaturesPlotWidget(
            mapping=self.temp_mapping,
            label_formatter_callback=lambda i: f"Sensor {i + 1}"
        )
        self._configure_plot(self.cell_temps_plot)
        temp_cell_row.add_item(self.cell_temps_plot)

        self.temp_histogram = BarChartWidget(
            title=Strings.TITLE_TEMP_HISTOGRAM,
            unit=Strings.UNIT_TEMP,
            bar_count=len(self.temp_mapping),
            label_formatter_callback=lambda i: f"Sensor {i + 1}",
            empty_text="No temperature data",
            heatmap=TemperatureHeatmap(Theme.TEMP_MIN, Theme.TEMP_OPT, Theme.TEMP_MAX),
            matrix_mapping=self.temp_mapping,
            matrix_rows=SLAVE_COUNT,
            matrix_cols=TEMP_SENSORS_PER_SLAVE,
            matrix_row_label=lambda i: f"Slave {i + 1}",
            matrix_col_label=lambda i: f"Sensor {i + 1}",
        )
        self._configure_plot(self.temp_histogram)
        temp_cell_row.add_item(self.temp_histogram)
        layout.addWidget(temp_cell_row)

        self.cell_voltages_plot.sig_signal_selected.connect(self.voltage_histogram.set_external_highlight)
        self.voltage_histogram.sig_signal_selected.connect(self.cell_voltages_plot.set_external_highlight)

        self.cell_temps_plot.sig_signal_selected.connect(self.temp_histogram.set_external_highlight)
        self.temp_histogram.sig_signal_selected.connect(self.cell_temps_plot.set_external_highlight)

        stack.addWidget(normal_page)
        self._init_plot_host(stack)

    def _build_simple_plot(self, title, unit, label, empty_text, color):
        plot = SimpleTimeSeriesPlot(
            title=title, unit=unit, label_formatter_callback=lambda i: label,
            empty_text=empty_text, colors=[color]
        )
        self._configure_plot(plot)
        return plot

    def _configure_plot(self, plot):
        plot.setMinimumHeight(Theme.H_SIZE_S)
        plot.setMinimumWidth(Theme.W_SIZE_S)
        plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        plot.sig_maximize_toggled.connect(self._on_plot_maximize)

    def add_point(self, current_time, state):
        self.soc_plot.add_point(current_time, [state.soc])
        self.pack_voltage_plot.add_point(current_time, [state.pack_voltage, state.post_air_voltage])
        self.pack_current_plot.add_point(current_time, [state.pack_current, state.sop_dischg, -state.sop_chg])

        if state.bms_status is not None:
            self.fsm_plot.add_point(current_time, [state.bms_status.value])

        c = state.contactors
        self.actuator_plot.add_point(current_time, [
            int(c["air_pos"]),
            int(c["air_neg"]),
            int(c["pre_charge"]),
            int(c["sdc"])
        ])

        if state.cell_voltages.size > 0:
            self.cell_voltages_plot.add_point(current_time, state.cell_voltages)
            self.voltage_histogram.update_data(state.cell_voltages)

        if state.cell_temperatures.size > 0:
            self.cell_temps_plot.add_point(current_time, state.cell_temperatures)
            self.temp_histogram.update_data(state.cell_temperatures)

    def inject_gap(self, timestamp):
        """Inserisce dei valori NaN per spezzare le linee di trend temporali."""
        import numpy as np # Assicurati che np sia importato in cima al file
        self.soc_plot.add_point(timestamp, [np.nan])
        self.pack_voltage_plot.add_point(timestamp, [np.nan, np.nan])
        self.pack_current_plot.add_point(timestamp, [np.nan])
        self.fsm_plot.add_point(timestamp, [np.nan])
        self.actuator_plot.add_point(timestamp, [np.nan, np.nan, np.nan, np.nan])

    def clear_selection(self):
        for plot in (
            self.pack_current_plot, self.soc_plot, self.pack_voltage_plot,
            self.fsm_plot, self.actuator_plot, self.cell_voltages_plot, self.cell_temps_plot,
            self.voltage_histogram, self.temp_histogram,
        ):
            if hasattr(plot, 'clear_selection'):
                plot.clear_selection() # pyright: ignore[reportAttributeAccessIssue]
