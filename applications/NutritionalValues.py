import os
import time

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from apps.VIGITIABaseApplication import VIGITIABaseApplication

class NutritionalValues(QWidget, VIGITIABaseApplication):
    """ NutritionalValues

    """

    present_tokens = []

    # It needs to receive the rendering manager as an argument
    def __init__(self, rendering_manager):
        super().__init__()  # Init the super class
        self.set_name(self.__class__.__name__)  # Register the application with their name
        self.set_rendering_manager(rendering_manager)  # Register the rendering manager

        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, self.get_width(), self.get_height())  # Initialize the application dimensions
        self.setStyleSheet("background-color: transparent;")

        self.nutri_score = NutriScore(self, 500, 600)

    def add_widget(self):
        self.moveToThread(self.rendering_manager)
        NutriScore(self, 100, 100)

    def on_new_token_messages(self, data):
        # print('Tokens:', data)
        for token in data:
            if token['component_id'] == 36:
                if token['component_id'] not in self.present_tokens:
                    print('Found Token 36')

                    self.nutri_score.move(token['x_pos'], token['y_pos'])

                    # self.add_widget()
                    #
                    # token_info = {
                    #     'id': token['component_id'],
                    #     'name': 'Banana',
                    #     'x': token['x_pos'],
                    #     'y': token['y_pos'],
                    #     'last_time_seen': time.time(),
                    #     'info_widget': ''
                    # }
                    # self.present_tokens.append(token['component_id'])


class NutriScore(QWidget):
    def __init__(self, parent, x, y):
        super(NutriScore, self).__init__(parent)
        self.x = x
        self.y = y

        self.setGeometry(x, y, 500, 500)
        uic.loadUi(os.path.abspath(os.path.join(os.path.dirname(__file__), 'NutriScore.ui')), self)
