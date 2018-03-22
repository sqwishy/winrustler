import argparse
import ctypes
from ctypes import wintypes

import attr

from winrustler.core import register_module
from winrustler.winconsts import *

user32 = ctypes.windll.user32

def from_args(collection, args):
    hwnd = collection.search(args.window)
    return BorderWindow(hwnd)


@register_module()
@attr.s(frozen=True)
class BorderWindow(object):
    hwnd = attr.ib()
    have = attr.ib(default=False)

    @classmethod
    def add_subparser(cls, subparsers):
        parser = subparsers.add_parser('border')
        parser.add_argument('--remove', action='store_false', dest='have')
        return parser

    def run(self):
        style = user32.GetWindowLongA(self.hwnd, GWL_STYLE)
        if self.have:
            style |= (WS_SIZEBOX | WS_CAPTION)
        else:
            style &= ~(WS_SIZEBOX | WS_CAPTION)
        if 0 == user32.SetWindowLongA(self.hwnd, GWL_STYLE, style):
            raise ctypes.WinError()

    def summarized(self):
        what = "Add" if self.have else "Remove"
        return "{} window border".format(what)
