import logging

import pytest
import attr

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QMenu, QAction

from winrustler.winapi import get_window_title
from winrustler.ui.debug import show_exceptions
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


class HistoryFeature(QObject):

    def __init__(self, winset, menu, *args, **kwargs):
        super().__init__(menu, *args, **kwargs)
        self.winset = winset
        self.menu = menu
        self.separator = self.menu.addSeparator()
        self.menu.addAction("&Clear")
        self.data = []
        self.actions = {}  # Maps data to actions?
        self.winset.tell_and_connect(self._update_engagement)

    @pyqtSlot(object, object)
    @show_exceptions
    def _update_engagement(self, new, lost):
        #new
        pass

    @pyqtSlot(object)
    @show_exceptions
    def update_from_rustle(self, rustle):
        icon = get_window_icon(rustle.hwnd)
        title = get_window_title(rustle.hwnd)
        rustle = attr.evolve(rustle, hwnd=None)
        past = PastRustle(window_icon=icon, window_title=title, rustle=rustle)
        self.extend_history(past)

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
            act = QAction(past.window_icon, past.window_title, parent=self.menu)
            act.triggered.connect(self._activate_past)
            self.menu.insertAction(before, act)
            self.actions[past] = act

            while len(self.data) > HISTORY_LENGTH:
                extranious = self.actions.remove(self.data.pop())
                self.menu.removeAction(extranious)

        logger.debug("data=%r", self.data)
        logger.debug("actions=%r", self.actions)

        return act

    @pyqtSlot()
    @show_exceptions
    def _activate_past(self):
        act = self.sender()
        print(act)


@pytest.fixture
def app():
    from PyQt5.QtWidgets import QApplication
    return QApplication([])


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
