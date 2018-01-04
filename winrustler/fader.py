import argparse
import ctypes
from ctypes import wintypes

import attr

from winrustler.core import register_module
from winrustler.winconsts import *

user32 = ctypes.windll.user32


def from_args(collection, args):
    hwnd = collection.search(args.window)
    return FadeWindow(hwnd, args.opacity)


@register_module()
@attr.s(frozen=True)
class FadeWindow(object):
    hwnd = attr.ib()
    opacity = attr.ib()

    @classmethod
    def add_subparser(cls, subparsers):
        parser = subparsers.add_parser('fade')
        parser.add_argument('opacity', type=int, help='Opaque at 255')
        return parser

    def run(self):
        style = user32.GetWindowLongA(self.hwnd, GWL_EXSTYLE)
        if self.opacity >= 255:
            style &= ~WS_EX_LAYERED
        else:
            style |= WS_EX_LAYERED
        if 0 == user32.SetWindowLongA(self.hwnd, GWL_EXSTYLE, style):
            raise ctypes.WinError()
        if self.opacity < 255:
            if 0 == user32.SetLayeredWindowAttributes(
                    self.hwnd,
                    wintypes.RGB(255, 255, 255),
                    self.opacity,
                    LWA_COLORKEY|LWA_ALPHA,
                    ):
                raise ctypes.WinError()
