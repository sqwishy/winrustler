import argparse
import ctypes
from ctypes import wintypes

import attr

from winrustler.core import register_module
from winrustler.winconsts import *

user32 = ctypes.windll.user32

parser = argparse.ArgumentParser()
parser.add_argument('window', type=str)


def from_args(collection, args):
    hwnd = collection.search(args.window)
    return DeborderWindow(hwnd)


@attr.s(frozen=True)
class DeborderWindow(object):
    hwnd = attr.ib()

    def run(self):
        style = user32.GetWindowLongA(self.hwnd, GWL_STYLE)
        style &= ~(WS_SIZEBOX | WS_CAPTION)
        if 0 == user32.SetWindowLongA(self.hwnd, GWL_STYLE, style):
            raise ctypes.WinError()
