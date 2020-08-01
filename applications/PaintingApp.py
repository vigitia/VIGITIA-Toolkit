

# Based on https://www.geeksforgeeks.org/pyqt5-create-paint-application/

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys

from apps.VIGITIABaseApplication import VIGITIABaseApplication

from pyQT5_experiments.VIGITIASensorDataInterface import VIGITIASensorDataInterface


# class VIGITIAPaintingApp(QMainWindow):
class VIGITIAPaintingApp(QMainWindow, VIGITIABaseApplication):
    def __init__(self):
        super().__init__()
        self.x = 0
        self.y = 0
        self.width = 2560
        self.height = 1440
        self.rotation = 0

        self.brushes = []

        self.present_markers = []

        # setting geometry to main window
        self.setGeometry(0, 0, self.width, self.height)

        self.image = QImage(self.size(), QImage.Format_ARGB32)
        self.image.fill(Qt.transparent)
        # drawing flag
        self.drawing = False

        self.brushSize = 150
        self.brushColor = Qt.green

        # QPoint object to tract the point
        self.lastPoint = QPoint()

        data_interface = VIGITIASensorDataInterface.Instance()
        data_interface.register_subscriber(self)

    def on_new_token_messages(self, messages):
        self.update_touch_points(messages)

        painter = QPainter(self.image)
        for brush in self.brushes:

            # set the pen of the painter
            painter.setPen(QPen(brush.get_color(), self.brushSize,
                                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

            painter.drawPoint(brush.get_pos(self))

        self.update()

        # for message in messages:
        #     marker_id = message[1]
        #     touch_x = message[4]
        #     touch_y = message[5]
        #
        #     print('Brushes:', self.brushes)
        #
        #     global_pos = QPoint(int(touch_x / 1280 * 2560), int(touch_y / 720 * 1440))
        #     local_pos = self.mapFromGlobal(global_pos)
        #
        #     # target = self.focusProxy()
        #     target = self
        #
        #     # print(global_pos)
        #
        #     self.emulate_mouse_event(QEvent.MouseMove, local_pos, global_pos, target)
        #     self.emulate_mouse_event(QEvent.MouseButtonPress, local_pos, global_pos, target)

    def on_new_pointer_messages(self, data):
        touch_x = data[4]
        touch_y = data[5]
        global_pos = QPoint(int(touch_x / 1280 * 2560), int(touch_y / 720 * 1440))
        local_pos = self.mapFromGlobal(global_pos)

        # target = self.focusProxy()
        target = self

        print(global_pos)

        #self.emulate_mouse_event(QEvent.MouseMove, local_pos, global_pos, target)
        #self.emulate_mouse_event(QEvent.MouseButtonPress, local_pos, global_pos, target)

    def emulate_mouse_event(self, event_type, local_pos, global_pos, target):
        #print('Emulating MouseEvent')
        mouse_event = QMouseEvent(event_type, local_pos, global_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QCoreApplication.sendEvent(target, mouse_event)

    def on_new_data(self, data):
        #print('Data arrived in Painting app:', data)
        pass

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

    def update_touch_points(self, messages):

        new_touch_point_ids = []

        for message in messages:
            marker_id = message[1]
            touch_x = message[4]
            touch_y = message[5]
            new_touch_point_ids.append(marker_id)

            found_brush = False
            for brush in self.brushes:
                if brush.marker_id == marker_id:
                    found_brush = True
                    brush.x = touch_x
                    brush.y = touch_y
                    brush.num_frames_missing = 0

            if not found_brush:
                self.brushes.append(PaintBrush(marker_id, touch_x, touch_y))

        for i, brush in enumerate(self.brushes):
            if brush.marker_id not in new_touch_point_ids:
                brush.num_frames_missing += 1

                if brush.num_frames_missing >= 30:
                    print('Brush', brush.marker_id, 'missing. Deleting it')
                    del self.brushes[i]


class PaintBrush:

    def __init__(self, marker_id, x, y):
        self.marker_id = marker_id
        self.x = x
        self.y = y

        self.num_frames_missing = 0

    def get_color(self):
        if self.marker_id == 36:
            return Qt.red
        if self.marker_id == 44:
            return Qt.yellow
        if self.marker_id == 40:
            return Qt.green
        if self.marker_id == 37:
            return Qt.magenta

    def get_pos(self, widget):
        CAMERA_RES_X = 1280
        CAMERA_RES_Y = 720
        CANVAS_RES_X = 2560
        CANVAS_RES_Y = 1440
        global_pos = QPoint(int(self.x / CAMERA_RES_X * CANVAS_RES_X), int(self.y / CAMERA_RES_Y * CANVAS_RES_Y))
        local_pos = widget.mapFromGlobal(global_pos)

        return local_pos

    def __repr__(self):
        return 'PaintBrush: ' + str(self.marker_id)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VIGITIAPaintingApp()
    window.show()
    sys.exit(app.exec_())
