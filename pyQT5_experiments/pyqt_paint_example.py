
# Based on: https://www.learnpyqt.com/courses/custom-widgets/bitmap-graphics/

import sys
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QMouseEvent

from pyQT5_experiments.demo_tuio_inteface import DataInterface


class Canvas(QtWidgets.QLabel):

    def __init__(self):
        super().__init__()
        
        data_interface = DataInterface()
        data_interface.register_subscriber(self)
        
        pixmap = QtGui.QPixmap(2000, 1000)
        self.setPixmap(pixmap)

        self.last_x, self.last_y = None, None
        self.pen_color = QtGui.QColor('#000000')

    def on_new_data(self, data):
        #print('Data arrived:', data)

        global_pos = QPoint(int(data[4] / 1280 * 2560), int(data[5] / 720 * 1440))
        local_pos = self.mapFromGlobal(global_pos)

        self.emulate_mouse_event(QtCore.QEvent.MouseMove, local_pos, global_pos, self)
        self.emulate_mouse_event(QtCore.QEvent.MouseButtonPress, local_pos, global_pos, self)

    def emulate_mouse_event(self, event_type, local_pos, global_pos, target):
        mouse_event = QMouseEvent(event_type, local_pos, global_pos, QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier)
        QtCore.QCoreApplication.sendEvent(target, mouse_event)

    def set_pen_color(self, c):
        self.pen_color = QtGui.QColor(c)

    def mouseMoveEvent(self, e):
        if self.last_x is None: # First event.
            self.last_x = e.x()
            self.last_y = e.y()
            return  # Ignore the first time.

        painter = QtGui.QPainter(self.pixmap())
        p = painter.pen()
        p.setWidth(4)
        p.setColor(self.pen_color)
        painter.setPen(p)
        painter.drawLine(self.last_x, self.last_y, e.x(), e.y())
        painter.end()
        self.update()

        # Update the origin for next time.
        self.last_x = e.x()
        self.last_y = e.y()

    def mouseReleaseEvent(self, e):
        self.last_x = None
        self.last_y = None

COLORS = [
# 17 undertones https://lospec.com/palette-list/17undertones
'#000000', '#141923', '#414168', '#3a7fa7', '#35e3e3', '#8fd970', '#5ebb49',
'#458352', '#dcd37b', '#fffee5', '#ffd035', '#cc9245', '#a15c3e', '#a42f3b',
'#f45b7a', '#c24998', '#81588d', '#bcb0c2', '#ffffff',
]


class QPaletteButton(QtWidgets.QPushButton):

    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QtCore.QSize(24,24))
        self.color = color
        self.setStyleSheet("background-color: %s;" % color)


class PaintExample(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.canvas = Canvas()

        w = QtWidgets.QWidget()
        l = QtWidgets.QVBoxLayout()
        w.setLayout(l)
        l.addWidget(self.canvas)

        palette = QtWidgets.QHBoxLayout()
        self.add_palette_buttons(palette)
        l.addLayout(palette)

        self.setCentralWidget(w)


    def add_palette_buttons(self, layout):
        for c in COLORS:
            b = QPaletteButton(c)
            b.pressed.connect(lambda c=c: self.canvas.set_pen_color(c))
            layout.addWidget(b)


# app = QtWidgets.QApplication(sys.argv)
# window = PaintExample()
# window.show()
# app.exec_()