import logging
import pathlib
import platform
import sys

from PyQt5.QtWidgets import qApp, QMenu

from winrustler.ui.app import WinRustlerApp
from winrustler.ui.history import HistoryFeature
from winrustler.ui.widgets.tray import RustlerTray


logger = logging.getLogger(__name__)
is_frozen = getattr(sys, 'frozen', False)
if platform.system() == 'Windows':
    runtime_path = pathlib.Path.home() / "AppData" / "Roaming" / "winrustler"
else:
    runtime_path = None


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-v', help='Verbosity, more of these increases logging.', action='count', default=0)
    parser.add_argument('--show', help='Display rustler window on startup.', action='store_true')
    parser.add_argument('qt_args', nargs='*')
    args = parser.parse_args()
    log_level = {0: logging.WARNING, 1: logging.INFO}.get(args.v, logging.DEBUG)
    logging.basicConfig(level=log_level)
    if is_frozen and runtime_path is not None:
        runtime_path.mkdir(exist_ok=True)
        logfile = str(runtime_path / 'logging.txt')
        logger.info("Logging to %s", logfile)
        handler = logging.FileHandler(logfile)
        logging.getLogger().addHandler(handler)
    logger.info("Logging level set to %s.", log_level)

    if not RustlerTray.isSystemTrayAvailable():
        raise Exception("System tray not available.")

    import signal
    def quit_on_sigint(*args):
        logger.info("CTRL-C handled, quitting...")
        qApp.quit()
    signal.signal(signal.SIGINT, quit_on_sigint)

    qt_args = [sys.argv[0]] + args.qt_args
    app = WinRustlerApp(qt_args, quitOnLastWindowClosed=False)
    app.startTimer(100)  # So the interpreter can handle SIGINT

    history_menu = QMenu(parent=None, toolTipsVisible=True)
    history_feature = HistoryFeature(app.winset, history_menu)
    history_feature.load()
    history_feature.rustle.connect(app.attempt_rustle)

    tray = RustlerTray(app.winset, history_feature)
    tray.show()
    tray.rustle.connect(app.do_rustling)

    app.rustled.connect(tray.show_rustle_message)
    app.rustled.connect(history_feature.update_from_rustle)

    app.setWindowIcon(tray.icon())

    if args.show:
        tray.show_window()

    logger.info("Lets go!")
    try:
        app.exec_()
    finally:
        tray.hide()
    logger.info("hey, we exited cleanly!")


if __name__ == "__main__":
    main()
