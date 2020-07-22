

# Based on https://www.geeksforgeeks.org/pyqt5-create-paint-application/

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys

from apps.vigitia_application import VIGITIAApplication


class VIGITIAPaintingApp(QMainWindow, VIGITIAApplication):
    def __init__(self):
        super().__init__()
        self.x = 0
        self.y = 100
        self.width = 800
        self.height = 400
        self.rotation = 0

        # setting geometry to main window
        self.setGeometry(0, 0, self.width, self.height)

        self.image = QImage(self.size(), QImage.Format_ARGB32)
        self.image.fill(Qt.transparent)
        # drawing flag
        self.drawing = False

        self.brushSize = 2
        self.brushColor = Qt.green

        # QPoint object to tract the point
        self.lastPoint = QPoint()


    def mousePressEvent(self, event):
        # if left mouse button is pressed
        if event.button() == Qt.LeftButton:
            # make drawing flag true
            self.drawing = True
            # make last point to the point of cursor
            self.lastPoint = event.pos()


    def mouseMoveEvent(self, event):

        # checking if left button is pressed and drawing flag is true
        if (event.buttons() & Qt.LeftButton) & self.drawing:
            # creating painter object
            painter = QPainter(self.image)

            # set the pen of the painter
            painter.setPen(QPen(self.brushColor, self.brushSize,
                                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

            # draw line from the last point of cursor to the current point
            # this will draw only one step
            painter.drawLine(self.lastPoint, event.pos())

            # change the last point
            self.lastPoint = event.pos()
            # update
            self.update()

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.LeftButton:
            # make drawing flag false
            self.drawing = False

    # paint event
    def paintEvent(self, event):
        # create a canvas
        canvasPainter = QPainter(self)

        # draw rectangle  on the canvas
        canvasPainter.drawImage(self.rect(), self.image, self.image.rect())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VIGITIAPaintingApp()
    window.show()
    sys.exit(app.exec_())
