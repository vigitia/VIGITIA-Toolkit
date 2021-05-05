import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer, QSvgWidget
from PyQt5.QtWidgets import QWidget, QLabel

from VIGITIA_toolkit.core.VIGITIABaseApplication import VIGITIABaseApplication


class DrawingCoach(QSvgWidget, VIGITIABaseApplication):

    marker_one_pos = None
    marker_two_pos = None

    move_image_signal = pyqtSignal(int, int)

    # It needs to receive the rendering manager as an argument
    def __init__(self, rendering_manager):
        super().__init__()  # Init the super class
        self.set_name(self.__class__.__name__)  # Register the application with their name
        self.set_rendering_manager(rendering_manager)  # Register the rendering manager

        self.width = 620
        self.height = 450

        self.move_image_signal.connect(self.move_image)

        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, self.width, self.height)  # Initialize the application dimensions

        # self.setAttribute(Qt.WA_TranslucentBackground)

        svg_img = os.path.join(os.path.dirname(__file__), os.path.join('assets', 'world_map.svg'))

        self.load(svg_img)

    def on_new_token_messages(self, data):
        print(data)
        for token in data:
            if token['component_id'] == 5:
                self.set_rotation(token['angle'])
                self.move_image_signal.emit(token['x_pos'], token['y_pos'])

    def move_image(self, new_x, new_y):
        self.setGeometry(new_x, new_y, self.width, self.height)

