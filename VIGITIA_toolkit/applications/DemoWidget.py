import datetime
import math
import os
import time
from datetime import datetime

from PyQt5 import uic
from PyQt5.QtCore import QThread, Qt, QPoint
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt5.QtGui import QPixmap, QTransform

from VIGITIA_toolkit.core.VIGITIABaseApplication import VIGITIABaseApplication


class DemoWidget(QWidget, VIGITIABaseApplication):

    def __init__(self, rendering_manager):
        super().__init__()
        self.set_name(self.__class__.__name__)
        self.set_rendering_manager(rendering_manager)

        self.z_index = 2
        self.width = 1000
        self.height = 800

        self.x = 1000
        self.y = 1000

        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, self.width, self.height)
        self.setStyleSheet("background-color: transparent;")
        # self.setStyleSheet("background-color: transparent; border: 3px solid #FF0000")

        #self.layout = QHBoxLayout()

        # Load the smartphone widget component
        #self.smartphone_widget = Smartphone(self, 0, 0, self.width, self.height)
        #self.smartphone_widget.show()

        #self.layout.addWidget(self.smartphone_widget)

        # How to display an image based on https://pythonspot.com/pyqt5-image/
        self.label = QLabel(self)
        self.label.show()
        self.label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(os.path.abspath(os.path.join(os.path.dirname(__file__), 'image.jpg')))
        self.label.setPixmap(pixmap)
        self.label.resize(self.width, self.height)



    def on_key_pressed(self, event):
        if event.key() == Qt.Key_F1:
            self.set_rotation(self.rotation - 1)

    def on_new_token_messages(self, data):
        # print('Tokens:', data)
        for token in data:
            if token['component_id'] == 4:
                pass
                #self.set_rotation(token['angle'])
                #self.set_x(token['x_pos'])
                #self.set_y(token['y_pos'])


class Smartphone(QWidget):

    # Pass its parent and coordinates on init
    def __init__(self, parent, x, y, width, height):
        super(Smartphone, self).__init__(parent)

        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.initUI()

        # Init a new thread for a constant update of the current time
        self.thread = TimeUpdaterThread(self)
        self.thread.start()

    def initUI(self):
        self.setGeometry(self.x, self.y, self.width, self.height)
        # Load the UI file
        uic.loadUi(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Smartphone.ui')), self)

        self.label_time = self.findChild(QLabel, 'time')

    # Call this function to update the displayed time
    def set_time(self):
        now = datetime.now()
        time_string = now.strftime('%H:%M:%S')
        self.label_time.setText(time_string)


# This thread updates the displayed clock in the smartphone widget
class TimeUpdaterThread(QThread):

    def __init__(self, smartphone):
        QThread.__init__(self)
        self.smartphone = smartphone

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            self.smartphone.set_time()
            time.sleep(0.1)