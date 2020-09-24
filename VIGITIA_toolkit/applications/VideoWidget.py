
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtGui import QImage, QPixmap

from VIGITIA_toolkit.core.VIGITIABaseApplication import VIGITIABaseApplication


class VideoWidget(QWidget, VIGITIABaseApplication):
    """ Example application to display a video

    """

    is_hidden = True

    def __init__(self, rendering_manager):
        super().__init__()
        self.set_name(self.__class__.__name__)
        self.set_rendering_manager(rendering_manager)

        self.x = 1000
        self.y = 300
        self.width = self.get_screen_resolution()[0]/2
        self.height = self.get_screen_resolution()[1]/2
        self.rotation = 30
        self.z_index = 50

        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, self.get_width(), self.get_height())
        self.setStyleSheet("background-color: transparent;")

        self.label = QLabel(self)
        self.label.resize(self.get_width(), self.get_height())

        self.hide()

    def on_new_video_frame(self, frame, name, origin_ip, port):
        available_video_streams = self.data_interface.get_available_video_streams()
        # print(available_video_streams)

        if name == 'Intel Realsense D435 RGB table' and frame is not None:
            image = self.opencv_imge_to_pyqt_image(frame)
            self.label.setPixmap(QPixmap.fromImage(image))

    def on_new_control_messages(self, data):

        # Show/hide video
        if data[2] == 2 and data[3] == 1:
            self.is_hidden = not self.is_hidden

        if self.is_hidden:
            self.hide()
        else:
            self.show()

    def opencv_imge_to_pyqt_image(self, image):
        # https://stackoverflow.com/questions/34232632/convert-python-opencv-image-numpy-array-to-pyqt-qpixmap-image
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        qt_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()

        return qt_image

    def resizeEvent(self, event):
        print("resize")


