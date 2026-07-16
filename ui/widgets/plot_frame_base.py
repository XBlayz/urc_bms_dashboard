"""Common chrome shared by all plot widgets.

Provides the header (title + widget-specific extra buttons + pause + table
toggle + maximize + reset + stats label) and a QStackedWidget hosting the
plot/table pages. Concrete widgets build their own pages and push them onto
self.stack; PlotFrameBase only owns the parts that were previously copy-pasted
verbatim across TimeSeriesPlotWidget, StackedBoolPlot and BarChartWidget.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSignal

from ui.strings import Strings
from ui.theme import CurrentTheme as Theme


class ToggleButton(QPushButton):
    def __init__(self, text, checked=True):
        super().__init__(text)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(22)
        self.setStyleSheet(Theme.toggle_button())


class PlotFrameBase(QFrame):
    sig_maximize_toggled = pyqtSignal(bool)

    def __init__(self, title, show_table_toggle=True, show_pause=True):
        super().__init__()
        self.title_text = title
        self._show_table_toggle = show_table_toggle
        self._show_pause = show_pause
        self.is_paused = False
        self.setStyleSheet(Theme.time_series_plot())
        self._init_frame()

    def _init_frame(self):
        self.setObjectName(type(self).__name__)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(40)
        header.setStyleSheet(Theme.plot_header())
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)

        title_lbl = QLabel(self.title_text)
        title_lbl.setStyleSheet(Theme.plot_title())
        header_layout.addWidget(title_lbl)

        self._build_extra_header_buttons(header_layout)

        if self._show_pause:
            self.pause_cb = ToggleButton(Strings.BTN_PAUSE, checked=False)
            self.pause_cb.toggled.connect(self._on_pause_toggled)
            header_layout.addWidget(self.pause_cb)

        if self._show_table_toggle:
            self.table_cb = ToggleButton(Strings.BTN_TABLE, checked=False)
            self.table_cb.toggled.connect(self.on_table_toggled)
            header_layout.addWidget(self.table_cb)

        self.maximize_cb = ToggleButton(Strings.BTN_MAXIMIZE, checked=False)
        self.maximize_cb.toggled.connect(self.on_maximize_toggled)
        header_layout.addWidget(self.maximize_cb)

        self.reset_btn = QPushButton(Strings.BTN_RESET)
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.setFixedHeight(22)
        self.reset_btn.setStyleSheet(Theme.toggle_button())
        self.reset_btn.clicked.connect(self.reset_data)
        header_layout.addWidget(self.reset_btn)

        header_layout.addStretch()

        self.stats_lbl = QLabel(Strings.STATS_EMPTY)
        self.stats_lbl.setStyleSheet(Theme.stats_label())
        header_layout.addWidget(self.stats_lbl)

        layout.addWidget(header)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, stretch=1)

    def _build_extra_header_buttons(self, header_layout):
        """Hook for subclasses to insert widget-specific header buttons
        (e.g. auto-scroll/fit for time series, matrix-view toggle for bar charts)."""
        pass

    @staticmethod
    def _make_header_button(text, slot):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(22)
        btn.setStyleSheet(Theme.toggle_button())
        btn.clicked.connect(slot)
        return btn

    def on_maximize_toggled(self, checked):
        self.sig_maximize_toggled.emit(checked)

    def _on_pause_toggled(self, checked):
        self.is_paused = checked
        self.on_pause_toggled(checked)

    def on_pause_toggled(self, checked):
        pass

    def on_table_toggled(self, checked):
        if checked:
            self.stack.setCurrentIndex(1)
            if hasattr(self, '_last_x_view'):
                self.table_model.update_data(self._last_x_view, self._last_data_2d)
        else:
            self.stack.setCurrentIndex(0)

    def reset_data(self):
        raise NotImplementedError
