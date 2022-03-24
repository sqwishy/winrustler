import os.path

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox

RES_DIR = os.path.join(os.path.dirname(__file__), 'res')


def icon(filename):
    return QIcon(os.path.join(RES_DIR, filename))


def show_critical(text, *, details=None):
    msg = QMessageBox(icon=QMessageBox.Critical,
                      text=text,
                      parent=None,
                      detailedText=details)
    msg.exec_()
    return msg
