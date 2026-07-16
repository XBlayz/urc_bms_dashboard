"""Table models backing the tabular views of the various plot widgets.

- SignalTimeTableModel: rows = signals, columns = time instants (time_series_plot spec 2.1).
- TransitionTableModel: same shape, but columns are limited to state-transition instants
  (time_series_plot_enum / time_series_stacked_plot_bool spec 2.1.1 / 2.1.2).
- MatrixTableModel: spatial rows(slave) x cols(local index) heatmap grid (bar_chart spec 2.2).
"""

import numpy as np
from PyQt6.QtCore import Qt, QAbstractTableModel
from PyQt6.QtGui import QColor


def _to_qcolor(color):
    if color is None:
        return None
    if isinstance(color, (list, tuple)):
        return QColor(*color)
    return QColor(color)


def compute_transition_indices(values_2d):
    """Returns sorted sample indices where at least one column's value changes,
    always including index 0 when data is present."""
    if len(values_2d) == 0:
        return np.empty(0, dtype=int)
    diffs = np.any(values_2d[1:] != values_2d[:-1], axis=1)
    change_indices = np.nonzero(diffs)[0] + 1
    return np.concatenate(([0], change_indices))


class SignalTimeTableModel(QAbstractTableModel):
    """Rows = signals, columns = time instants; row labels colored like their curve."""

    def __init__(self, series_count, label_formatter, colors, parent=None):
        super().__init__(parent)
        self.series_count = series_count
        self.label_formatter = label_formatter
        self.colors = colors
        self._x = np.empty(0, dtype=np.float64)
        self._y = np.empty((0, series_count), dtype=np.float64)

    def update_data(self, x_data, y_data):
        self.beginResetModel()
        self._x = x_data
        self._y = y_data
        self.endResetModel()

    def rowCount(self, parent=None):
        return self.series_count

    def columnCount(self, parent=None):
        return len(self._x)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if col >= len(self._x) or row >= self._y.shape[1]:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return f"{self._y[col, row]:.3f}"
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Vertical:
            if role == Qt.ItemDataRole.DisplayRole:
                return self.label_formatter(section)
            if role == Qt.ItemDataRole.ForegroundRole and section < len(self.colors):
                return _to_qcolor(self.colors[section])
        elif orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole and section < len(self._x):
                return f"{self._x[section]:.2f}s"
        return None


class TransitionTableModel(QAbstractTableModel):
    """Tabular view limited to time instants where at least one tracked signal changed value."""

    def __init__(self, series_count, label_formatter, value_formatter, colors=None, parent=None):
        super().__init__(parent)
        self.series_count = series_count
        self.label_formatter = label_formatter
        self.value_formatter = value_formatter
        self.colors = colors or []
        self._x = np.empty(0, dtype=np.float64)
        self._y = np.empty((0, series_count), dtype=np.float64)
        self._transition_idx = np.empty(0, dtype=int)

    def update_data(self, x_data, y_data):
        self.beginResetModel()
        self._x = x_data
        self._y = y_data
        self._transition_idx = compute_transition_indices(y_data)
        self.endResetModel()

    def rowCount(self, parent=None):
        return self.series_count

    def columnCount(self, parent=None):
        return len(self._transition_idx)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if col >= len(self._transition_idx):
            return None
        sample_idx = self._transition_idx[col]
        if role == Qt.ItemDataRole.DisplayRole:
            return self.value_formatter(row, self._y[sample_idx, row])
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Vertical:
            if role == Qt.ItemDataRole.DisplayRole:
                return self.label_formatter(section)
            if role == Qt.ItemDataRole.ForegroundRole and section < len(self.colors):
                return _to_qcolor(self.colors[section])
        elif orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole and section < len(self._transition_idx):
                return f"{self._x[self._transition_idx[section]]:.2f}s"
        return None


class MatrixTableModel(QAbstractTableModel):
    """Spatial rows(slave) x cols(local index) heatmap grid for the bar_chart matrix view."""

    def __init__(self, mapping, rows, cols, heatmap, row_label_fmt, col_label_fmt, parent=None):
        super().__init__(parent)
        self.mapping = mapping
        self.rows = rows
        self.cols = cols
        self.heatmap = heatmap
        self.row_label_fmt = row_label_fmt
        self.col_label_fmt = col_label_fmt
        self._values = [[None for _ in range(cols)] for _ in range(rows)]

    def update_data(self, values_1d):
        for flat_idx, (r, c) in enumerate(self.mapping):
            if flat_idx >= len(values_1d):
                break
            if r < self.rows and c < self.cols:
                self._values[r][c] = float(values_1d[flat_idx])
        self.layoutChanged.emit()

    def rowCount(self, parent=None):
        return self.rows

    def columnCount(self, parent=None):
        return self.cols

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        val = self._values[index.row()][index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            return f"{val:.2f}" if val is not None else ""
        if role == Qt.ItemDataRole.BackgroundRole and self.heatmap is not None and val is not None:
            return self.heatmap.color_for(val)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self.col_label_fmt(section)
        return self.row_label_fmt(section)
