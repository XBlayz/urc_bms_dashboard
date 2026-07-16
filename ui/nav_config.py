"""Single source of truth for sidebar navigation entries and their screen order."""

from collections import namedtuple

from ui.strings import Strings

NavEntry = namedtuple("NavEntry", ["key", "label", "section_break"])

# section_break=True draws a separator line below this entry.
# Sections per UI_definition.md (1.2): [Metrics] | [Charging, Override] | [Logs] | [Settings]
NAV_ENTRIES = [
    NavEntry("metrics", Strings.NAV_METRICS, True),
    NavEntry("charging", Strings.NAV_CHARGING, False),
    NavEntry("override", Strings.NAV_OVERRIDE, True),
    NavEntry("logs", Strings.NAV_LOGS, True),
    NavEntry("settings", Strings.NAV_SETTINGS, False),
]

DEFAULT_NAV_KEY = NAV_ENTRIES[0].key
