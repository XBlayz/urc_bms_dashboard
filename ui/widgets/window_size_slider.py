"""Sidebar control for the global autoscroll sliding-window size (UI_definition.md 2.1)."""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSlider
from PyQt6.QtCore import Qt

from ui.widgets.plot_settings import global_plot_settings
from ui.theme import CurrentTheme as Theme

MIN_WINDOW_SECONDS = 5
MAX_WINDOW_SECONDS = 120


class WindowSizeSlider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(Theme.plate())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 3, 4, 3)
        layout.setSpacing(2)

        title = QLabel("AUTOSCROLL WINDOW")
        title.setStyleSheet(Theme.plate_title())
        layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(6)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(MIN_WINDOW_SECONDS)
        self.slider.setMaximum(MAX_WINDOW_SECONDS)
        self.slider.setValue(int(global_plot_settings.window_size_seconds))
        self.slider.valueChanged.connect(self._on_slider_changed)
        row.addWidget(self.slider, stretch=1)

        self.value_lbl = QLabel(f"{self.slider.value()}s")
        self.value_lbl.setStyleSheet("color: #FFFFFF; font-size: 11px; font-family: monospace;")
        self.value_lbl.setFixedWidth(32)
        row.addWidget(self.value_lbl)

        layout.addLayout(row)

    def _on_slider_changed(self, value):
        self.value_lbl.setText(f"{value}s")
        global_plot_settings.set_window_size_seconds(value)
