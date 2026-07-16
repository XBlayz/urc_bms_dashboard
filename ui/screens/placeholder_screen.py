"""Simple placeholder screen for not-yet-implemented sections (Override, Logs, Settings)."""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt

from ui.theme import CurrentTheme as Theme


class PlaceholderScreen(QFrame):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(Theme.plot_title())
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(message)
        desc_lbl.setStyleSheet("color: #888888; font-size: 14px;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_lbl)

        layout.addStretch()
