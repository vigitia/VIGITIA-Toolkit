import os
import time

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

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

        self.nutri_score_banana = NutriScore(self, 100, 600, 'Banane', '115', '26,4g', '1,2g', '0,2g')
        self.nutri_score_orange = NutriScore(self, 600, 600, 'Orange', '115', '26,4g', '1,2g', '0,2g')
        self.nutri_score_carrot = NutriScore(self, 1100, 600, 'Karotte', '115', '26,4g', '1,2g', '0,2g')
        self.nutri_score_banana.hide()
        self.nutri_score_orange.hide()
        self.nutri_score_carrot.hide()

    def add_widget(self):
        self.moveToThread(self.rendering_manager)
        NutriScore(self, 100, 100)

    def on_new_token_messages(self, data):
        # print('Tokens:', data)
        for token in data:
            if token['component_id'] == 36:
                self.nutri_score_orange.show()
                self.nutri_score_orange.move(token['x_pos'], token['y_pos'])
            elif token['component_id'] == 37:
                self.nutri_score_carrot.show()
                self.nutri_score_carrot.move(token['x_pos'], token['y_pos'])
            elif token['component_id'] == 44:
                self.nutri_score_banana.show()
                self.nutri_score_banana.move(token['x_pos'], token['y_pos'])

                #if token['component_id'] not in self.present_tokens:
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

    WIDTH = 500
    HEIGHT = 500

    def __init__(self, parent, x, y, item_name, calories, carbohydrates, protein, fat):
        super(NutriScore, self).__init__(parent)

        self.x = x
        self.y = y
        self.item_name = item_name
        self.calories_name = calories + ' Kalorien'
        self.carbohydrates_name = carbohydrates + ' Kohlenhydrate'
        self.protein_name = protein + ' Eiweiß'
        self.fat_name = fat + ' Fett'

        self.initUI()
        self.init_values()

    def initUI(self):
        self.setGeometry(self.x, self.y, self.WIDTH, self.HEIGHT)
        uic.loadUi(os.path.abspath(os.path.join(os.path.dirname(__file__), 'NutriScore.ui')), self)

        self.label_name = self.findChild(QLabel, 'name')
        self.label_calories = self.findChild(QLabel, 'calories')
        self.label_carbohydrates = self.findChild(QLabel, 'carbohydrates')
        self.label_protein = self.findChild(QLabel, 'protein')
        self.label_fat = self.findChild(QLabel, 'fat')

    def init_values(self):
        print(self.calories)

        self.label_name.setText(self.item_name)
        self.label_calories.setText(self.calories_name)
        self.label_carbohydrates.setText(self.carbohydrates_name)
        self.label_protein.setText(self.protein_name)
        self.label_fat.setText(self.fat_name)
