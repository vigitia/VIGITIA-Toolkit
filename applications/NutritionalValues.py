import os

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

from apps.VIGITIABaseApplication import VIGITIABaseApplication


# A toolkit applications needs to be a valid PyQt application. It also needs to inherit from VIGITIABaseApplication
class NutritionalValues(QWidget, VIGITIABaseApplication):
    """ Example of how an application should look like

    """

    # It needs to receive the rendering manager as an argument
    def __init__(self, rendering_manager):
        super().__init__()  # Init the super class
        self.set_name(self.__class__.__name__)  # Register the application with their name
        self.set_rendering_manager(rendering_manager)  # Register the rendering manager

        # If you want to change the resolution, position or rotation of the application, define it here

        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, self.get_width(), self.get_height())  # Initialize the application dimensions

        # Make the background transparent to allow stacking of applications
        self.setStyleSheet("background-color: red;")

        self.nutri_score = NutriScore(self, 500, 600)
        self.nutri_score2 = NutriScore(self, 800, 200)
        #nutri_score.setAlignment(Qt.AlignCenter)

        # window_layout = QVBoxLayout()
        # window_layout.addWidget(nutri_score, Qt.AlignCenter)
        # window_layout
        # self.setLayout(window_layout)

    def on_new_token_messages(self, data):
        # print('Tokens:', data)
        for token in data:
            if token['component_id'] == 40:
                print('Found Token 40')


class NutriScore(QWidget):
    def __init__(self, parent, x, y):
        super(NutriScore, self).__init__(parent)
        self.setGeometry(x, y, 600, 200)
        uic.loadUi(os.path.abspath(os.path.join(os.path.dirname(__file__), 'NutriScore.ui')), self)