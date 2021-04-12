import traceback

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
import os
from os import listdir
from pathlib import Path
from os.path import isfile, join
from importlib import import_module
import pyclbr

# The following import needs to be present otherwise the rendering manager will throw an error
# from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebEngineWidgets import *

from VIGITIA_toolkit.core.VIGITIABaseApplication import VIGITIABaseApplication

# Folder path to search for applications
APPLICATIONS_BASE_FOLDER = 'applications'

# Name of the parent class that all toolkit applications inherit from
APPLICATION_PARENT_CLASS = 'VIGITIABaseApplication'

# Enable debug mode to get additional data printed to console
DEBUG_MODE = True

# Add the names of all applications that you dont want to render to this list
#BLACKLIST = ['ImageWidget', 'VideoWidget', 'BrowserWidget', 'PaintingWidget', 'ButtonWidget']
BLACKLIST = ['VideoWidget', 'ButtonWidget', 'Patterns', 'NutritionalValues', 'ImageWidget', 'PaintingWidget', 'BrowserWidget', 'BrowserWidget2']


class VIGITIARenderingManager(QMainWindow, VIGITIABaseApplication):
    """ Responsible for drawing all applications on the same canvas (a fullscreen QMainWindow)

    """

    # all active applications will be stored in that list
    applications = []

    def __init__(self):
        super().__init__()
        self.set_name(self.__class__.__name__)
        self.set_rendering_manager(self)
        self.initUI()

    def initUI(self):
        # TODO: Define screen where the QMainWindow should be displayed
        self.showFullScreen()  # Application should run in Fullscreen

        # Define width and height as global variables
        #self.width = QApplication.desktop().screenGeometry().width()
        #self.height = QApplication.desktop().screenGeometry().height()
        self.width = 3840
        self.height = 2160

        # Attention: The window resolution might not be the same as the screen resolution
        # Screen scaling can influence the resolution
        print('[VIGITIARenderingManager]: Main Window width:', self.width, 'height:', self.height)

        # The QMainWindow should have a black background so that no light will be projected if no application is shown
        self.setStyleSheet("background-color: transparent;")

        # Define a parent widget that will contain all applications
        parent_widget = QWidget(self)
        parent_widget.setStyleSheet("background-color: transparent;")
        parent_widget.setFixedSize(self.width, self.height)
        self.setCentralWidget(parent_widget)

        # Load applications and add them to the canvas
        self.add_applications(parent_widget)

    def update_application(self, application_name, rotate=True):
        """ This function is called if an application changes its size, position or rotation.

            The RenderingManager is notified to redraw the application.

            Args:
                application_name (str): The name of the application that has changed
        """
        if self.applications is not None:
            # Iterate over all applications to find the correct one
            for application in self.applications:
                if application['name'] == application_name:

                    # Rotate application
                    if rotate:
                        application = self.rotate_applicaton(application)

                    # Update width and height
                    application['instance'].setGeometry(0, 0, application['instance'].get_width(),
                                                        application['instance'].get_height())

                    # Move application on canvas
                    application['parent'].move(application['instance'].get_x(), application['instance'].get_y())

                    # Update z-Position (lower or raise them on the canvas)
                    self.update_z_position_of_applications()

    def get_screen_resolution(self):
        """ Return the resolution of the QMainWindow

        """
        return self.width, self.height

    # Add all desired applications to the canvas
    def add_applications(self, parent_widget):
        self.applications = self.find_available_applications()

        # TODO: Combine with update applications function
        for application in self.applications:
            print('[VIGITIARenderingManager]: Placing Application "{}" on canvas.'.format(application['name']))

            application = self.embed_application_in_graphics_view(application)

            # Rotate applications
            self.rotate_applicaton(application)

            application['instance'].setGeometry(0, 0, application['instance'].get_width(),
                                                application['instance'].get_height())

            if DEBUG_MODE:
                application['parent'].setStyleSheet('border: 3px solid #FF0000')

            application['parent'].setParent(parent_widget)
            application['parent'].move(application['instance'].get_x(), application['instance'].get_y())


        self.update_z_position_of_applications()

    # Raise or lower applications on the canvas
    def update_z_position_of_applications(self):

        # Check the current z-index of all applications
        list_of_z_indexes = []

        for application in self.applications:
            z_index = application['instance'].get_z_index()
            list_of_z_indexes.append([application, z_index])

        # Sort list by second element (the z-index)
        list_of_z_indexes = sorted(list_of_z_indexes, key=lambda x: x[1])

        for entry in list_of_z_indexes:
            application = entry[0]
            if application['parent'] is None:
                application['instance'].raise_()
            else:
                application['parent'].raise_()

    # Based on https://stackoverflow.com/questions/58020983/rotate-the-widget-for-some-degree
    def rotate_applicaton(self, application):
        """Allows the rotation of an application (a QT Widget)

        """

        angle = application['instance'].rotation
        if not 0 <= angle <= 360:
            return application

        try:
            print('Rotating to :', angle)

            center_x = application['instance'].frameGeometry().width()/2
            center_y = application['instance'].frameGeometry().height()/2
            print(center_x, center_y)

            application['proxy'].setTransformOriginPoint(self.mapFromGlobal(QPoint(center_x, center_y)))
            application['proxy'].setRotation(angle)

            application['parent'].adjustSize()

        except AttributeError as e:
            print(e)

        return application

    def embed_application_in_graphics_view(self, application):
        graphics_view = QGraphicsView()

        # Disable scrollbars
        graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #graphics_view.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        scene = QGraphicsScene(graphics_view)
        graphics_view.setScene(scene)

        # Embed application in a QGraphicsProxyWidget
        proxy = QGraphicsProxyWidget()

        proxy.setWidget(application['instance'])
        scene.addItem(proxy)

        # Set initial size of graphics view
        #graphics_view.setGeometry(0, 0, self.width, self.height)  # Fullscreen
        #graphics_view.setGeometry(0, 0, application['instance'].get_width()*2, application['instance'].get_height()*2)
        #graphics_view.adjustSize()

        application['parent'] = graphics_view
        application['proxy'] = proxy

        return application

    def find_available_applications(self):
        """ Checking the folder APPLICATIONS_BASE_FOLDER for all classes that inherit from the superclass
            'VIGITIAApplication'.
            These are the applications that are currently available for display
        """
        applications = []

        # Searching for applications in the following directory
        # TODO: Also allow for searching in subdirectories and therefore add support for Git Repositories
        applications_path = os.path.join(Path(__file__).resolve().parent, APPLICATIONS_BASE_FOLDER)

        # Inspired by https://stackoverflow.com/questions/1057431/how-to-load-all-modules-in-a-folder
        files = [f for f in listdir(applications_path) if isfile(join(applications_path, f)) and f != '__init__.py']
        for file in files:
            file_type = os.path.splitext(file)[1]
            if file_type == '.py':
                module_name = f"{'applications'}.{file[:-3]}"
                try:
                    module_info = pyclbr.readmodule(module_name)
                    module = import_module(module_name)
                except:
                    print('[VIGITIARenderingManager]: ERROR IN APPLICATION ', class_name)
                    print('[VIGITIARenderingManager]: Fix the following problem and try again:')
                    traceback.print_exc()
                    self.close()
                    sys.exit(1)

                for item in module_info.values():
                    class_name = item.name  # The name of the found class
                    my_class = getattr(module, class_name)
                    superclasses = my_class.mro()
                    # Check if the class has the required superclass
                    for superclass in superclasses:
                        if superclass.__name__ == APPLICATION_PARENT_CLASS:

                            if class_name not in BLACKLIST:

                                try:
                                    instance = my_class(self)
                                except:
                                    print('[VIGITIARenderingManager]: ERROR IN APPLICATION ', class_name)
                                    print('[VIGITIARenderingManager]: Fix the following problem and try again:')
                                    traceback.print_exc()
                                    self.close()
                                    sys.exit(1)

                                application = {
                                    'name': class_name,
                                    'instance': instance,  # Pass the RenderingManager on to the class
                                    'parent': None,
                                    'proxy': None
                                }

                                applications.append(application)
                            else:
                                print('[VIGITIARenderingManager]: Not adding "{}" because it is on the Blacklist.'.format(class_name))

        return applications

    # Handle Key-press events
    def keyPressEvent(self, event):
        for application in self.applications:
            application['instance'].on_key_pressed(event)

        # Close the application if the ESC button is pressed
        if event.key() == Qt.Key_Escape:
            self.close_window()

    # Terminate the main window
    def close_window(self):
        self.close()
        sys.exit(app.exec_)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    window = VIGITIARenderingManager()
    sys.exit(app.exec_())
