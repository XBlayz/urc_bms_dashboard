from ui.widgets.time_series_plot import TimeSeriesPlotWidget
from ui.strings import Strings


class TemperaturesPlotWidget(TimeSeriesPlotWidget):
    """Cell temperatures over time. Row/column layout with heatmap coloring lives on the
    corresponding temperature histogram's matrix view (BarChartWidget), not here."""

    def __init__(self, mapping, label_formatter_callback=None):
        self.mapping = mapping
        formatter = label_formatter_callback or self._default_label
        super().__init__(
            title=Strings.TITLE_TEMPERATURES,
            unit=Strings.UNIT_TEMP,
            series_count=len(mapping),
            label_formatter_callback=formatter,
            empty_text=Strings.EMPTY_SENSOR,
            stats_mode="instantaneous",
            show_stats_label=False
        )

    def _default_label(self, i):
        slave, sensor = self.mapping[i]
        return Strings.FMT_SENSOR_LABEL.format(slave=slave + 1, sensor=sensor + 1)
