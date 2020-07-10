from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *
import sys


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.showFullScreen()

        self.initUI()

        self.show()

    def initUI(self):
        web = QWebEngineView()
        web.setMaximumHeight(1000)
        web.setMaximumWidth(1000)
        web.load(QUrl('https://maps.google.com'))

        self.setCentralWidget(web)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())

