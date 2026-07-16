"""ViewBox variant that only zooms on wheel when CTRL is held.

pyqtgraph's default ViewBox zooms on every wheel event, which conflicts with
normal page scrolling over a plot embedded in a scroll area.
"""

from PyQt6.QtCore import Qt
import pyqtgraph as pg


class CtrlZoomViewBox(pg.ViewBox):
    def wheelEvent(self, ev, axis=None):
        if ev.modifiers() & Qt.KeyboardModifier.ControlModifier:
            super().wheelEvent(ev, axis)
        else:
            ev.ignore()
