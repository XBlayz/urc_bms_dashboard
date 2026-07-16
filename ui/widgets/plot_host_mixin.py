"""Mixin providing a unified 'maximize a child plot into the full visible area' behavior.

Replaces the divergent maximize implementations that used to live separately
in MetricsScreen (grid-swap via QStackedWidget) and ChargingScreen (hiding
whole side panels, with no viewport-size constraint). Screens using this
mixin must call _init_plot_host(stack) once, with a QStackedWidget whose
index 0 is the normal page; this mixin appends the maximize page at index 1.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt6.QtCore import QTimer


class PlotHostMixin:
    def _init_plot_host(self, stack):
        self._stack = stack
        self._max_page = QWidget()
        self._max_layout = QVBoxLayout(self._max_page)
        self._max_layout.setContentsMargins(0, 0, 0, 0)
        self._stack.addWidget(self._max_page)
        self._maximized_widget = None
        self._maximized_origin_grid = None

    def _on_plot_maximize(self, checked):
        sender = self.sender() # pyright: ignore[reportAttributeAccessIssue]
        if not sender:
            return
        if checked:
            self._maximize_plot(sender)
        else:
            self._restore_normal()

    def _maximize_plot(self, plot_widget):
        self._maximized_widget = plot_widget
        self._maximized_origin_grid = getattr(plot_widget, '_origin_grid', None)
        if self._maximized_origin_grid:
            self._maximized_origin_grid.remove_item(plot_widget)
        self._max_layout.addWidget(plot_widget)
        self._stack.setCurrentIndex(1)
        QTimer.singleShot(0, self._constrain_max_page)

    def _constrain_max_page(self):
        scroll_area = None
        parent = self.parent() # pyright: ignore[reportAttributeAccessIssue]
        while parent:
            if isinstance(parent, QScrollArea):
                scroll_area = parent
                break
            parent = parent.parent()
        if scroll_area and scroll_area.viewport():
            size = scroll_area.viewport().size() # pyright: ignore[reportOptionalMemberAccess]
            self._max_page.setMaximumSize(size)
            self._max_page.setMinimumSize(size)

    def _restore_normal(self):
        if self._maximized_widget:
            self._max_layout.removeWidget(self._maximized_widget)
            if self._maximized_origin_grid:
                self._maximized_origin_grid.add_item(self._maximized_widget)
                self._maximized_widget.show()
            self._maximized_widget = None
            self._maximized_origin_grid = None
        self._max_page.setMaximumSize(16777215, 16777215)
        self._max_page.setMinimumSize(0, 0)
        self._stack.setCurrentIndex(0)
