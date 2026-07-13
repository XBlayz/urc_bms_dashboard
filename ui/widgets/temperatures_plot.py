from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QAbstractTableModel
from ui.widgets.time_series_plot import TimeSeriesPlotWidget
from ui.strings import Strings

class TemperaturesTableModel(QAbstractTableModel):
    def __init__(self, mapping, parent=None):
        super().__init__(parent)
        self.mapping = mapping

        self.rows = 25
        self.cols = 7

        self.index_to_rc = {}
        for i, (slave, sensor) in enumerate(self.mapping):
            self.index_to_rc[i] = (slave, sensor)

        self.latest_matrix = [[None for _ in range(self.cols)] for _ in range(self.rows)]

        self.MIN_T = 15.0
        self.OPT_T = 35.0
        self.MAX_T = 60.0

    def update_data(self, x_data, y_data):
        if len(x_data) > 0:
            latest = y_data[-1]
            for i, val in enumerate(latest):
                if i in self.index_to_rc:
                    r, c = self.index_to_rc[i]
                    self.latest_matrix[r][c] = val
            self.layoutChanged.emit()

    def rowCount(self, parent=None):
        return self.rows

    def columnCount(self, parent=None):
        return self.cols

    def get_heatmap_color(self, value):
        if value is None:
            return None

        if value <= self.MIN_T:
            return QColor(0, 0, 255, 60)
        elif value >= self.MAX_T:
            return QColor(255, 0, 0, 60)

        if value <= self.OPT_T:
            ratio = (value - self.MIN_T) / (self.OPT_T - self.MIN_T)
            b = int((1 - ratio) * 255)
            g = int(ratio * 255)
            return QColor(0, g, b, 80)
        else:
            ratio = (value - self.OPT_T) / (self.MAX_T - self.OPT_T)
            r = int(ratio * 255)
            g = int((1 - ratio) * 255)
            return QColor(r, g, 0, 80)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        r, c = index.row(), index.column()
        val = self.latest_matrix[r][c]

        if role == Qt.ItemDataRole.DisplayRole:
            if val is not None:
                return f"{val:.1f}"
            return ""

        elif role == Qt.ItemDataRole.BackgroundRole:
            color = self.get_heatmap_color(val)
            if color:
                return color

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return f"Sensor {section + 1}"
            elif orientation == Qt.Orientation.Vertical:
                return f"Slave {section + 1}"
        return None

class TemperaturesPlotWidget(TimeSeriesPlotWidget):
    def __init__(self, mapping, label_formatter_callback):
        self.mapping = mapping
        super().__init__(
            title=Strings.TITLE_TEMPERATURES,
            unit=Strings.UNIT_TEMP,
            series_count=len(mapping),
            label_formatter_callback=label_formatter_callback,
            empty_text=Strings.EMPTY_SENSOR
        )

    def _create_table_model(self):
        return TemperaturesTableModel(self.mapping)
