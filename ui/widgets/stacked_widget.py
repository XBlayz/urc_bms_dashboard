"""QStackedWidget variant that reports size hints based on the current page only.

The default QStackedWidget computes its size hints as the maximum across every
page it holds, so switching pages never triggers a resize. This is undesirable
when the stack lives inside a QScrollArea: it forces the scroll area to always
reserve space for the largest page (e.g. MetricsScreen) even while a small
page (e.g. SettingsScreen) is the one actually shown, making the scroll area
scrollable even when the visible content fits comfortably.
"""

from PyQt6.QtWidgets import QStackedWidget


class CurrentPageStackedWidget(QStackedWidget):
    def sizeHint(self):
        widget = self.currentWidget()
        return widget.sizeHint() if widget else super().sizeHint()

    def minimumSizeHint(self):
        widget = self.currentWidget()
        return widget.minimumSizeHint() if widget else super().minimumSizeHint()
