'''
Moves the given window such that the viewport/client area (stuff
inside the window borders) is shown at the given x, y coords
'''

import argparse
import ctypes
from ctypes import wintypes

__all__ = ['parser', 'do']

user32 = ctypes.windll.user32

GWL_STYLE = -16
GWL_EXSTYLE = -20

parser = argparse.ArgumentParser()
parser.add_argument('window', type=str)
parser.add_argument('x', type=int)
parser.add_argument('y', type=int)

def _translate_coords(hwnd, x, y):
    # Grab the window styles
    style = user32.GetWindowLongA(hwnd, GWL_STYLE)
    exstyle = user32.GetWindowLongA(hwnd, GWL_EXSTYLE)

    r = wintypes.RECT(x, y, 0, 0)
    # False assumes the window does not have a menu
    user32.AdjustWindowRectEx(ctypes.pointer(r), style, False, exstyle)
    return r.left, r.top

def run(collection, args):
    hwnd = collection.search(args.window)
    x = args.x
    y = args.y

    SWP_NOSIZE = 0x0001 # Flag to ignore the size params
    x, y = _translate_coords(hwnd, x, y)
    print('Moving "%s" to (%i, %i)' % (collection[hwnd], x, y))
    user32.SetWindowPos(hwnd, 0, x, y, 0, 0, SWP_NOSIZE)
