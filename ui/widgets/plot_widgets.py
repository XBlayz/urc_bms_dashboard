import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton,QGraphicsPathItem
)
from PyQt6.QtCore import Qt, QAbstractTableModel, pyqtSignal
from PyQt6.QtGui import QPainterPath

from ui.widgets.time_series_plot import TimeSeriesPlotWidget
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme


class SimpleTableModel(QAbstractTableModel):
    def __init__(self, rows=1, cols=1, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.cols = cols
        self.latest_matrix = [[None for _ in range(self.cols)] for _ in range(self.rows)]

    def update_data(self, x_data, y_data):
        if len(x_data) > 0:
            latest = y_data[-1]
            for i in range(min(len(latest), self.cols)):
                if i < self.rows:
                    self.latest_matrix[i][0] = latest[i]
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
            if val is not None:
                return f"{val:.3f}"
            return ""
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return f"Series {section + 1}"
            elif orientation == Qt.Orientation.Vertical:
                return f"Row {section + 1}"
        return None


class SimpleTimeSeriesPlot(TimeSeriesPlotWidget):
    def __init__(self, title, unit, label_formatter_callback, empty_text=Strings.EMPTY_CELL):
        super().__init__(
            title=title,
            unit=unit,
            series_count=1,
            label_formatter_callback=label_formatter_callback,
            empty_text=empty_text
        )

    def _create_table_model(self):
        return SimpleTableModel(rows=1, cols=1)


class EnumPlot(TimeSeriesPlotWidget):
    def __init__(self, title, enum_map, label_formatter_callback, empty_text=Strings.EMPTY_CELL):
        self.enum_map = enum_map
        super().__init__(
            title=title,
            unit="",
            series_count=1,
            label_formatter_callback=label_formatter_callback,
            empty_text=empty_text
        )

    def init_ui(self):
        super().init_ui()
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.hideButtons()
        self.auto_scroll_cb.setEnabled(False)
        self.auto_scroll_cb.setChecked(True)
        self.pause_cb.setEnabled(False)

    def on_auto_scroll_toggled(self, checked):
        pass

    def on_pause_toggled(self, checked):
        pass

    def update_data(self, x_view, data_2d, force=False):
        if len(x_view) == 0:
            return

        self._last_x_view = x_view
        self._last_data_2d = data_2d

        if self.stack.currentIndex() == 1:
            self.table_model.update_data(x_view, data_2d)

        if self.is_paused and not force:
            return

        # Map enum values to Y positions and colors
        values = data_2d[:len(x_view), 0]
        unique_states = sorted(set(values.astype(int)))
        state_to_y = {s: i for i, s in enumerate(unique_states)}

        y_positions = np.array([state_to_y.get(int(v), 0) for v in values])
        colors = []
        for v in values:
            state_name = self.enum_map.get(int(v), "NONE")
            color = Theme.STATE_COLORS.get(state_name, "#444444")
            colors.append(color)

        # Clear previous scatter
        if hasattr(self, '_scatter'):
            self.plot_widget.removeItem(self._scatter)

        # Create scatter with colored points
        spots = []
        for i in range(len(x_view)):
            spots.append(
                {'pos': (x_view[i], y_positions[i]), 'size': 8,
                 'brush': pg.mkBrush(colors[i]), 'pen': pg.mkPen(None)}
            )
        self._scatter = pg.ScatterPlotItem(spots=spots)
        self.plot_widget.addItem(self._scatter)

        # Update Y axis labels
        y_ticks = [(i, self.enum_map.get(s, str(s))) for s, i in state_to_y.items()]
        self.plot_widget.getAxis('left').setTicks([y_ticks])

        if self.auto_scroll_cb.isChecked():
            current_time = x_view[-1]
            window_size_seconds = 10
            min_x = max(0, current_time - window_size_seconds)
            self.plot_widget.setXRange(min_x, max(window_size_seconds, current_time))
            y_padding = 0.5
            self.plot_widget.setYRange(-y_padding, len(unique_states) - 1 + y_padding)

        # Update stats with current state
        current_state = int(values[-1]) if len(values) > 0 else -1
        state_name = self.enum_map.get(current_state, "--")
        self.stats_lbl.setText(f"STATE: {state_name}")

    def _create_table_model(self):
        return SimpleTableModel(rows=1, cols=1)


class StackedBoolPlot(QFrame):
    sig_maximize_toggled = pyqtSignal(bool)

    def __init__(self, title, series_labels, empty_text=Strings.EMPTY_CELL):
        super().__init__()
        self.title_text = title
        self.series_labels = series_labels
        self.series_count = len(series_labels)
        self.empty_text = empty_text

        self.curves = []
        self.fill_items = []
        self.colors = [
            "#00FF00", "#00AAFF", "#FFAA00", "#FF00FF",
            "#AA00FF", "#FF8800", "#00FFAA"
        ]

        self.hr_max = 1200
        self.hr_x = np.empty(self.hr_max, dtype=np.float64)
        self.hr_y = np.empty((self.hr_max, self.series_count), dtype=np.float64)
        self.hr_ptr = 0
        self.hr_count = 0

        self.lr_max = 10000
        self.lr_x = np.empty(self.lr_max, dtype=np.float64)
        self.lr_y = np.empty((self.lr_max, self.series_count), dtype=np.float64)
        self.lr_ptr = 0
        self.lr_count = 0

        self.ds_rate = 20
        self.ds_counter = 0
        self.is_paused = False

        self.setStyleSheet("""
            StackedBoolPlot {
                background-color: transparent;
            }
        """)

        self.init_ui()

    def init_ui(self):
        self.setObjectName("StackedBoolPlot")
        self.setStyleSheet(Theme.time_series_plot())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(40)
        header.setStyleSheet(Theme.plot_header())
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)

        title_lbl = QLabel(self.title_text)
        title_lbl.setStyleSheet(Theme.plot_title())
        header_layout.addWidget(title_lbl)

        self.reset_btn = QPushButton(Strings.BTN_RESET)
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setFixedHeight(22)
        self.reset_btn.setStyleSheet(Theme.toggle_button())
        self.reset_btn.clicked.connect(self.reset_data)
        header_layout.addWidget(self.reset_btn)

        header_layout.addStretch()

        self.stats_lbl = QLabel(Strings.STATS_EMPTY)
        self.stats_lbl.setStyleSheet(Theme.stats_label())
        header_layout.addWidget(self.stats_lbl)

        layout.addWidget(header)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(Theme.PG_BG)
        self.plot_widget.showGrid(x=True, y=True, alpha=Theme.PG_GRID_ALPHA)
        self.plot_widget.getAxis('bottom').setPen(Theme.PG_AXIS_PEN)
        self.plot_widget.getAxis('left').setPen(Theme.PG_AXIS_PEN)
        self.plot_widget.getAxis('bottom').setTextPen(Theme.PG_AXIS_TEXT)
        self.plot_widget.getAxis('left').setTextPen(Theme.PG_AXIS_TEXT)

        self.plot_widget.hideButtons()
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.setMouseEnabled(x=False, y=False)

        # Initialize fill paths
        for i in range(self.series_count):
            color = self.colors[i % len(self.colors)]
            path_item = QGraphicsPathItem()
            path_item.setPen(pg.mkPen(color=color, width=1))
            path_item.setBrush(pg.mkBrush(color + "40"))
            self.plot_widget.addItem(path_item)
            self.fill_items.append(path_item)

            # Top edge curve
            pen = pg.mkPen(color=color, width=2)
            curve = self.plot_widget.plot(pen=pen, stepMode=True)
            self.curves.append(curve)

        y_ticks = [(i, label) for i, label in enumerate(self.series_labels)]
        self.plot_widget.getAxis('left').setTicks([y_ticks])

        layout.addWidget(self.plot_widget, stretch=1)

    def add_point(self, current_time, y_data):
        if self.hr_count == self.hr_max:
            self.ds_counter += 1
            if self.ds_counter >= self.ds_rate:
                self.ds_counter = 0
                oldest_ptr = self.hr_ptr
                self.lr_x[self.lr_ptr] = self.hr_x[oldest_ptr]
                self.lr_y[self.lr_ptr, :] = self.hr_y[oldest_ptr, :]
                self.lr_ptr = (self.lr_ptr + 1) % self.lr_max
                if self.lr_count < self.lr_max:
                    self.lr_count += 1

        self.hr_x[self.hr_ptr] = current_time
        self.hr_y[self.hr_ptr, :] = y_data
        self.hr_ptr = (self.hr_ptr + 1) % self.hr_max
        if self.hr_count < self.hr_max:
            self.hr_count += 1

        if self.lr_count == 0:
            lr_x_out = np.array([], dtype=np.float64)
            lr_y_out = np.empty((0, self.series_count), dtype=np.float64)
        elif self.lr_count < self.lr_max:
            lr_x_out = self.lr_x[:self.lr_count]
            lr_y_out = self.lr_y[:self.lr_count]
        else:
            lr_x_out = np.concatenate((self.lr_x[self.lr_ptr:], self.lr_x[:self.lr_ptr]))
            lr_y_out = np.concatenate((self.lr_y[self.lr_ptr:], self.lr_y[:self.lr_ptr]))

        if self.hr_count < self.hr_max:
            hr_x_out = self.hr_x[:self.hr_count]
            hr_y_out = self.hr_y[:self.hr_count]
        else:
            hr_x_out = np.concatenate((self.hr_x[self.hr_ptr:], self.hr_x[:self.hr_ptr]))
            hr_y_out = np.concatenate((self.hr_y[self.hr_ptr:], self.hr_y[:self.hr_ptr]))

        if self.lr_count > 0:
            x_out = np.concatenate((lr_x_out, hr_x_out))
            y_out = np.concatenate((lr_y_out, hr_y_out))
        else:
            x_out = hr_x_out
            y_out = hr_y_out

        self.update_data(x_out, y_out)

    def update_data(self, x_view, data_2d, force=False):
        if len(x_view) == 0:
            return

        self._last_x_view = x_view
        self._last_data_2d = data_2d

        if self.is_paused and not force:
            return

        # Compute stacked cumulative sums
        cumsum = np.cumsum(data_2d[:len(x_view), :], axis=1)

        for i in range(self.series_count):
            upper = cumsum[:, i]
            if i == 0:
                lower = np.zeros(len(x_view))
            else:
                lower = cumsum[:, i - 1]

            # Update top curve (stepMode requires len(X) == len(Y) + 1)
            if len(x_view) > 0:
                x_step = np.empty(len(x_view) + 1, dtype=x_view.dtype)
                x_step[:-1] = x_view
                x_step[-1] = x_view[-1] + 1.0
            else:
                x_step = x_view
            self.curves[i].setData(x_step, upper, stepMode=True)

            # Build fill path between upper and lower
            path = QPainterPath()
            n = len(x_view)
            if n == 0:
                continue

            path.moveTo(x_view[0], lower[0])
            for j in range(n):
                path.lineTo(x_view[j], lower[j])
            for j in range(n - 1, -1, -1):
                path.lineTo(x_view[j], upper[j])
            path.closeSubpath()

            self.fill_items[i].setPath(path)

        current_time = x_view[-1]
        window_size_seconds = 10
        min_x = max(0, current_time - window_size_seconds)
        self.plot_widget.setXRange(min_x, max(window_size_seconds, current_time))
        self.plot_widget.setYRange(-0.2, self.series_count + 0.2)

        active_count = np.sum(data_2d[len(x_view) - 1, :])
        self.stats_lbl.setText(f"ACTIVE: {int(active_count)}/{self.series_count}")

    def reset_data(self):
        self.hr_ptr = 0
        self.hr_count = 0
        self.lr_ptr = 0
        self.lr_count = 0
        self.ds_counter = 0

        for curve in self.curves:
            curve.setData([], [])
        for item in self.fill_items:
            item.setPath(QPainterPath())
        self.stats_lbl.setText(Strings.STATS_EMPTY)


