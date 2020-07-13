from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *
import sys

from pyQT5_experiments.qt_custom_transparent_widget_example import TransparentWidget
from pyQT5_experiments.pyqt_paint_example import PaintExample
from pyQT5_experiments.pyQT5_browser import BrowserWidget

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
        web.load(QUrl('https://maps.google.com'))

        graphics_view = QGraphicsView()
        scene = QGraphicsScene(graphics_view)
        graphics_view.setScene(scene)

        proxy = QGraphicsProxyWidget()
        proxy.setWidget(web)
        proxy.setTransformOriginPoint(proxy.boundingRect().center())
        scene.addItem(proxy)

        proxy.setRotation(45)

        paint = PaintExample()


        transparent = TransparentWidget()
        transparent.setMaximumWidth(1000)

        # Use a 1x1 Grid layout to allow free placement of the widgets
        layout = QGridLayout()
        #layout.addWidget(web, 0, 0, Qt.AlignLeft)
        #layout.addWidget(web2, 0, 0, Qt.AlignLeft)
        #layout.addWidget(transparent, 0, 0, Qt.AlignLeft)
        layout.addWidget(paint, 0, 0, Qt.AlignRight)
        layout.addWidget(graphics_view, 0, 0, Qt.AlignLeft)


        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)



        #self.setCentralWidget(web)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())

