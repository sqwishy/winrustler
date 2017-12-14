import ctypes
from ctypes import wintypes

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWinExtras import QtWin

from winrustler.winconsts import (WM_GETICON, ICON_SMALL, ICON_BIG, GW_OWNER,
        GCL_HICON, GCL_HICONSM)

user32 = ctypes.windll.user32


def get_hicons(hwnd):
    return (user32.SendMessageW(hwnd, WM_GETICON, ICON_SMALL, 0) or user32.GetClassLongW(hwnd, GCL_HICONSM),
            user32.SendMessageW(hwnd, WM_GETICON, ICON_BIG, 0) or user32.GetClassLongW(hwnd, GCL_HICON))


def get_window_icon(hwnd):
    """ Try a bunch of different thigns to get the icon...
    """
    icon = QIcon()
    small, big = get_hicons(hwnd)
    if small:
        icon.addPixmap(QtWin.fromHICON(small))
    if big:
        icon.addPixmap(QtWin.fromHICON(big))
    if icon.isNull():
        phwnd = user32.GetWindow(hwnd, GW_OWNER)
        if phwnd:
            icon = get_window_icon(phwnd)
    return icon


class WinHooker(QObject):

    event = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        @ctypes.WINFUNCTYPE(wintypes.HANDLE, wintypes.DWORD, wintypes.HWND, wintypes.LONG, wintypes.LONG, wintypes.DWORD, wintypes.DWORD)
        def wineventproc(something, event, hwnd, no, body, cares):
            self.event.emit()

        self.wineventproc = wineventproc

        EVENT_SYSTEM_FOREGROUND = 0x3
        self.hook = user32.SetWinEventHook(EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND, 0, self.wineventproc, 0, 0, 0)
        if 0 == self.hook:
            raise ctypes.WinError()

    def __del__(self):
        if not user32.UnhookWinEvent(self.hook):
            raise ctypes.WinError()
