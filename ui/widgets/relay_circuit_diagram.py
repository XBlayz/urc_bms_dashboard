"""Static circuit schematic for the pack relay topology: SDC and AIR+ in series,
feeding a parallel pair (AIR- direct, or Pre-Charge + resistor) before the bus.
Relays are colored green (closed) / red (open); pack/bus voltages and pack
current are overlaid live."""

from PyQt6.QtWidgets import QFrame
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt, QRectF, QPointF

CLOSED_COLOR = QColor("#00FF00")
OPEN_COLOR = QColor("#FF4444")
WIRE_COLOR = QColor("#888888")
TEXT_COLOR = QColor("#DDDDDD")
BG_COLOR = "#2A2A2A"


class RelayCircuitDiagram(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)
        self.setStyleSheet(f"background-color: {BG_COLOR}; border-radius: 8px;")
        self._states = {"sdc": False, "air_pos": False, "air_neg": False, "pre_charge": False}
        self._pack_voltage = 0.0
        self._post_air_voltage = 0.0
        self._pack_current = 0.0

    def update_values(self, states, pack_voltage, post_air_voltage, pack_current):
        self._states = states
        self._pack_voltage = pack_voltage
        self._post_air_voltage = post_air_voltage
        self._pack_current = pack_current
        self.update()

    def paintEvent(self, event): # pyright: ignore[reportIncompatibleMethodOverride]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        mid_y = h * 0.42
        margin = 50

        painter.setPen(QPen(WIRE_COLOR, 2))

        x_pack = margin
        x_sdc = w * 0.28
        x_air_pos = w * 0.5
        x_split = w * 0.64
        x_join = w * 0.84
        x_bus = w - margin

        painter.drawLine(QPointF(x_pack, mid_y), QPointF(x_sdc - 22, mid_y))
        self._draw_relay(painter, x_sdc, mid_y, "SDC", self._states.get("sdc", False))

        painter.drawLine(QPointF(x_sdc + 22, mid_y), QPointF(x_air_pos - 22, mid_y))
        self._draw_relay(painter, x_air_pos, mid_y, "AIR+", self._states.get("air_pos", False))

        painter.drawLine(QPointF(x_air_pos + 22, mid_y), QPointF(x_split, mid_y))

        y_top = mid_y - 40
        y_bot = mid_y + 40

        painter.setPen(QPen(WIRE_COLOR, 2))
        painter.drawLine(QPointF(x_split, mid_y), QPointF(x_split, y_top))
        painter.drawLine(QPointF(x_split, mid_y), QPointF(x_split, y_bot))

        x_branch = (x_split + x_join) / 2
        painter.drawLine(QPointF(x_split, y_top), QPointF(x_branch - 22, y_top))
        self._draw_relay(painter, x_branch, y_top, "AIR-", self._states.get("air_neg", False))
        painter.drawLine(QPointF(x_branch + 22, y_top), QPointF(x_join, y_top))

        x_pc = x_branch - 28
        x_res = x_branch + 32
        painter.drawLine(QPointF(x_split, y_bot), QPointF(x_pc - 20, y_bot))
        self._draw_relay(painter, x_pc, y_bot, "P.C.", self._states.get("pre_charge", False))
        painter.drawLine(QPointF(x_pc + 20, y_bot), QPointF(x_res - 14, y_bot))
        self._draw_resistor(painter, x_res, y_bot)
        painter.drawLine(QPointF(x_res + 14, y_bot), QPointF(x_join, y_bot))

        painter.setPen(QPen(WIRE_COLOR, 2))
        painter.drawLine(QPointF(x_join, y_top), QPointF(x_join, mid_y))
        painter.drawLine(QPointF(x_join, y_bot), QPointF(x_join, mid_y))
        painter.drawLine(QPointF(x_join, mid_y), QPointF(x_bus, mid_y))

        font = QFont("monospace", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(TEXT_COLOR))
        painter.drawText(QRectF(x_pack - 30, mid_y + 18, 110, 36),
                          Qt.AlignmentFlag.AlignLeft, f"PACK\n{self._pack_voltage:.1f} V")
        painter.drawText(QRectF(x_bus - 90, mid_y + 18, 110, 36),
                          Qt.AlignmentFlag.AlignRight, f"BUS\n{self._post_air_voltage:.1f} V")
        painter.drawText(QRectF((x_pack + x_bus) / 2 - 50, mid_y - h * 0.22, 100, 20),
                          Qt.AlignmentFlag.AlignCenter, f"I = {self._pack_current:.1f} A")

        painter.end()

    def _draw_relay(self, painter, x, y, label, closed):
        color = CLOSED_COLOR if closed else OPEN_COLOR
        painter.save()
        painter.setPen(QPen(color, 3))
        painter.drawRect(QRectF(x - 20, y - 12, 40, 24))
        if closed:
            painter.drawLine(QPointF(x - 20, y), QPointF(x + 20, y))
        else:
            painter.drawLine(QPointF(x - 20, y), QPointF(x - 5, y - 10))
            painter.drawLine(QPointF(x + 5, y - 10), QPointF(x + 20, y))

        painter.setFont(QFont("monospace", 8, QFont.Weight.Bold))
        painter.setPen(QPen(TEXT_COLOR))
        painter.drawText(QRectF(x - 30, y - 34, 60, 16), Qt.AlignmentFlag.AlignCenter, label)

        painter.setPen(QPen(color))
        state_text = "CLOSED" if closed else "OPEN"
        painter.drawText(QRectF(x - 30, y + 14, 60, 16), Qt.AlignmentFlag.AlignCenter, state_text)
        painter.restore()

    def _draw_resistor(self, painter, x, y):
        painter.save()
        painter.setPen(QPen(WIRE_COLOR, 2))
        zigzag_w = 26
        points = [
            QPointF(x - zigzag_w / 2 + i * (zigzag_w / 6), y + (6 if i % 2 else -6))
            for i in range(7)
        ]
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
        painter.restore()
