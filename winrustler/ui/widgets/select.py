import logging

from PyQt5.QtCore import (
        QObject,
        pyqtSignal,
        Qt,
        QSortFilterProxyModel,
)
from PyQt5.QtWidgets import QWidget, QComboBox, QVBoxLayout
from PyQt5.QtGui import QStandardItemModel

from winrustler.ui.widgets.sync import SyncToStandardItemModel

logger = logging.getLogger(__name__)


class WindowSelect(QWidget):
    """
    Input:
        Call sync_windows() (SyncToStandardItemModel.__call__()) to tell it about the
        hwnds that are going on.

    Output:
        The hwnd() function for the currently selected hwnd.
        Emits updated() when this changes.
    """

    updated = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._select = QComboBox(self)
        self._proxy = QSortFilterProxyModel(self._select)
        self._model = QStandardItemModel(0, 1, self._proxy)
        self._proxy.setSourceModel(self._model)
        self._select.setModel(self._proxy)
        self._select.currentIndexChanged.connect(self.updated)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._select)
        self.setLayout(self._layout)

        self.sync_windows = SyncToStandardItemModel(self._model)

    def hwnd(self):
        return self._select.currentData()
