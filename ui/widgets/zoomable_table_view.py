"""QTableView variant supporting Ctrl+wheel zoom of cell size, used by matrix/heatmap views."""

from PyQt6.QtWidgets import QTableView
from PyQt6.QtCore import Qt


class ZoomableTableView(QTableView):
    MIN_CELL_SIZE = 24
    MAX_CELL_SIZE = 96

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cell_size = 48
        self.horizontalHeader().setDefaultSectionSize(self._cell_size)
        self.verticalHeader().setDefaultSectionSize(self._cell_size)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = 4 if event.angleDelta().y() > 0 else -4
            self._cell_size = max(self.MIN_CELL_SIZE, min(self.MAX_CELL_SIZE, self._cell_size + delta))
            self.horizontalHeader().setDefaultSectionSize(self._cell_size)
            self.verticalHeader().setDefaultSectionSize(self._cell_size)
            event.accept()
        else:
            super().wheelEvent(event)
