import logging

import pytest
import attr

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QMenu, QAction

from winrustler.winapi import get_window_title
from winrustler.winapi import query_one, NoResults, TooManyResults
from winrustler.ui.debug import show_exceptions
from winrustler.ui.state import program_settings, Serialization
from winrustler.ui.winapi import get_window_icon

logger = logging.getLogger(__name__)

HISTORY_LENGTH = 10


@attr.s(frozen=True, cmp=False)
class PastRustle(object):
    window_icon = attr.ib()
    window_title = attr.ib()
    #process_path = attr.ib()
    rustle = attr.ib()

    def __hash__(self):
        return hash((self.window_title, self.rustle))

    def __eq__(self, other):  # Match
        return self.rustle == other.rustle \
                and self.window_title == other.window_title
                #and self.process_path == other.process_path

    def save(self):
        return attr.asdict(self)

    @classmethod
    def restore(cls, data):
        #data['rustle'] = 
        return cls(**data)


from winrustler.fader import FadeWindow
from winrustler.mover import MoveWindow
serialization = Serialization()
serialization.know(FadeWindow, 'fade')
serialization.know(MoveWindow, 'move')
serialization.know(PastRustle, 'past')


class HistoryFeature(QObject):
    rustle = pyqtSignal(object, object)

    def __init__(self, winset, menu, *args, **kwargs):
        super().__init__(menu, *args, **kwargs)
        self.winset = winset
        self.menu = menu
        self.separator = self.menu.addSeparator()
        self.menu.addAction("&Clear", self.clear_and_save)
        self.data = []
        self.actions = {}  # Maps data to actions?
        self.winset.tell_and_connect(self._refresh_engagement)

    @pyqtSlot(object, object)
    @show_exceptions
    def _refresh_engagement(self, new, old):
        for past in self.data:
            act = self.actions[past]
            try:
                hwnd = query_one(self.winset.hwnds, past.window_title)
            except NoResults as e:
                act.setToolTip("No matching windows found.")
                act.setEnabled(False)
            except TooManyResult as es:
                act.setToolTip("Multiple matching windows found.")
                act.setEnabled(False)
            else:
                #act.setIcon(get_window_icon(hwnd)) # hrm...
                act.setEnabled(True)

    def save(self):
        settings = program_settings()
        logger.debug("Saving history.")
        settings.setValue("history", serialization.savable(self.data))

    def load(self):
        settings = program_settings()
        logger.debug("Loading history.")
        for past in serialization.restored(settings.value("history", [])):
            self.extend_history(past)

    @pyqtSlot()
    @show_exceptions
    def clear_and_save(self):
        self.clear()
        self.save()

    def clear(self):
        while self.data:
            self.menu.removeAction(self.actions.pop(self.data.pop()))

    @pyqtSlot(object)
    @show_exceptions
    def update_from_rustle(self, rustle):
        icon = get_window_icon(rustle.hwnd)
        title = get_window_title(rustle.hwnd)
        rustle = attr.evolve(rustle, hwnd=None)
        past = PastRustle(window_icon=icon, window_title=title, rustle=rustle)
        self.extend_history(past)
        self.save()

    def extend_history(self, past):
        """ Inserts at the "beginning" of the menu, should be the most recent.
        """
        logger.debug("Extending %r into history.", past)

        if self.data:
            before = self.actions[self.data[0]]
        else:
            before = self.separator

        if past in self.data:
            act = self.actions[past]
            if act != before:
                self.data.remove(past)
                self.data.insert(0, past)
                self.menu.removeAction(act)
                self.menu.insertAction(before, act)
        else:
            self.data.insert(0, past)
            text = "{} - {}".format(past.window_title, past.rustle.summarized())
            act = QAction(past.window_icon, text, parent=self.menu)
            act.triggered.connect(self._activate_past)
            act.setData(past)
            self.menu.insertAction(before, act)
            self.actions[past] = act

            while len(self.data) > HISTORY_LENGTH:
                extranious = self.actions.pop(self.data.pop())
                self.menu.removeAction(extranious)

        return act

    @pyqtSlot()
    @show_exceptions
    def _activate_past(self):
        act = self.sender()
        past = act.data()
        self.rustle.emit(past.window_title, past.rustle)


@pytest.fixture
def app():
    from PyQt5.QtWidgets import QApplication
    return QApplication([])


def test_save(app):
    from winrustler.mover import MoveWindow
    from winrustler.ui import icon
    window_icon = icon('1f412.png')
    rustle = MoveWindow(hwnd=None, x=1, y=2)
    past = PastRustle(window_icon=window_icon, window_title="foobar", rustle=rustle)
    settings = program_settings("-test")
    settings.setValue("past", serialization.savable(past))

    loaded_past = serialization.restored(settings.value("past"))
    # The icons won't be equal, comparing them is hard...
    assert past.rustle == loaded_past.rustle


def test(app):
    from winrustler.mover import MoveWindow
    from winrustler.ui.app import WindowSet
    from PyQt5.QtGui import QIcon

    winset = WindowSet()
    menu = QMenu()
    history = HistoryFeature(winset, menu)
    assert len(menu.actions()) == 2
    assert menu.actions()[0] == history.separator

    # First second past item
    first_rustle = MoveWindow(hwnd=None, x=1, y=2)
    first_past = PastRustle(window_icon=QIcon(), window_title="foobar", rustle=first_rustle)
    first_act = history.extend_history(first_past)
    assert len(menu.actions()) == 3
    assert history.data == [first_past]
    assert menu.actions()[:-2] == [first_act]

    # Add second past item
    second_rustle = MoveWindow(hwnd=None, x=1, y=2)
    second_past = PastRustle(window_icon=QIcon(), window_title="foobar2", rustle=second_rustle)
    second_act = history.extend_history(second_past)
    assert len(menu.actions()) == 4
    assert history.data == [second_past, first_past]
    assert menu.actions()[:-2] == [second_act, first_act]

    # Update first past item
    third_rustle = MoveWindow(hwnd=None, x=1, y=2)
    third_past = PastRustle(window_icon=QIcon(), window_title="foobar", rustle=third_rustle)
    third_act = history.extend_history(third_past)
    assert len(menu.actions()) == 4
    assert first_act == third_act
    assert history.data == [third_past, second_past]
    assert menu.actions()[:-2] == [third_act, second_act]
