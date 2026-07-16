from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel

from ui.strings import Strings
from ui.theme import CurrentTheme as Theme

class SelectionPanel(QFrame):
    def __init__(self, empty_text=Strings.EMPTY_CELL):
        super().__init__()
        self.empty_text = empty_text
        self.setStyleSheet(Theme.selection_panel())
        self.setFixedHeight(50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(20)

        # Color indicator dot
        self.color_indicator = QFrame()
        self.color_indicator.setFixedSize(14, 14)
        self.color_indicator.setStyleSheet(Theme.color_indicator())
        layout.addWidget(self.color_indicator)

        self.cell_lbl = QLabel(self.empty_text)
        self.cell_lbl.setStyleSheet(Theme.cell_label_empty())
        layout.addWidget(self.cell_lbl)

        layout.addStretch()

        self.time_lbl = QLabel(Strings.EMPTY_TIME)
        self.time_lbl.setStyleSheet(Theme.time_label())
        layout.addWidget(self.time_lbl)

        self.value_lbl = QLabel(Strings.EMPTY_VALUE)
        self.value_lbl.setStyleSheet(Theme.value_label())
        layout.addWidget(self.value_lbl)

    def update_selection(self, label_text, time_val, value, unit, color_hex):
        if not label_text:
            self.color_indicator.setStyleSheet(Theme.color_indicator())
            self.cell_lbl.setText(self.empty_text)
            self.cell_lbl.setStyleSheet(Theme.cell_label_empty())
            self.time_lbl.setText(Strings.EMPTY_TIME)
            self.value_lbl.setText(Strings.EMPTY_VALUE)
        else:
            self.color_indicator.setStyleSheet(Theme.color_indicator(color_hex))
            self.cell_lbl.setText(label_text)
            self.cell_lbl.setStyleSheet(Theme.cell_label_active())
            self.time_lbl.setText(Strings.FMT_TIME.format(time=time_val))
            if isinstance(value, str):
                self.value_lbl.setText(value)
            else:
                self.value_lbl.setText(Strings.FMT_VALUE.format(value=value, unit=unit))
