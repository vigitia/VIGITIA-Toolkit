import os
import time
from datetime import datetime

from PyQt5 import uic
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QImage, QPainter, QPen, QColor
from PyQt5.QtWidgets import QWidget, QLabel

from VIGITIA_toolkit.core.VIGITIABaseApplication import VIGITIABaseApplication

# Constants for smoothing detected object positions
MAX_TIME_MISSING_MS = 1000  # Remove a displayed NutriScore if object is missing for more than the given time in ms
SMOOTHING_FACTOR = 0.7  # Value between 0 and 1, depending if the old or the new value should count more.


class NutritionalValues(QWidget, VIGITIABaseApplication):
    """ NutritionalValues

        This class displays Nutritional infos for detected objects on the table

    """

    present_tokens = []

    running = False

    # It needs to receive the rendering manager as an argument
    def __init__(self, rendering_manager):
        super().__init__()  # Init the super class
        self.set_name(self.__class__.__name__)  # Register the application with their name
        self.set_rendering_manager(rendering_manager)  # Register the rendering manager

        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, self.get_width(), self.get_height())  # Initialize the application dimensions
        self.setStyleSheet("background-color: transparent;")

        self.image = QImage(self.size(), QImage.Format_ARGB32)

        # A list to keep track of all displayed nutritional scores
        self.nutri_scores = []

        # Init for all objects that should be detected
        self.nutri_score_banana = NutriScore(self, 0, 0, 'Banane', '115kcal', '26,4g', '1,2g', '0,2g')
        self.nutri_score_orange = NutriScore(self, 0, 0, 'Orange', '56kcal', '10,7g', '1,3g', '0,3g')
        self.nutri_score_carrot = NutriScore(self, 0, 0, 'Karotte', '32kcal', '7,2g', '0,8g', '0,0g')
        self.nutri_score_apple = NutriScore(self, 0, 0, 'Apfel', '65kcal', '14,3g', '0,4g', '0,5g')
        self.nutri_score_donut = NutriScore(self, 0, 0, 'Donut', '201kcal', '19,5g', '3,5g', '11,5g')

        # Hide the widgets and only show them if the object is detected
        self.nutri_score_banana.hide()
        self.nutri_score_orange.hide()
        self.nutri_score_carrot.hide()
        self.nutri_score_apple.hide()
        self.nutri_score_donut.hide()

        self.nutri_scores.append({
            'id': 10000,
            'x': 0,
            'y': 0,
            'width': 0,
            'height': 0,
            'hidden': True,
            'last_time_seen': 0,
            'widget': self.nutri_score_orange
        })

        self.nutri_scores.append({
            'id': 10001,
            'x': 0,
            'y': 0,
            'width': 0,
            'height': 0,
            'hidden': True,
            'last_time_seen': 0,
            'widget': self.nutri_score_banana
        })

        self.nutri_scores.append({
            'id': 10002,
            'x': 0,
            'y': 0,
            'width': 0,
            'height': 0,
            'hidden': True,
            'last_time_seen': 0,
            'widget': self.nutri_score_carrot
        })

        self.nutri_scores.append({
            'id': 10004,
            'x': 0,
            'y': 0,
            'width': 0,
            'height': 0,
            'hidden': True,
            'last_time_seen': 0,
            'widget': self.nutri_score_apple
        })

        self.nutri_scores.append({
            'id': 10005,
            'x': 0,
            'y': 0,
            'width': 0,
            'height': 0,
            'hidden': True,
            'last_time_seen': 0,
            'widget': self.nutri_score_donut
        })

        # Load the smartphone widget component
        self.smartphone_widget = Smartphone(self, 0, 0)
        self.smartphone_widget.hide()
        self.smartphone = {
            'x': 0,
            'y': 0,
            'width': 0,
            'height': 0,
            'last_time_seen': 0,
            'hidden': True,
            'widget': self.smartphone_widget
        }

        # Loading everything finished
        self.running = True

    # Clear everything that has been painted on the screen
    def reset_image(self):
        self.image.fill(Qt.transparent)

    # Draw a circle around detected objects
    def draw_circle(self, x, y, width, height):
        painter = QPainter(self.image)
        painter.setPen(QPen(QColor(255, 255, 255, 150), 10, Qt.SolidLine))
        painter.drawEllipse(x, y, width, height)

    # Function for handling Qt Paint Events to draw on the canvas
    def paintEvent(self, event):
        # Create a canvas
        canvasPainter = QPainter(self)

        # draw rectangle  on the canvas
        canvasPainter.drawImage(self.rect(), self.image, self.image.rect())

    # This function will be automatically called by the SensorDataInterface if new data is available
    def on_new_tuio_bundle(self, data):
        if self.running:

            bounding_boxes = data['bounding_boxes']

            now = int(round(time.time() * 1000))

            ids_food = [10000, 10001, 10002, 10004, 10005]
            id_smartphone = 10003

            for bounding_box in bounding_boxes:
                if bounding_box['session_id'] in ids_food or bounding_box['session_id'] == id_smartphone:
                    if bounding_box['session_id'] in ids_food:
                        entry = list(filter(lambda entry: entry['id'] == bounding_box['session_id'], self.nutri_scores))[0]
                    if bounding_box['session_id'] == id_smartphone:
                        entry = self.smartphone

                    entry['x'] = int(SMOOTHING_FACTOR * (bounding_box['x_pos'] - entry['x']) + entry['x'])
                    entry['y'] = int(SMOOTHING_FACTOR * (bounding_box['y_pos'] - entry['y']) + entry['y'])
                    entry['width'] = int(SMOOTHING_FACTOR * (bounding_box['width'] - entry['width']) + entry['width'])
                    entry['height'] = int(SMOOTHING_FACTOR * (bounding_box['height'] - entry['height']) + entry['height'])
                    entry['last_time_seen'] = int(round(time.time() * 1000))

                    if entry['hidden']:
                        entry['hidden'] = False
                        entry['widget'].show()

            self.update()
            self.reset_image()

            for entry in self.nutri_scores:

                if not entry['hidden']:
                    # Hide element if missing for too long
                    if now - entry['last_time_seen'] > MAX_TIME_MISSING_MS:
                        entry['hidden'] = True
                        entry['widget'].hide()
                        break

                    # Draw elements:
                    self.draw_circle(entry['x'], entry['y'], entry['width'], entry['height'])

                    entry['widget'].move(entry['x'] + entry['width'], entry['y'])

            # Update smartphone
            if not self.smartphone['hidden']:
                # Hide element if missing for too long
                if now - self.smartphone['last_time_seen'] > MAX_TIME_MISSING_MS:
                    self.smartphone['hidden'] = True
                    self.smartphone['widget'].hide()
                else:
                    self.smartphone['widget'].move(int(self.smartphone['x'] + self.smartphone['width'] * 0.75), self.smartphone['y'])


