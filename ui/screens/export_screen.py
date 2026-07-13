from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt

from ui.strings import Strings
from ui.theme import CurrentTheme as Theme


class ExportScreen(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QLabel(Strings.NAV_EXPORT)
        title.setStyleSheet(Theme.plot_title())
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(Strings.LBL_NO_EXPORT)
        desc.setStyleSheet("color: #888888; font-size: 14px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addStretch()
