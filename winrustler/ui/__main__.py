""" hi
"""

import sys
import os.path
import logging
import functools

import attr

from PyQt5.QtCore import (
        QObject,
        pyqtSignal,
        Qt,
        QTimer,
        QSettings,
)
from PyQt5.QtGui import (
        QIcon,
)
from PyQt5.QtWidgets import (
        qApp,
        QApplication,
        QSystemTrayIcon,
        QMenu,
        QDialog,
        QMainWindow,
        QMessageBox,
        QAction,
        QSizePolicy,
)

from winrustler.core import REGISTRY
from winrustler.winapi import WindowDiscovery, get_window_title
from winrustler.ui.winapi import get_window_icon, WinHooker

VERSION = 420
ABOUT_TEXT = """\
<h1>WinRustler</h1>

<p>Version: <b>{VERSION}</b></p>

<p><a href='https://bitbucket.org/sqwishy/winrustler'>bitbucket.org/sqwishy/winrustler</a></p>

<p>Project built with
<a href='https://www.python.org/'>Python 3</a>,
<a href='https://www.riverbankcomputing.com/software/pyqt/intro'>Qt 5</a>,
<a href='https://www.qt.io/'>PyQt5</a>, and
<a href='https://www.emojione.com/emoji/v2'>EmojiOne v2</a>.</p>
""".format(**locals())
RES_DIR = os.path.join(os.path.dirname(__file__), 'res')

logger = logging.getLogger(__name__)


def icon(filename):
    return QIcon(os.path.join(RES_DIR, filename))


