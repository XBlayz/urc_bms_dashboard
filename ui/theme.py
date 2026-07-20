from typing import Optional


class Theme:
    H_SIZE_S = 500
    W_SIZE_S = 1100

    # Heatmap gradient thresholds (min / optimal / max) for cell values.
    VOLTAGE_MIN = 2.5
    VOLTAGE_OPT = 3.6
    VOLTAGE_MAX = 4.2
    TEMP_MIN = 15.0
    TEMP_OPT = 35.0
    TEMP_MAX = 60.0

    @classmethod
    def main_window(cls):
        return "background-color: #121212;"

    @classmethod
    def sidebar(cls):
        return "background-color: #1A1A1A;"

    @classmethod
    def logo_label(cls):
        return """
            color: #E0E0E0;
            font-size: 14px;
            font-weight: 900;
            letter-spacing: 2px;
        """

    @classmethod
    def nav_button(cls, is_active):
        bg_color = "#B22222" if is_active else "#8B1A1A"
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 13px;
                text-align: left;
                padding-left: 15px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #CD2626;
            }}
        """

    @classmethod
    def state_container(cls):
        return "background-color: #2A2A2A; border-radius: 8px; padding: 15px;"

    @classmethod
    def led_indicator(cls, color_hex):
        return f"""
            QFrame {{
                background-color: {color_hex};
                border-radius: 6px;
            }}
        """

    @classmethod
    def driving_label(cls):
        return "color: #FFFFFF; font-weight: bold; font-size: 14px;"

    @classmethod
    def time_series_plot(cls):
        return "background-color: #1A1A1A; border-radius: 12px;"

    @classmethod
    def plot_header(cls):
        return """
            QFrame {
                background-color: #3B3B3B;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }
            QLabel {
                background: transparent;
            }
        """

    @classmethod
    def toggle_button(cls):
        return """
            QPushButton {
                background-color: #2A2A2A;
                color: #777777;
                border-radius: 11px;
                padding: 0 12px;
                font-weight: bold;
                font-size: 10px;
                letter-spacing: 1px;
                border: 1px solid #444444;
            }
            QPushButton:checked {
                background-color: #A3202B;
                color: #FFFFFF;
                border: 1px solid #C02835;
            }
            QPushButton:hover {
                border: 1px solid #666666;
            }
            QPushButton:checked:hover {
                background-color: #CD2626;
            }
        """

    @classmethod
    def simple_button(cls):
        return """
            QPushButton {
                background-color: #777777;
                color: #2A2A2A;
                border-radius: 11px;
                padding: 0 12px;
                font-weight: bold;
                font-size: 10px;
                letter-spacing: 1px;
                border: 1px solid #333333;
            }
            QPushButton:hover {
                border: 1px solid #555555;
            }
        """

    @classmethod
    def plot_title(cls):
        return "color: #FFFFFF; font-weight: bold; font-size: 14px; letter-spacing: 1px;"

    @classmethod
    def stats_label(cls):
        return "color: #DDDDDD; font-size: 12px; font-family: monospace;"

    @classmethod
    def table_view(cls):
        return f"""
            QTableView {{
                background-color: {cls.PG_BG};
                color: #FFFFFF;
                gridline-color: #444444;
                border: none;
                font-family: monospace;
            }}
            QHeaderView::section {{
                background-color: #3B3B3B;
                color: #FFFFFF;
                padding: 4px;
                border: 1px solid #444444;
                font-weight: bold;
            }}
            QTableView::item:selected {{
                background-color: #A3202B;
                color: #FFFFFF;
            }}
            QTableCornerButton::section {{
                background-color: #3B3B3B;
                border: 1px solid #444444;
            }}
        """

    @classmethod
    def selection_panel(cls):
        return """
            QFrame {
                background-color: #2B2B2B;
                border-radius: 8px;
                border: 1px solid #3A3A3A;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """

    @classmethod
    def color_indicator(cls, color_hex=None):
        if color_hex is None:
            color_hex = "#444444"
        return f"background-color: {color_hex}; border-radius: 7px;"

    @classmethod
    def cell_label_empty(cls):
        return "color: #888888; font-weight: bold; font-size: 13px;"

    @classmethod
    def cell_label_active(cls):
        return "color: #FFFFFF; font-weight: bold; font-size: 14px; letter-spacing: 1px;"

    @classmethod
    def time_label(cls):
        return "color: #777777; font-size: 12px; font-family: monospace;"

    @classmethod
    def value_label(cls):
        return "color: #DDDDDD; font-weight: bold; font-size: 16px; font-family: monospace;"

    @classmethod
    def separator(cls):
        return """
            QFrame[frameShape="4"] {
                background-color: #3A3A3A;
                max-height: 1px;
            }
        """

    @classmethod
    def plate(cls):
        return """
            QFrame {
                background-color: #2A2A2A;
                border-radius: 8px;
                border: 1px solid #3A3A3A;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """

    @classmethod
    def plate_title(cls):
        return "color: #AAAAAA; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;"

    @classmethod
    def plate_value(cls):
        return "color: #FFFFFF; font-size: 14px; font-weight: bold; font-family: monospace;"

    @classmethod
    def plate_unit(cls):
        return "color: #888888; font-size: 10px; font-family: monospace;"

    @classmethod
    def connection_panel(cls):
        return """
            QFrame {
                background-color: #2A2A2A;
                border-radius: 8px;
                border: 1px solid #3A3A3A;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """

    @classmethod
    def connection_led_connected(cls):
        return "background-color: #00FF00; border-radius: 6px;"

    @classmethod
    def connection_led_disconnected(cls):
        return "background-color: #FF0000; border-radius: 6px;"

    @classmethod
    def connection_label(cls):
        return "color: #DDDDDD; font-size: 12px; font-weight: bold;"

    @classmethod
    def charging_control(cls):
        return """
            QFrame {
                background-color: #2A2A2A;
                border-radius: 8px;
                border: 1px solid #3A3A3A;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """

    @classmethod
    def line_edit(cls, applied: Optional[bool]=None):
        if applied is None:
            return """
                QLineEdit {
                    background-color: #1A1A1A;
                    color: #FFFFFF;
                    border: 2px dashed #444444;
                    border-radius: 6px;
                    padding: 8px;
                    font-family: monospace;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border: 1px solid #A3202B;
                }
            """
        elif applied:
            return """
                QLineEdit {
                    background-color: #1A1A1A;
                    color: #FFFFFF;
                    border: 1px solid #444444;
                    border-radius: 6px;
                    padding: 8px;
                    font-family: monospace;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border: 1px solid #A3202B;
                }
            """
        else:
            return """
                QLineEdit {
                    background-color: #1A1A1A;
                    color: #FFFFFF;
                    border: 1px solid #B7761A;
                    border-radius: 6px;
                    padding: 8px;
                    font-family: monospace;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border: 1px solid #A3202B;
                }
            """

    @classmethod
    def button_primary(cls):
        return """
            QPushButton {
                background-color: #A3202B;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #CD2626;
            }
            QPushButton:pressed {
                background-color: #8B1A1A;
            }
        """

    @classmethod
    def button_danger(cls):
        return """
            QPushButton {
                background-color: #8B1A1A;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #A3202B;
            }
        """

    @classmethod
    def charging_button(cls, is_active, color_string):
        #TODO: Fix colors
        if color_string == "gray":
            color = "#777777"
            color_darker = "#555555"
        elif color_string == "yellow":
            color = "#BB8800"
            color_darker = "#997700"
        elif color_string == "green":
            color = "#00AA00"
            color_darker = "#008800"
        elif color_string == "red":
            color = "#BB0000"
            color_darker = "#990000"
        elif color_string == "blue":
            color = "#004499"
            color_darker = "#002277"
        else:
            raise ValueError(f"Invalid `color_string` for charging button: {color_string}")

        if is_active:
            mouse_change = f"""
                QPushButton:hover {{
                    background-color: {color_darker};
                }}
                QPushButton:pressed {{
                    background-color: {color};
                }}
            """
        else:
            mouse_change = ""

        return f"""
            QPushButton {{
                background-color: {color};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
            }}
            {mouse_change}
        """

    @classmethod
    def feedback_label(cls, is_success=True):
        color = "#00FF00" if is_success else "#FF4444"
        return f"color: {color}; font-size: 12px; font-weight: bold;"

    # PyQtGraph Colors
    PG_BG = "#2A2A2A"
    PG_GRID_ALPHA = 0.15
    PG_AXIS_PEN = "#555555"
    PG_AXIS_TEXT = "#888888"
    PG_CROSSHAIR = "#888888"

    STATE_COLORS = {
        "STANDBY": "#888888",
        "DRIVING": "#00FF00",
        "CHARGING": "#00AAFF",
        "ERROR": "#FF0000",
        "PRECHARGING": "#FFAA00",
        "PREPARING CHARGING": "#FF8800",
        "INITIALIZING": "#AA00FF",
        "EXITING CHARGING": "#00FFAA",
        "OVERRIDE": "#FF00FF",
        "NONE": "#444444",
    }

    SIGNAL_COLORS = {
        "pack_voltage_pre_air": "#00FF00",
        "pack_voltage_post_air": "#008000",
        "pack_current": "#FFAA00",
        "sop_dischg": "#FF4444",
        "sop_chg": "#00AAFF",
        "soc": "#AA00FF",
        "actuator_air_pos": "#FF4444",
        "actuator_air_neg": "#00AAFF",
        "actuator_pre_charge": "#FFAA00",
        "actuator_sdc": "#00FF00",
    }


CurrentTheme = Theme
