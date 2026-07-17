"""Mixin adding a mouse-following live cursor plus up to two click-pinned
'time-fixed' cursors, shared by EnumPlot and StackedBoolPlot.

Both host classes already own a v_line (live cursor) and a plot_widget from
their own page-building code; this mixin only owns the fixed-cursor
bookkeeping (creation, repositioning on redraw/pan, eviction, clearing),
leaving the per-widget hit-testing (segment lookup vs. band lookup) to the
host class's on_mouse_click/on_mouse_move.
"""

import pyqtgraph as pg
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

MAX_FIXED_CURSORS = 2
FIXED_CURSOR_COLORS = ["#FFFFFF", "#FFD700"]


class MultiCursorMixin:
    def _init_multi_cursor(self, label_container):
        self._mc_container = label_container
        self._fixed_cursors = []  # [{'line': InfiniteLine, 'label': QLabel, 'x': float}]
        self._last_mouse_scene_pos = None

    def _mc_add_fixed_cursor(self, x_value, text):
        if len(self._fixed_cursors) >= MAX_FIXED_CURSORS:
            oldest = self._fixed_cursors.pop(0)
            self.plot_widget.removeItem(oldest['line']) # pyright: ignore[reportAttributeAccessIssue]
            oldest['label'].deleteLater()

        color = FIXED_CURSOR_COLORS[len(self._fixed_cursors) % len(FIXED_CURSOR_COLORS)]
        line = pg.InfiniteLine(
            angle=90, movable=False,
            pen=pg.mkPen(color=color, width=2, style=Qt.PenStyle.SolidLine)
        )
        line.setPos(x_value)
        self.plot_widget.addItem(line) # pyright: ignore[reportAttributeAccessIssue]

        label = QLabel(text, self._mc_container)
        label.setStyleSheet(
            f"color: {color}; font-size: 11px; font-family: monospace; "
            "background: rgba(0,0,0,150); padding: 2px 4px; border-radius: 4px;"
        )
        label.adjustSize()
        label.show()

        self._fixed_cursors.append({'line': line, 'label': label, 'x': x_value})
        self._mc_reposition_fixed_labels()

    def _mc_clear_fixed_cursors(self):
        for cursor in self._fixed_cursors:
            self.plot_widget.removeItem(cursor['line']) # pyright: ignore[reportAttributeAccessIssue]
            cursor['label'].deleteLater()
        self._fixed_cursors = []

    def _mc_reposition_fixed_labels(self):
        if not self._fixed_cursors:
            return
        vb = self.plot_widget.getViewBox() # pyright: ignore[reportAttributeAccessIssue]
        y_top = vb.viewRange()[1][1]
        for cursor in self._fixed_cursors:
            scene_pt = vb.mapViewToScene(pg.Point(float(cursor['x']), y_top))
            plot_pos = self.plot_widget.mapFromScene(scene_pt) # pyright: ignore[reportAttributeAccessIssue]
            container_pos = self.plot_widget.mapTo(self._mc_container, plot_pos) # pyright: ignore[reportAttributeAccessIssue]
            cursor['label'].move(int(container_pos.x()) + 6, int(container_pos.y()) + 6)
            cursor['label'].raise_()
