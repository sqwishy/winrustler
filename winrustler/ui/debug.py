import functools
import logging
import traceback


from winrustler.ui import show_critical

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
            show_critical("Unhandled exception in %r" % fn,
                          details=traceback.format_exc())
    return inner
