import functools
import logging

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
