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

#from pyQT5_experiments.qt_custom_transparent_widget_example import TransparentWidget
#from pyQT5_experiments.pyqt_paint_example import PaintExample
from pyQT5_experiments.pyQT5_browser import BrowserWidget

APPLICATIONS_BASE_FOLDER = 'applications'

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.showFullScreen()

        self.initUI()

        self.show()

        print(QApplication.desktop().screenGeometry().width(), QApplication.desktop().screenGeometry().height())


    def initUI(self):
        self.setStyleSheet("background-color: black;")

        # web = QWebEngineView()
        # web.setMaximumWidth(500)
        # web.load(QUrl('https://maps.google.com'))
        #
        # # web = BrowserWidget()
        #
        # web2 = QWebEngineView()
        # web2.setMaximumHeight(1000)
        # web2.setMaximumWidth(2000)
        # web2.load(QUrl('https://google.com'))
        # web2.setGeometry(1000, 1000, 300, 300)


        web = QWebEngineView()
        web.setMaximumWidth(1000)
        web.load(QUrl('https://youtube.com'))

        graphics_view = QGraphicsView()
        scene = QGraphicsScene(graphics_view)
        graphics_view.setScene(scene)

        proxy = QGraphicsProxyWidget()
        proxy.setWidget(web)
        proxy.setTransformOriginPoint(proxy.boundingRect().center())
        scene.addItem(proxy)

        proxy.setRotation(45)

        #paint = PaintExample()


        #transparent = TransparentWidget()
        #transparent.setMaximumWidth(1000)


        # Use a 1x1 Grid layout to allow free placement of the widgets
        layout = QGridLayout()

        applications = self.find_available_applications()
        for application in applications:
            layout.addWidget(application, 0, 0, Qt.AlignLeft)

        layout.addWidget(graphics_view, 0, 0, Qt.AlignLeft)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

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
                    class_name = item.name
                    my_class = getattr(module, class_name)
                    superclasses = my_class.mro()
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
    window = Window()
    sys.exit(app.exec_())

