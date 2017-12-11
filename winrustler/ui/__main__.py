import sys
import os.path
import logging
import functools

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
        QSystemTrayIcon,
        QMenu,
        QDialog,
        QMainWindow,
        QMessageBox,
)

from PyQt5.QtWinExtras import (
        QtWin,
)

from winrustler.core import REGISTRY
from winrustler.windows import WindowCollection
from winrustler.mover import MoveWindow

VERSION = 420
ABOUT_TEXT = """\
<h1>WinRustler</h1>

<p>Version: <b>{VERSION}</b></p>

<p><a href='https://bitbucket.org/sqwishy/winrustler'>bitbucket.org/sqwishy/winrustler</a></p>

<p>Project built with
<a href='https://www.python.org/'>Python 3 </a>,
<a href='https://www.riverbankcomputing.com/software/pyqt/intro'>Qt 5</a>,
<a href='https://www.qt.io/'>PyQt5</a>, and
<a href='https://www.emojione.com/emoji/v2'>EmojiOne v2</a>.</p>
""".format(**locals())
RES_DIR = os.path.join(os.path.dirname(__file__), 'res')

logger = logging.getLogger(__name__)


def log_exceptions(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            logger.exception("Unhandled exception in %r", fn)
            raise
    return inner


from winrustler.winconsts import WM_GETICON, ICON_SMALL, ICON_BIG, GW_OWNER, GCL_HICON, GCL_HICONSM
import ctypes
user32 = ctypes.windll.user32


def get_hicons(hwnd):
    return (user32.SendMessageW(hwnd, WM_GETICON, ICON_SMALL, 0) or user32.GetClassLongW(hwnd, GCL_HICONSM),
            user32.SendMessageW(hwnd, WM_GETICON, ICON_BIG, 0) or user32.GetClassLongW(hwnd, GCL_HICON))


def get_window_icon(hwnd):
    """ Try a bunch of different thigns to get the icon...
    """
    icon = QIcon()
    small, big = get_hicons(hwnd)
    if small:
        icon.addPixmap(QtWin.fromHICON(small))
    if big:
        icon.addPixmap(QtWin.fromHICON(big))
    if icon.isNull():
        phwnd = user32.GetWindow(hwnd, GW_OWNER)
        if phwnd:
            icon = get_window_icon(phwnd)
    return icon


class RustlerWindow(QDialog):

    rustle = pyqtSignal(object)

    def __init__(self, wc, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("WinRustler")

        from PyQt5.QtWidgets import QComboBox
        self._window_select = QComboBox(self)
        for hwnd, title in wc.items():
            if not title.strip():
                continue
            icon = get_window_icon(hwnd)
            self._window_select.addItem(icon, title, hwnd)

        from PyQt5.QtWidgets import QSpinBox, QCheckBox, QLabel
        self._description = QLabel("<p>Move a window by setting the the top-left \
                of the window some number of pixels away from the top-left of \
                the desktop.</p>", self)
        self._x = QSpinBox(self, value=0, minimum=-2**16, maximum=2**16)
        self._y = QSpinBox(self, value=0, minimum=-2**16, maximum=2**16)
        self._move_viewport = QCheckBox("Set position of &internal viewport", self)
        self._move_viewport.setCheckState(Qt.Checked)

        from PyQt5.QtWidgets import QDialogButtonBox
        self._bb = QDialogButtonBox(self)
        self._bb.accepted.connect(self.accept)
        self._bb.rejected.connect(self.reject)
        self._bb.clicked.connect(self._on_clicked)

        self._apply = self._bb.addButton(QDialogButtonBox.Apply)
        self._apply_and_close = self._bb.addButton('&Apply && Close', QDialogButtonBox.AcceptRole)
        self._close = self._bb.addButton(QDialogButtonBox.Close)

        from PyQt5.QtWidgets import QFormLayout
        self._layout = QFormLayout(self)
        self._layout.addRow(self._description)
        self._layout.addRow("&Window", self._window_select)
        self._layout.addRow("&Left", self._x)
        self._layout.addRow("&Top", self._y)
        self._layout.addRow(self._move_viewport)
        self._layout.addRow(self._bb)
        self.setLayout(self._layout)

    def _on_clicked(self, button):
        from PyQt5.QtWidgets import QDialogButtonBox
        if button == self._apply:
            self.rustle.emit(self.request)
        elif button == self._apply_and_close:
            self.rustle.emit(self.request)
            self.accept()
        elif button == self._close:
            self.reject()
        else:
            raise NotImplementedError()

    @property
    def request(self):
        hwnd = self._window_select.currentData()
        return MoveWindow(hwnd, self._x.value(), self._y.value(),
                self._move_viewport.checkState() == Qt.Checked)


class RustlerTray(QSystemTrayIcon):

    rustle = pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rustle_icon = QIcon(os.path.join(RES_DIR, '1f412.png'))
        self.about_icon = QIcon(os.path.join(RES_DIR, '1f49f.png'))
        self.exit_icon = QIcon()

        self.menu = QMenu(parent=None)
        self.menu.addSeparator()
        self.menu.addAction(self.rustle_icon, '&Rustle...', self.show_window)
        self.menu.addAction(self.about_icon, '&About...', self._about)
        self.menu.addAction(self.exit_icon, '&Exit', self._exit)

        self.setContextMenu(self.menu)
        self.activated.connect(self._icon_clicky)

        self.window = None
        self.setIcon(self.rustle_icon)

    def _icon_clicky(self, reason):
        if reason == QSystemTrayIcon.Trigger:  # Left-click
            self.show_window()

    def show_window(self):
        if self.window is None:
            wc = WindowCollection()
            self.window = RustlerWindow(wc)
            self.window.setAttribute(Qt.WA_DeleteOnClose)
            self.window.rustle.connect(self.rustle)
            self.window.destroyed.connect(self._window_destroyed)
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def show_rustle_message(self, req):
        msg = "Moved {req.hwnd} to {req.x} x {req.y}.".format(**locals())
        self.showMessage("Hello world", msg)

    def _window_destroyed(self, ptr):
        self.window = None

    def _about(self):
        QMessageBox.about(None, "About WinRustler", ABOUT_TEXT)

    def _exit(self):
        qApp.quit()


class WinRustlerApp(QApplication):

    #rustle = pyqtSignal(object)
    rustled = pyqtSignal(object)

    def event(self, e):
        # This is here just so we can go into the interpreter in case SIGINT.
        return super().event(e)

    def do_rustling(self, req):
        try:
            req.run()
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            logger.exception("Unhandled exception moving %s", wc[hwnd])
        else:
            self.rustled.emit(req)


if __name__ == "__main__":
    if not QSystemTrayIcon.isSystemTrayAvailable():
        raise Exception("System tray not available.")

    import signal
    @log_exceptions
    def quit_on_sigint(*args):
        qApp.quit()
    signal.signal(signal.SIGINT, quit_on_sigint)

    app = WinRustlerApp(sys.argv, quitOnLastWindowClosed=False)
    app.startTimer(100)  # So the interpreter can handle SIGINT
    tray = RustlerTray(app)
    tray.show()
    tray.rustle.connect(app.do_rustling)
    app.rustled.connect(tray.show_rustle_message)
    app.setWindowIcon(tray.icon())

    #tray.show_window()

    print("Lets go!")
    try:
        app.exec_()
    finally:
        tray.hide()
