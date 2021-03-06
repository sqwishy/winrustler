import logging

import attr

from PyQt5.QtCore import (
        QObject,
        pyqtSignal,
        pyqtSlot,
        QTimer,
)
from PyQt5.QtWidgets import QApplication, QMessageBox

from winrustler.winapi import WindowDiscovery, query_one, NoResults, TooManyResults
from winrustler.ui import show_critical
from winrustler.ui.winapi import WinHooker
from winrustler.ui.debug import show_exceptions

logger = logging.getLogger(__name__)


class WindowSet(QObject):
    """ This is very much like the WindowDiscovery but it has a signal ...
    """
    discovered = pyqtSignal(set, set)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hwnds = set()

    def tell_and_connect(self, slot):
        slot(self.hwnds, ())
        self.discovered.connect(slot)

    def sync(self, adds, removes):
        self.hwnds.update(adds)
        self.hwnds.difference_update(removes)
        self.discovered.emit(adds, removes)


class WinRustlerApp(QApplication):
    rustled = pyqtSignal(object)
    suggested = pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.winset = WindowSet(self)
        self.windisc = WindowDiscovery(self.winset.sync)
        self.discovery_timer = QTimer(self, interval=200, singleShot=True)  # refresh debounce
        self.hooker = WinHooker(self)
        # Some goofy meme because we get window events after the QObject is
        # deleted but not the python object.
        self.aboutToQuit.connect(self.hooker._unhook)
        # Use a windows event hook to determine when we might want to update
        # the list of windows. Connect it to the debounce timer.
        self.hooker.winevent.connect(self.discovery_timer.start)
        # When this debounce timer fires, we tell the window discovery to do
        # update its list of windows.
        self.discovery_timer.timeout.connect(self.windisc.refresh)

    def event(self, e):
        # This is here just so we can go into the interpreter in case SIGINT.
        return super().event(e)

    @pyqtSlot(object)
    @show_exceptions
    def do_rustling(self, rustle):
        rustle.run()
        self.rustled.emit(rustle)

    @pyqtSlot(str, object)
    @show_exceptions
    def attempt_rustle(self, window_title, rustle):
        try:
            hwnd = query_one(self.winset.hwnds, window_title)
        except NoResults as e:
            show_critical("No windows found named \"%s\"." % window_title)
        except TooManyResults as es:
            show_critical("Multiple windows named \"%s\". Couldn't decide which to use." % window_title)
        else:
            rustle = attr.evolve(rustle, hwnd=hwnd)
            self.do_rustling(rustle)
