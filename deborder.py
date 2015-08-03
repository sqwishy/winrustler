
import argparse
import ctypes
from ctypes import wintypes

GWL_STYLE = -16
WS_EX_LAYERED = 0x00080000

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms632600%28v=vs.85%29.aspx
WS_SIZEBOX = 0x00040000
WS_CAPTION = 0x00C00000

user32 = ctypes.windll.user32

parser = argparse.ArgumentParser()
parser.add_argument('window', type=str)

def run(collection, args):
    hwnd = collection.search(args.window)

    style = user32.GetWindowLongA(hwnd, GWL_STYLE)
    style &= ~(WS_SIZEBOX | WS_CAPTION)
    if 0 == user32.SetWindowLongA(hwnd, GWL_STYLE, style):
        raise ctypes.WinError()

__all__ = [parser, run]
