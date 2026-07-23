"""0-100% horizontal status bar with a threshold marker, used by the Override
screen to visualize the post-AIR/pack voltage ratio against the configured
main-relay closing threshold."""

from PyQt6.QtWidgets import QFrame
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QRectF

GREY = "#666666"
RED = "#FF4444"
ORANGE = "#FFAA00"
GREEN = "#00AA00"
BRIGHT_GREEN = "#00FF00"
TRACK_COLOR = "#1A1A1A"
MARKER_COLOR = "#FFFFFF"


def ratio_status_color(value_pct: float, threshold_pct: float) -> str:
    if value_pct < 5:
        return GREY
    if value_pct < threshold_pct - 25:
        return RED
    if value_pct < threshold_pct:
        return ORANGE
    if value_pct > 95:
        return BRIGHT_GREEN
    return GREEN


class PercentageBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(18)
        self.setMinimumWidth(120)
        self._value = 0.0
        self._threshold = 90.0

    def set_values(self, value_pct: float, threshold_pct: float):
        self._value = max(0.0, min(100.0, value_pct))
        self._threshold = max(0.0, min(100.0, threshold_pct))
        self.update()

    def paintEvent(self, event): # pyright: ignore[reportIncompatibleMethodOverride]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0, 0, self.width(), self.height())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(TRACK_COLOR))
        painter.drawRoundedRect(rect, 4, 4)

        fill_width = rect.width() * (self._value / 100.0)
        if fill_width > 0:
            painter.setBrush(QColor(ratio_status_color(self._value, self._threshold)))
            painter.drawRoundedRect(QRectF(0, 0, fill_width, rect.height()), 4, 4)

        marker_x = rect.width() * (self._threshold / 100.0)
        painter.setPen(QPen(QColor(MARKER_COLOR), 2))
        painter.drawLine(int(marker_x), 0, int(marker_x), int(rect.height()))

        painter.end()
