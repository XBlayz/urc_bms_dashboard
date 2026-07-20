import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QTableView
from PyQt6.QtCore import Qt, pyqtSignal

from ui.widgets.plot_frame_base import PlotFrameBase, ToggleButton
from ui.widgets.ring_buffer import TimeSeriesRingBuffer
from ui.widgets.table_models import SignalTimeTableModel
from ui.widgets.legend import LegendPanel
from ui.widgets.selection_panel import SelectionPanel
from ui.widgets.ctrl_zoom_viewbox import CtrlZoomViewBox
from ui.widgets.plot_settings import global_plot_settings
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme


class TimeSeriesPlotWidget(PlotFrameBase):
    """Plots one or more signals over time (UI_definition.md 2.1)."""

    sig_signal_selected = pyqtSignal(object)

    def __init__(self, title, unit, series_count, label_formatter_callback,
                 empty_text=Strings.EMPTY_CELL, colors=None,
                 y_zoom_enabled=True, fit_mode="xy", stats_mode="instantaneous",
                 show_stats_label=True, dashed=None):
        self.unit = unit
        self.series_count = series_count
        self.label_formatter = label_formatter_callback
        self.empty_text = empty_text
        self._signal_colors = colors
        self._dashed = dashed or []
        self._y_zoom_enabled = y_zoom_enabled
        self._fit_mode = fit_mode
        self.stats_mode = stats_mode
        self._show_stats_label = show_stats_label

        self.curves = []
        self.colors = []
        self._series_visible = [True] * series_count
        self.buffer = TimeSeriesRingBuffer(series_count)
        self.selected_series_idx = None

        super().__init__(title, show_table_toggle=True, show_pause=True)
        if not self._show_stats_label:
            self.stats_lbl.hide()
        self._build_pages()

    # --- header ---

    def _build_extra_header_buttons(self, header_layout):
        self.auto_scroll_cb = ToggleButton(Strings.BTN_AUTO_SCROLL, checked=True)
        self.auto_scroll_cb.toggled.connect(self.on_auto_scroll_toggled)
        header_layout.addWidget(self.auto_scroll_cb)

        if self._fit_mode in ("x", "xy"):
            header_layout.addWidget(self._make_header_button(Strings.BTN_FIT_X, self.on_fit_x))
        if self._fit_mode == "xy":
            header_layout.addWidget(self._make_header_button(Strings.BTN_FIT_Y, self.on_fit_y))
            header_layout.addWidget(self._make_header_button(Strings.BTN_FIT_XY, self.on_fit_xy))

    # --- page construction ---

    def _build_pages(self):
        self._plot_container = QFrame()
        self._plot_container.setStyleSheet("""
            QFrame {
                background-color: #2A2A2A;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)
        plot_layout = QVBoxLayout(self._plot_container)
        plot_layout.setContentsMargins(10, 10, 10, 10)

        self.plot_widget = pg.PlotWidget(viewBox=CtrlZoomViewBox())
        self.plot_widget.setBackground(Theme.PG_BG)
        self.plot_widget.showGrid(x=True, y=True, alpha=Theme.PG_GRID_ALPHA)
        self.plot_widget.getAxis('bottom').setPen(Theme.PG_AXIS_PEN)
        self.plot_widget.getAxis('left').setPen(Theme.PG_AXIS_PEN)
        self.plot_widget.getAxis('bottom').setTextPen(Theme.PG_AXIS_TEXT)
        self.plot_widget.getAxis('left').setTextPen(Theme.PG_AXIS_TEXT)
        self.plot_widget.hideButtons()
        # Mouse stays enabled so native pyqtgraph drag-pan/wheel-zoom work; autoscroll
        # is disengaged reactively via sigRangeChangedManually below.
        self.plot_widget.setMouseEnabled(x=True, y=self._y_zoom_enabled)
        self.plot_widget.getViewBox().sigRangeChangedManually.connect(self._on_manual_range_change)

        for i in range(self.series_count):
            if self._signal_colors and i < len(self._signal_colors):
                color = self._signal_colors[i]
            else:
                color = np.random.randint(50, 255, 3).tolist()
            self.colors.append(color)
            style = Qt.PenStyle.DashLine if (i < len(self._dashed) and self._dashed[i]) else Qt.PenStyle.SolidLine
            pen = pg.mkPen(color=color, width=1, style=style)
            curve = self.plot_widget.plot(pen=pen, autoDownsample=True, clipToView=True)
            self.curves.append(curve)

        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(color=Theme.PG_CROSSHAIR, width=1, style=Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.v_line)
        self.v_line.hide()

        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen(color=Theme.PG_CROSSHAIR, width=1, style=Qt.PenStyle.DashLine))
        self.plot_widget.addItem(self.h_line)
        self.h_line.hide()

        self.hover_point = pg.ScatterPlotItem(size=8, pen=pg.mkPen(None), brush=pg.mkBrush(255, 255, 255, 255))
        self.hover_point.setZValue(20)
        self.plot_widget.addItem(self.hover_point)
        self.hover_point.hide()

        self.cursor_label = QLabel("", self._plot_container)
        self.cursor_label.setStyleSheet("color: #DDDDDD; font-size: 11px; font-family: monospace; background: rgba(0,0,0,120); padding: 2px 4px; border-radius: 4px;")
        self.cursor_label.hide()

        plot_layout.addWidget(self.plot_widget, stretch=1)
        self.cursor_label.raise_()

        labels = [self.label_formatter(i) for i in range(self.series_count)]
        self.legend = LegendPanel(labels, self.colors)
        self.legend.sig_visibility_changed.connect(self._on_legend_visibility_changed)
        plot_layout.addWidget(self.legend)

        self.selection_panel = SelectionPanel(self.empty_text)
        plot_layout.addWidget(self.selection_panel)

        self.stack.addWidget(self._plot_container)

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
        self.table_view.horizontalHeader().setDefaultSectionSize(70) # pyright: ignore[reportOptionalMemberAccess]
        self.table_view.verticalHeader().setDefaultSectionSize(24) # pyright: ignore[reportOptionalMemberAccess]
        table_layout.addWidget(self.table_view, stretch=1)
        self.stack.addWidget(table_container)

        self.plot_widget.scene().sigMouseClicked.connect(self.on_mouse_click) # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
        self.plot_widget.scene().sigMouseMoved.connect(self.on_mouse_move) # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]

        global_plot_settings.window_size_changed.connect(self._on_window_size_changed)

    def _create_table_model(self):
        return SignalTimeTableModel(self.series_count, self.label_formatter, self.colors)

    # --- legend ---

    def _on_legend_visibility_changed(self, idx, visible):
        self._series_visible[idx] = visible
        self.curves[idx].setVisible(visible)
        if hasattr(self, '_last_x_view'):
            self.update_data(self._last_x_view, self._last_data_2d, force=True)

    # --- pan/zoom/autoscroll ---

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

    def on_fit_y(self):
        self.auto_scroll_cb.setChecked(False)
        if not hasattr(self, '_last_data_2d') or self._last_data_2d.size == 0:
            return
        mask = np.array(self._series_visible, dtype=bool)
        if not np.any(mask):
            return
        y_vals = self._last_data_2d[:len(self._last_x_view), mask]

        # Check if we have data and if it's not all NaNs
        if y_vals.size == 0 or np.all(np.isnan(y_vals)):
            return

        y_min, y_max = float(np.nanmin(y_vals)), float(np.nanmax(y_vals))
        padding = (y_max - y_min) * 0.1 or 0.1
        self.plot_widget.setYRange(y_min - padding, y_max + padding)

    def on_fit_xy(self):
        self.on_fit_x()
        self.on_fit_y()

    # --- pause ---

    def on_pause_toggled(self, checked):
        if not checked and hasattr(self, '_last_x_view'):
            self.update_data(self._last_x_view, self._last_data_2d, force=True)

    # --- data flow ---

    def reset_data(self):
        self.buffer.reset()
        self._series_visible = [True] * self.series_count

        for curve in self.curves:
            curve.setData([], [])
            curve.setVisible(True)
        for btn in self.legend.buttons:
            btn.set_visible_state(True)

        self.table_model.update_data(np.empty(0), np.empty((0, self.series_count)))
        self.stats_lbl.setText(Strings.STATS_EMPTY)
        self.clear_selection()

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
            self.curves[i].setData(x_view, data_2d[:len(x_view), i])
            self.curves[i].setVisible(self._series_visible[i])

        if self.auto_scroll_cb.isChecked():
            current_time = x_view[-1]
            window_size_seconds = global_plot_settings.window_size_seconds
            min_x = max(0, current_time - window_size_seconds)
            self.plot_widget.setXRange(min_x, max(window_size_seconds, current_time))

            mask = x_view >= min_x
            if np.any(mask):
                visible_data = data_2d[mask, :]
                visible_mask = np.array(self._series_visible, dtype=bool)
                y_vals = visible_data[:, visible_mask]

                # Check if we have data and if it's not all NaNs
                if y_vals.size > 0 and not np.all(np.isnan(y_vals)):
                    y_min = np.nanmin(y_vals)
                    y_max = np.nanmax(y_vals)

                    padding = (y_max - y_min) * 0.1
                    if padding == 0:
                        padding = 0.1

                    self.plot_widget.setYRange(y_min - padding, y_max + padding)

    def _window_stats_text(self, index):
        """MIN/MAX/AVG/STD over the full visible window for a single series.
        Only meaningful for stats_mode='window'; feeds the selection panel,
        shown only while that series is selected."""
        if self.stats_mode != "window" or index is None:
            return None
        if not hasattr(self, '_last_x_view') or len(self._last_x_view) == 0:
            return None
        col = self._last_data_2d[:len(self._last_x_view), index]
        col = col[~np.isnan(col)]
        if col.size == 0:
            return None
        return Strings.FMT_STATS_SELECTED.format(
            min=float(np.min(col)), max=float(np.max(col)),
            avg=float(np.mean(col)), std=float(np.std(col)), unit=self.unit
        )

    def _update_stats(self, x_view, data_2d):
        """Instantaneous multi-signal stats (min/max/avg/std/delta over the latest
        sample across visible signals), or time-window single-signal stats
        (min/max/avg/std per signal over the whole visible window), per stats_mode."""
        visible_mask = np.array(self._series_visible, dtype=bool)
        if not np.any(visible_mask):
            self.stats_lbl.setText(Strings.STATS_EMPTY)
            return

        if self.stats_mode == "window":
            parts = []
            for i in range(self.series_count):
                if not visible_mask[i]:
                    continue
                col = data_2d[:len(x_view), i]
                col = col[~np.isnan(col)]
                if col.size == 0:
                    continue
                parts.append(Strings.FMT_STATS_WINDOW_SIGNAL.format(
                    label=self.label_formatter(i),
                    min=np.min(col), max=np.max(col),
                    avg=np.mean(col), std=np.std(col), unit=self.unit
                ))
            self.stats_lbl.setText("   |   ".join(parts) if parts else Strings.STATS_EMPTY)
            return

    # --- selection / cursor ---

    def _reset_curve_highlight(self):
        for i, curve in enumerate(self.curves):
            style = Qt.PenStyle.DashLine if (i < len(self._dashed) and self._dashed[i]) else Qt.PenStyle.SolidLine
            curve.setPen(pg.mkPen(color=self.colors[i], width=1, style=style))
            curve.setZValue(0)

    def _apply_curve_highlight(self, index):
        for i, curve in enumerate(self.curves):
            style = Qt.PenStyle.DashLine if (i < len(self._dashed) and self._dashed[i]) else Qt.PenStyle.SolidLine
            if i == index:
                curve.setPen(pg.mkPen(color=self.colors[i], width=2, style=style))
                curve.setZValue(10)
            else:
                curve.setPen(pg.mkPen(color='#444444', width=1, style=style))
                curve.setZValue(0)

    def set_external_highlight(self, index):
        """Applies the highlight driven by a paired widget's selection (e.g. the
        matching bar chart). Does not emit sig_signal_selected, to avoid feedback loops."""
        self.selected_series_idx = index
        if index is None or index >= self.series_count:
            self.v_line.hide()
            self.h_line.hide()
            self.hover_point.hide()
            self.selection_panel.update_selection(None, 0, 0, "", "")
            self._reset_curve_highlight()
            return

        self._apply_curve_highlight(index)
        if hasattr(self, '_last_x_view') and len(self._last_x_view):
            last_idx = len(self._last_x_view) - 1
            r, g, b = (int(c) for c in self.colors[index][:3])
            color_hex = f'#{r:02x}{g:02x}{b:02x}'
            label_text = self.label_formatter(index)
            stats_text = self._window_stats_text(index)
            self.selection_panel.update_selection(
                label_text, self._last_x_view[last_idx],
                self._last_data_2d[last_idx, index], self.unit, color_hex, stats_text
            )

    def clear_selection(self):
        self.selected_series_idx = None
        self.v_line.hide()
        self.h_line.hide()
        self.hover_point.hide()
        self.selection_panel.update_selection(None, 0, 0, "", "")
        self._reset_curve_highlight()
        self.sig_signal_selected.emit(None)

    def on_mouse_click(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if not self.plot_widget.sceneBoundingRect().contains(event.scenePos()):
            return

        visible_indices = [i for i in range(self.series_count) if self._series_visible[i]]
        if not visible_indices:
            return

        x_data, _ = self.curves[visible_indices[0]].getData()
        if x_data is None or len(x_data) == 0:
            return

        vb = self.plot_widget.getViewBox()
        mouse_point = vb.mapSceneToView(event.scenePos())
        click_x, click_y = mouse_point.x(), mouse_point.y()

        closest_x_idx = np.argmin(np.abs(x_data - click_x))
        actual_x = x_data[closest_x_idx]

        y_values = {}
        for i in visible_indices:
            _, y_data = self.curves[i].getData()
            if y_data is not None and len(y_data) > closest_x_idx:
                y_values[i] = y_data[closest_x_idx]

        if not y_values:
            return

        closest_series_idx = min(y_values, key=lambda i: abs(y_values[i] - click_y))
        actual_y = y_values[closest_series_idx]

        y_span = vb.viewRange()[1][1] - vb.viewRange()[1][0]
        threshold = y_span * 0.02
        is_empty_click = abs(actual_y - click_y) > threshold

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
            color_hex = self.colors[closest_series_idx]
            label_text = self.label_formatter(closest_series_idx)
            stats_text = self._window_stats_text(closest_series_idx)
            self.selection_panel.update_selection(label_text, actual_x, actual_y, self.unit, color_hex, stats_text)
            self._apply_curve_highlight(closest_series_idx)
            self.sig_signal_selected.emit(closest_series_idx)

    def on_mouse_move(self, pos):
        if not self.plot_widget.sceneBoundingRect().contains(pos):
            self.v_line.hide()
            self.h_line.hide()
            self.hover_point.hide()
            self.cursor_label.hide()
            return

        if self.selected_series_idx is None:
            self.cursor_label.hide()
            return

        vb = self.plot_widget.getViewBox()
        mouse_point = vb.mapSceneToView(pos)
        hover_x = mouse_point.x()

        x_data, y_data = self.curves[self.selected_series_idx].getData()
        if x_data is None or len(x_data) == 0:
            self.cursor_label.hide()
            return

        closest_x_idx = np.argmin(np.abs(x_data - hover_x))
        actual_x = x_data[closest_x_idx]
        actual_y = y_data[closest_x_idx]

        self.v_line.setPos(actual_x)
        self.v_line.show()
        self.h_line.setPos(actual_y)
        self.h_line.show()
        self.hover_point.setData(pos=[(actual_x, actual_y)])
        self.hover_point.setBrush(pg.mkBrush(self.colors[self.selected_series_idx]))
        self.hover_point.show()

        color_hex = self.colors[self.selected_series_idx]
        label_text = self.label_formatter(self.selected_series_idx)
        stats_text = self._window_stats_text(self.selected_series_idx)
        self.selection_panel.update_selection(label_text, actual_x, actual_y, self.unit, color_hex, stats_text)

        # Anchor the floating cursor plate to the intersection point between the
        # selected curve and the cursor, not to the raw mouse position.
        self.cursor_label.setText(f"T: {actual_x:.2f}s\n{label_text}: {actual_y:.3f}")
        scene_pt = vb.mapViewToScene(pg.Point(float(actual_x), float(actual_y)))
        plot_pos = self.plot_widget.mapFromScene(scene_pt)
        container_pos = self.plot_widget.mapTo(self._plot_container, plot_pos)
        self.cursor_label.move(int(container_pos.x()) + 15, int(container_pos.y()) - 10)
        self.cursor_label.show()

    def keyPressEvent(self, event): # pyright: ignore[reportIncompatibleMethodOverride]
        if event.key() == Qt.Key.Key_Escape:
            self.clear_selection()
        super().keyPressEvent(event)
