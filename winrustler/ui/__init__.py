import os.path

from PyQt5.QtGui import QIcon


RES_DIR = os.path.join(os.path.dirname(__file__), 'res')


def icon(filename):
    return QIcon(os.path.join(RES_DIR, filename))
