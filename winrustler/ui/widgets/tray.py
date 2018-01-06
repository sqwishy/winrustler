from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
        QAction,
        QDialog,
        QMainWindow,
        QMenu,
        QMessageBox,
        QSizePolicy,
        QSystemTrayIcon,
        qApp,
)

from winrustler import __version__
from winrustler.winapi import get_window_title
from winrustler.mover import MoveWindow
from winrustler.fader import FadeWindow
from winrustler.ui import icon
from winrustler.ui.debug import show_exceptions
from winrustler.ui.rustle import rustle_description
from winrustler.ui.winapi import get_window_icon
from winrustler.ui.widgets.rustlerwindow import RustlerWindow

ABOUT_TEXT = """\
<h1>WinRustler</h1>

<p>Version: <b>{__version__}</b></p>

<p><a href='https://bitbucket.org/sqwishy/winrustler'>bitbucket.org/sqwishy/winrustler</a></p>

<p>Project built with
<a href='https://www.python.org/'>Python 3</a>,
<a href='https://www.riverbankcomputing.com/software/pyqt/intro'>Qt 5</a>,
<a href='https://www.qt.io/'>PyQt5</a>, and
<a href='https://www.emojione.com/emoji/v2'>EmojiOne v2</a>.</p>
""".format(**locals())


class RustlerTray(QSystemTrayIcon):

    rustle = pyqtSignal(object)

    def __init__(self, winset, history_feature, *args, **kwargs):
        super().__init__(winset, *args, **kwargs)
        self.rustle_icon = icon('1f412.png')
        self.about_icon = icon('1f49f.png')
        self.alligator_icon = icon('1f40a.png')
        self.exit_icon = QIcon()

        self.menu = QMenu(parent=None)
        self.rustle_act = self.menu.addAction(self.rustle_icon, '&Rustle...', self.show_window)
        self.history_act = self.menu.addAction(self.alligator_icon, '&History')
        self.about_act = self.menu.addAction(self.about_icon, '&About...', self._about)
        self.about_act.setMenuRole(QAction.AboutRole)
        self.exit_act = self.menu.addAction(self.exit_icon, '&Exit', self._exit)
        self.about_act.setMenuRole(QAction.QuitRole)

        self.history_feature = history_feature
        self.history_act.setMenu(self.history_feature.menu)

        self.setContextMenu(self.menu)
        self.activated.connect(self._icon_clicky)

        self.winset = winset
        self.window = None
        self.setIcon(self.rustle_icon)

    def _icon_clicky(self, reason):
        if reason == QSystemTrayIcon.Trigger:  # Left-click
            self.show_window()

    def show_window(self):
        if self.window is None:
            self.window = RustlerWindow(self.winset)
            self.window.rustle.connect(self.rustle)
            self.window.destroyed.connect(self._window_destroyed)
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    @pyqtSlot(object)
    @show_exceptions
    def show_rustle_message(self, req):
        icon = get_window_icon(req.hwnd)
        msg = rustle_description(req)
        self.showMessage("I did something.", msg, icon)

    def _window_destroyed(self, ptr):
        self.window = None

    def _about(self):
        QMessageBox.about(None, "About WinRustler", ABOUT_TEXT)

    def _exit(self):
        qApp.quit()

