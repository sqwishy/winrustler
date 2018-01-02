import argparse
import ctypes
from ctypes import wintypes

import attr

from winrustler.core import register_module
from winrustler.winconsts import *

user32 = ctypes.windll.user32

def from_args(collection, args):
    hwnd = collection.search(args.window)
    return DeborderWindow(hwnd)


@register_module()
@attr.s(frozen=True)
class DeborderWindow(object):
    hwnd = attr.ib()

    @classmethod
    def add_subparser(cls, subparsers):
        parser = subparsers.add_parser('deborder')
        return parser

    def run(self):
        style = user32.GetWindowLongA(self.hwnd, GWL_STYLE)
        style &= ~(WS_SIZEBOX | WS_CAPTION)
        if 0 == user32.SetWindowLongA(self.hwnd, GWL_STYLE, style):
            raise ctypes.WinError()
