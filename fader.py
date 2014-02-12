import argparse
import ctypes
from ctypes import wintypes

__all__ = ['parser', 'do']

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000

LWA_COLORKEY = 0x1
LWA_ALPHA = 0x2

user32 = ctypes.windll.user32

parser = argparse.ArgumentParser()
parser.add_argument('window', type=str)
parser.add_argument('opacity', type=int, help='Opaque at 255')

def run(collection, args):
    hwnd = collection.search(args.window)

    style = user32.GetWindowLongA(hwnd, GWL_EXSTYLE)
    style |= WS_EX_LAYERED
    if 0 == user32.SetWindowLongA(hwnd, GWL_EXSTYLE, style):
        raise ctypes.WinError()

    if 0 == user32.SetLayeredWindowAttributes(
            hwnd,
            wintypes.RGB(255, 255, 255),
            args.opacity,
            LWA_COLORKEY|LWA_ALPHA,
            ):
        raise ctypes.WinError()
