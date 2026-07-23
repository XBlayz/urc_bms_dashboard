"""Modal dialogs for the Override screen's relay-closing voltage guardrail."""

from PyQt6.QtWidgets import QMessageBox, QPushButton
from PyQt6.QtCore import QTimer

from ui.strings import Strings
from ui.theme import CurrentTheme as Theme


class GuardrailDialog(QMessageBox):
    """Shown when closing a main relay (SDC/AIR+/AIR-) would close all three
    before the post-AIR/pack voltage ratio has reached the configured threshold."""

    CANCEL, PRE_CHARGE, FORCE = "cancel", "pre_charge", "force"

    def __init__(self, ratio_pct, threshold_pct, parent=None):
        super().__init__(parent)
        self.setWindowTitle(Strings.TITLE_GUARDRAIL_DIALOG)
        self.setIcon(QMessageBox.Icon.Question)
        self.setText(Strings.MSG_GUARDRAIL_VOLTAGE.format(ratio=ratio_pct, threshold=threshold_pct))

        self.choice = self.CANCEL

        self.cancel_btn = self.addButton(Strings.BTN_CANCEL, QMessageBox.ButtonRole.RejectRole)
        self.precharge_btn = self.addButton(Strings.BTN_PRE_CHARGE_OPTION, QMessageBox.ButtonRole.ActionRole)
        self.force_btn = self.addButton(Strings.BTN_FORCE_OPTION, QMessageBox.ButtonRole.DestructiveRole)

        # Apply identical base geometries, changing only the border color
        Theme.pop_up_button_style(self.cancel_btn, "#666666") # pyright: ignore[reportArgumentType]
        Theme.pop_up_button_style(self.precharge_btn, "orange") # pyright: ignore[reportArgumentType]
        Theme.pop_up_button_style(self.force_btn, "red") # pyright: ignore[reportArgumentType]

        self.buttonClicked.connect(self._on_button_clicked)

    def _on_button_clicked(self, button: QPushButton):
        if button == self.cancel_btn:
            self.choice = self.CANCEL
        elif button == self.precharge_btn:
            self.choice = self.PRE_CHARGE
        elif button == self.force_btn:
            self.choice = self.FORCE


class ForceConfirmDialog(QMessageBox):
    """Second-stage warning for the 'Force' guardrail bypass; Confirm stays
    disabled for a 5-second countdown, then becomes clickable with a red border."""

    COUNTDOWN_SECONDS = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(Strings.TITLE_FORCE_CONFIRM_DIALOG)
        self.setIcon(QMessageBox.Icon.Warning)
        self.setText(Strings.MSG_FORCE_WARNING)

        self.confirmed = False
        self._remaining = self.COUNTDOWN_SECONDS

        self.cancel_btn = self.addButton(Strings.BTN_CANCEL, QMessageBox.ButtonRole.RejectRole)
        self.confirm_btn = self.addButton(self._countdown_text(), QMessageBox.ButtonRole.DestructiveRole)
        self.confirm_btn.setEnabled(False) # pyright: ignore[reportOptionalMemberAccess]

        # Apply styles
        Theme.pop_up_button_style(self.cancel_btn, "#666666") # pyright: ignore[reportArgumentType]
        Theme.pop_up_button_style(self.confirm_btn, "#444444")  # pyright: ignore[reportArgumentType]

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

        self.buttonClicked.connect(self._on_button_clicked)

    def _countdown_text(self):
        return Strings.BTN_CONFIRM if self._remaining <= 0 else f"{Strings.BTN_CONFIRM} ({self._remaining})"

    def _tick(self):
        self._remaining -= 1
        if self._remaining <= 0:
            self._timer.stop()
            self.confirm_btn.setEnabled(True) # pyright: ignore[reportOptionalMemberAccess]
            # Update to red border once enabled
            Theme.pop_up_button_style(self.confirm_btn, "red") # pyright: ignore[reportArgumentType]

        self.confirm_btn.setText(self._countdown_text()) # pyright: ignore[reportOptionalMemberAccess]

    def _on_button_clicked(self, button: QPushButton):
        if button == self.confirm_btn:
            self.confirmed = True
