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


class VIGITIARenderingManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.showFullScreen()
        self.initUI()
        self.show()

        print('Main Window width:', QApplication.desktop().screenGeometry().width(),
              'height: ', QApplication.desktop().screenGeometry().height())

    def initUI(self):
        self.setStyleSheet("background-color: black;")

        widget = QWidget(self)
        widget.setStyleSheet("background-color: transparent;")
        widget.setFixedSize(QApplication.desktop().screenGeometry().width(),
                            QApplication.desktop().screenGeometry().height())

        # Load applications and add them to the canvas
        applications = self.find_available_applications()
        for application in applications:

            # TEST
            #application.setStyleSheet("background-color: rgb(255,0,0); border:1px solid rgb(0, 255, 0); ")
            print('Placing {} on canvas.'.format(application.__class__.__name__))

            x = application.x
            y = application.y
            application = self.rotate_applicaton(application, 70)

            application.move(x, y)
            application.setStyleSheet('border: 3px solid #FF0000')

            application.setParent(widget)

        self.setCentralWidget(widget)

    # Allows the rotation of an application (A QT Widget)
    # Based on https://stackoverflow.com/questions/58020983/rotate-the-widget-for-some-degree
    def rotate_applicaton(self, application, angle):
        graphics_view = QGraphicsView()
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

        print('Graphics view width:', graphics_view.width(), graphics_view.height())

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
                            print('"{}" in Module "{}" is a VIGITIA Application'.format(class_name, module_name))
                            application = my_class()
                            applications.append(application)

        return applications

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VIGITIARenderingManager()
    sys.exit(app.exec_())

