from ui.screens.placeholder_screen import PlaceholderScreen
from ui.strings import Strings


class SettingsScreen(PlaceholderScreen):
    def __init__(self, parent=None):
        super().__init__(Strings.NAV_SETTINGS, Strings.MSG_TODO_SETTINGS, parent)
