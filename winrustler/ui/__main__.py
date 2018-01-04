""" hi
"""

import sys
import os.path
import logging

import attr

from PyQt5.QtCore import (
        QObject,
        pyqtSignal,
        pyqtSlot,
        Qt,
        QTimer,
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
from winrustler.ui.state import save_window_state, restore_window_state

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


@attr.s(frozen=True)
class History(object):
    search = attr.ib()
    rustle = attr.ib()


class RustlerWindow(QDialog):

    rustle = pyqtSignal(object)

    def __init__(self, winset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("WinRustler")

        from .widgets.select import WindowSelect
        from .widgets.rustle import MoveControls, FadeControls

        self._select = WindowSelect(self)
        from PyQt5.QtWidgets import QPushButton
        self._match_select = QPushButton(icon('1f984.png'), "", self, shortcut="Alt+m")
        self._match_select.clicked.connect(self._show_match)

        #from PyQt5.QtWidgets import QTabWidget
        #self._window_tab = QTabWidget(self)
        #self._window_tab.addTab(self._select, icon('1f44b.png'), "&Selection")
        #self._window_tab.addTab(self._match, icon('1f50d.png'), "&Match")

        self._move = MoveControls(self)
        self._fade = FadeControls(self)

        from PyQt5.QtWidgets import QTabWidget
        self._function_tab = QTabWidget(self)
        self._function_tab.addTab(self._move, icon('1f4d0.png'), "M&ove")
        self._function_tab.addTab(self._fade, icon('1f47b.png'), "F&ade")

        from PyQt5.QtWidgets import QDialogButtonBox
        self._bb = QDialogButtonBox(self)
        self._bb.accepted.connect(self.accept)
        self._bb.rejected.connect(self.reject)
        self._bb.clicked.connect(self._bb_on_clicked)

        self._apply = self._bb.addButton(QDialogButtonBox.Apply)
        self._apply_and_close = self._bb.addButton('&Apply && Close', QDialogButtonBox.AcceptRole)
        self._close = self._bb.addButton(QDialogButtonBox.Close)

        from PyQt5.QtWidgets import QVBoxLayout
        self._layout = QVBoxLayout(self)
        from PyQt5.QtWidgets import QHBoxLayout
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

    def _show_match(self):
        #from .widgets import ComposeMatch
        from .widgets.match import MatchDialog
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
        restore_window_state(self)
        return super().showEvent(event)

    def hideEvent(self, event):
        save_window_state(self)
        return super().hideEvent(event)


class RustlerTray(QSystemTrayIcon):

    rustle = pyqtSignal(object)

    def __init__(self, winset, *args, **kwargs):
        super().__init__(winset, *args, **kwargs)
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
        self.winset = winset
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
            self.window = RustlerWindow(self.winset)
            self.window.rustle.connect(self.rustle)
            self.window.destroyed.connect(self._window_destroyed)
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def show_rustle_message(self, req):
        icon = get_window_icon(req.hwnd)
        title = get_window_title(req.hwnd)
        from winrustler.mover import MoveWindow
        from winrustler.fader import FadeWindow
        if isinstance(req, MoveWindow):
            msg = "Moved {title} to {req.x} x {req.y}.".format(**locals())
        elif isinstance(req, FadeWindow):
            msg = "Set {title} opacity to {req.opacity}.".format(**locals())
        else:
            assert False, req
            msg = "Did something, not sure what."
        self.showMessage("I did something.", msg, icon)

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

        self.suggesty = SuggestiveRustles(self)

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
    tray = RustlerTray(app.winset)
    tray.show()
    tray.rustle.connect(app.do_rustling)
    app.rustled.connect(tray.show_rustle_message)
    #app.suggested.connect(tray.add_suggestion)
    app.setWindowIcon(tray.icon())

    if args.show:
        tray.show_window()

    print("Lets go!")
    try:
        app.exec_()
    finally:
        tray.hide()
    print("hey, we exited cleanly!")
