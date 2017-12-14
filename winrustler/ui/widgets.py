from PyQt5.QtCore import (
        QObject,
        pyqtSignal,
        Qt,
)
from PyQt5.QtGui import (
        QPixmap,
        QIcon,
)
from PyQt5.QtWidgets import (
        qApp,
        QApplication,
        QWidget,
        QSystemTrayIcon,
        QMenu,
        QDialog,
        QMainWindow,
        QMessageBox,
        QAction,
        QSizePolicy,
        QGridLayout,
        QFormLayout,
)

from PyQt5.QtWinExtras import (
        QtWin,
)


class WindowPicker(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class WindowMatch(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MoverWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._layout = QGridLayout(self)
        #self._layout
        self.setLayout(self._layout)
