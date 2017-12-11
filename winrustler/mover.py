'''
Moves the given window such that the viewport/client area (stuff
inside the window borders) is shown at the given x, y coords
'''
import argparse
import ctypes
from ctypes import wintypes

import attr

from winrustler.core import register_module, FIELD_HELP
from winrustler.winconsts import *

user32 = ctypes.windll.user32

parser = argparse.ArgumentParser()
parser.add_argument('window', type=str)
parser.add_argument('x', type=int)
parser.add_argument('y', type=int)


def _translate_coords(hwnd, x, y):
    """
    Something about moving the window based on the internal border instead of
    the window border.
    """
    # Grab the window styles
    style = user32.GetWindowLongA(hwnd, GWL_STYLE)
    exstyle = user32.GetWindowLongA(hwnd, GWL_EXSTYLE)

    r = wintypes.RECT(x, y, 0, 0)
    # False assumes the window does not have a menu
    user32.AdjustWindowRectEx(ctypes.pointer(r), style, False, exstyle)
    return r.left, r.top


def run_from_args(collection, args):
    hwnd = collection.search(args.window)
    return MoveWindow(hwnd, args.x, args.y)


@register_module()
@attr.s(frozen=True)
class MoveWindow(object):
    hwnd = attr.ib()
    x = attr.ib()
    y = attr.ib()
    move_viewport = attr.ib(default=True) #metadata={FIELD_HELP: ""})

    def run(self):
        if self.move_viewport:
            x, y = _translate_coords(self.hwnd, self.x, self.y)
        else:
            x, y = self.x, self.y
        user32.SetWindowPos(self.hwnd, 0, x, y, 0, 0, SWP_NOSIZE)
