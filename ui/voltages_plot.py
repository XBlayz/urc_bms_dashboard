from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QAbstractTableModel
from ui.time_series_plot import TimeSeriesPlotWidget
from ui.strings import Strings

class VoltagesTableModel(QAbstractTableModel):
    def __init__(self, mapping, parent=None):
        super().__init__(parent)
        self.mapping = mapping
        
        self.rows = 25
        self.cols = 6
        
        self.index_to_rc = {}
        for i, (slave, cell) in enumerate(self.mapping):
            self.index_to_rc[i] = (slave, cell)
            
        self.latest_matrix = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        
        self.MIN_V = 2.5
        self.OPT_V = 3.6
        self.MAX_V = 4.2

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
        if value is None: return None
        
        if value <= self.MIN_V:
            return QColor(255, 0, 0, 60)
        elif value >= self.MAX_V:
            return QColor(255, 0, 0, 60)
            
        if value <= self.OPT_V:
            ratio = (value - self.MIN_V) / (self.OPT_V - self.MIN_V)
            r = int((1 - ratio) * 255)
            g = int(ratio * 255)
            return QColor(r, g, 0, 80)
        else:
            ratio = (value - self.OPT_V) / (self.MAX_V - self.OPT_V)
            r = int(ratio * 255)
            g = int((1 - ratio) * 255)
            return QColor(r, g, 0, 80)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): return None
        r, c = index.row(), index.column()
        val = self.latest_matrix[r][c]
        
        if role == Qt.ItemDataRole.DisplayRole:
            if val is not None:
                return f"{val:.3f}"
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
                return f"Cell {section + 1}"
            elif orientation == Qt.Orientation.Vertical:
                return f"Slave {section + 1}"
        return None

class VoltagesPlotWidget(TimeSeriesPlotWidget):
    def __init__(self, mapping, label_formatter_callback):
        self.mapping = mapping
        super().__init__(
            title=Strings.TITLE_VOLTAGES,
            unit=Strings.UNIT_VOLTAGE,
            series_count=len(mapping),
            label_formatter_callback=label_formatter_callback,
            empty_text=Strings.EMPTY_CELL
        )
        
    def _create_table_model(self):
        return VoltagesTableModel(self.mapping)
