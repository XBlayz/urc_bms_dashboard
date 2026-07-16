from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

from ui.theme import CurrentTheme as Theme
from ui.strings import Strings


class Plate(QFrame):
    """Base widget for sidebar/status 'plates': a titled box showing an instantaneous value."""

    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.setStyleSheet(Theme.plate())

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 3, 4, 3)
        self._layout.setSpacing(0)

        title = QLabel(label)
        title.setStyleSheet(Theme.plate_title())
        self._layout.addWidget(title)

        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(0)
        self._layout.addLayout(self.body_layout)

    def update_value(self, value):
        raise NotImplementedError


class EnumStatePlate(Plate):
    def __init__(self, label, enum_map, parent=None):
        super().__init__(label, parent)
        self.enum_map = enum_map

        self.value_lbl = QLabel("--")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; font-family: monospace;")
        self.body_layout.addWidget(self.value_lbl)

    def update_value(self, value):
        text = self.enum_map.get(value, "UNKNOWN")
        color = Theme.STATE_COLORS.get(text, "#444444")
        self.value_lbl.setText(text)
        self.value_lbl.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; font-family: monospace;")


class UnitPlate(Plate):
    def __init__(self, label, value="--", unit="", color_hex=None, parent=None):
        super().__init__(label, parent)
        self.color_hex = color_hex

        value_layout = QHBoxLayout()
        value_layout.setSpacing(1)

        self.value_lbl = QLabel(str(value))
        self.value_lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; font-family: monospace;")
        value_layout.addWidget(self.value_lbl)

        self.unit_lbl = None
        if unit:
            self.unit_lbl = QLabel(unit)
            self.unit_lbl.setStyleSheet("color: #888888; font-size: 10px; font-family: monospace;")
            value_layout.addWidget(self.unit_lbl)

        value_layout.addStretch()
        self.body_layout.addLayout(value_layout)

    def update_value(self, value):
        self.value_lbl.setText(str(value))
        if self.color_hex:
            self.value_lbl.setStyleSheet(f"color: {self.color_hex}; font-size: 14px; font-weight: bold; font-family: monospace;")


class ActuatorStatePlate(Plate):
    def __init__(self, label, value=False,
                 true_label=Strings.LBL_ACTUATOR_CLOSE, false_label=Strings.LBL_ACTUATOR_OPEN,
                 true_color="#00FF00", false_color="#FF4444", parent=None):
        super().__init__(label, parent)
        self.true_label = true_label
        self.false_label = false_label
        self.true_color = true_color
        self.false_color = false_color

        self.value_lbl = QLabel("")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body_layout.addWidget(self.value_lbl)

        self.update_value(value)

    def update_value(self, value):
        if value:
            self.value_lbl.setText(self.true_label)
            self.value_lbl.setStyleSheet(f"color: {self.true_color}; font-size: 14px; font-weight: bold; font-family: monospace;")
        else:
            self.value_lbl.setText(self.false_label)
            self.value_lbl.setStyleSheet(f"color: {self.false_color}; font-size: 14px; font-weight: bold; font-family: monospace;")


class StatSummaryPlate(Plate):
    """Shows MIN/MAX/AVG/DELTA across a series, colored per UI_definition.md 1.3
    (min=cyan, max=red, avg=yellow, delta=default)."""

    MIN_COLOR = "#00AAFF"
    MAX_COLOR = "#FF4444"
    AVG_COLOR = "#FFDD00"
    DELTA_COLOR = "#888888"

    def __init__(self, label, unit="", parent=None):
        super().__init__(label, parent)
        self.unit = unit

        self.min_lbl = QLabel("MIN: --")
        self.max_lbl = QLabel("MAX: --")
        self.avg_lbl = QLabel("AVG: --")
        self.delta_lbl = QLabel("DELTA: --")

        for lbl, color in (
            (self.min_lbl, self.MIN_COLOR),
            (self.max_lbl, self.MAX_COLOR),
            (self.avg_lbl, self.AVG_COLOR),
            (self.delta_lbl, self.DELTA_COLOR),
        ):
            lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-family: monospace;")
            self.body_layout.addWidget(lbl)

    def update_stats(self, min_val, max_val, avg_val, delta_val):
        self.min_lbl.setText(f"MIN: {min_val:.3f}{self.unit}")
        self.max_lbl.setText(f"MAX: {max_val:.3f}{self.unit}")
        self.avg_lbl.setText(f"AVG: {avg_val:.3f}{self.unit}")
        self.delta_lbl.setText(f"DELTA: {delta_val:.3f}{self.unit}")


class TimePlate(Plate):
    def __init__(self, label, seconds=None, parent=None):
        super().__init__(label, parent)

        self.value_lbl = QLabel("")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; font-family: monospace;")
        self.body_layout.addWidget(self.value_lbl)

        self.update_value(seconds)

    def update_value(self, seconds): # pyright: ignore[reportIncompatibleMethodOverride]
        if seconds is None or seconds < 0:
            self.value_lbl.setText("--:--:--")
            return

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        self.value_lbl.setText(f"{hours:02d}:{minutes:02d}:{secs:02d}")


class FaultCounterPlate(Plate):
    """Shows the number of currently active faults.

    diagnostic_state is treated as a bitmask of active fault flags (popcount).
    No bit layout is defined by the firmware yet; update this once one exists.
    """

    def __init__(self, label, parent=None):
        super().__init__(label, parent)

        self.value_lbl = QLabel("--")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; font-family: monospace;")
        self.body_layout.addWidget(self.value_lbl)

    def update_value(self, diagnostic_state): # pyright: ignore[reportIncompatibleMethodOverride]
        fault_count = bin(diagnostic_state).count("1") if diagnostic_state else 0
        color = "#FF4444" if fault_count > 0 else "#00FF00"
        self.value_lbl.setText(str(fault_count))
        self.value_lbl.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; font-family: monospace;")
