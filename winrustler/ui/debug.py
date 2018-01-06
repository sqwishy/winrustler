import functools
import logging
import traceback

from PyQt5.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


def log_exceptions(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            logger.exception("Unhandled exception in %r", fn)
    return inner


def show_exceptions(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            logger.exception("Unhandled exception in %r", fn)
            msg = QMessageBox(
                    icon=QMessageBox.Critical,
                    text="Unhandled exception in %r" % fn,
                    parent=None,
                    detailedText=traceback.format_exc())
            msg.exec_()
    return inner
