import random

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

APPLICATIONS_BASE_FOLDER = 'applications'

DEBUG_MODE = False


class VIGITIARenderingManager(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.show()

    def initUI(self):
        self.showFullScreen()
        self.width = QApplication.desktop().screenGeometry().width()
        self.height = QApplication.desktop().screenGeometry().height()

        # TODO: Take into consideration that the window resolution might not be the same as the screen resolution
        # Screen scaling can influence the resolution
        print('Main Window width:', self.width, 'height: ', self.height)

        self.setStyleSheet("background-color: black;")

        parent_widget = QWidget(self)
        parent_widget.setStyleSheet("background-color: transparent;")
        parent_widget.setFixedSize(self.width, self.height)

        # Load applications and add them to the canvas
        self.add_applications(parent_widget)

        self.setCentralWidget(parent_widget)

    def add_applications(self, parent_widget):
        self.applications = self.find_available_applications()

        for application in self.applications:
            hidden_applications = ['BrowserWidget', 'ExampleWidget']
            # if application['name'] == 'VIGITIAPaintingApp' or application['name'] == 'BrowserWidget':
            if application['name'] in hidden_applications:
                print('Test. Not adding', application['name'])
            else:
                print('Placing {} on canvas.'.format(application['name']))

                x = application['instance'].get_x()
                y = application['instance'].get_y()
                if application['instance'].get_rotation() != 0:
                    application['parent'] = self.rotate_applicaton(application['instance'],
                                                                   application['instance'].rotation)

                if application['parent'] is None:
                    if DEBUG_MODE:
                        application['instance'].setStyleSheet('border: 3px solid #FF0000')
                    application['instance'].move(x, y)
                    application['instance'].setParent(parent_widget)
                else:
                    if DEBUG_MODE:
                        application['parent'].setStyleSheet('border: 3px solid #FF0000')
                    application['parent'].move(x, y)
                    application['parent'].setParent(parent_widget)

        # TODO: Add unified system to define application position
        # Test of raising an application to the top
        for application in self.applications:
            if application['name'] == 'BrowserWidget':
                print('Bring painting app to front')
                if application['parent'] is None:
                    application['instance'].raise_()
                else:
                    application['parent'].raise_()

    # Allows the rotation of an application (A QT Widget)
    # Based on https://stackoverflow.com/questions/58020983/rotate-the-widget-for-some-degree
    def rotate_applicaton(self, application, angle):
        graphics_view = QGraphicsView()
        # Disable scrollbars
        graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scene = QGraphicsScene(graphics_view)
        graphics_view.setScene(scene)

        proxy = QGraphicsProxyWidget()
        proxy.setWidget(application)
        proxy.setTransformOriginPoint(proxy.boundingRect().center())
        scene.addItem(proxy)

        proxy.setRotation(angle)

        # TODO: Check if width/height of graphics_wiew > width/height of QMainWindow. If yes, scale down
        # TODO: Notify application about new position, rotation and size
        #
        #print('Graphics view width:', graphics_view.width(), graphics_view.height())

        #pts1 = np.float32([[100, 100], [200, 10], [10, 200], [200, 200]])
        #pts2 = np.float32([[10, 10], [100, 110], [10, 100], [100, 100]])

        #matrix = cv2.getPerspectiveTransform(pts1, pts2)

        #print(matrix)

        # matrix = [[0, 0,  0],
        #           [0, 0,  0],
        #           [0, 0,  0]]
        #
        # transform = QTransform()
        # transform.setMatrix(matrix[0][0], matrix[0][1], matrix[0][2],
        #                     matrix[1][0], matrix[1][1], matrix[1][2],
        #                     matrix[2][0], matrix[2][1], matrix[2][2])
        #graphics_view.setTransform(transform)

        return graphics_view

    # Checking the folder APPLICATIONS_BASE_FOLDER for all classes that inherit from the superclass "VIGITIAApplication"
    # These are the applications that are currently available for display
    def find_available_applications(self):
        applications = []

        # Searching for applications in the following directory
        # TODO: Also allow for searching in subdirectories and add support for Git Repositories
        applications_path = os.path.join(Path(__file__).resolve().parent.parent, APPLICATIONS_BASE_FOLDER)

        # Inspired by https://stackoverflow.com/questions/1057431/how-to-load-all-modules-in-a-folder
        files = [f for f in listdir(applications_path) if isfile(join(applications_path, f)) and f != '__init__.py']
        for file in files:
            file_type = os.path.splitext(file)[1]
            if file_type == '.py':
                module_name = f"{'applications'}.{file[:-3]}"
                module_info = pyclbr.readmodule(module_name)
                module = import_module(module_name)

                for item in module_info.values():
                    class_name = item.name  # The name of the found class
                    my_class = getattr(module, class_name)
                    superclasses = my_class.mro()
                    # Check if the class has the required superclass
                    for superclass in superclasses:
                        if superclass.__name__ == 'VIGITIAApplication':
                            # print('"{}" in Module "{}" is a VIGITIA Application'.format(class_name, module_name))
                            # application = my_class()
                            application = {
                                'name': class_name,
                                'instance': my_class(),
                                'parent': None
                            }
                            applications.append(application)

        return applications

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VIGITIARenderingManager()
    sys.exit(app.exec_())

