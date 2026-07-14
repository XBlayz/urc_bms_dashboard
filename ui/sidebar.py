from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.strings import Strings
from ui.theme import CurrentTheme as Theme
from ui.widgets.plates import (
    EnumStatePlate, UnitPlate, ActuatorStatePlate,
    StatSummaryPlate, TimePlate
)


class LEDIndicator(QFrame):
    def __init__(self, color_hex="#444444"):
        super().__init__()
        self.setFixedSize(6, 6)
        self.set_color(color_hex)

    def set_color(self, color_hex):
        self.setStyleSheet(Theme.led_indicator(color_hex))


class NavButton(QPushButton):
    clicked_with_key = pyqtSignal(str)

    def __init__(self, text, screen_key, is_active=False):
        super().__init__(text)
        self.screen_key = screen_key
        self.setFixedHeight(32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(Theme.nav_button(is_active))
        self.clicked.connect(lambda: self.clicked_with_key.emit(self.screen_key))


class Sidebar(QFrame):
    nav_clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #222222; border: none;")
        self.setMinimumWidth(240)
        self.setMaximumWidth(340)
        self.nav_buttons = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        # Logo
        logo_lbl = QLabel(Strings.LOGO_TEXT)
        logo_lbl.setStyleSheet("color: #E0E0E0; font-size: 12px; font-weight: 900; letter-spacing: 1px;")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setWordWrap(True)
        logo_lbl.setMaximumHeight(70)
        layout.addWidget(logo_lbl)

        layout.addSpacing(10)

        # Navigation buttons with separators
        nav_items = [
            (Strings.NAV_METRICS, "metrics", True, True),
            (Strings.NAV_CHARGING, "charging", False, False),
            (Strings.NAV_OVERRIDE, "override", False, True),
            (Strings.NAV_LOGS, "logs", False, True),
            (Strings.NAV_EXPORT, "export", False, False),
        ]

        nav_layout = QVBoxLayout()
        for (text, key, active, line) in nav_items:
            btn = NavButton(text, key, is_active=active)
            btn.clicked_with_key.connect(self.on_nav_clicked)
            self.nav_buttons[key] = btn
            nav_layout.addWidget(btn)

            if line:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setFixedHeight(1)
                sep.setStyleSheet("background-color: #3A3A3A; border: none;")
                nav_layout.addWidget(sep)
        layout.addLayout(nav_layout)

        layout.addSpacing(10)

        # State panel - no container frame, no scroll
        state_layout = QVBoxLayout()
        state_layout.setSpacing(3)

        # Grid for paired metrics
        grid = QVBoxLayout()
        grid.setSpacing(2)

        # Row: Pack V pre | Pack V post
        row1 = QHBoxLayout()
        row1.setSpacing(2)
        self.pack_voltage_plate = UnitPlate(Strings.LBL_PACK_VOLTAGE, unit="V")
        self.pack_voltage_plate.setMaximumHeight(50)
        row1.addWidget(self.pack_voltage_plate, stretch=1)
        self.pack_voltage_post_air_plate = UnitPlate(Strings.LBL_PACK_VOLTAGE_POST_AIR, unit="V")
        self.pack_voltage_post_air_plate.setMaximumHeight(50)
        row1.addWidget(self.pack_voltage_post_air_plate, stretch=1)
        grid.addLayout(row1)

        # Row: Pack I | SoC
        row2 = QHBoxLayout()
        row2.setSpacing(2)
        self.pack_current_plate = UnitPlate(Strings.LBL_PACK_CURRENT, unit="A")
        self.pack_current_plate.setMaximumHeight(50)
        row2.addWidget(self.pack_current_plate, stretch=1)
        self.soc_plate = UnitPlate(Strings.LBL_SOC, unit="%")
        self.soc_plate.setMaximumHeight(50)
        row2.addWidget(self.soc_plate, stretch=1)
        grid.addLayout(row2)

        # Row: SOP disch | SOP chg
        row3 = QHBoxLayout()
        row3.setSpacing(2)
        self.sop_dischg_plate = UnitPlate(Strings.LBL_SOP_DISCHG, unit="W")
        self.sop_dischg_plate.setMaximumHeight(50)
        row3.addWidget(self.sop_dischg_plate, stretch=1)
        self.sop_chg_plate = UnitPlate(Strings.LBL_SOP_CHG, unit="W")
        self.sop_chg_plate.setMaximumHeight(50)
        row3.addWidget(self.sop_chg_plate, stretch=1)
        grid.addLayout(row3)

        state_layout.addLayout(grid)

        # Stats: Volt | Temp side by side
        stats_row = QHBoxLayout()
        stats_row.setSpacing(2)
        self.voltage_stats_plate = StatSummaryPlate(Strings.LBL_VOLT_STATS, unit="V")
        self.voltage_stats_plate.setMaximumHeight(80)
        stats_row.addWidget(self.voltage_stats_plate, stretch=1)
        self.temp_stats_plate = StatSummaryPlate(Strings.LBL_TEMP_STATS, unit="°C")
        self.temp_stats_plate.setMaximumHeight(80)
        stats_row.addWidget(self.temp_stats_plate, stretch=1)
        state_layout.addLayout(stats_row)

        # Actuators: 2x2 grid
        actuators_row = QHBoxLayout()
        actuators_row.setSpacing(2)
        actuator_col1 = QVBoxLayout()
        actuator_col1.setSpacing(2)
        actuator_col2 = QVBoxLayout()
        actuator_col2.setSpacing(2)

        actuator_rows = [
            (Strings.STATE_AIR_PLUS, "air_pos", True, "#00FF00"),
            (Strings.STATE_PRECHARGE, "pre_charge", True, "#00FF00"),
        ]
        self.actuator_plates = {}
        for label, field, default, color in actuator_rows:
            plate = ActuatorStatePlate(label, value=default, true_color=color, false_color="#444444")
            plate.setMaximumHeight(45)
            self.actuator_plates[field] = plate
            actuator_col1.addWidget(plate)

        actuator_rows2 = [
            (Strings.STATE_AIR_MINUS, "air_neg", True, "#FF4444"),
            (Strings.STATE_SDC, "sdc", True, "#00FF00"),
        ]
        for label, field, default, color in actuator_rows2:
            plate = ActuatorStatePlate(label, value=default, true_color=color, false_color="#444444")
            plate.setMaximumHeight(45)
            self.actuator_plates[field] = plate
            actuator_col2.addWidget(plate)

        actuators_row.addLayout(actuator_col1, stretch=1)
        actuators_row.addLayout(actuator_col2, stretch=1)
        state_layout.addLayout(actuators_row)

        # FSM state plate (penultimo)
        self.fsm_plate = EnumStatePlate(
            Strings.LBL_FSM_STATE,
            {
                0: Strings.STATE_STANDBY,
                1: Strings.STATE_DRIVING,
                2: Strings.STATE_CHARGING,
                3: Strings.STATE_ERROR,
                4: Strings.STATE_PRECHARGING,
                5: Strings.STATE_PREPARING_CHARGING,
                6: Strings.STATE_INITIALIZING,
                7: Strings.STATE_EXITING_CHARGING,
                8: Strings.STATE_OVERRIDE,
                10: Strings.STATE_NONE,
            },
            value_key="state"
        )
        self.fsm_plate.setMaximumHeight(55)
        state_layout.addWidget(self.fsm_plate)

        # Uptime plate (ultimo)
        self.uptime_plate = TimePlate(Strings.LBL_UPTIME)
        self.uptime_plate.setMaximumHeight(50)
        state_layout.addWidget(self.uptime_plate)

        layout.addLayout(state_layout, stretch=1)

        # Connection status panel
        conn_panel = QFrame()
        conn_panel.setStyleSheet(Theme.connection_panel())
        conn_panel.setMaximumHeight(30)
        conn_layout = QHBoxLayout(conn_panel)
        conn_layout.setContentsMargins(4, 2, 4, 2)
        conn_layout.setSpacing(3)

        self.conn_led = LEDIndicator("#444444")
        conn_layout.addWidget(self.conn_led)

        self.conn_lbl = QLabel(Strings.LBL_DISCONNECTED)
        self.conn_lbl.setStyleSheet("color: #DDDDDD; font-size: 9px; font-weight: bold;")
        conn_layout.addWidget(self.conn_lbl)

        conn_layout.addStretch()
        layout.addWidget(conn_panel)

    def on_nav_clicked(self, key):
        self.nav_clicked.emit(key)
        for k, btn in self.nav_buttons.items():
            btn.setStyleSheet(Theme.nav_button(k == key))

    def update_connection_status(self, connected, is_mock=False):
        if connected:
            self.conn_led.setStyleSheet(Theme.connection_led_connected())
            self.conn_lbl.setText(Strings.LBL_CONNECTED if not is_mock else Strings.LBL_MOCK_MODE)
        else:
            self.conn_led.setStyleSheet(Theme.connection_led_disconnected())
            self.conn_lbl.setText(Strings.LBL_DISCONNECTED)
