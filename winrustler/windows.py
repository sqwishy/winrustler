import ctypes
import re
from ctypes import wintypes

from winrustler.winconsts import *

user32 = ctypes.windll.user32


class WindowCollection(dict):

    def __init__(self):
        dict.__init__(self)
        self.refresh()

    def refresh(self):
        self.clear()

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def cb(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True

            # TODO GetWindowTextLength
            buf = ctypes.create_unicode_buffer(255)
            user32.GetWindowTextW(hwnd, buf, 254)
            self[hwnd] = buf.value
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
