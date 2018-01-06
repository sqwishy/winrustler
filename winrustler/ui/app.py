import logging

from PyQt5.QtCore import (
        QObject,
        pyqtSignal,
        pyqtSlot,
        QTimer,
)
from PyQt5.QtWidgets import QApplication, QMenu

from winrustler.winapi import WindowDiscovery
from winrustler.ui.winapi import WinHooker
from winrustler.ui.history import HistoryFeature


logger = logging.getLogger(__name__)


class WindowSet(QObject):
    """ This is very much like the WindowDiscovery but it has a signal ...
    """

    discovered = pyqtSignal(set, set)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = set()

    def tell_and_connect(self, slot):
        slot(self.data, ())
        self.discovered.connect(slot)

    def sync(self, adds, removes):
        self.data.update(adds)
        self.data.difference_update(removes)
        self.discovered.emit(adds, removes)


class WinRustlerApp(QApplication):

    #rustle = pyqtSignal(object)
    rustled = pyqtSignal(object)
    suggested = pyqtSignal(object)
    # Tells you of hwnds that are newly added and removed.
    # For use with something like `SyncToComboBox.sync()`.
    #windows_discovered = pyqtSignal(set, set)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.winset = WindowSet(self)
        self.windisc = WindowDiscovery(self.winset.sync)
        self.discovery_timer = QTimer(self, interval=200, singleShot=True)  # refresh debounce
        self.hooker = WinHooker(self)
        # Use a windows event hook to determine when we might want to update
        # the list of windows. Connect it to the debounce timer.
        self.hooker.event.connect(self.discovery_timer.start)
        # When this debounce timer fires, we tell the window discovery to do
        # update its list of windows.
        self.discovery_timer.timeout.connect(self.windisc.refresh)

        self.history_menu = QMenu(parent=None)
        self.history_feature = HistoryFeature(self.winset, self.history_menu)
        self.rustled.connect(self.history_feature.update_from_rustle)

    def event(self, e):
        # This is here just so we can go into the interpreter in case SIGINT.
        return super().event(e)

    def do_rustling(self, rustle):
        try:
            rustle.run()
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            logger.exception("Unhandled exception doing %s", rustle)
        else:
            self.rustled.emit(rustle)

