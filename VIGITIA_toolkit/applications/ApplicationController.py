from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget

from VIGITIA_toolkit.core.VIGITIABaseApplication import VIGITIABaseApplication


class ApplicationController(QWidget, VIGITIABaseApplication):

    selected_application_id = -1

    applications_dict = {1: 'BrowserWidget',
                         2: 'ButtonWidget',
                         3: 'DemoWidget',
                         4: 'BrowserWidget2',
                         5: 'DemoWidget',
                         6: 'BrowserWidget'}

    add_application = pyqtSignal(str)
    remove_application = pyqtSignal(str)

    # It needs to receive the rendering manager as an argument
    def __init__(self, rendering_manager):
        super().__init__()  # Init the super class
        self.set_name(self.__class__.__name__)  # Register the application with their name
        self.set_rendering_manager(rendering_manager)  # Register the rendering manager

        self.initUI()

        self.width = 1
        self.height = 1

        self.init_signals()

    def initUI(self):
        self.setGeometry(0, 0, self.get_width(), self.get_height())  # Initialize the application dimensions

        # Make the background transparent to allow stacking of applications
        self.setStyleSheet("background-color: transparent;")

    def init_signals(self):
        self.add_application.connect(self.rendering_manager.add_application_by_name)
        self.remove_application.connect(self.rendering_manager.remove_application)

    def on_new_token_messages(self, data):
        for token in data:
            token_id = token['component_id']
            if token_id in range(1, 7):
                self.add_selected_application(token_id)

    def add_selected_application(self, new_id):
        if self.selected_application_id != new_id:  # Check if the selected application is already shown
            self.remove_previous_application()  # Remove the previously selected application
            self.add_application.emit(self.applications_dict[new_id])
            self.selected_application_id = new_id

    def remove_previous_application(self):
        if self.selected_application_id != -1:
            self.remove_application.emit(self.applications_dict[self.selected_application_id])
