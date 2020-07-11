
# Example for a custom Widget with a transparent background

import sys
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton


class TransparentWidget(QWidget):

    def __init__(self):
        super().__init__()

        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480

        # Make window frameless
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        # Make background transparent
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color:transparent;")

        self.initUI()

    def initUI(self):
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.button = QPushButton("Button1")

        window_layout = QVBoxLayout()
        window_layout.addWidget(self.button)
        self.setLayout(window_layout)

        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TransparentWidget()
    sys.exit(app.exec_())
