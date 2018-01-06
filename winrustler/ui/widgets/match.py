import logging
import textwrap

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QSortFilterProxyModel
from PyQt5.QtWidgets import QWidget, QComboBox, QListView, QLineEdit, QLabel
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout
from PyQt5.QtGui import QStandardItemModel

from winrustler.winapi import test_window_match
from winrustler.ui.widgets.sync import SyncToStandardItemModel
from winrustler.ui.state import save_window_geometry, restore_window_geometry

logger = logging.getLogger(__name__)


class ComposeMatch(QWidget):
    """
    Input:
        Call sync_windows() (SyncToStandardItemModel.__call__()) to tell it about the
        hwnds that are going on.

    Output:
        The filter property will be a the user filter as a string.
        Emits updated() when this changes.
    """

    updated = pyqtSignal()

    def __init__(self, winset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.winset = winset

        help_text = textwrap.dedent("""\
                <p>Filter on the window title. The filter is a case insensitive
                <a href='https://docs.python.org/3/library/re.html'>regular
                expression</a>.</p>
                """)
        self._help = QLabel(help_text, self, openExternalLinks=True)
        self._filter = QLineEdit(self, placeholderText="Filter...")
        self._list = QListView(self)

        self._proxy = QSortFilterProxyModel(self._list)
        self._model = QStandardItemModel(0, 1, self._proxy)
        self._proxy.setSourceModel(self._model)
        self._list.setModel(self._proxy)

        self._filter.textEdited.connect(self._refilter)
        self._filter.textEdited.connect(self.updated)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._help)
        self._layout.addWidget(self._filter)
        self._layout.addWidget(self._list)
        self.setLayout(self._layout)

        self._sync = SyncToStandardItemModel(self._model)
        self.winset.tell_and_connect(self.sync_windows)

    @pyqtSlot(object, object)
    def sync_windows(self, *args, **kwargs):  # Because slots and reference counting
        self._sync(*args, **kwargs)

    def _refilter(self, pattern):
        items = [self._model.item(row) for row in range(self._model.rowCount())]
        #hwnds = [item.data(role=Qt.UserRole) for item in items]
        for item in items:
            title, test = test_window_match(item.data(role=Qt.UserRole), pattern)
            item.setText(title)  # In case it changed??
            item.setEnabled(test)

    @property
    def filter(self):
        return self._filter.text()


class MatchDialog(QDialog):

    def __init__(self, winset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("Window Match")

        self._match = ComposeMatch(winset, parent=self)

        self._bb = QDialogButtonBox(self)
        self._bb.accepted.connect(self.accept)
        self._bb.rejected.connect(self.reject)
        #self._bb.clicked.connect(self._bb_on_clicked)

        self._apply = self._bb.addButton(QDialogButtonBox.Apply)
        #self._apply_and_close = self._bb.addButton('&Apply && Close', QDialogButtonBox.AcceptRole)
        self._close = self._bb.addButton(QDialogButtonBox.Close)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self._match)
        self._layout.addWidget(self._bb)

    def showEvent(self, event):
        restore_window_geometry(self)
        return super().showEvent(event)

    def hideEvent(self, event):
        save_window_geometry(self)
        return super().hideEvent(event)