class BarChartWidget(QFrame):
    def __init__(self, title, unit, bar_count, label_formatter_callback, empty_text=Strings.EMPTY_CELL):
        super().__init__()
        self.title_text = title
        self.unit = unit
        self.bar_count = bar_count
        self.label_formatter = label_formatter_callback
        self.empty_text = empty_text

        self.values = np.zeros(bar_count, dtype=np.float64)
        self.current_data = np.zeros(bar_count, dtype=np.float64)

        self.setStyleSheet("""
            BarChartWidget {
                background-color: transparent;
            }
        """)

        self.init_ui()

    def init_ui(self):
        self.setObjectName("BarChartWidget")
        self.setStyleSheet(Theme.time_series_plot())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(40)
        header.setStyleSheet(Theme.plot_header())
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)

        title_lbl = QLabel(self.title_text)
        title_lbl.setStyleSheet(Theme.plot_title())
        header_layout.addWidget(title_lbl)

        self.reset_btn = QPushButton(Strings.BTN_RESET)
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setFixedHeight(22)
        self.reset_btn.setStyleSheet(Theme.toggle_button())
        self.reset_btn.clicked.connect(self.reset_data)
        header_layout.addWidget(self.reset_btn)

        header_layout.addStretch()

        self.stats_lbl = QLabel(Strings.STATS_EMPTY)
        self.stats_lbl.setStyleSheet(Theme.stats_label())
        header_layout.addWidget(self.stats_lbl)

        layout.addWidget(header)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(Theme.PG_BG)
        self.plot_widget.showGrid(x=True, y=True, alpha=Theme.PG_GRID_ALPHA)
        self.plot_widget.getAxis('bottom').setPen(Theme.PG_AXIS_PEN)
        self.plot_widget.getAxis('left').setPen(Theme.PG_AXIS_PEN)
        self.plot_widget.getAxis('bottom').setTextPen(Theme.PG_AXIS_TEXT)
        self.plot_widget.getAxis('left').setTextPen(Theme.PG_AXIS_TEXT)

        self.plot_widget.hideButtons()
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.setMouseEnabled(x=False, y=False)

        self.avg_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen(color="#FFAA00", width=1, style=Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.avg_line)

        self._dynamic_items = []
        layout.addWidget(self.plot_widget, stretch=1)

        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_move) # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]

    def _clear_dynamic(self):
        for item in self._dynamic_items:
            self.plot_widget.removeItem(item)
        self._dynamic_items = []

    def update_data(self, data_1d):
        self.current_data = np.array(data_1d, dtype=np.float64)
        self._render_bars()

    def _render_bars(self):
        self._clear_dynamic()

        data = self.current_data
        n = len(data)
        if n == 0:
            return

        x = np.arange(n)
        width = 0.6

        # Color bars: red for outliers (outside mean +/- 2*std), else green
        mean_val = np.mean(data)
        std_val = np.std(data)
        brushes = []
        for v in data:
            if abs(v - mean_val) > 2 * std_val:
                brushes.append(pg.mkBrush("#FF4444"))
            else:
                brushes.append(pg.mkBrush("#00FF00"))

        self.bar_item = pg.BarGraphItem(
            x=x, height=data, width=width, brushes=brushes,
            pen=pg.mkPen(None)
        )
        self.plot_widget.addItem(self.bar_item)
        self._dynamic_items.append(self.bar_item)

        # Value labels on top of bars (omitted for compatibility)

        # Average line
        self.avg_line.setPos(mean_val)
        self.avg_line.show()

        # Update stats
        d_min = np.min(data)
        d_max = np.max(data)
        self.stats_lbl.setText(Strings.FMT_STATS.format(std=std_val, max=d_max, min=d_min, unit=self.unit))

        # X axis labels
        ticks = []
        step = max(1, n // 10)
        for i in range(0, n, step):
            ticks.append((i, self.label_formatter(i)))
        self.plot_widget.getAxis('bottom').setTicks([ticks])

    def on_mouse_move(self, pos):
        if not self.plot_widget.sceneBoundingRect().contains(pos):
            return
        vb = self.plot_widget.getViewBox()
        mouse_point = vb.mapSceneToView(pos)
        x_data = np.arange(len(self.current_data))
        if len(x_data) == 0:
            return
        closest_idx = int(np.argmin(np.abs(x_data - mouse_point.x())))
        if 0 <= closest_idx < len(self.current_data):
            val = self.current_data[closest_idx]
            mean_val = np.mean(self.current_data)
            delta = val - mean_val
            label = self.label_formatter(closest_idx)
            tooltip = f"{label}: {val:.3f} {self.unit}\nDelta from avg: {delta:+.3f} {self.unit}"
            self.plot_widget.setToolTip(tooltip)

    def reset_data(self):
        self.current_data = np.zeros(self.bar_count, dtype=np.float64)
        self._render_bars()
