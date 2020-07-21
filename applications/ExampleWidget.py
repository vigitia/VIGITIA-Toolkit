
# Example for a custom Widget with a transparent background

import random
import sys

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QMouseEvent, QPainter, QPen, QBrush
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel

from apps.vigitia_application import VIGITIAApplication


class ExampleWidget(QWidget, VIGITIAApplication):

    def __init__(self):
        super().__init__()

        self.x = 1500
        self.y = 100
        self.width = 500
        self.height = 400

        # Make window frameless
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        # Make background transparent
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color:transparent;")

        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, self.width, self.height)

        self.button = QPushButton("Button1")
        self.button.clicked.connect(self.onButtonClicked)

        self.label_1 = QLabel('Light green', self)
        self.label_1.move(100, 100)
        self.label_1.setStyleSheet("background-color: lightgreen")

        window_layout = QVBoxLayout()
        window_layout.addWidget(self.button)
        self.setLayout(window_layout)

        self.show()

        #self.grab().save('test.jpg')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(Qt.black, 10, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.yellow, Qt.SolidPattern))
        painter.drawRect(40, 40, 400, 200)

    def keyPressEvent(self, event):

        # Inject a touch event at the current mouse cursor pos if "1" is pressed on the keyboard
        if event.key() == Qt.Key_Control:
            touch_x = self.cursor().pos().x()
            touch_y = self.cursor().pos().y()

            global_pos = QPoint(touch_x, touch_y)
            # local_pos = self.web.mapFromGlobal(global_pos)
            local_pos = self.button.mapFromGlobal(global_pos)
            print('global to local:', self.mapFromGlobal(global_pos))

            #target = self.web.focusProxy()
            target = self.button

            self.emulate_mouse_event(QtCore.QEvent.MouseMove, local_pos, global_pos, target)
            self.emulate_mouse_event(QtCore.QEvent.MouseButtonPress, local_pos, global_pos, target)

    def emulate_mouse_event(self, event_type, local_pos, global_pos, target):
        mouse_event = QMouseEvent(event_type, local_pos, global_pos, QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier)
        QtCore.QCoreApplication.sendEvent(target, mouse_event)

    # handler for the signal aka slot
    def onButtonClicked(self):
        print('Button clicked')

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            print('Mouse Press ( %d, %d )' % (event.x(), event.y()))
            #self.cursor().setPos(self.mapToGlobal(QPoint(event.x(), event.y())))

            # If mouse pressed on label, change color
            if self.label_1.pos().x() <= event.x() <= self.label_1.pos().x() + self.label_1.width():
                if self.label_1.pos().y() <= event.y() <= self.label_1.pos().y() + self.label_1.height():

                    colors = ['blue', 'green', 'red']
                    color = random.choice(colors)

                    self.label_1.setStyleSheet("background-color: " + color)

    def mouseReleaseEvent(self, event):
        print('Mouse released: ( %d, %d )' % (event.x(), event.y()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ExampleWidget()
    sys.exit(app.exec_())
