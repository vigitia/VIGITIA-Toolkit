import math
import os
import time

from PyQt5.QtCore import QThread, Qt, QPoint
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtGui import QPixmap, QTransform

from apps.VIGITIABaseApplication import VIGITIABaseApplication


class Thread(QThread):

    def __init__(self, widget):
        QThread.__init__(self)
        self.widget = widget

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            TIME_FOR_IMAGE_TO_DISAPPEAR = 2  # sec
            if time.time() - self.widget.last_time_token_seen > TIME_FOR_IMAGE_TO_DISAPPEAR and self.widget.image_visible:
                self.widget.image_visible = False
                self.widget.label.hide()


class ImageWidget(QWidget, VIGITIABaseApplication):

    image_rotation = 0
    last_time_token_seen = 0
    image_visible = False

    def __init__(self, rendering_manager):
        super().__init__()
        self.set_name(self.__class__.__name__)
        self.set_rendering_manager(rendering_manager)
        self.initUI()

        self.myThread = Thread(self)
        self.myThread.start()

    def initUI(self):
        self.setGeometry(0, 0, self.get_width(), self.get_height())
        self.setStyleSheet("background-color: transparent;")

        # How to display an image based on https://pythonspot.com/pyqt5-image/
        self.label = QLabel(self)
        self.label.hide()
        self.label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(os.path.abspath(os.path.join(os.path.dirname(__file__), 'image.jpg')))
        image_diagonal = self.get_diagonal(pixmap.width(), pixmap.height())
        self.label.resize(image_diagonal, image_diagonal)
        self.label.setPixmap(pixmap)

    def get_diagonal(self, width, height):
        diagonal = math.ceil(math.sqrt(width * width + height * height))
        return diagonal

    def on_new_token_messages(self, data):
        # print('Tokens:', data)
        for token in data:
            if token['component_id'] == 40:
                self.last_time_token_seen = time.time()
                self.image_visible = True
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
