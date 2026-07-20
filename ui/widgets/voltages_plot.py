from ui.widgets.time_series_plot import TimeSeriesPlotWidget
from ui.strings import Strings


class VoltagesPlotWidget(TimeSeriesPlotWidget):
    """Cell voltages over time. Row/column layout with heatmap coloring lives on the
    corresponding voltage histogram's matrix view (BarChartWidget), not here."""

    def __init__(self, mapping, label_formatter_callback=None):
        self.mapping = mapping
        formatter = label_formatter_callback or self._default_label
        super().__init__(
            title=Strings.TITLE_VOLTAGES,
            unit=Strings.UNIT_VOLTAGE,
            series_count=len(mapping),
            label_formatter_callback=formatter,
            empty_text=Strings.EMPTY_CELL,
            stats_mode="instantaneous",
            show_stats_label=False
        )

    def _default_label(self, i):
        slave, cell = self.mapping[i]
        return Strings.FMT_CELL_LABEL.format(slave=slave + 1, cell=cell + 1)