# Class for loading the Nutriscore widget
class NutriScore(QWidget):

    WIDTH = 500
    HEIGHT = 500

    # Pass its parent, coordinates and data that should be displayed on init
    def __init__(self, parent, x, y, item_name, calories, carbohydrates, protein, fat):
        super(NutriScore, self).__init__(parent)

        self.x = x
        self.y = y
        self.item_name = item_name
        self.calories_name = 'Brennwert: ' + calories
        self.carbohydrates_name = carbohydrates + ' Kohlenhydrate'
        self.protein_name = protein + ' Eiweiß'
        self.fat_name = fat + ' Fett'

        self.initUI()
        self.init_values()

    def initUI(self):
        self.setGeometry(self.x, self.y, self.WIDTH, self.HEIGHT)
        uic.loadUi(os.path.abspath(os.path.join(os.path.dirname(__file__), 'NutriScore.ui')), self)

        # Find the labeles in the UI by name
        self.label_name = self.findChild(QLabel, 'name')
        self.label_calories = self.findChild(QLabel, 'calories')
        self.label_carbohydrates = self.findChild(QLabel, 'carbohydrates')
        self.label_protein = self.findChild(QLabel, 'protein')
        self.label_fat = self.findChild(QLabel, 'fat')

    # Update the label values
    def init_values(self):
        self.label_name.setText(self.item_name)
        self.label_calories.setText(self.calories_name)
        self.label_carbohydrates.setText(self.carbohydrates_name)
        self.label_protein.setText(self.protein_name)
        self.label_fat.setText(self.fat_name)


# Class for loading the smartphone widget from the UI file
class Smartphone(QWidget):
    WIDTH = 400
    HEIGHT = 600

    # Pass its parent and coordinates on init
    def __init__(self, parent, x, y):
        super(Smartphone, self).__init__(parent)

        self.x = x
        self.y = y

        self.initUI()

        # Init a new thread for a constant update of the current time
        self.thread = TimeUpdaterThread(self)
        self.thread.start()

    def initUI(self):
        self.setGeometry(self.x, self.y, self.WIDTH, self.HEIGHT)
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
