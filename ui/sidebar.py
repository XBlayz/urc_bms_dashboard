from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy, QWidget
from PyQt6.QtCore import Qt

from ui.strings import Strings
from ui.theme import CurrentTheme as Theme

class LEDIndicator(QFrame):
    def __init__(self, color_hex="#444444"):
        super().__init__()
        self.setFixedSize(12, 12)
        self.set_color(color_hex)
        
    def set_color(self, color_hex):
        self.setStyleSheet(Theme.led_indicator(color_hex))

class NavButton(QPushButton):
    def __init__(self, text, is_active=False):
        super().__init__(text)
        self.setFixedHeight(40)
        self.setProperty("active", is_active)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(Theme.nav_button(is_active))

class Sidebar(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #222222; border: none;")
        self.setFixedWidth(260)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Top tiny text
        layout.addSpacing(20)
        
        # Logo placeholder (text based)
        logo_lbl = QLabel(Strings.LOGO_TEXT)
        logo_lbl.setStyleSheet(Theme.logo_label())
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_lbl)
        
        layout.addSpacing(40)
        
        # Buttons
        layout.addWidget(NavButton(Strings.NAV_METRICS, is_active=True))
        layout.addWidget(NavButton(Strings.NAV_CHARGING))
        layout.addWidget(NavButton(Strings.NAV_OVERRIDE))
        layout.addWidget(NavButton(Strings.NAV_LOGS))
        layout.addWidget(NavButton(Strings.NAV_EXPORT))
        
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # State Panel
        state_container = QFrame()
        state_container.setStyleSheet(Theme.state_container())
        state_layout = QVBoxLayout(state_container)
        state_layout.setSpacing(10)
        
        # Status indicators
        states = [
            (Strings.STATE_SDC, "#00FF00"),
            (Strings.STATE_AIR_PLUS, "#00FF00"),
            (Strings.STATE_AIR_MINUS, "#FF0000"),
            (Strings.STATE_PRECHARGE, "#00FF00"),
            (Strings.STATE_M_AIR_PLUS, "#00FF00"),
            (Strings.STATE_M_AIR_MINUS, "#FF0000"),
            (Strings.STATE_M_PRECHARGE, "#00FF00"),
        ]
        
        self.leds = {}
        for state, color in states:
            row = QHBoxLayout()
            row.setContentsMargins(0,0,0,0)
            led = LEDIndicator(color)
            self.leds[state] = led
            lbl = QLabel(state)
            lbl.setStyleSheet("color: #DDDDDD; font-size: 12px;")
            row.addWidget(led)
            row.addWidget(lbl)
            row.addStretch()
            state_layout.addLayout(row)
            
        state_layout.addSpacing(20)
        
        # Big status text
        driving_lbl = QLabel(Strings.STATUS_DRIVING)
        driving_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        driving_lbl.setStyleSheet(Theme.driving_label())
        state_layout.addWidget(driving_lbl)
            
        layout.addWidget(state_container)
