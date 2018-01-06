from winrustler.mover import MoveWindow
from winrustler.fader import FadeWindow
from winrustler.winapi import get_window_title


def rustle_description(rustle):
    title = get_window_title(rustle.hwnd)
    if isinstance(rustle, MoveWindow):
        return "Moved {title} to {rustle.x} x {rustle.y}.".format(**locals())
    elif isinstance(rustle, FadeWindow):
        return "Set {title} opacity to {rustle.opacity}.".format(**locals())
    else:
        return "Did something, not sure what."
