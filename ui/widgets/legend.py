"""Reusable interactive legend: per-series visibility toggle buttons in a horizontally
scrollable strip, plus select-all / deselect-all controls.

The original legend was a plain QHBoxLayout with no scroll area, which overflows
badly once series_count reaches cell-array sizes (100+ cells/sensors).
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QWidget, QScrollArea, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

from ui.strings import Strings
from ui.theme import CurrentTheme as Theme


class LegendButton(QPushButton):
    def __init__(self, label, color, index, parent=None):
        super().__init__(parent)
        self._index = index
        self._visible = True
        self._color = color
        self.setText(f"  {label}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(20)
        self._update_style()

    def _update_style(self):
        color = self._color if self._visible else "#555555"
        bg = "#2A2A2A" if self._visible else "#1A1A1A"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {color};
                border: none;
                border-radius: 4px;
                text-align: left;
                font-size: 11px;
                font-family: monospace;
                padding-left: 4px;
                padding-right: 8px;
            }}
            QPushButton:hover {{
                background-color: #333333;
            }}
        """)

    def set_visible_state(self, visible):
        self._visible = visible
        self._update_style()

    def toggle_visibility(self):
        self.set_visible_state(not self._visible)
        return self._visible

    def is_visible(self):
        return self._visible

    def index(self):
        return self._index


class LegendPanel(QFrame):
    """Horizontally-scrollable strip of LegendButtons, with select-all/deselect-all controls."""

    sig_visibility_changed = pyqtSignal(int, bool)

    def __init__(self, labels, colors, parent=None):
        super().__init__(parent)
        self.buttons = []
        self.setStyleSheet("background-color: #222222;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        self.select_all_btn = QPushButton(Strings.BTN_SELECT_ALL)
        self.deselect_all_btn = QPushButton(Strings.BTN_DESELECT_ALL)
        for btn in (self.select_all_btn, self.deselect_all_btn):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(20)
            btn.setStyleSheet(Theme.toggle_button())
        self.select_all_btn.clicked.connect(lambda: self._set_all(True))
        self.deselect_all_btn.clicked.connect(lambda: self._set_all(False))
        layout.addWidget(self.select_all_btn)
        layout.addWidget(self.deselect_all_btn)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setFixedHeight(28)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        strip = QWidget()
        strip_layout = QHBoxLayout(strip)
        strip_layout.setContentsMargins(0, 0, 0, 0)
        strip_layout.setSpacing(4)

        for i, label in enumerate(labels):
            color = colors[i] if i < len(colors) else "#888888"
            color_hex = '#%02x%02x%02x' % tuple(color) if isinstance(color, (list, tuple)) else color
            btn = LegendButton(label, color_hex, i)
            btn.clicked.connect(self._on_button_clicked)
            strip_layout.addWidget(btn)
            self.buttons.append(btn)
        strip_layout.addStretch()

        scroll.setWidget(strip)
        layout.addWidget(scroll, stretch=1)

    def _on_button_clicked(self):
        sender = self.sender()
        if not isinstance(sender, LegendButton):
            return
        visible = sender.toggle_visibility()
        self.sig_visibility_changed.emit(sender.index(), visible)

    def _set_all(self, visible):
        for btn in self.buttons:
            if btn.is_visible() != visible:
                btn.set_visible_state(visible)
                self.sig_visibility_changed.emit(btn.index(), visible)

    def visibility_mask(self):
        return [btn.is_visible() for btn in self.buttons]
