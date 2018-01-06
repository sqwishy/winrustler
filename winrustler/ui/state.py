import logging

from PyQt5.QtCore import QSettings

from winrustler.ui.debug import log_exceptions

logger = logging.getLogger(__name__)


def program_settings(suffix=""):
    return QSettings("WinRustler Corp.", "WinRustler" + suffix)


import attr
from attr.exceptions import NotAnAttrsClassError

IDENT_KEY = "__typename__"

@attr.s()
class Serialization():
    """
    Some crap for transforming attr classes into data types that can be
    stored and restored into QSettings without PyQt5 being a dick and trying to
    use pickling...
    """

    _cls_idents = attr.ib(default=attr.Factory(dict))
    _ident_clss = attr.ib(default=attr.Factory(dict))

    def know(self, cls, ident):
        self._cls_idents[cls] = ident
        self._ident_clss[ident] = cls

    def savable(self, obj):
        if isinstance(obj, list):
            return list(map(self.savable, obj))
        elif isinstance(obj, tuple):
            return tuple(map(self.savable, obj))
        elif isinstance(obj, object):
            try:
                data = attr.asdict(obj, recurse=False)
            except NotAnAttrsClassError:
                return obj
            else:
                for cls, ident in self._cls_idents.items():
                    if type(obj) == cls:
                        for key, value in data.items():
                            data[key] = self.savable(value)
                        data[IDENT_KEY] = ident
                        return data
                else:
                    raise NotImplementedError("Not sure what to do with %s?" % type(obj))
        else:
            return obj  # Assume savable?

    def restored(self, data):
        if isinstance(data, list):
            return list(map(self.restored, data))
        elif isinstance(data, tuple):
            return tuple(map(self.restored, data))
        elif isinstance(data, dict):
            for key, value in data.items():
                data[key] = self.restored(value)
            if IDENT_KEY in data:
                ctor = self._ident_clss[data.pop(IDENT_KEY)]
                data = ctor(**data)
                return data
            else:
                return data
        else:
            return data


@log_exceptions
def save_window_geometry(window):
    classname = type(window).__name__
    assert classname
    settings = program_settings()
    logger.debug("Saving %r", classname + "/geometry")
    settings.setValue(classname + "/geometry", window.saveGeometry())


@log_exceptions
def restore_window_geometry(window):
    classname = type(window).__name__
    assert classname
    settings = program_settings()
    logger.debug("Loading %r", classname + "/geometry")
    geometry = settings.value(classname + "/geometry")
    if geometry is not None:
        window.restoreGeometry(geometry)
