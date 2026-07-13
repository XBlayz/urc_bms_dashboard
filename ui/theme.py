class Theme:
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
        return """
            #TimeSeriesPlotWidget {
                background-color: #1A1A1A;
                border-radius: 12px;
            }
        """
        
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

    # PyQtGraph Colors
    PG_BG = "#2A2A2A"
    PG_GRID_ALPHA = 0.15
    PG_AXIS_PEN = "#555555"
    PG_AXIS_TEXT = "#888888"
    PG_CROSSHAIR = "#888888"

CurrentTheme = Theme
