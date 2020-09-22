
# Example for a custom Widget with a transparent background
import os
import random
import sys

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel

from apps.VIGITIABaseApplication import VIGITIABaseApplication


class ButtonWidget(QWidget, VIGITIABaseApplication):

    def __init__(self, rendering_manager):
        super().__init__()
        self.set_name(self.__class__.__name__)
        self.set_rendering_manager(rendering_manager)

        self.x = self.get_screen_resolution()[0]/5
        self.y = self.get_screen_resolution()[1]/5
        self.width = 200
        self.height = 200
        self.rotation = 0

        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, self.get_width(), self.get_height())
        self.setStyleSheet("background-color:transparent;")

        self.label_1 = QLabel('', self)
        self.label_1.resize(self.width, self.width)
        self.label_1.setStyleSheet("background-color: red")

        window_layout = QVBoxLayout()
        window_layout.addWidget(self.label_1, Qt.AlignCenter)
        self.setLayout(window_layout)

        #self.grab().save('test.jpg')

    # def paintEvent(self, event):
    #     painter = QPainter(self)
    #     painter.setPen(QPen(Qt.black, 10, Qt.SolidLine))
    #     painter.setBrush(QBrush(Qt.yellow, Qt.SolidPattern))
    #     painter.drawRect(40, 40, 400, 200)

    def on_new_pointer_messages(self, data):
        for message in data:
            print(message)
            local_pos = self.mapFromGlobal(QPoint(message['x_pos'], message['y_pos']))

            if self.label_1.pos().x() <= local_pos.x() <= self.label_1.pos().x() + self.label_1.width():
                if self.label_1.pos().y() <= local_pos.y() <= self.label_1.pos().y() + self.label_1.height():
                    colors = ['blue', 'green', 'red', 'brown', 'DarkGreen', 'DarkMagenta']
                    color = random.choice(colors)

                    self.label_1.setStyleSheet("background-color: " + color)

    def get_pos(self, x, y):
        CAMERA_RES_X = 1280
        CAMERA_RES_Y = 720
        CANVAS_RES_X = 2560
        CANVAS_RES_Y = 1440
        global_pos = QPoint(int(x / CAMERA_RES_X * CANVAS_RES_X), int(y / CAMERA_RES_Y * CANVAS_RES_Y))
        local_pos = self.mapFromGlobal(global_pos)

        return local_pos, global_pos

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
        colors = ['blue', 'green', 'red', 'yellow', 'orange', 'brown']
        color = random.choice(colors)

        self.button.setStyleSheet("background-color: " + color)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            print('Mouse Press ( %d, %d )' % (event.x(), event.y()))
            #self.cursor().setPos(self.mapToGlobal(QPoint(event.x(), event.y())))

            # If mouse pressed on label, change color
            if self.label_1.pos().x() <= event.x() <= self.label_1.pos().x() + self.label_1.width():
                if self.label_1.pos().y() <= event.y() <= self.label_1.pos().y() + self.label_1.height():

                    colors = ['blue', 'red', 'orange', 'brown']
                    color = random.choice(colors)

                    self.label_1.setStyleSheet("background-color: " + color)

    def mouseReleaseEvent(self, event):
        print('Mouse released: ( %d, %d )' % (event.x(), event.y()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ButtonWidget()
    sys.exit(app.exec_())
