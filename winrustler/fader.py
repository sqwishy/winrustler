import argparse
import ctypes
from ctypes import wintypes

import attr

from winrustler.core import register_module
from winrustler.winconsts import *

user32 = ctypes.windll.user32

parser = argparse.ArgumentParser()
parser.add_argument('window', type=str)
parser.add_argument('opacity', type=int, help='Opaque at 255')


def from_args(collection, args):
    hwnd = collection.search(args.window)
    return FadeWindow(hwnd, args.opacity)


@attr.s(frozen=True)
class FadeWindow(object):
    hwnd = attr.ib()
    opacity = attr.ib()

    def run(self):
        style = user32.GetWindowLongA(self.hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED
        if 0 == user32.SetWindowLongA(self.hwnd, GWL_EXSTYLE, style):
            raise ctypes.WinError()
        if 0 == user32.SetLayeredWindowAttributes(
                self.hwnd,
                wintypes.RGB(255, 255, 255),
                self.opacity,
                LWA_COLORKEY|LWA_ALPHA,
                ):
            raise ctypes.WinError()
