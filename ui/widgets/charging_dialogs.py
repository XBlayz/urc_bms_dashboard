"""Modal dialog for confirming the start of the charging process."""

from PyQt6.QtWidgets import QMessageBox, QPushButton

from ui.strings import Strings
from ui.theme import CurrentTheme as Theme


class ChargingConfirmDialog(QMessageBox):
    """Shown when the user clicks 'Start Charging' to confirm the set voltage and current."""

    def __init__(self, voltage: float, current: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle(Strings.TITLE_CHARGING_SUMMARY)
        self.setIcon(QMessageBox.Icon.Question)
        self.setText(Strings.MSG_CONFIRM_START.format(voltage=voltage, current=current))

        self.confirmed = False

        self.no_btn = self.addButton(QMessageBox.StandardButton.No)
        self.yes_btn = self.addButton(QMessageBox.StandardButton.Yes)

        # Apply identical base geometries, changing only the border color
        Theme.pop_up_button_style(self.no_btn, "#666666") # pyright: ignore[reportArgumentType]
        Theme.pop_up_button_style(self.yes_btn, "#00AA00") # pyright: ignore[reportArgumentType]

        self.buttonClicked.connect(self._on_button_clicked)

    def _on_button_clicked(self, button: QPushButton):
        if button == self.yes_btn:
            self.confirmed = True
        else:
            self.confirmed = False
