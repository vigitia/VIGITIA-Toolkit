
# Based on https://pythonspot.com/pyqt5-image/
import math
import os
import sys
from time import sleep

from PyQt5.QtCore import QThread, Qt, QPoint
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QIcon, QPixmap, QTransform

from apps.VIGITIABaseApplication import VIGITIABaseApplication


class Thread(QThread):

    def __init__(self, widget):
        QThread.__init__(self)
        self.widget = widget

    def __del__(self):
        self.wait()

    def run(self):
        pass
        # for i in range(1000):
        #     sleep(1)
        #     self.widget.set_rotation(self.widget.get_rotation() + 1)
        #     self.widget.set_x(self.widget.get_x() + i)
        #     #self.widget.set_width(self.widget.get_width() - 25)
        #     print('Move widget to {}'.format(self.widget.get_x()))


class ImageWidget(QWidget, VIGITIABaseApplication):

    image_rotation = 0

    def __init__(self, rendering_manager):
        super().__init__()
        self.set_name(self.__class__.__name__)
        self.set_rendering_manager(rendering_manager)
        # self.set_position(1000, 500)
        # self.set_dimensions(800, 600)
        # self.set_rotation(45)
        self.initUI()

        self.myThread = Thread(self)
        self.myThread.start()

    def initUI(self):
        self.setGeometry(0, 0, self.get_width(), self.get_height())
        self.setStyleSheet("background-color: transparent;")

        self.label = QLabel(self)
        self.label.hide()
        #self.label.resize(self.get_width(), self.get_height())
        self.label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(os.path.abspath(os.path.join(os.path.dirname(__file__), 'image.jpg')))
        image_diagonal = self.get_diagonal(pixmap.width(), pixmap.height())
        self.label.resize(image_diagonal, image_diagonal)
        self.label.setPixmap(pixmap)

        # self.resize(pixmap.width(), pixmap.height())

    def get_diagonal(self, width, height):
        diagonal = math.ceil(math.sqrt(width * width + height * height))
        return diagonal

    def on_new_token_messages(self, data):
        # print('Tokens:', data)
        for token in data:
            if token['component_id'] == 40:
                self.label.show()
                token_angle = token['angle']
                if self.image_rotation not in range(token_angle - 1, token_angle + 1):
                    # Based on https://stackoverflow.com/questions/31892557/rotating-a-pixmap-in-pyqt4-gives-undesired-translation
                    pixmap = QPixmap(os.path.abspath(os.path.join(os.path.dirname(__file__), 'image.jpg')))
                    transform = QTransform().rotate(token_angle)
                    self.image_rotation = token_angle
                    pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)


                    self.label.setPixmap(pixmap)

                global_pos = QPoint(int(token['x_pos'] / 1280 * 2560), int(token['y_pos'] / 720 * 1440))
                local_pos = self.mapFromGlobal(global_pos)

                try:
                    self.label.move(local_pos.x() - self.label.width()/2, local_pos.y() - self.label.height()/2 + 500)
                except Exception as e:
                    print(e)

            if token['component_id'] != 40:
                self.label.hide()

