from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QDialogButtonBox,
        QHBoxLayout,
        QPushButton,
        QTabWidget,
        QVBoxLayout,
)

from winrustler.ui import icon
from winrustler.ui.debug import show_exceptions
from winrustler.ui.widgets.select import WindowSelect
from winrustler.ui.widgets.rustle import MoveControls, FadeControls
from winrustler.ui.widgets.match import MatchDialog
from winrustler.ui.state import save_window_geometry, restore_window_geometry


class RustlerWindow(QDialog):

    rustle = pyqtSignal(object)

    def __init__(self, winset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("WinRustler")

        self._select = WindowSelect(self)
        self._match_select = QPushButton(icon('1f984.png'), "", self, shortcut="Alt+m")
        self._match_select.clicked.connect(self._show_match)

        self._move = MoveControls(self)
        self._fade = FadeControls(self)

        self._function_tab = QTabWidget(self)
        self._function_tab.addTab(self._move, icon('1f4d0.png'), "M&ove")
        self._function_tab.addTab(self._fade, icon('1f47b.png'), "&Fade")

        self._bb = QDialogButtonBox(self)
        self._bb.accepted.connect(self.accept)
        self._bb.rejected.connect(self.reject)
        self._bb.clicked.connect(self._bb_on_clicked)

        self._apply = self._bb.addButton(QDialogButtonBox.Apply)
        self._apply_and_close = self._bb.addButton('&Apply && Close', QDialogButtonBox.AcceptRole)
        self._close = self._bb.addButton(QDialogButtonBox.Close)

        self._layout = QVBoxLayout(self)
        self._select_layout = QHBoxLayout()
        self._select_layout.addWidget(self._select, stretch=1)
        self._select_layout.addWidget(self._match_select)
        self._layout.addLayout(self._select_layout)
        self._layout.addWidget(self._function_tab)
        self._layout.addWidget(self._bb)
        self._layout.setSizeConstraint(QVBoxLayout.SetFixedSize)

        self._select.updated.connect(self._refresh_engagement)
        self._move.updated.connect(self._refresh_engagement)
        self._refresh_engagement()

        self.winset = winset
        self.winset.tell_and_connect(self.sync_windows)

    @pyqtSlot(object, object)
    @show_exceptions
    def sync_windows(self, *args, **kwargs):
        """
        This needs to exist so that it can be a slot and Qt disconnects it
        properly, otherwise PyQt start holding reference to things and fucks
        everything up.
        """
        self._select.sync_windows(*args, **kwargs)

    def _refresh_engagement(self):
        is_acceptable = self.request() is not None
        self._apply.setEnabled(is_acceptable)
        self._apply_and_close.setEnabled(is_acceptable)

    def _bb_on_clicked(self, button):
        if button == self._apply:
            self.rustle.emit(self.request())
        elif button == self._apply_and_close:
            self.rustle.emit(self.request())
            self.accept()
        elif button == self._close:
            self.reject()
        else:
            raise NotImplementedError()

    def _show_match(self):
        m = MatchDialog(self.winset, parent=self)
        #m = ComposeMatch(self.winset)
        #app.tell_windows_and_connect(m.sync_windows)
        print(m.exec_())

    def request(self):
        hwnd = self._select.hwnd
        tab = self._function_tab.currentWidget() 
        if tab is not None:
            hwnd = self._select.hwnd()
            return tab.window_request(hwnd)

    def showEvent(self, event):
        restore_window_geometry(self)
        return super().showEvent(event)

    def hideEvent(self, event):
        save_window_geometry(self)
        return super().hideEvent(event)
