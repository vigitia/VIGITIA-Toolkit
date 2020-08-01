
import cv2
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

from apps.vigitia_application import VIGITIAApplication

from gstreamer.VIGITIAVideoStreamReceiver import VIGITIAVideoStreamReceiver


class VideoWidget(QWidget, VIGITIAApplication):
#class VideoWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

        receiver = VIGITIAVideoStreamReceiver()
        receiver.register_subscriber(self)
        receiver.start()

    def initUI(self):
        self.setGeometry(0, 0, self.get_width(), self.get_height())

        self.label = QLabel(self)
        self.label.resize(1280, 720)

    def on_new_frame(self, frame):
        if frame is not None:
            print('New FRAME')
            # https://stackoverflow.com/questions/34232632/convert-python-opencv-image-numpy-array-to-pyqt-qpixmap-image
            height, width, channel = frame.shape
            bytesPerLine = 3 * width
            image = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
            self.label.setPixmap(QPixmap.fromImage(image))

