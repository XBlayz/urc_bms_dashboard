import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsPathItem, QTableView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainterPath, QColor

from ui.widgets.plot_frame_base import PlotFrameBase, ToggleButton
from ui.widgets.time_series_plot import TimeSeriesPlotWidget
from ui.widgets.ring_buffer import TimeSeriesRingBuffer
from ui.widgets.table_models import TransitionTableModel, MatrixTableModel
from ui.widgets.legend import LegendPanel
from ui.widgets.selection_panel import SelectionPanel
from ui.widgets.zoomable_table_view import ZoomableTableView
from ui.widgets.ctrl_zoom_viewbox import CtrlZoomViewBox
from ui.widgets.plot_settings import global_plot_settings
from ui.widgets.multi_cursor_mixin import MultiCursorMixin
from ui.fsm_state import fsm_state_labels
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme


class SimpleTimeSeriesPlot(TimeSeriesPlotWidget):
    def __init__(self, title, unit, label_formatter_callback, empty_text=Strings.EMPTY_CELL, colors=None):
        super().__init__(
            title=title,
            unit=unit,
            series_count=1,
            label_formatter_callback=label_formatter_callback,
            empty_text=empty_text,
            colors=colors,
            stats_mode="window",
            show_stats_label=False
        )


class EnumPlot(TimeSeriesPlotWidget, MultiCursorMixin):
    """time_series_plot_enum (UI_definition.md 2.1.1): Y-zoom locked, Fit-X only,
    per-segment coloring by state, transition-only table view."""

    def __init__(self, title, label_formatter_callback, enum_map=None, empty_text=Strings.EMPTY_CELL):
        self.enum_map = enum_map or fsm_state_labels()
        super().__init__(
            title=title, unit="", series_count=1,
            label_formatter_callback=label_formatter_callback,
            empty_text=empty_text, y_zoom_enabled=False, fit_mode="x"
        )
        self.plot_widget.getAxis('left').setTicks(None)
        self._init_multi_cursor(self._plot_container)

    def _create_table_model(self): # pyright: ignore[reportIncompatibleMethodOverride]
        return TransitionTableModel(
            series_count=1,
            label_formatter=self.label_formatter,
            value_formatter=lambda row, val: self.enum_map.get(int(val), "NONE"),
            colors=self.colors,
        )

    def update_data(self, x_view, data_2d, force=False):
        if len(x_view) == 0:
            return

        self._last_x_view = x_view
        self._last_data_2d = data_2d

        if self.stack.currentIndex() == 1:
            self.table_model.update_data(x_view, data_2d)

        if self.is_paused and not force:
            return

        # Extract the values and identify valid (non-NaN) data points
        raw_values = data_2d[:len(x_view), 0]
        valid_mask = ~np.isnan(raw_values)

        # If there are no valid data points, clear the plot and return
        if not np.any(valid_mask):
            if hasattr(self, '_segments'):
                for item in self._segments:
                    self.plot_widget.removeItem(item)
            self._segments = []
            self.stats_lbl.setText("STATE: --")
            return

        # We will iterate through the data, breaking segments when we encounter NaNs or state changes.
        change_points = [0]
        for i in range(1, len(raw_values)):
            # A change point occurs if the state changes, or if we transition to/from a NaN gap
            if np.isnan(raw_values[i]) != np.isnan(raw_values[i-1]):
                 change_points.append(i)
            elif not np.isnan(raw_values[i]) and raw_values[i] != raw_values[i - 1]:
                change_points.append(i)
        change_points.append(len(raw_values))

        # Determine the unique valid states for the Y-axis ticks
        valid_values = raw_values[valid_mask].astype(int)
        unique_states = sorted(set(valid_values))
        state_to_y = {s: i for i, s in enumerate(unique_states)}

        if hasattr(self, '_segments'):
            for item in self._segments:
                self.plot_widget.removeItem(item)
        self._segments = []

        # Draw the segments
        for i in range(len(change_points) - 1):
            start = change_points[i]
            end = change_points[i + 1]
            if end <= start:
                continue

            # If this segment starts with a NaN, it's a gap; skip drawing
            if np.isnan(raw_values[start]):
                continue

            state = int(raw_values[start])
            state_name = self.enum_map.get(state, "NONE")
            color = Theme.STATE_COLORS.get(state_name, "#888888")
            y_val = state_to_y.get(state, 0)

            seg_x = x_view[start:end]
            x_step = np.empty(len(seg_x) + 1, dtype=seg_x.dtype)
            x_step[:-1] = seg_x
            if end < len(x_view):
                x_step[-1] = x_view[end]
            else:
                x_step[-1] = seg_x[-1] + 1.0
            y_step = np.full(len(seg_x), y_val)

            curve = self.plot_widget.plot(x_step, y_step, stepMode="center", pen=pg.mkPen(color, width=2))
            self._segments.append(curve)

        y_ticks = [(i, self.enum_map.get(s, str(s))) for s, i in state_to_y.items()]
        self.plot_widget.getAxis('left').setTicks([y_ticks])

        if self.auto_scroll_cb.isChecked():
            current_time = x_view[-1]
            window_size_seconds = global_plot_settings.window_size_seconds
            min_x = max(0, current_time - window_size_seconds)
            self.plot_widget.setXRange(min_x, max(window_size_seconds, current_time))
            y_padding = 0.5
            self.plot_widget.setYRange(-y_padding, len(unique_states) - 1 + y_padding)

        # Update the stats label with the last valid state, or "--" if the last value is NaN
        if np.isnan(raw_values[-1]):
             self.stats_lbl.setText("STATE: --")
        else:
            current_state = int(raw_values[-1])
            state_name = self.enum_map.get(current_state, "--")
            self.stats_lbl.setText(f"STATE: {state_name}")

        # Keep the cursor(s) aligned to the mouse even if it hasn't moved
        # (e.g. autoscroll just shifted which sample sits under the pointer).
        if self.selected_series_idx is not None and self._last_mouse_scene_pos is not None:
            self.on_mouse_move(self._last_mouse_scene_pos)
        else:
            self._mc_reposition_fixed_labels()

    def on_mouse_click(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if not self.plot_widget.sceneBoundingRect().contains(event.scenePos()):
            return
        if not hasattr(self, '_last_x_view') or len(self._last_x_view) == 0:
            return

        vb = self.plot_widget.getViewBox()
        mouse_point = vb.mapSceneToView(event.scenePos())
        idx = int(np.argmin(np.abs(self._last_x_view - mouse_point.x())))
        actual_x = self._last_x_view[idx]
        state = int(self._last_data_2d[idx, 0])

        # Reject clicks that land far from the state's plotted y-level (empty space).
        unique_states = sorted(set(self._last_data_2d[:len(self._last_x_view), 0].astype(int)))
        state_to_y = {s: i for i, s in enumerate(unique_states)}
        line_y = state_to_y.get(state, 0)

        y_range = vb.viewRange()[1]
        threshold = (y_range[1] - y_range[0]) * 0.15
        if abs(line_y - mouse_point.y()) > threshold:
            self.clear_selection()
            return

        label = self.enum_map.get(state, "NONE")

        if self.selected_series_idx == 0:
            # Signal already selected: pin a time-fixed cursor instead of moving the live one.
            self._mc_add_fixed_cursor(actual_x, f"T: {actual_x:.2f}s\n{label}")
            return

        self._mc_clear_fixed_cursors()
        self.selected_series_idx = 0
        color = Theme.STATE_COLORS.get(label, "#888888")

        self.v_line.setPos(actual_x)
        self.v_line.show()
        self.selection_panel.update_selection(self.label_formatter(0), actual_x, label, "", color)

    def on_mouse_move(self, pos):
        self._last_mouse_scene_pos = pos
        self._mc_reposition_fixed_labels()

        if self.selected_series_idx is None:
            return
        if not self.plot_widget.sceneBoundingRect().contains(pos):
            return
        if not hasattr(self, '_last_x_view') or len(self._last_x_view) == 0:
            return

        vb = self.plot_widget.getViewBox()
        mouse_point = vb.mapSceneToView(pos)
        idx = int(np.argmin(np.abs(self._last_x_view - mouse_point.x())))
        actual_x = self._last_x_view[idx]
        state = int(self._last_data_2d[idx, 0])
        label = self.enum_map.get(state, "NONE")
        color = Theme.STATE_COLORS.get(label, "#888888")

        self.v_line.setPos(actual_x)
        self.v_line.show()
        self.selection_panel.update_selection(self.label_formatter(0), actual_x, label, "", color)

    def clear_selection(self):
        self.selected_series_idx = None
        self.v_line.hide()
        self.selection_panel.update_selection(None, 0, 0, "", "")
        self._mc_clear_fixed_cursors()


class StackedBoolPlot(PlotFrameBase, MultiCursorMixin):
    """time_series_stacked_plot_bool (UI_definition.md 2.1.2): boolean signals as stacked
    square-wave bands, Y-zoom locked, Fit-X only, transition-only table view."""

    BAND_HEIGHT = 1.0
    PADDING = 0.3

    def __init__(self, title, series_labels, empty_text=Strings.EMPTY_CELL):
        self.series_labels = series_labels
        self.series_count = len(series_labels)
        self.empty_text = empty_text

        self.curves = []
        self.fill_items = []
        self.selected_series_idx = None
        self.colors = [
            Theme.SIGNAL_COLORS.get("actuator_air_pos", "#00FF00"),
            Theme.SIGNAL_COLORS.get("actuator_air_neg", "#FF4444"),
            Theme.SIGNAL_COLORS.get("actuator_pre_charge", "#FFAA00"),
            Theme.SIGNAL_COLORS.get("actuator_sdc", "#00AAFF"),
        ]
        self.buffer = TimeSeriesRingBuffer(self.series_count)

        super().__init__(title, show_table_toggle=True, show_pause=True)
        self._build_pages()
        self._init_multi_cursor(self._plot_page)

    def _build_extra_header_buttons(self, header_layout):
        self.auto_scroll_cb = ToggleButton(Strings.BTN_AUTO_SCROLL, checked=True)
        self.auto_scroll_cb.toggled.connect(self.on_auto_scroll_toggled)
        header_layout.addWidget(self.auto_scroll_cb)
        header_layout.addWidget(self._make_header_button(Strings.BTN_FIT_X, self.on_fit_x))

    def _build_pages(self):
        plot_page = QFrame()
        self._plot_page = plot_page
        plot_layout = QVBoxLayout(plot_page)
        plot_layout.setContentsMargins(10, 10, 10, 10)

        self.plot_widget = pg.PlotWidget(viewBox=CtrlZoomViewBox())
        self.plot_widget.setBackground(Theme.PG_BG)
        self.plot_widget.showGrid(x=True, y=True, alpha=Theme.PG_GRID_ALPHA)
        self.plot_widget.getAxis('bottom').setPen(Theme.PG_AXIS_PEN)
        self.plot_widget.getAxis('left').setPen(Theme.PG_AXIS_PEN)
        self.plot_widget.getAxis('bottom').setTextPen(Theme.PG_AXIS_TEXT)
        self.plot_widget.getAxis('left').setTextPen(Theme.PG_AXIS_TEXT)
        self.plot_widget.hideButtons()
        self.plot_widget.setMouseEnabled(x=True, y=False)
        self.plot_widget.getViewBox().sigRangeChangedManually.connect(self._on_manual_range_change)

        for i in range(self.series_count):
            color = self.colors[i % len(self.colors)]
            path_item = QGraphicsPathItem()
            path_item.setPen(pg.mkPen(color=color, width=1))
            path_item.setBrush(pg.mkBrush(color + "40"))
            self.plot_widget.addItem(path_item)
            self.fill_items.append(path_item)

            pen = pg.mkPen(color=color, width=2)
            curve = self.plot_widget.plot(pen=pen, stepMode="center")
            self.curves.append(curve)

        y_ticks = [
            (i * (self.BAND_HEIGHT + self.PADDING) + self.BAND_HEIGHT / 2, label)
            for i, label in enumerate(self.series_labels)
        ]
        self.plot_widget.getAxis('left').setTicks([y_ticks])

        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(color=Theme.PG_CROSSHAIR, width=1, style=Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.v_line)
        self.v_line.hide()

        self.cursor_label = QLabel("", plot_page)
        self.cursor_label.setStyleSheet("color: #DDDDDD; font-size: 11px; font-family: monospace; background: rgba(0,0,0,120); padding: 2px 4px; border-radius: 4px;")
        self.cursor_label.hide()

        plot_layout.addWidget(self.plot_widget, stretch=1)
        self.cursor_label.raise_()

        self.selection_panel = SelectionPanel(self.empty_text)
        plot_layout.addWidget(self.selection_panel)

        self.stack.addWidget(plot_page)

        table_page = QFrame()
        table_layout = QVBoxLayout(table_page)
        table_layout.setContentsMargins(10, 10, 10, 10)
        self.table_view = QTableView()
        self.table_view.setStyleSheet(Theme.table_view())
        self.table_model = TransitionTableModel(
            series_count=self.series_count,
            label_formatter=lambda i: self.series_labels[i],
            value_formatter=lambda row, val: Strings.LBL_TRUE if val else Strings.LBL_FALSE,
            colors=self.colors,
        )
        self.table_view.setModel(self.table_model)
        self.table_view.horizontalHeader().setDefaultSectionSize(70) # pyright: ignore[reportOptionalMemberAccess]
        self.table_view.verticalHeader().setDefaultSectionSize(24) # pyright: ignore[reportOptionalMemberAccess]
        table_layout.addWidget(self.table_view, stretch=1)
        self.stack.addWidget(table_page)

        self.plot_widget.scene().sigMouseClicked.connect(self.on_mouse_click) # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_move) # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]

        global_plot_settings.window_size_changed.connect(self._on_window_size_changed)

    def _on_manual_range_change(self, *args):
        if self.auto_scroll_cb.isChecked():
            self.auto_scroll_cb.setChecked(False)

    def _on_window_size_changed(self, value):
        if self.auto_scroll_cb.isChecked() and hasattr(self, '_last_x_view'):
            self.update_data(self._last_x_view, self._last_data_2d, force=True)

    def on_auto_scroll_toggled(self, checked):
        if checked and hasattr(self, '_last_x_view'):
            self.update_data(self._last_x_view, self._last_data_2d, force=True)

    def on_fit_x(self):
        self.auto_scroll_cb.setChecked(False)
        if hasattr(self, '_last_x_view') and len(self._last_x_view):
            self.plot_widget.setXRange(float(self._last_x_view[0]), float(self._last_x_view[-1]))

    def on_pause_toggled(self, checked):
        if not checked and hasattr(self, '_last_x_view'):
            self.update_data(self._last_x_view, self._last_data_2d, force=True)

    def add_point(self, current_time, y_data):
        self.buffer.append(current_time, y_data)
        x_out, y_out = self.buffer.snapshot()
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
            base = i * (self.BAND_HEIGHT + self.PADDING)
            lower = np.full(len(x_view), base)
            upper = lower + data_2d[:len(x_view), i] * self.BAND_HEIGHT

            x_step = np.empty(len(x_view) + 1, dtype=x_view.dtype)
            x_step[:-1] = x_view
            x_step[-1] = x_view[-1] + 1.0
            self.curves[i].setData(x_step, upper, stepMode="center")

            path = QPainterPath()
            n = len(x_view)
            if n == 0:
                continue

            path.moveTo(x_step[0], base)
            path.lineTo(x_step[0], upper[0])
            for j in range(len(x_step) - 1):
                path.lineTo(x_step[j + 1], upper[j])
                if j + 1 < len(upper):
                    path.lineTo(x_step[j + 1], upper[j + 1])
            path.lineTo(x_step[-1], base)
            path.closeSubpath()
            self.fill_items[i].setPath(path)

        if self.auto_scroll_cb.isChecked():
            current_time = x_view[-1]
            window_size_seconds = global_plot_settings.window_size_seconds
            min_x = max(0, current_time - window_size_seconds)
            self.plot_widget.setXRange(min_x, max(window_size_seconds, current_time))

        max_y = self.series_count * self.BAND_HEIGHT + (self.series_count - 1) * self.PADDING
        self.plot_widget.setYRange(-0.2, max_y + 0.2)

        # Handle NaN values injected during disconnections
        last_row = data_2d[len(x_view) - 1, :]
        if np.any(np.isnan(last_row)):
            self.stats_lbl.setText(f"ACTIVE: --/{self.series_count}")
        else:
            active_count = np.sum(last_row)
            self.stats_lbl.setText(f"ACTIVE: {int(active_count)}/{self.series_count}")

        # Keep the cursor(s) aligned to the mouse even if it hasn't moved
        # (e.g. autoscroll just shifted which sample sits under the pointer).
        if self.selected_series_idx is not None and self._last_mouse_scene_pos is not None:
            self.on_mouse_move(self._last_mouse_scene_pos)
        else:
            self._mc_reposition_fixed_labels()

    def on_mouse_click(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if not self.plot_widget.sceneBoundingRect().contains(event.scenePos()):
            return
        if not hasattr(self, '_last_x_view') or len(self._last_x_view) == 0:
            return

        vb = self.plot_widget.getViewBox()
        mouse_point = vb.mapSceneToView(event.scenePos())
        click_x, click_y = mouse_point.x(), mouse_point.y()

        idx = int(np.argmin(np.abs(self._last_x_view - click_x)))
        actual_x = self._last_x_view[idx]

        # A click selects a band either near its current step line (True/False
        # level) or anywhere inside its filled area (base..top when True).
        threshold = 0.15
        band_idx = None
        for i in range(self.series_count):
            base = i * (self.BAND_HEIGHT + self.PADDING)
            val = bool(self._last_data_2d[idx, i])
            top = base + self.BAND_HEIGHT if val else base
            if (base - threshold) <= click_y <= (top + threshold):
                band_idx = i
                break

        if band_idx is None:
            self.clear_selection()
            return

        val = bool(self._last_data_2d[idx, band_idx])
        label = self.series_labels[band_idx]
        text = Strings.LBL_TRUE if val else Strings.LBL_FALSE

        if band_idx == self.selected_series_idx:
            # Signal already selected: pin a time-fixed cursor instead of moving the live one.
            self._mc_add_fixed_cursor(actual_x, f"T: {actual_x:.2f}s\n{label}: {text}")
            return

        self._mc_clear_fixed_cursors()
        self.selected_series_idx = band_idx
        self.v_line.setPos(actual_x)
        self.v_line.show()

        color = self.colors[band_idx % len(self.colors)]
        self.selection_panel.update_selection(label, actual_x, text, "", color)
        self._apply_curve_highlight(band_idx)

    def _apply_curve_highlight(self, index):
        for i, curve in enumerate(self.curves):
            color = self.colors[i % len(self.colors)]
            if i == index:
                curve.setPen(pg.mkPen(color=color, width=3))
            else:
                curve.setPen(pg.mkPen(color="#444444", width=2))
        for i, item in enumerate(self.fill_items):
            color = self.colors[i % len(self.colors)]
            item.setBrush(pg.mkBrush(color + ("80" if i == index else "20")))

    def on_mouse_move(self, pos):
        self._last_mouse_scene_pos = pos
        self._mc_reposition_fixed_labels()

        if self.selected_series_idx is None:
            return
        if not self.plot_widget.sceneBoundingRect().contains(pos):
            return
        if not hasattr(self, '_last_x_view') or len(self._last_x_view) == 0:
            return

        vb = self.plot_widget.getViewBox()
        mouse_point = vb.mapSceneToView(pos)
        idx = int(np.argmin(np.abs(self._last_x_view - mouse_point.x())))
        actual_x = self._last_x_view[idx]

        band_idx = self.selected_series_idx
        val = bool(self._last_data_2d[idx, band_idx])
        label = self.series_labels[band_idx]
        color = self.colors[band_idx % len(self.colors)]
        text = Strings.LBL_TRUE if val else Strings.LBL_FALSE

        self.v_line.setPos(actual_x)
        self.v_line.show()
        self.selection_panel.update_selection(label, actual_x, text, "", color)

    def reset_data(self):
        self.buffer.reset()
        for curve in self.curves:
            curve.setData([], [])
        for item in self.fill_items:
            item.setPath(QPainterPath())
        self.table_model.update_data(np.empty(0), np.empty((0, self.series_count)))
        self.stats_lbl.setText(Strings.STATS_EMPTY)
        self.clear_selection()

    def clear_selection(self):
        self.selected_series_idx = None
        self.v_line.hide()
        self.cursor_label.hide()
        self.selection_panel.update_selection(None, 0, 0, "", "")
        for i, curve in enumerate(self.curves):
            curve.setPen(pg.mkPen(color=self.colors[i % len(self.colors)], width=2))
        for i, item in enumerate(self.fill_items):
            item.setBrush(pg.mkBrush(self.colors[i % len(self.colors)] + "40"))
        self._mc_clear_fixed_cursors()


class BarChartWidget(PlotFrameBase):
    """bar_chart (UI_definition.md 2.2): last instantaneous value per signal as bars,
    heatmap-colored, with a scrollable legend, min/max/avg/delta overlays and an
    optional spatial matrix/heatmap view."""

    # Emits the selected bar index (or None on clear) so a paired time series plot
    # (e.g. the corresponding cell voltage/temperature history) can mirror the highlight.
    sig_signal_selected = pyqtSignal(object)

    def __init__(self, title, unit, bar_count, label_formatter_callback,
                 empty_text=Strings.EMPTY_CELL, heatmap=None,
                 matrix_mapping=None, matrix_rows=0, matrix_cols=0,
                 matrix_row_label=None, matrix_col_label=None):
        self.unit = unit
        self.bar_count = bar_count
        self.label_formatter = label_formatter_callback
        self.empty_text = empty_text
        self.heatmap = heatmap
        self.matrix_mapping = matrix_mapping
        self.matrix_rows = matrix_rows
        self.matrix_cols = matrix_cols
        self.matrix_row_label = matrix_row_label or (lambda i: f"Row {i + 1}")
        self.matrix_col_label = matrix_col_label or (lambda i: f"Col {i + 1}")

        self.current_data = np.zeros(bar_count, dtype=np.float64)
        self._series_visible = [True] * bar_count
        self._default_colors = ["#00AAFF"] * bar_count
        self.selected_idx = None
        self._smart_scale = True

        super().__init__(title, show_table_toggle=False, show_pause=True)
        self._build_pages()

    def _build_extra_header_buttons(self, header_layout):
        self.smart_scale_cb = ToggleButton(Strings.BTN_SMART_SCALE, checked=True)
        self.smart_scale_cb.toggled.connect(self.on_smart_scale_toggled)
        header_layout.addWidget(self.smart_scale_cb)

        if self.matrix_mapping is not None:
            self.matrix_cb = ToggleButton(Strings.BTN_MATRIX_VIEW, checked=False)
            self.matrix_cb.toggled.connect(self.on_matrix_toggled)
            header_layout.addWidget(self.matrix_cb)

    def on_smart_scale_toggled(self, checked):
        self._smart_scale = checked
        self._render_bars()

    def _build_pages(self):
        bars_page = QFrame()
        bars_layout = QVBoxLayout(bars_page)
        bars_layout.setContentsMargins(10, 10, 10, 10)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(Theme.PG_BG)
        self.plot_widget.showGrid(x=True, y=True, alpha=Theme.PG_GRID_ALPHA)
        self.plot_widget.getAxis('bottom').setPen(Theme.PG_AXIS_PEN)
        self.plot_widget.getAxis('left').setPen(Theme.PG_AXIS_PEN)
        self.plot_widget.getAxis('bottom').setTextPen(Theme.PG_AXIS_TEXT)
        self.plot_widget.getAxis('left').setTextPen(Theme.PG_AXIS_TEXT)
        self.plot_widget.hideButtons()
        self.plot_widget.setMouseEnabled(x=False, y=False)

        self.avg_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen(color="#FFDD00", width=1, style=Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.avg_line)
        self.avg_line.hide()

        self.bar_item = None
        self.highlight_item = None
        self.delta_bar_item = None
        self.selected_highlight_item = None

        bars_layout.addWidget(self.plot_widget, stretch=1)

        labels = [self.label_formatter(i) for i in range(self.bar_count)]
        self.legend = LegendPanel(labels, self._default_colors)
        self.legend.sig_visibility_changed.connect(self._on_legend_visibility_changed)
        bars_layout.addWidget(self.legend)

        self.selection_panel = SelectionPanel(self.empty_text)
        bars_layout.addWidget(self.selection_panel)

        self.stack.addWidget(bars_page)

        if self.matrix_mapping is not None:
            matrix_page = QFrame()
            matrix_layout = QVBoxLayout(matrix_page)
            matrix_layout.setContentsMargins(10, 10, 10, 10)
            self.matrix_view = ZoomableTableView()
            self.matrix_view.setStyleSheet(Theme.table_view())
            self.matrix_model = MatrixTableModel(
                self.matrix_mapping, self.matrix_rows, self.matrix_cols,
                self.heatmap, self.matrix_row_label, self.matrix_col_label,
            )
            self.matrix_view.setModel(self.matrix_model)
            for r in range(self.matrix_rows):
                self.matrix_view.setColumnWidth(r, 70)
            for c in range(self.matrix_cols):
                self.matrix_view.setRowHeight(c, 40)
            matrix_layout.addWidget(self.matrix_view, stretch=1)
            self.stack.addWidget(matrix_page)

        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_move) # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
        self.plot_widget.scene().sigMouseClicked.connect(self.on_mouse_click) # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]

    def on_matrix_toggled(self, checked):
        if checked:
            self.stack.setCurrentIndex(1)
            self.matrix_model.update_data(self.current_data)
        else:
            self.stack.setCurrentIndex(0)

    def _on_legend_visibility_changed(self, idx, visible):
        self._series_visible[idx] = visible
        self._render_bars()

    def on_pause_toggled(self, checked):
        if not checked:
            self._render_bars()

    def update_data(self, data_1d):
        self.current_data = np.array(data_1d, dtype=np.float64)
        if self.matrix_mapping is not None and self.stack.currentIndex() == 1:
            self.matrix_model.update_data(self.current_data)
        if self.is_paused:
            return
        self._render_bars()

    def _clear_dynamic(self):
        for item in (self.bar_item, self.highlight_item, self.delta_bar_item, self.selected_highlight_item):
            if item is not None:
                self.plot_widget.removeItem(item)
        self.bar_item = None
        self.highlight_item = None
        self.delta_bar_item = None
        self.selected_highlight_item = None

    def _render_bars(self):
        self._clear_dynamic()

        visible_mask = np.array(self._series_visible, dtype=bool)
        data = self.current_data
        n = len(data)
        if n == 0 or not np.any(visible_mask):
            self.avg_line.hide()
            return

        x_all = np.arange(n)
        x = x_all[visible_mask]
        vis_data = data[visible_mask]
        width = 0.6

        if self.heatmap is not None:
            colors = [self.heatmap.color_for(v) for v in vis_data]
        else:
            colors = [QColor("#00AAFF") for _ in vis_data]

        # Dim every bar except the one selected via click (or via a paired plot).
        if self.selected_idx is not None:
            for i, xi in enumerate(x):
                if xi != self.selected_idx:
                    colors[i] = QColor(colors[i])
                    colors[i].setAlpha(max(0, colors[i].alpha() - 60))

        brushes = [pg.mkBrush(c) for c in colors]

        self.bar_item = pg.BarGraphItem(x=x, height=vis_data, width=width, brushes=brushes, pen=pg.mkPen(None))
        self.plot_widget.addItem(self.bar_item)

        mean_val = float(np.mean(vis_data))
        std_val = float(np.std(vis_data))
        d_min = float(np.min(vis_data))
        d_max = float(np.max(vis_data))
        min_idx = int(x[np.argmin(vis_data)])
        max_idx = int(x[np.argmax(vis_data)])

        self.highlight_item = pg.BarGraphItem(
            x=[min_idx, max_idx], height=[data[min_idx], data[max_idx]], width=width,
            pens=[pg.mkPen("#00AAFF", width=2), pg.mkPen("#FF4444", width=2)],
            brushes=[pg.mkBrush(None), pg.mkBrush(None)],
        )
        self.plot_widget.addItem(self.highlight_item)

        if self.selected_idx is not None and 0 <= self.selected_idx < n and visible_mask[self.selected_idx]:
            self.selected_highlight_item = pg.BarGraphItem(
                x=[self.selected_idx], height=[data[self.selected_idx]], width=width,
                pens=[pg.mkPen("#FFFFFF", width=2)], brushes=[pg.mkBrush(None)],
            )
            self.plot_widget.addItem(self.selected_highlight_item)

        self.avg_line.setPos(mean_val)
        self.avg_line.show()

        if self._smart_scale:
            padding = (d_max - d_min) * 0.1 or 0.1
            self.plot_widget.setYRange(d_min - padding, d_max + padding)
        else:
            self.plot_widget.enableAutoRange(axis='y')

        delta_x = float(x_all[0]) - 1.5 if len(x_all) else -1.5
        self.delta_bar_item = pg.BarGraphItem(
            x=[delta_x], height=[d_max - d_min], y0=[d_min], width=0.6,
            brush=pg.mkBrush(136, 136, 136, 128), pen=pg.mkPen(None),
        )
        self.plot_widget.addItem(self.delta_bar_item)

        self.stats_lbl.setText(Strings.FMT_STATS.format(
            min=d_min, max=d_max, avg=mean_val, std=std_val, delta=d_max - d_min, unit=self.unit
        ))

        ticks = []
        step = max(1, n // 10)
        for i in range(0, n, step):
            ticks.append((i, self.label_formatter(i)))
        self.plot_widget.getAxis('bottom').setTicks([ticks])

    def on_mouse_click(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if not self.plot_widget.sceneBoundingRect().contains(event.scenePos()):
            return
        if len(self.current_data) == 0:
            return

        vb = self.plot_widget.getViewBox()
        mouse_point = vb.mapSceneToView(event.scenePos())
        click_x, click_y = mouse_point.x(), mouse_point.y()

        idx = int(round(click_x))
        width = 0.6
        valid = (
            0 <= idx < len(self.current_data)
            and self._series_visible[idx]
            and abs(click_x - idx) <= width / 2
        )
        if valid:
            bar_val = self.current_data[idx]
            lo, hi = (0.0, bar_val) if bar_val >= 0 else (bar_val, 0.0)
            valid = lo <= click_y <= hi

        self._select_bar(idx if valid else None)

    def _select_bar(self, idx):
        self.selected_idx = idx
        self._render_bars()
        if idx is None:
            self.selection_panel.update_selection(None, 0, 0, "", "")
        else:
            label = self.label_formatter(idx)
            self.selection_panel.update_selection(label, 0.0, self.current_data[idx], self.unit, "#FFFFFF")
        self.sig_signal_selected.emit(idx)

    def set_external_highlight(self, index):
        """Applies the highlight driven by a paired time series plot's selection.
        Does not emit sig_signal_selected, to avoid feedback loops."""
        if index is not None and (index < 0 or index >= len(self.current_data)):
            index = None
        self.selected_idx = index
        self._render_bars()
        if index is None:
            self.selection_panel.update_selection(None, 0, 0, "", "")
        else:
            label = self.label_formatter(index)
            self.selection_panel.update_selection(label, 0.0, self.current_data[index], self.unit, "#FFFFFF")

    def clear_selection(self):
        self._select_bar(None)

    def on_mouse_move(self, pos):
        pass

    def reset_data(self):
        self.current_data = np.zeros(self.bar_count, dtype=np.float64)
        self._series_visible = [True] * self.bar_count
        self.selected_idx = None
        for btn in self.legend.buttons:
            btn.set_visible_state(True)
        self._render_bars()
        self.selection_panel.update_selection(None, 0, 0, "", "")
