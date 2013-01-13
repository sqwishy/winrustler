# Copyright 2013 Sqwishy Trick. All rights reserved.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

''' winrustler is a python script that facilitates moving windows on MS Windows
winrustler can be invoked from a command prompt in three different manners.

winrustler.py [title [x y]]
 Without title, winrustler enters interactive mode and prompts for a selection
  from a list of window. The input there can be an index or a substring of one
  of the window titles (case insensitive comparison).
 If title is given, it will select a window by its title as previously
  described and move it to x, y which default to 0, 0

winrustler can also imported as a library, although I have no idea why you
 would want to do that.
'''

import sys
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32


class WindowMover(object):
    ''' Finds windows and lets you move them
    '''
    def __init__(self):
        self._windows = {}

    @property
    def windows(self):
        return self._windows

    def fetch_windows(self):
        self._windows.clear()

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def cb(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True

            buf = ctypes.create_string_buffer(255)
            user32.GetWindowTextA(hwnd, buf, 255)
            self._windows[hwnd] = buf.value
            return True

        user32.EnumWindows(cb, 0)

    def search_window(self, match):
        ''' Case insensitive search of window thingy
        '''
        match = match.lower()
        for hwnd, title in self._windows.iteritems():
            if match in title.lower():
                return hwnd
        raise ValueError('No window with matching title found')

    def _translate_coords(self, hwnd, x, y):
        # Grab the window styles
        GWL_STYLE = -16
        GWL_EXSTYLE = -20
        style = user32.GetWindowLongA(hwnd, GWL_STYLE)
        exstyle = user32.GetWindowLongA(hwnd, GWL_EXSTYLE)

        r = wintypes.RECT(x, y, 0, 0)
        # False assumes the window does not have a menu
        user32.AdjustWindowRectEx(ctypes.pointer(r), style, False, exstyle)
        return r.left, r.top

    def move_window(self, hwnd, x, y):
        ''' Moves the given window such that the viewport/client area (stuff
        inside the window borders) is shown at the given x, y coords
        '''
        SWP_NOSIZE = 0x0001 # Flag to ignore the size params
        x, y = self._translate_coords(hwnd, x, y)
        print 'Moving "%s" to (%i, %i)' % (self._windows[hwnd], x, y)
        user32.SetWindowPos(hwnd, 0, x, y, 0, 0, SWP_NOSIZE)


def main_interactive(m):
    for e, (win, title) in enumerate(m.windows.iteritems()):
        print str(e).rjust(3), ':', title

    wnd = None
    while wnd == None:
        match = raw_input('> ')

        if not match:
            print 'Nope...'
            continue

        # Allow lookup either by index or by search string
        try:
            idx = int(match)
        except ValueError:
            wnd = m.search_window(match)
        else:
            try:
                wnd = m.windows.keys()[idx]
            except IndexError:
                print 'Out of range...'
                continue

    m.move_window(wnd, 0, 0)


if __name__ == '__main__':
    argc = len(sys.argv)

    m = WindowMover()
    m.fetch_windows()

    if argc == 1:
        main_interactive(m)
    elif argc >= 2:
        if argc == 2:
            x = y = 0
        elif argc == 4:
            x = int(sys.argv[2])
            y = int(sys.argv[3])
        else:
            print 'Improper usage...'
            sys.exit(1)
        m.move_window(m.search_window(sys.argv[1]), x, y)
