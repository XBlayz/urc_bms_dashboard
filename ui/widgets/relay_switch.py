"""Manual actuator control switch for the Override screen. Always reflects the
actual telemetry-reported relay state; a click only requests a transition and
is confirmed (or reverted) once new telemetry arrives via set_actual_state() -
there is no local optimistic state, per UI_definition.md Override spec."""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

from ui.strings import Strings

CLOSED_COLOR = "#00FF00"
OPEN_COLOR = "#FF4444"


class RelaySwitch(QPushButton):
    sig_user_toggled = pyqtSignal(bool) # requested new state

    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.label = label
        self._actual_state = False
        self._control_enabled = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.setEnabled(False)
        self.clicked.connect(self._on_clicked)
        self._refresh()

    def set_actual_state(self, closed: bool):
        if closed == self._actual_state:
            return
        self._actual_state = closed
        self._refresh()

    def set_control_enabled(self, enabled: bool):
        self._control_enabled = enabled
        self.setEnabled(enabled)
        self._refresh()

    def _on_clicked(self):
        self.sig_user_toggled.emit(not self._actual_state)

    def _refresh(self):
        state_text = Strings.LBL_ACTUATOR_CLOSE if self._actual_state else Strings.LBL_ACTUATOR_OPEN
        self.setText(f"{self.label}: {state_text}")

        border = (CLOSED_COLOR if self._actual_state else OPEN_COLOR) if self._control_enabled else "#444444"
        text_color = "#FFFFFF" if self._control_enabled else "#777777"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #2A2A2A;
                color: {text_color};
                border: 2px solid {border};
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
                font-family: monospace;
            }}
            QPushButton:hover {{
                background-color: #333333;
            }}
            QPushButton:disabled {{
                background-color: #222222;
            }}
        """)
