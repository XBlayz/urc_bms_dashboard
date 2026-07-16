from ui.screens.placeholder_screen import PlaceholderScreen
from ui.strings import Strings


class LogsScreen(PlaceholderScreen):
    def __init__(self, parent=None):
        super().__init__(Strings.NAV_LOGS, Strings.MSG_TODO_LOGS, parent)
