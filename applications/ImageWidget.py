
# Based on https://pythonspot.com/pyqt5-image/
import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QIcon, QPixmap

from apps.VIGITIABaseApplication import VIGITIABaseApplication


class ImageWidget(QWidget, VIGITIABaseApplication):

    def __init__(self):
        super().__init__()
        self.x = 300
        self.y = 200
        self.width = 800
        self.height = 600
        self.rotation = 45
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, self.get_width(), self.get_height())

        label = QLabel(self)
        pixmap = QPixmap(os.path.abspath(os.path.join(os.path.dirname(__file__), 'image.jpg')))
        label.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())