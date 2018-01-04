import logging

from PyQt5.QtCore import QSettings

from winrustler.ui.debug import log_exceptions

logger = logging.getLogger(__name__)


@log_exceptions
def save_window_state(window):
    classname = type(window).__name__
    assert classname
    settings = QSettings("WinRustler Corp.", "WinRustler")
    logger.debug("Saving %r", classname + "/geometry")
    settings.setValue(classname + "/geometry", window.saveGeometry())


@log_exceptions
def restore_window_state(window):
    classname = type(window).__name__
    assert classname
    settings = QSettings("WinRustler Corp.", "WinRustler")
    logger.debug("Loading %r", classname + "/geometry")
    geometry = settings.value(classname + "/geometry")
    if geometry is not None:
        window.restoreGeometry(geometry)
