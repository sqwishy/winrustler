import logging

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
        QCheckBox,
        QFormLayout,
        QFormLayout,
        QLabel,
        QSlider,
        QSpinBox,
        QWidget,
)

from winrustler.mover import MoveWindow
from winrustler.fader import FadeWindow
from winrustler.border import BorderWindow


class MoveControls(QWidget):

    updated = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._description = QLabel("<p>Move a window by setting the the top-left \
                of the window some number of pixels away from the top-left of \
                the desktop.</p>", self)
        self._x = QSpinBox(self, value=0, minimum=-2**16, maximum=2**16)
        self._y = QSpinBox(self, value=0, minimum=-2**16, maximum=2**16)
        self._move_viewport = QCheckBox("Set position of &internal viewport rather than the window frame", self)
        self._move_viewport.setCheckState(Qt.Checked)

        self._layout = QFormLayout(self)
        self._layout.addRow(self._description)
        self._layout.addRow("&Left", self._x)
        self._layout.addRow("&Top", self._y)
        self._layout.addRow(self._move_viewport)
        self.setLayout(self._layout)

    def window_request(self, hwnd):
        return MoveWindow(hwnd, self._x.value(), self._y.value(),
                self._move_viewport.checkState() == Qt.Checked)


class FadeControls(QWidget):

    DESCRIPTION_TEMPLATE = "<p>Set a window's opacity to {opacity}. At zero, it \
    is transparent; at 255 it is opaque.</p>"

    updated = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._description = QLabel(parent=self)
        self._opacity = QSlider(Qt.Horizontal, parent=self, minimum=0, maximum=255)#, tickInterval=127, tickPosition=QSlider.TicksBelow)
        # This can't be a kwarg, probably because PyQt applies those in no
        # particular order and this should happen after setting the maximum.
        self._opacity.setValue(255)

        self._layout = QFormLayout(self)
        self._layout.addRow(self._description)
        self._layout.addRow("&Opacity", self._opacity)
        self.setLayout(self._layout)

        self._opacity.valueChanged.connect(self.updated)
        self.updated.connect(self._refresh_engagement)
        self._refresh_engagement()
    
    def _refresh_engagement(self):
        self._description.setText(self.DESCRIPTION_TEMPLATE.format(opacity=self._opacity.value()))

    def window_request(self, hwnd):
        return FadeWindow(hwnd, self._opacity.value())


class BorderControls(QWidget):

    updated = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._description = QLabel("<p>Add or remove a window border.</p>", parent=self)
        self._have = QCheckBox("Add a border, leave unchecked to eliminate it", self)

        self._layout = QFormLayout(self)
        self._layout.addRow(self._description)
        self._layout.addRow(self._have)
        self.setLayout(self._layout)

    def window_request(self, hwnd):
        return BorderWindow(hwnd, have=self._have.checkState()==Qt.Checked)