def log_exceptions(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            logger.exception("Unhandled exception in %r", fn)
    return inner


@attr.s(frozen=True)
class Suggestion(object):
    search = attr.ib()
    rustle = attr.ib()


class RustlerWindow(QDialog):

    rustle = pyqtSignal(object)

    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("WinRustler")

        from .widgets import WindowSelect, MoveControls#, MatchSelect

        self._select = WindowSelect(self)
        #from PyQt5.QtWidgets import QPushButton
        #self._match_select = QPushButton(icon('1f984.png'), "", self)
        #menu = QMenu(self._match_select)
        #menu.addAction("hi")
        #self._match_select.setMenu(menu)

        #self._match = WindowMatch(self)

        #from PyQt5.QtWidgets import QTabWidget
        #self._window_tab = QTabWidget(self)
        #self._window_tab.addTab(self._select, icon('1f44b.png'), "&Selection")
        #self._window_tab.addTab(self._match, icon('1f50d.png'), "&Match")

        self._move = MoveControls(self)

        from PyQt5.QtWidgets import QTabWidget
        self._function_tab = QTabWidget(self)
        self._function_tab.addTab(self._move, icon('1f4d0.png'), "M&ove")

        from PyQt5.QtWidgets import QDialogButtonBox
        self._bb = QDialogButtonBox(self)
        self._bb.accepted.connect(self.accept)
        self._bb.rejected.connect(self.reject)
        self._bb.clicked.connect(self._on_clicked)

        self._apply = self._bb.addButton(QDialogButtonBox.Apply)
        self._apply_and_close = self._bb.addButton('&Apply && Close', QDialogButtonBox.AcceptRole)
        self._close = self._bb.addButton(QDialogButtonBox.Close)

        #from PyQt5.QtWidgets import QFormLayout
        #self._layout = QFormLayout(self)
        #self._layout.addRow(self._description)
        ##self._layout.addRow("&Window", self._window_select)
        ##self._layout.addRow("&Left", self._x)
        ##self._layout.addRow("&Top", self._y)
        #self._layout.addRow(self._move_viewport)
        #self._layout.addRow(self._bb)
        #self._layout.setSizeConstraint(QFormLayout.SetFixedSize)
        from PyQt5.QtWidgets import QVBoxLayout
        self._layout = QVBoxLayout(self)
        from PyQt5.QtWidgets import QHBoxLayout
        self._select_layout = QHBoxLayout()
        self._select_layout.addWidget(self._select, stretch=1)
        #self._select_layout.addWidget(self._match_select)
        #self._layout.addWidget(self._window_tab)
        self._layout.addLayout(self._select_layout)
        #self._layout.addWidget(self._select)
        #self._layout.addWidget(self._match_select)
        self._layout.addWidget(self._function_tab)
        self._layout.addWidget(self._bb)
        self._layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        #self.setLayout(self._layout)

        self._select.updated.connect(self._refresh_engagement)
        #self._match.updated.connect(self._refresh_engagement)
        self._move.updated.connect(self._refresh_engagement)
        self._refresh_engagement()

    def sync_windows(self, *args):
        self._select.sync_windows(*args)

    def _refresh_engagement(self):
        is_acceptable = self.request() is not None
        self._apply.setEnabled(is_acceptable)
        self._apply_and_close.setEnabled(is_acceptable)

    def _on_clicked(self, button):
        from PyQt5.QtWidgets import QDialogButtonBox
        if button == self._apply:
            self.rustle.emit(self.request())
        elif button == self._apply_and_close:
            self.rustle.emit(self.request())
            self.accept()
        elif button == self._close:
            self.reject()
        else:
            raise NotImplementedError()

    def request(self):
        #hwnd = self._window_tab.currentWidget().hwnd()
        hwnd = self._select.hwnd()
        if hwnd is not None:
            return self._function_tab.currentWidget().window_request(hwnd)

    def showEvent(self, event):
        settings = QSettings("WinRustler Corp.", "WinRustler")
        geometry = settings.value("RustlerWindow/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        return super().showEvent(event)

    def closeEvent(self, event):
        settings = QSettings("WinRustler Corp.", "WinRustler")
        settings.setValue("RustlerWindow/geometry", self.saveGeometry())
        return super().closeEvent(event)


class RustlerTray(QSystemTrayIcon):

    rustle = pyqtSignal(object)

    def __init__(self, app, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.rustle_icon = icon('1f412.png')
        self.about_icon = icon('1f49f.png')
        self.exit_icon = QIcon()

        self.menu = QMenu(parent=None)
        self.separator = self.menu.addSeparator()
        self.rustle_act = self.menu.addAction(self.rustle_icon, '&Rustle...', self.show_window)
        self.about_act = self.menu.addAction(self.about_icon, '&About...', self._about)
        self.exit_act = self.menu.addAction(self.exit_icon, '&Exit', self._exit)

        self.setContextMenu(self.menu)
        self.activated.connect(self._icon_clicky)

        #self.suggest = []
        self.app = app
        self.window = None
        self.setIcon(self.rustle_icon)

    #def add_suggestion(self, suggestion):
    #    #try:
    #    #    replace = next(s for s in self.suggest if s.value())
    #    #except StopIteration:
    #    #    else:
    #    before = self.suggest[-1] if self.suggest else self.separator
    #    icon = get_window_icon(suggestion.rustle.hwnd)
    #    msg = "Move {s.search} to {s.rustle.x}, {s.rustle.y}.".format(s=suggestion)
    #    act = QAction(icon, msg, self.menu)
    #    act.setData(suggestion)
    #    act.triggered.connect(self._do_suggestion)
    #    self.suggest.append(act)
    #    self.menu.insertAction(before, act)
    #    if len(self.suggest) > 2:
    #        self.menu.removeAction(self.suggest.pop(0))

    #def _do_suggestion(self):
    #    suggestion = self.sender().data()
    #    try:
    #        hwnd = next(hwnd for (hwnd, title) in WindowCollection().items() if title == suggestion.search)
    #    except StopIteration:
    #        self.showMessage("Yikes!", "Couldn't find a window matching %r." % suggestion.search)
    #    else:
    #        rustle = attr.evolve(suggestion.rustle, hwnd=hwnd)
    #        self.rustle.emit(rustle)

    def _icon_clicky(self, reason):
        if reason == QSystemTrayIcon.Trigger:  # Left-click
            self.show_window()

    def show_window(self):
        if self.window is None:
            self.window = RustlerWindow(self.app)
            self.window.setAttribute(Qt.WA_DeleteOnClose)
            self.window.rustle.connect(self.rustle)
            self.window.destroyed.connect(self._window_destroyed)
            self.app.tell_windows_and_connect(self.window.sync_windows)
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def show_rustle_message(self, req):
        icon = get_window_icon(req.hwnd)
        title = get_window_title(req.hwnd)
        msg = "Moved {title} to {req.x} x {req.y}.".format(**locals())
        self.showMessage("I moved a window.", msg, icon)

    def _window_destroyed(self, ptr):
        self.window = None

    def _about(self):
        QMessageBox.about(None, "About WinRustler", ABOUT_TEXT)

    def _exit(self):
        qApp.quit()


class SuggestiveRustles(QObject):

    def __init__(self, app, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        #self.app = app
        #app.rustled.connect(
        #suggestion = self.create_rustle_suggestion(rustle, self.suggestions)
        #self.suggested.emit(suggestion)

    def create_rustle_suggestion(self, rustle, suggestions):
        """ Something was rustled, make a suggestion for repeating...
        """
        search = get_window_title(rustle.hwnd)
        return Suggestion(search, rustle)


class WinRustlerApp(QApplication):

    #rustle = pyqtSignal(object)
    rustled = pyqtSignal(object)
    suggested = pyqtSignal(object)
    # Tells you of hwnds that are newly added and removed.
    # For use with something like `SyncToComboBox.sync()`.
    windows_discovered = pyqtSignal(set, set)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.windows = WindowDiscovery(self.windows_discovered.emit)
        self.discovery_timer = QTimer(self, interval=200, singleShot=True)  # refresh debounce
        self.hooker = WinHooker(self)
        # Use a windows event hook to determine when we might want to update
        # the list of windows. Connect it to the debounce timer.
        self.hooker.event.connect(self.discovery_timer.start)
        # When this debounce timer fires, we tell the window discovery to do
        # update its list of windows.
        self.discovery_timer.timeout.connect(self.windows.refresh)

        self.suggesty = SuggestiveRustles(self)

    def tell_windows_and_connect(self, slot):
        slot(app.windows.discovered, set())
        self.windows_discovered.connect(slot)

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


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--show', action='store_true')
    parser.add_argument('qt_args', nargs='*')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        raise Exception("System tray not available.")

    import signal
    #@log_exceptions
    def quit_on_sigint(*args):
        print("CTRL-C handled, quitting...")
        qApp.quit()
    signal.signal(signal.SIGINT, quit_on_sigint)

    qt_args = [sys.argv[0]] + args.qt_args
    app = WinRustlerApp(qt_args, quitOnLastWindowClosed=False)
    app.startTimer(100)  # So the interpreter can handle SIGINT
    tray = RustlerTray(app)
    tray.show()
    tray.rustle.connect(app.do_rustling)
    app.rustled.connect(tray.show_rustle_message)
    #app.suggested.connect(tray.add_suggestion)
    app.setWindowIcon(tray.icon())

    if args.show:
        from .widgets import ComposeMatch
        #m = ComposeMatch()
        #m.show()
        #app.tell_windows_and_connect(m.sync_windows)
        tray.show_window()

    print("Lets go!")
    try:
        app.exec_()
    finally:
        tray.hide()
    print("hey, we exited cleanly!")
