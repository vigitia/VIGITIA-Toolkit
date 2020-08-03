
# Based on https://pythonspot.com/pyqt5-image/
import os
import sys
from time import sleep

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QIcon, QPixmap

from apps.VIGITIABaseApplication import VIGITIABaseApplication


class Thread(QThread):

    def __init__(self, widget):
        QThread.__init__(self)
        self.widget = widget

    def __del__(self):
        self.wait()

    def run(self):
        for i in range(1000):
            sleep(1)
            self.widget.set_rotation(self.widget.get_rotation() + 1)
            self.widget.set_x(self.widget.get_x() + i)
            #self.widget.set_width(self.widget.get_width() - 25)
            print('Move widget to {}'.format(self.widget.get_x()))


class ImageWidget(QWidget, VIGITIABaseApplication):

    def __init__(self, rendering_manager):
        super().__init__()
        self.set_name(self.__class__.__name__)
        self.set_rendering_manager(rendering_manager)
        self.x = 300
        self.y = 200
        self.width = 800
        self.height = 600
        self.rotation = 45
        self.initUI()

        self.myThread = Thread(self)
        self.myThread.start()

    def initUI(self):
        self.setGeometry(0, 0, self.get_width(), self.get_height())
        self.setStyleSheet("background-color: transparent;")

        label = QLabel(self)
        pixmap = QPixmap(os.path.abspath(os.path.join(os.path.dirname(__file__), 'image.jpg')))
        label.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())