"""Abstract base for main-area screens that receive live telemetry.

main_window.py checks isinstance(screen, TelemetryScreen) instead of the
previous hasattr(screen, 'add_point') duck-typing.
"""

from abc import ABCMeta, abstractmethod
from PyQt6.QtWidgets import QFrame


class _QFrameABCMeta(type(QFrame), ABCMeta):
    """Metaclass merging QFrame's and ABC's metaclasses so screens can use @abstractmethod."""
    pass


class TelemetryScreen(QFrame, metaclass=_QFrameABCMeta):
    """Contract for screens shown in the main stacked area that consume telemetry."""

    @abstractmethod
    def add_point(self, current_time, telemetry):
        """Called on every telemetry update while this screen is active."""
        raise NotImplementedError

    def clear_selection(self):
        """Clears any plot selection/cursor state on this screen. No-op by default."""
        pass
