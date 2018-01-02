import logging
import textwrap

from PyQt5.QtCore import (
        QObject,
        pyqtSignal,
        Qt,
)
from PyQt5.QtGui import (
        QPixmap,
        QIcon,
)
from PyQt5.QtWidgets import (
        qApp,
        QApplication,
        QWidget,
        QSystemTrayIcon,
        QMenu,
        QDialog,
        QMainWindow,
        QMessageBox,
        QAction,
        QSizePolicy,
        QVBoxLayout,
        QGridLayout,
        QFormLayout,
)

from PyQt5.QtWinExtras import (
        QtWin,
)

from winrustler.winapi import get_window_title, test_window_match
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

        from PyQt5.QtWidgets import QComboBox
        from PyQt5.QtGui import QStandardItemModel
        from PyQt5.QtCore import QSortFilterProxyModel
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


#class MatchSelect(QAction):
#
#    def __init__
#    pass


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from PyQt5.QtWidgets import QComboBox, QListView, QLineEdit, QLabel
        from PyQt5.QtGui import QStandardItemModel
        from PyQt5.QtCore import QSortFilterProxyModel

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

        self.sync_windows = SyncToStandardItemModel(self._model)

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


from winrustler.mover import MoveWindow

class MoveControls(QWidget):

    updated = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from PyQt5.QtWidgets import QSpinBox, QCheckBox, QLabel
        self._description = QLabel("<p>Move a window by setting the the top-left \
                of the window some number of pixels away from the top-left of \
                the desktop.</p>", self)
        self._x = QSpinBox(self, value=0, minimum=-2**16, maximum=2**16)
        self._y = QSpinBox(self, value=0, minimum=-2**16, maximum=2**16)
        self._move_viewport = QCheckBox("Set position of &internal viewport rather than the window frame", self)
        self._move_viewport.setCheckState(Qt.Checked)

        from PyQt5.QtWidgets import QFormLayout
        self._layout = QFormLayout(self)
        self._layout.addRow(self._description)
        self._layout.addRow("&Left", self._x)
        self._layout.addRow("&Top", self._y)
        self._layout.addRow(self._move_viewport)
        self.setLayout(self._layout)

    def window_request(self, hwnd):
        return MoveWindow(hwnd, self._x.value(), self._y.value(),
                self._move_viewport.checkState() == Qt.Checked)
