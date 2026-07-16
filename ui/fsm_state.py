"""Single source of truth for FSM state labels and colors.

Replaces the FSM enum_map dict that used to be duplicated verbatim in
sidebar.py, metrics_screen.py and charging_screen.py.
"""

from data.proto import messages_pb2
from ui.strings import Strings
from ui.theme import CurrentTheme as Theme

_STATE_LABELS = {
    messages_pb2.SYSTEM_STATE_STANDBY: Strings.STATE_STANDBY,
    messages_pb2.SYSTEM_STATE_DRIVING: Strings.STATE_DRIVING,
    messages_pb2.SYSTEM_STATE_CHARGING: Strings.STATE_CHARGING,
    messages_pb2.SYSTEM_STATE_ERROR: Strings.STATE_ERROR,
    messages_pb2.SYSTEM_STATE_PRECHARGING: Strings.STATE_PRECHARGING,
    messages_pb2.SYSTEM_STATE_PREPARING_CHARGING: Strings.STATE_PREPARING_CHARGING,
    messages_pb2.SYSTEM_STATE_INITIALIZING: Strings.STATE_INITIALIZING,
    messages_pb2.SYSTEM_STATE_EXITING_CHARGING: Strings.STATE_EXITING_CHARGING,
    messages_pb2.SYSTEM_STATE_OVERRIDE: Strings.STATE_OVERRIDE,
    messages_pb2.SYSTEM_STATE_NONE: Strings.STATE_NONE,
}


def fsm_state_labels():
    """Returns a fresh {enum_value: label} dict; safe for callers to mutate."""
    return dict(_STATE_LABELS)


def fsm_state_color(label):
    return Theme.STATE_COLORS.get(label, "#444444")
