import sys
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import QApplication, QMainWindow


class FullscreenBrowser(QMainWindow):
    def __init__(self, parent=None):
        super(FullscreenBrowser, self).__init__()  # Call the inherited classes __init__ method
        uic.loadUi('browser.ui', self)  # Load the .ui file

        self.showMaximized()
        self.initUI()

        self.show()  # Show the GUI

    def initUI(self):
        self.web = self.findChild(QWebEngineView, 'web')
        self.web.load(QUrl('https://google.de'))


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FullscreenBrowser()
    window.show()
    sys.exit(app.exec_())
