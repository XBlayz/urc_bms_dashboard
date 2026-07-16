"""Grid that reflows its items into N columns based on available width.

Was previously duplicated in metrics_screen.py and charging_screen.py with
diverging behavior (only one copy debounced recalculation via QTimer, only
one copy supported remove_item). This is the merged, complete version.
"""

from PyQt6.QtWidgets import QWidget, QGridLayout
from PyQt6.QtCore import QTimer

from ui.theme import CurrentTheme as Theme


class ResponsiveGrid(QWidget):
    def __init__(self, min_item_width=Theme.W_SIZE_S, parent=None):
        super().__init__(parent)
        self._items = []
        self._min_item_width = min_item_width
        self._cols = 1
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(10)
        self._pending_recalc = False

    def add_item(self, widget):
        widget._origin_grid = self
        self._items.append(widget)
        self._grid.addWidget(widget, 0, len(self._items) - 1)
        self._relayout()
        self._schedule_recalc()

    def remove_item(self, widget):
        if widget in self._items:
            self._items.remove(widget)
            self._grid.removeWidget(widget)
            self._relayout()

    def resizeEvent(self, event): # pyright: ignore[reportIncompatibleMethodOverride]
        super().resizeEvent(event)
        self._schedule_recalc()

    def showEvent(self, event): # pyright: ignore[reportIncompatibleMethodOverride]
        super().showEvent(event)
        self._schedule_recalc()

    def _schedule_recalc(self):
        if not self._pending_recalc:
            self._pending_recalc = True
            QTimer.singleShot(0, self._recalc_columns)

    def _recalc_columns(self):
        self._pending_recalc = False
        width = self.width()
        if width <= 0:
            if self._cols != 1:
                self._cols = 1
                self._relayout()
            return
        new_cols = max(1, width // self._min_item_width)
        if new_cols != self._cols:
            self._cols = new_cols
            self._relayout()

    def _relayout(self):
        for i, widget in enumerate(self._items):
            row = i // self._cols
            col = i % self._cols
            self._grid.addWidget(widget, row, col)
