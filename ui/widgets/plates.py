from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

from ui.theme import CurrentTheme as Theme


class EnumStatePlate(QFrame):
    def __init__(self, label, enum_map, value_key, parent=None):
        super().__init__(parent)
        self.enum_map = enum_map
        self.value_key = value_key
        self.setStyleSheet(Theme.plate())
        self.init_ui(label)

    def init_ui(self, label):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 3, 4, 3)
        layout.setSpacing(0)

        title = QLabel(label)
        title.setStyleSheet("color: #AAAAAA; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        layout.addWidget(title)

        self.value_lbl = QLabel("--")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; font-family: monospace;")
        layout.addWidget(self.value_lbl)

    def update_value(self, value):
        text = self.enum_map.get(value, "UNKNOWN")
        color = Theme.STATE_COLORS.get(text, "#444444")
        self.value_lbl.setText(text)
        self.value_lbl.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; font-family: monospace;")


class UnitPlate(QFrame):
    def __init__(self, label, value="--", unit="", color_hex=None, parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self.setStyleSheet(Theme.plate())
        self.init_ui(label, value, unit)

    def init_ui(self, label, value, unit):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 3, 4, 3)
        layout.setSpacing(0)

        title = QLabel(label)
        title.setStyleSheet("color: #AAAAAA; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        layout.addWidget(title)

        value_layout = QHBoxLayout()
        value_layout.setSpacing(1)

        self.value_lbl = QLabel(str(value))
        self.value_lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; font-family: monospace;")
        value_layout.addWidget(self.value_lbl)

        if unit:
            unit_lbl = QLabel(unit)
            unit_lbl.setStyleSheet("color: #888888; font-size: 10px; font-family: monospace;")
            value_layout.addWidget(unit_lbl)

        value_layout.addStretch()
        layout.addLayout(value_layout)

    def update_value(self, value):
        self.value_lbl.setText(str(value))
        if self.color_hex:
            self.value_lbl.setStyleSheet(f"color: {self.color_hex}; font-size: 14px; font-weight: bold; font-family: monospace;")


class ActuatorStatePlate(QFrame):
    def __init__(self, label, value=False, true_label="ON", false_label="OFF",
                 true_color="#00FF00", false_color="#FF4444", parent=None):
        super().__init__(parent)
        self.true_label = true_label
        self.false_label = false_label
        self.true_color = true_color
        self.false_color = false_color
        self.setStyleSheet(Theme.plate())
        self.init_ui(label, value)

    def init_ui(self, label, value):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 3, 4, 3)
        layout.setSpacing(0)

        title = QLabel(label)
        title.setStyleSheet("color: #AAAAAA; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        layout.addWidget(title)

        self.value_lbl = QLabel("")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_lbl)

        self.update_value(value)

    def update_value(self, value):
        if value:
            self.value_lbl.setText(self.true_label)
            self.value_lbl.setStyleSheet(f"color: {self.true_color}; font-size: 14px; font-weight: bold; font-family: monospace;")
        else:
            self.value_lbl.setText(self.false_label)
            self.value_lbl.setStyleSheet(f"color: {self.false_color}; font-size: 14px; font-weight: bold; font-family: monospace;")


class StatSummaryPlate(QFrame):
    def __init__(self, label, unit="", parent=None):
        super().__init__(parent)
        self.setStyleSheet(Theme.plate())
        self.unit = unit
        self.init_ui(label)

    def init_ui(self, label):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 3, 4, 3)
        layout.setSpacing(0)

        title = QLabel(label)
        title.setStyleSheet("color: #AAAAAA; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        layout.addWidget(title)

        self.min_lbl = QLabel("--")
        self.max_lbl = QLabel("--")
        self.avg_lbl = QLabel("--")
        self.delta_lbl = QLabel("--")

        for lbl in (self.min_lbl, self.max_lbl, self.avg_lbl, self.delta_lbl):
            lbl.setStyleSheet("color: #888888; font-size: 10px; font-family: monospace;")
            layout.addWidget(lbl)

    def update_stats(self, min_val, max_val, avg_val, delta_val):
        self.min_lbl.setText(f"MIN: {min_val:.3f}{self.unit}")
        self.max_lbl.setText(f"MAX: {max_val:.3f}{self.unit}")
        self.avg_lbl.setText(f"AVG: {avg_val:.3f}{self.unit}")
        self.delta_lbl.setText(f"DELTA: {delta_val:.3f}{self.unit}")


class TimePlate(QFrame):
    def __init__(self, label, seconds=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(Theme.plate())
        self.init_ui(label, seconds)

    def init_ui(self, label, seconds):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 3, 4, 3)
        layout.setSpacing(0)

        title = QLabel(label)
        title.setStyleSheet("color: #AAAAAA; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        layout.addWidget(title)

        self.value_lbl = QLabel("")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold; font-family: monospace;")
        layout.addWidget(self.value_lbl)

        self.update_value(seconds)

    def update_value(self, seconds):
        if seconds is None or seconds < 0:
            self.value_lbl.setText("--:--:--")
            return

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        self.value_lbl.setText(f"{hours:02d}:{minutes:02d}:{secs:02d}")
