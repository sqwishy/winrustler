import sys
import logging

from PyQt5.QtWidgets import qApp

from winrustler.ui.app import WinRustlerApp
from winrustler.ui.widgets.tray import RustlerTray


logger = logging.getLogger(__name__)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-v', help='Verbosity, more of these increases logging.', action='count', default=0)
    parser.add_argument('--show', help='Display rustler window on startu..', action='store_true')
    parser.add_argument('qt_args', nargs='*')
    args = parser.parse_args()
    log_level = {0: logging.WARNING, 1: logging.INFO}.get(args.v, logging.DEBUG)
    logging.basicConfig(level=log_level)
    logger.info("Logging level set to %s.", log_level)

    if not RustlerTray.isSystemTrayAvailable():
        raise Exception("System tray not available.")

    import signal
    def quit_on_sigint(*args):
        print("CTRL-C handled, quitting...")
        qApp.quit()
    signal.signal(signal.SIGINT, quit_on_sigint)

    qt_args = [sys.argv[0]] + args.qt_args
    app = WinRustlerApp(qt_args, quitOnLastWindowClosed=False)
    app.startTimer(100)  # So the interpreter can handle SIGINT
    tray = RustlerTray(app.winset, app.history_feature)
    tray.show()
    tray.rustle.connect(app.do_rustling)
    app.rustled.connect(tray.show_rustle_message)
    app.setWindowIcon(tray.icon())

    if args.show:
        tray.show_window()

    print("Lets go!")
    try:
        app.exec_()
    finally:
        tray.hide()
    print("hey, we exited cleanly!")


if __name__ == "__main__":
    main()
