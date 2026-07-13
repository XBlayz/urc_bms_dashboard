from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QSizePolicy

from ui.widgets.plot_widgets import EnumPlot, StackedBoolPlot, BarChartWidget, SimpleTimeSeriesPlot
from ui.widgets.voltages_plot import VoltagesPlotWidget
from ui.widgets.temperatures_plot import TemperaturesPlotWidget
from ui.strings import Strings


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

        # Section A: Pack-level metrics grouped by unit
        section_a = QFrame()
        section_a_layout = QVBoxLayout(section_a)
        section_a_layout.setContentsMargins(0, 0, 0, 0)
        section_a_layout.setSpacing(8)

        # Row: Pack V pre | Pack V post (same unit: V)
        voltage_row = QHBoxLayout()
        voltage_row.setSpacing(8)

        self.pack_voltage_plot = SimpleTimeSeriesPlot(
            title=Strings.TITLE_PACK_VOLTAGE,
            unit="V",
            label_formatter_callback=lambda i: Strings.LBL_PACK_VOLTAGE,
            empty_text="No voltage data"
        )
        self.pack_voltage_plot.setMinimumHeight(180)
        self.pack_voltage_plot.setMinimumWidth(300)
        self.pack_voltage_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        voltage_row.addWidget(self.pack_voltage_plot, stretch=1)

        self.pack_voltage_post_air_plot = SimpleTimeSeriesPlot(
            title=Strings.TITLE_PACK_VOLTAGE_POST_AIR,
            unit="V",
            label_formatter_callback=lambda i: Strings.LBL_PACK_VOLTAGE_POST_AIR,
            empty_text="No post-AIR voltage data"
        )
        self.pack_voltage_post_air_plot.setMinimumHeight(180)
        self.pack_voltage_post_air_plot.setMinimumWidth(300)
        self.pack_voltage_post_air_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        voltage_row.addWidget(self.pack_voltage_post_air_plot, stretch=1)

        section_a_layout.addLayout(voltage_row)

        # Row: Pack I | SoC
        current_soc_row = QHBoxLayout()
        current_soc_row.setSpacing(8)

        self.pack_current_plot = SimpleTimeSeriesPlot(
            title=Strings.TITLE_PACK_CURRENT,
            unit="A",
            label_formatter_callback=lambda i: Strings.LBL_PACK_CURRENT,
            empty_text="No current data"
        )
        self.pack_current_plot.setMinimumHeight(180)
        self.pack_current_plot.setMinimumWidth(300)
        self.pack_current_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        current_soc_row.addWidget(self.pack_current_plot, stretch=1)

        self.soc_plot = SimpleTimeSeriesPlot(
            title=Strings.TITLE_SOC,
            unit="%",
            label_formatter_callback=lambda i: "SoC",
            empty_text="No SoC data"
        )
        self.soc_plot.setMinimumHeight(180)
        self.soc_plot.setMinimumWidth(300)
        self.soc_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        current_soc_row.addWidget(self.soc_plot, stretch=1)

        section_a_layout.addLayout(current_soc_row)

        layout.addWidget(section_a)

        # Section B: State charts
        section_b = QFrame()
        section_b_layout = QHBoxLayout(section_b)
        section_b_layout.setContentsMargins(0, 0, 0, 0)
        section_b_layout.setSpacing(10)

        # FSM state plot
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
        self.fsm_plot.setMinimumHeight(160)
        self.fsm_plot.setMinimumWidth(300)
        self.fsm_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        section_b_layout.addWidget(self.fsm_plot, stretch=1)

        # Actuator states plot
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
        self.actuator_plot.setMinimumHeight(160)
        self.actuator_plot.setMinimumWidth(300)
        self.actuator_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        section_b_layout.addWidget(self.actuator_plot, stretch=1)

        layout.addWidget(section_b)

        # Section C: Cell statistics grouped by unit
        section_c = QFrame()
        section_c_layout = QVBoxLayout(section_c)
        section_c_layout.setContentsMargins(0, 0, 0, 0)
        section_c_layout.setSpacing(8)

        # Row: Cell voltages time series | Voltage histogram (same unit: V)
        voltage_cell_row = QHBoxLayout()
        voltage_cell_row.setSpacing(8)

        self.cell_voltages_plot = VoltagesPlotWidget(
            mapping=self.volt_mapping,
            label_formatter_callback=lambda i: f"Cell {i+1}"
        )
        self.cell_voltages_plot.setMinimumHeight(250)
        self.cell_voltages_plot.setMinimumWidth(300)
        self.cell_voltages_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        voltage_cell_row.addWidget(self.cell_voltages_plot, stretch=1)

        self.voltage_histogram = BarChartWidget(
            title=Strings.TITLE_VOLTAGE_HISTOGRAM,
            unit=Strings.UNIT_VOLTAGE,
            bar_count=len(self.volt_mapping),
            label_formatter_callback=lambda i: f"Cell {i+1}",
            empty_text="No voltage data"
        )
        self.voltage_histogram.setMinimumHeight(250)
        self.voltage_histogram.setMinimumWidth(300)
        self.voltage_histogram.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        voltage_cell_row.addWidget(self.voltage_histogram, stretch=1)

        section_c_layout.addLayout(voltage_cell_row)

        # Row: Cell temperatures time series | Temperature histogram (same unit: °C)
        temp_cell_row = QHBoxLayout()
        temp_cell_row.setSpacing(8)

        self.cell_temps_plot = TemperaturesPlotWidget(
            mapping=self.temp_mapping,
            label_formatter_callback=lambda i: f"Sensor {i+1}"
        )
        self.cell_temps_plot.setMinimumHeight(250)
        self.cell_temps_plot.setMinimumWidth(300)
        self.cell_temps_plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        temp_cell_row.addWidget(self.cell_temps_plot, stretch=1)

        self.temp_histogram = BarChartWidget(
            title=Strings.TITLE_TEMP_HISTOGRAM,
            unit=Strings.UNIT_TEMP,
            bar_count=len(self.temp_mapping),
            label_formatter_callback=lambda i: f"Sensor {i+1}",
            empty_text="No temperature data"
        )
        self.temp_histogram.setMinimumHeight(250)
        self.temp_histogram.setMinimumWidth(300)
        self.temp_histogram.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        temp_cell_row.addWidget(self.temp_histogram, stretch=1)

        section_c_layout.addLayout(temp_cell_row)

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
