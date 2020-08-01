
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtGui import QImage, QPixmap

from apps.VIGITIABaseApplication import VIGITIABaseApplication

from pyQT5_experiments.VIGITIASensorDataInterface import VIGITIASensorDataInterface


class VideoWidget(QWidget, VIGITIABaseApplication):
    def __init__(self):
        super().__init__()

        self.x = 1000
        self.y = 300
        self.width = 1280
        self.height = 720
        self.rotation = 150

        self.initUI()

        data_interface = VIGITIASensorDataInterface.Instance()
        data_interface.register_subscriber(self)

    def initUI(self):
        self.setGeometry(0, 0, self.get_width(), self.get_height())

        self.label = QLabel(self)
        self.label.resize(self.get_width(), self.get_height())

    def on_new_video_frame(self, frame, name):
        if frame is not None:
            # print('New FRAME:', name)
            image = self.opencv_imge_to_pyqt_image(frame)
            self.label.setPixmap(QPixmap.fromImage(image))

    def opencv_imge_to_pyqt_image(self, image):
        # https://stackoverflow.com/questions/34232632/convert-python-opencv-image-numpy-array-to-pyqt-qpixmap-image
        height, width, channel = image.shape
        bytesPerLine = 3 * width
        qt_image = QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()

        return qt_image

    def resizeEvent(self, event):
        print("resize")


