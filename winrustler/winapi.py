import ctypes
import re
from ctypes import wintypes

from winrustler.winconsts import *

user32 = ctypes.windll.user32

    
def get_window_title(hwnd):
    # TODO GetWindowTextLength
    buf = ctypes.create_unicode_buffer(255)
    user32.GetWindowTextW(hwnd, buf, 254)
    return buf.value


import contextlib
@contextlib.contextmanager
def exception_diaper():
    try:
        yield
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        logger.exception("Unhandled exception", fn)
        raise


class WindowDiscovery(object):
    """ Calls `sync` which is a `callable(new_hwnds, removed_hwnds)`
    """

    def __init__(self, sync, show_untitled=False):
        self.show_untitled = show_untitled
        self._discovered = set()
        self.sync = sync

    @classmethod
    def fresh(cls, *args, **kwargs):
        inst = cls(*args, **kwargs)
        inst.refresh()
        return inst

    @classmethod
    def get_current_hwnds(cls, *args, **kwargs):
        """ Returns a set of hwnds for current windows.
        """
        results = set()
        update = lambda new, gone: (results.update(new), results.difference_update(gone))
        cls.fresh(update, *args, **kwargs)
        return results

    @property
    def discovered(self):
        return self._discovered

    def refresh(self):
        seen = set()

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def cb(hwnd, _):
            if user32.IsWindowVisible(hwnd) and (self.show_untitled or get_window_title(hwnd).strip()):
                seen.add(hwnd)
            return True  # I think this means keep enumerating

        if 0 == user32.EnumWindows(cb, 0):
            raise ctypes.WinError()

        new = seen - self._discovered
        gone = self._discovered - seen
        if new or gone:
            self._discovered.difference_update(gone)
            self._discovered.update(new)
            self.sync(new, gone)


def test_window_match(hwnd, pat):
    """ Return (window title, whether it matches the pattern)
    """
    title = get_window_title(hwnd)
    return title, re.search(pat, title, re.I) is not None


def multi_search(hwnds, pat):
    '''
    Generator yielding hwnd, window title pairs for all windows which match
    `pat` as a case insensitive regex.
    '''
    for hwnd in hwnds:
        title = get_window_title(hwnd)
        if re.search(pat, title, re.I) is not None:
            yield hwnd, title


def search(hwnds, pat):
    '''
    Like multi_search but will throw an exception if it receives more or
    fewer than one result. And only returns the hwnd.
    '''
    r = list(multi_search(hwnds, pat))
    if len(r) > 1:
        raise ValueError('Multiple matches found: %s' % r)
    elif not r:
        raise ValueError('No window with matching title found')
    return r[0]


#def test_WindowDiscovery(app):
#    from PyQt5.QtWidgets import QComboBox
#    cb = QComboBox()
#    adapter = Adapter(cb)  # The combobox itself is pretty model enough for us.
#    disc = WindowDiscovery.fresh(adapter.sync)
#    assert cb.count() > 0  # This might fail if you minimize everything
#    disc.refresh()
