import traceback

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *
import sys
import os
from os import listdir
from pathlib import Path
from os.path import isfile, join
from importlib import import_module
import pyclbr

from apps.VIGITIABaseApplication import VIGITIABaseApplication

APPLICATIONS_BASE_FOLDER = 'applications'
APPLICATION_PARENT_CLASS = 'VIGITIABaseApplication'

DEBUG_MODE = False

#BLACKLIST = ['ImageWidget', 'VideoWidget', 'BrowserWidget', 'VIGITIAPaintingApp', 'ButtonWidget']
BLACKLIST = ['ImageWidget', 'VideoWidget', 'VIGITIAPaintingApp', 'ButtonWidget', 'NutritionalValues']


class VIGITIARenderingManager(QMainWindow, VIGITIABaseApplication):
    """Responsible for drawing all applications on the same canvas (a fullscreen QMainWindow)

    """

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
        self.width = QApplication.desktop().screenGeometry().width()
        self.height = QApplication.desktop().screenGeometry().height()

        # Attention: The window resolution might not be the same as the screen resolution
        # Screen scaling can influence the resolution
        print('[VIGITIARenderingManager]: Main Window width:', self.width, 'height:', self.height)

        # The QMainWindow should have a black background so that no light will be projected if no application is shown
        self.setStyleSheet("background-color: black;")

        # Define a parent widget that will contain all applications
        parent_widget = QWidget(self)
        parent_widget.setStyleSheet("background-color: transparent;")
        parent_widget.setFixedSize(self.width, self.height)
        self.setCentralWidget(parent_widget)

        # Load applications and add them to the canvas
        self.add_applications(parent_widget)

    def on_application_updated(self, application_name):
        """ This function is called if an application changes its size, position or rotation.

            The RenderingManager is notified to redraw the application.

            Args:
                application_name (str): The name of the application that has changed
        """
        print('[VIGITIARenderingManager]:', application_name, 'has been updated')
        self.update_application(application_name)

    def update_application(self, application_name):
        if self.applications is not None:
            for application in self.applications:
                if application['name'] == application_name:

                    application['instance'].setGeometry(0, 0, application['instance'].get_width(),
                                                        application['instance'].get_height())

                    # Rotate application
                    if application['instance'].get_rotation() != 0:
                        application = self.rotate_applicaton(application)

                    if application['parent'] is None:
                        application['instance'].move(application['instance'].get_x(), application['instance'].get_y())
                    else:

                        # Set parent of rotated widget to fullscreen to make sure that the rotated widget fits
                        application['parent'].setGeometry(0, 0, self.width, self.height)

                        # Since the rotated widget is now placed in the center of the parent instead of at the origin,
                        # we move the entire parent so that the rotated widget is back at 0,0
                        origin_x = self.width / 2 - application['instance'].frameGeometry().width() / 2
                        origin_y = self.height / 2 - application['instance'].frameGeometry().height() / 2

                        # Now we move the rotated widget including its parent to the desired position
                        application['parent'].move(
                            -origin_x + application['parent'].geometry().x() + application['instance'].get_x(),
                            -origin_y + application['parent'].geometry().y() + application['instance'].get_y())

                    # TODO: Test
                    self.update_z_position_of_applications()

    def get_screen_resolution(self):
        """Return the resolution of the QMainWindow

        """
        return self.width, self.height

    # Add all desired applications to the canvas
    def add_applications(self, parent_widget):
        self.applications = self.find_available_applications()

        # TODO: Combine with update applications function
        for application in self.applications:
            print('[VIGITIARenderingManager]: Placing {} on canvas.'.format(application['name']))

            application['instance'].setGeometry(0, 0, application['instance'].get_width(),
                                                application['instance'].get_height())

            # Rotate applications
            if application['instance'].get_rotation() != 0:
                application = self.rotate_applicaton(application)

            if application['parent'] is None:
                if DEBUG_MODE:
                    application['instance'].setStyleSheet('border: 3px solid #FF0000')
                application['instance'].move(application['instance'].get_x(), application['instance'].get_y())
                application['instance'].setParent(parent_widget)
            else:
                if DEBUG_MODE:
                    application['parent'].setStyleSheet('border: 3px solid #FF0000')
                application['parent'].setParent(parent_widget)

                # Set parent of rotated widget to fullscreen to make sure that the rotated widget fits
                application['parent'].setGeometry(0, 0, self.width, self.height)

                # Since the rotated widget is now placed in the center of the parent instead of at the origin,
                # we move the entire parent so that the rotated widget is back at 0,0
                origin_x = self.width/2 - application['instance'].frameGeometry().width()/2
                origin_y = self.height/2 - application['instance'].frameGeometry().height()/2

                # Now we move the rotated widget inluding its parent to the desired position
                application['parent'].move(-origin_x + application['parent'].geometry().x() + application['instance'].get_x(),
                                           -origin_y + application['parent'].geometry().y() + application['instance'].get_y())

        self.update_z_position_of_applications()

        # Test of raising an application to the top
        # TODO: Implement z-index feature
        # for application in self.applications:
        #     if application['name'] == 'ButtonWidget':
        #         print('Bring painting app to front')
        #         if application['parent'] is None:
        #             application['instance'].raise_()
        #         else:
        #             application['parent'].raise_()

    def update_z_position_of_applications(self):

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

        print(list_of_z_indexes)

    # Based on https://stackoverflow.com/questions/58020983/rotate-the-widget-for-some-degree
    def rotate_applicaton(self, application):
        """Allows the rotation of an application (a QT Widget)

        """

        angle = application['instance'].rotation
        if application['proxy'] is None:
            graphics_view = QGraphicsView()
            scene = QGraphicsScene(graphics_view)

            # Disable scrollbars
            graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            graphics_view.setScene(scene)

            proxy = QGraphicsProxyWidget()
            proxy.setWidget(application['instance'])
            proxy.setTransformOriginPoint(proxy.boundingRect().center())
            scene.addItem(proxy)

            proxy.setTransform(QTransform().rotate(angle))

            graphics_view.adjustSize()

            application['parent'] = graphics_view
            application['proxy'] = proxy
        else:
            proxy = application['proxy']
            proxy.setTransform(QTransform().rotate(angle))

        # TODO: Check if width/height of graphics_wiew > width/height of QMainWindow. If yes, scale down
        # TODO: Notify application about new position, rotation and size
        #
        #print('Graphics view width:', graphics_view.width(), graphics_view.height())

        #pts1 = np.float32([[100, 100], [200, 10], [10, 200], [200, 200]])
        #pts2 = np.float32([[10, 10], [100, 110], [10, 100], [100, 100]])

        #matrix = cv2.getPerspectiveTransform(pts1, pts2)

        #print(matrix)

        #matrix = [[1, 1,  1],
        #          [1, 10,  1],
        #          [1, 1,  1]]

        #transform = QTransform()
        #transform.setMatrix(matrix[0][0], matrix[0][1], matrix[0][2],
        #                    matrix[1][0], matrix[1][1], matrix[1][2],
        #                    matrix[2][0], matrix[2][1], matrix[2][2])
        #proxy.setTransform(transform)

        # Prove that transform works
        #proxy.setTransform(QTransform().shear(2.0, 0))

        #print('GW:', proxy.width(), proxy.height(), proxy.x(), proxy.y())

        return application

    def find_available_applications(self):
        """ Checking the folder APPLICATIONS_BASE_FOLDER for all classes that inherit from the superclass
            'VIGITIAApplication'.
            These are the applications that are currently available for display
        """
        applications = []

        # Searching for applications in the following directory
        # TODO: Also allow for searching in subdirectories and therefore add support for Git Repositories
        applications_path = os.path.join(Path(__file__).resolve().parent.parent, APPLICATIONS_BASE_FOLDER)

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
                            # print('"{}" in Module "{}" is a VIGITIA Application'.format(class_name, module_name))

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
        # Close the application if the ESC button is pressed
        if event.key() == Qt.Key_Escape:
            self.close()
            sys.exit(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VIGITIARenderingManager()
    sys.exit(app.exec_())