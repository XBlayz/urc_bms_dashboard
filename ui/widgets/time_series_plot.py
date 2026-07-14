import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QTableView
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from ui.widgets.selection_panel import SelectionPanel
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme

class ToggleButton(QPushButton):
    def __init__(self, text=Strings.BTN_AUTO_SCROLL, checked=True):
        super().__init__(text)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(22)
        self.setStyleSheet(Theme.toggle_button())

class LegendButton(QPushButton):
    def __init__(self, label, color, index, parent=None):
        super().__init__(parent)
        self._index = index
        self._visible = True
        self._color = color
        self.setText(f"  {label}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(20)
        self._update_style()

    def _update_style(self):
        color = self._color if self._visible else "#555555"
        bg = "#2A2A2A" if self._visible else "#1A1A1A"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {color};
                border: none;
                border-radius: 4px;
                text-align: left;
                font-size: 11px;
                font-family: monospace;
                padding-left: 4px;
            }}
            QPushButton:hover {{
                background-color: #333333;
            }}
        """)

    def toggle_visibility(self):
        self._visible = not self._visible
        self._update_style()
        return self._visible

    def is_visible(self):
        return self._visible

    def index(self):
        return self._index

class TimeSeriesPlotWidget(QFrame):
    sig_maximize_toggled = pyqtSignal(bool)

    def __init__(self, title, unit, series_count, label_formatter_callback, empty_text=Strings.EMPTY_CELL, colors=None):
        super().__init__()
        self.title_text = title
        self.unit = unit
        self.series_count = series_count
        self.label_formatter = label_formatter_callback
        self.empty_text = empty_text
        self._signal_colors = colors

        self.curves = []
        self.colors = []
        self._series_visible = [True] * series_count

        # High-res buffer
        self.hr_max = 1200
        self.hr_x = np.empty(self.hr_max, dtype=np.float64)
        self.hr_y = np.empty((self.hr_max, self.series_count), dtype=np.float64)
        self.hr_ptr = 0
        self.hr_count = 0

        # Low-res buffer
        self.lr_max = 10000
        self.lr_x = np.empty(self.lr_max, dtype=np.float64)
        self.lr_y = np.empty((self.lr_max, self.series_count), dtype=np.float64)
        self.lr_ptr = 0
        self.lr_count = 0

        # Decimation config
        self.ds_rate = 20
        self.ds_counter = 0

        self._is_dragging = False

        self.setStyleSheet("""
            TimeSeriesPlotWidget {
                background-color: transparent;
            }
        """)

        self.init_ui()

    def init_ui(self):
        self.setObjectName("TimeSeriesPlotWidget")
        self.setStyleSheet(Theme.time_series_plot())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(40)
        header.setStyleSheet(Theme.plot_header())
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)

        title_lbl = QLabel(self.title_text)
        title_lbl.setStyleSheet(Theme.plot_title())
        header_layout.addWidget(title_lbl)

        self.auto_scroll_cb = ToggleButton(Strings.BTN_AUTO_SCROLL, checked=True)
        self.auto_scroll_cb.toggled.connect(self.on_auto_scroll_toggled)
        header_layout.addWidget(self.auto_scroll_cb)

        self.pause_cb = ToggleButton(Strings.BTN_PAUSE, checked=False)
        self.pause_cb.toggled.connect(self.on_pause_toggled)
        header_layout.addWidget(self.pause_cb)

        self.table_cb = ToggleButton(Strings.BTN_TABLE, checked=False)
        self.table_cb.toggled.connect(self.on_table_toggled)
        header_layout.addWidget(self.table_cb)

        self.maximize_cb = ToggleButton(Strings.BTN_MAXIMIZE, checked=False)
        self.maximize_cb.toggled.connect(self.on_maximize_toggled)
        header_layout.addWidget(self.maximize_cb)

        self.reset_btn = QPushButton(Strings.BTN_RESET)
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setFixedHeight(22)
        self.reset_btn.setStyleSheet(Theme.toggle_button())
        self.reset_btn.clicked.connect(self.reset_data)
        header_layout.addWidget(self.reset_btn)

        self.is_paused = False

        header_layout.addStretch()

        self.stats_lbl = QLabel(Strings.STATS_EMPTY)
        self.stats_lbl.setStyleSheet(Theme.stats_label())
        header_layout.addWidget(self.stats_lbl)

        layout.addWidget(header)

        # Main stack
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, stretch=1)

        # Plot Area Container (Page 0)
        self._plot_container = QFrame()
        self._plot_container.setStyleSheet("""
            QFrame {
                background-color: #2A2A2A;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)
        self._plot_layout = QVBoxLayout(self._plot_container)
        self._plot_layout.setContentsMargins(10, 10, 10, 10)

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

        # Initialize curves
        for i in range(self.series_count):
            if self._signal_colors and i < len(self._signal_colors):
                color = self._signal_colors[i]
            else:
                color = np.random.randint(50, 255, 3).tolist()
            self.colors.append(color)
            pen = pg.mkPen(color=color, width=1)
            curve = self.plot_widget.plot(pen=pen, autoDownsample=True, clipToView=True)
            self.curves.append(curve)

        # Cursor lines
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(color=Theme.PG_CROSSHAIR, width=1, style=Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.v_line)
        self.v_line.hide()

        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen(color=Theme.PG_CROSSHAIR, width=1, style=Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.h_line)
        self.h_line.hide()

        # Hover point
        self.hover_point = pg.ScatterPlotItem(size=8, pen=pg.mkPen(None), brush=pg.mkBrush(255, 255, 255, 255))
        self.hover_point.setZValue(20)
        self.plot_widget.addItem(self.hover_point)
        self.hover_point.hide()

        # Cursor value label
        self.cursor_label = QLabel("", self._plot_container)
        self.cursor_label.setStyleSheet("color: #DDDDDD; font-size: 11px; font-family: monospace; background: rgba(0,0,0,120); padding: 2px 4px; border-radius: 4px;")
        self.cursor_label.hide()

        self.selected_series_idx = None

        self._plot_layout.addWidget(self.plot_widget, stretch=1)

        # Legend Panel (below plot)
        self.legend_panel = QFrame()
        self.legend_panel.setStyleSheet("""
            QFrame {
                background-color: #222222;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)
        self.legend_layout = QHBoxLayout(self.legend_panel)
        self.legend_layout.setContentsMargins(8, 4, 8, 4)
        self.legend_layout.setSpacing(4)
        self.legend_buttons = []
        for i in range(self.series_count):
            label = self.label_formatter(i)
            color = self.colors[i] if i < len(self.colors) else "#888888"
            if isinstance(color, list):
                color_hex = '#%02x%02x%02x' % tuple(color)
            else:
                color_hex = color
            btn = LegendButton(label, color_hex, i)
            btn.clicked.connect(self._on_legend_clicked)
            self.legend_layout.addWidget(btn)
            self.legend_buttons.append(btn)
        self.legend_layout.addStretch()
        self._plot_layout.addWidget(self.legend_panel)

        # Selection Panel
        self.selection_panel = SelectionPanel(self.empty_text)
        self._plot_layout.addWidget(self.selection_panel)

        self.stack.addWidget(self._plot_container)

        # Table View Container (Page 1)
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: #2A2A2A;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(10, 10, 10, 10)

        self.table_view = QTableView()
        self.table_view.setStyleSheet(Theme.table_view())
        self.table_model = self._create_table_model()
        self.table_view.setModel(self.table_model)

        from PyQt6.QtWidgets import QHeaderView
        table_header = self.table_view.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            table_header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        table_layout.addWidget(self.table_view, stretch=1)
        self.stack.addWidget(table_container)

        # Events
        self.plot_widget.scene().sigMouseClicked.connect(self.on_mouse_click)
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_move)

    def _on_legend_clicked(self):
        sender = self.sender()
        if not isinstance(sender, LegendButton):
            return
        idx = sender.index()
        visible = sender.toggle_visibility()
        self._series_visible[idx] = visible
        self.curves[idx].setVisible(visible)
        if hasattr(self, '_last_x_view'):
            self.update_data(self._last_x_view, self._last_data_2d, force=True)

    def on_maximize_toggled(self, checked):
        self.sig_maximize_toggled.emit(checked)

    def on_auto_scroll_toggled(self, checked):
        is_auto = checked
        if is_auto:
            self.plot_widget.setMouseEnabled(x=False, y=False)
            self.plot_widget.setMenuEnabled(False)
            self.plot_widget.hideButtons()
        else:
            self.plot_widget.setMouseEnabled(x=True, y=True)
            self.plot_widget.setMenuEnabled(True)
            self.plot_widget.showButtons()
            self.plot_widget.enableAutoRange(axis='y')

    def on_pause_toggled(self, checked):
        self.is_paused = checked
        if not self.is_paused and hasattr(self, '_last_x_view'):
            self.update_data(self._last_x_view, self._last_data_2d, force=True)

    def reset_data(self):
        self.hr_ptr = 0
        self.hr_count = 0
        self.lr_ptr = 0
        self.lr_count = 0
        self.ds_counter = 0
        self._series_visible = [True] * self.series_count

        for curve in self.curves:
            curve.setData([], [])
            curve.setVisible(True)
        for btn in self.legend_buttons:
            btn._visible = True
            btn._update_style()

        self.table_model.latest_matrix = [[None for _ in range(self.table_model.cols)] for _ in range(self.table_model.rows)]
        self.table_model.layoutChanged.emit()

        self.stats_lbl.setText(Strings.STATS_EMPTY)
        self.clear_selection()

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

        if self.stack.currentIndex() == 1:
            self.table_model.update_data(x_view, data_2d)

        if self.is_paused and not force:
            return

        for i in range(self.series_count):
            self.curves[i].setData(x_view, data_2d[:len(x_view), i])
            self.curves[i].setVisible(self._series_visible[i])

        if self.auto_scroll_cb.isChecked():
            current_time = x_view[-1]
            window_size_seconds = 10
            min_x = max(0, current_time - window_size_seconds)
            self.plot_widget.setXRange(min_x, max(window_size_seconds, current_time))

            mask = x_view >= min_x
            if np.any(mask):
                visible_data = data_2d[mask, :]
                y_vals = visible_data[:, self._series_visible]
                if y_vals.size > 0:
                    y_min = np.min(y_vals)
                    y_max = np.max(y_vals)
                    padding = (y_max - y_min) * 0.1
                    if padding == 0:
                        padding = 0.1
                    self.plot_widget.setYRange(y_min - padding, y_max + padding)

        # Update stats
        current_data = data_2d[len(x_view) - 1, :]
        d_min = np.min(current_data)
        d_max = np.max(current_data)
        d_std = np.std(current_data)
        self.stats_lbl.setText(Strings.FMT_STATS.format(std=d_std, max=d_max, min=d_min, unit=self.unit))

    def clear_selection(self):
        self.selected_series_idx = None
        self.v_line.hide()
        self.h_line.hide()
        self.hover_point.hide()
        self.selection_panel.update_selection(None, 0, 0, "", "")
        for i, curve in enumerate(self.curves):
            curve.setPen(pg.mkPen(color=self.colors[i], width=1))
            curve.setZValue(0)

    def on_mouse_click(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        if not self.plot_widget.sceneBoundingRect().contains(event.scenePos()):
            return

        x_data, _ = self.curves[0].getData()
        if x_data is None or len(x_data) == 0:
            return

        vb = self.plot_widget.getViewBox()
        mouse_point = vb.mapSceneToView(event.scenePos())
        click_x, click_y = mouse_point.x(), mouse_point.y()

        closest_x_idx = np.argmin(np.abs(x_data - click_x))
        actual_x = x_data[closest_x_idx]

        y_values = np.zeros(self.series_count)
        for i in range(self.series_count):
            _, y_data = self.curves[i].getData()
            if y_data is not None and len(y_data) > closest_x_idx:
                y_values[i] = y_data[closest_x_idx]

        distances = np.abs(y_values - click_y)
        closest_series_idx = np.argmin(distances)
        actual_y = y_values[closest_series_idx]

        y_span = vb.viewRange()[1][1] - vb.viewRange()[1][0]
        threshold = y_span * 0.02

        is_empty_click = distances[closest_series_idx] > threshold

        if is_empty_click:
            self.clear_selection()
        else:
            self.selected_series_idx = closest_series_idx
            self.v_line.setPos(actual_x)
            self.v_line.show()
            self.h_line.setPos(actual_y)
            self.h_line.show()
            self.hover_point.setData(pos=[(actual_x, actual_y)])
            self.hover_point.setBrush(pg.mkBrush(self.colors[closest_series_idx]))
            self.hover_point.show()
            color_hex = '#%02x%02x%02x' % tuple(self.colors[closest_series_idx])
            label_text = self.label_formatter(closest_series_idx)
            self.selection_panel.update_selection(label_text, actual_x, actual_y, self.unit, color_hex)

            for i, curve in enumerate(self.curves):
                if i == closest_series_idx:
                    curve.setPen(pg.mkPen(color=self.colors[i], width=2))
                    curve.setZValue(10)
                else:
                    curve.setPen(pg.mkPen(color='#444444', width=1))
                    curve.setZValue(0)

    def on_mouse_move(self, pos):
        if not self.plot_widget.sceneBoundingRect().contains(pos):
            self.v_line.hide()
            self.h_line.hide()
            self.hover_point.hide()
            self.cursor_label.hide()
            return

        vb = self.plot_widget.getViewBox()
        mouse_point = vb.mapSceneToView(pos)
        hover_x = mouse_point.x()
        hover_y = mouse_point.y()

        if self.selected_series_idx is not None:
            x_data, y_data = self.curves[self.selected_series_idx].getData()
            if x_data is not None and len(x_data) > 0:
                closest_x_idx = np.argmin(np.abs(x_data - hover_x))
                actual_x = x_data[closest_x_idx]
                actual_y = y_data[closest_x_idx]
                self.v_line.setPos(actual_x)
                self.h_line.setPos(actual_y)
                self.hover_point.setData(pos=[(actual_x, actual_y)])
                color_hex = '#%02x%02x%02x' % tuple(self.colors[self.selected_series_idx])
                label_text = self.label_formatter(self.selected_series_idx)
                self.selection_panel.update_selection(label_text, actual_x, actual_y, self.unit, color_hex)

        # Cursor value label with visible signals
        x_data, _ = self.curves[0].getData()
        if x_data is not None and len(x_data) > 0:
            closest_x_idx = np.argmin(np.abs(x_data - hover_x))
            actual_x = x_data[closest_x_idx]
            lines = [f"T: {actual_x:.2f}s"]
            for i in range(self.series_count):
                if not self._series_visible[i]:
                    continue
                _, y_data = self.curves[i].getData()
                if y_data is not None and closest_x_idx < len(y_data):
                    val = y_data[closest_x_idx]
                    label = self.label_formatter(i)
                    lines.append(f"{label}: {val:.3f}")
            if len(lines) > 1:
                self.cursor_label.setText("\n".join(lines))
                plot_pos = self.plot_widget.mapFromScene(pos)
                container_pos = self.plot_widget.mapTo(self._plot_container, plot_pos)
                self.cursor_label.move(int(container_pos.x()) + 15, int(container_pos.y()) - 10)
                self.cursor_label.show()
        else:
            self.cursor_label.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.auto_scroll_cb.isChecked():
                self.auto_scroll_cb.setChecked(False)
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            vb = self.plot_widget.getViewBox()
            mouse_point = vb.mapSceneToView(event.scenePos())
            zoom_x = mouse_point.x()
            zoom_y = mouse_point.y()
            zoom_factor = 1.2
            if event.angleDelta().y() > 0:
                factor = 1.0 / zoom_factor
            else:
                factor = zoom_factor
            x_range = vb.viewRange()[0]
            y_range = vb.viewRange()[1]
            new_x_width = (x_range[1] - x_range[0]) * factor
            new_y_height = (y_range[1] - y_range[0]) * factor
            vb.setXRange(zoom_x - new_x_width * 0.5, zoom_x + new_x_width * 0.5)
            vb.setYRange(zoom_y - new_y_height * 0.5, zoom_y + new_y_height * 0.5)
            event.accept()
        else:
            super().wheelEvent(event)

    def _create_table_model(self):
        raise NotImplementedError("Subclasses must implement _create_table_model")

    def on_table_toggled(self, checked):
        if checked:
            self.stack.setCurrentIndex(1)
            if hasattr(self, '_last_x_view'):
                self.table_model.update_data(self._last_x_view, self._last_data_2d)
        else:
            self.stack.setCurrentIndex(0)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.clear_selection()
        super().keyPressEvent(event)
