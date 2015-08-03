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

winrustler can be invoked from a command prompt

winrustler can also imported as a library, although I have no idea why you
would want to do that.
'''

import sys
import argparse
import ctypes
import re
from ctypes import wintypes

user32 = ctypes.windll.user32


class WindowCollection(dict):

    def __init__(self):
        dict.__init__(self)

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def cb(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True

            buf = ctypes.create_string_buffer(255)
            user32.GetWindowTextA(hwnd, buf, 255)
            self[hwnd] = buf.value.decode('latin1')
            return True

        user32.EnumWindows(cb, 0)

    def multi_search(self, pat):
        '''
        Case insensitive regex search of window thingy.
        Returns, a dict of hwnd, window title pairs.
        '''
        return dict(filter(
            lambda i: re.search(pat, i[1], re.I) is not None,
            self.items(),
        ))

    def search(self, pat):
        '''
        Like multi_search but will throw an exception if it receives more or
        fewer than one result. And only returns the hwnd.
        '''
        r = self.multi_search(pat)
        if len(r) > 1:
            raise ValueError('Multiple matches found: %s' % r)
        elif not r:
            raise ValueError('No window with matching title found')
        return r.popitem()[0]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('function')

    args = parser.parse_args(sys.argv[1:2])
    module = __import__(args.function)

    args = module.parser.parse_args(sys.argv[2:])
    c = WindowCollection()
    module.run(c, args)
