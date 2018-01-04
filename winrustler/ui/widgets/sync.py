import logging

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSlot

from winrustler.winapi import get_window_title
from winrustler.ui.winapi import get_window_icon

logger = logging.getLogger(__name__)


class SyncToStandardItemModel(object):

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.added_items = {}

    def __call__(self, adds, removes):
        from PyQt5.QtGui import QStandardItem
        logger.debug("Resyncing %s, adds=%r, removes=%r", self.model, adds, removes)
        try:
            for hwnd in removes:
                item = self.added_items.pop(hwnd)
                row = self.model.indexFromItem(item).row()
                assert [item] == self.model.takeRow(row)
            for hwnd in adds:
                # FIXME CURRENT WINDOW SYNCRONIZIATION STATE MEMES
                item = QStandardItem(get_window_icon(hwnd), get_window_title(hwnd))
                item.setData(hwnd, Qt.UserRole)
                self.model.appendRow(item)
                self.added_items[hwnd] = item
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            logger.exception("Uh oh...")
