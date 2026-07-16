"""Process-wide settings shared by all temporal plots.

UI_definition.md 2.1: the autoscroll sliding window is global across every
time series plot, not per-widget.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class PlotSettings(QObject):
    window_size_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self._window_size_seconds = 10.0

    @property
    def window_size_seconds(self):
        return self._window_size_seconds

    def set_window_size_seconds(self, value):
        value = max(1.0, float(value))
        if value != self._window_size_seconds:
            self._window_size_seconds = value
            self.window_size_changed.emit(value)


# Single shared instance used by every temporal plot widget.
global_plot_settings = PlotSettings()
