
from PyQt5.QtWidgets import QWidget

from VIGITIA_toolkit.core.VIGITIABaseApplication import VIGITIABaseApplication


# A toolkit applications needs to be a valid PyQt application. It also needs to inherit from VIGITIABaseApplication
class ToolkitApplication(QWidget, VIGITIABaseApplication):
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
        self.setStyleSheet("background-color: transparent;")

    # If you want to get data from the SensorDataInterface, place the methods documented in VIGITIABaseApplication here
