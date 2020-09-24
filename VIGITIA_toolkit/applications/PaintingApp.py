

# Based on https://www.geeksforgeeks.org/pyqt5-create-paint-application/

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from VIGITIA_toolkit.core.VIGITIABaseApplication import VIGITIABaseApplication


class PaintingWidget(QMainWindow, VIGITIABaseApplication):
    def __init__(self, rendering_manager):
        super().__init__()
        self.set_name(self.__class__.__name__)
        self.set_rendering_manager(rendering_manager)

        self.set_z_index(1000)

        self.brushes = []
        self.present_markers = []

        self.initUI()

        # drawing flag
        self.drawing = False

        self.show_touch_points = True

        self.brushSize = 100
        self.brushColor = Qt.green

        # QPoint object to tract the point
        self.lastPoint = QPoint()

    def initUI(self):
        # setting geometry to main window
        self.setGeometry(0, 0, self.get_width(), self.get_height())

        self.reset_image()

    def reset_image(self):
        self.image = QImage(self.size(), QImage.Format_ARGB32)
        self.image.fill(Qt.transparent)

    def on_new_token_messages(self, messages):
        try:
            self.update_touch_points(messages)

            painter = QPainter(self.image)
            for brush in self.brushes:

                # set the pen of the painter
                if brush.get_color() is not None:
                    painter.setPen(QPen(brush.get_color(), 20))
                    # painter.setPen(QPen(brush.get_color(), self.brushSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

                    #painter.drawPoint(brush.get_pos(self))
                    painter.drawEllipse(brush.get_pos(self), self.brushSize, self.brushSize)

            self.update()
        except AttributeError:
            # TODO: Fix Function called before initUI()
            pass

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

    def on_new_pointer_messages(self, messages):
        try:
            if not self.show_touch_points:
                return
        except AttributeError:
            return
            # TODO: FIX function called before class has been initialized

        painter = QPainter(self.image)
        painter.setPen(QPen(Qt.green, 30, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        for message in messages:
            #painter.drawPoint(self.get_pos(message['x_pos'], message['y_pos']))
            painter.drawPoint(message['x_pos'], message['y_pos'])

        self.update()

            # global_pos = QPoint(int(touch_x / 1280 * 2560), int(touch_y / 720 * 1440))
            # local_pos = self.mapFromGlobal(global_pos)
            #
            # # target = self.focusProxy()
            # target = self
            #
            # print(global_pos)
            # self.emulate_mouse_event(QEvent.MouseMove, local_pos, global_pos, target)
            # self.emulate_mouse_event(QEvent.MouseButtonPress, local_pos, global_pos, target)

    def on_new_control_messages(self, data):
        print('control message in painting app', data)

        # Clear canvas
        if data[2] == 0 and data[3] == 1:
            self.reset_image()

        # Toggle flag 'show_touch_points'
        if data[2] == 1 and data[3] == 1:
            self.show_touch_points = not self.show_touch_points

    def get_pos(self, x, y):
        #     CAMERA_RES_X = 1280
        #     CAMERA_RES_Y = 720
        #     CANVAS_RES_X = 2560
        #     CANVAS_RES_Y = 1440
        #     global_pos = QPoint(int(x / CAMERA_RES_X * CANVAS_RES_X), int(y / CAMERA_RES_Y * CANVAS_RES_Y))
        global_pos = QPoint(x, y)
        local_pos = self.mapFromGlobal(global_pos)

        return local_pos

    def emulate_mouse_event(self, event_type, local_pos, global_pos, target):
        #print('Emulating MouseEvent')
        mouse_event = QMouseEvent(event_type, local_pos, global_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QCoreApplication.sendEvent(target, mouse_event)

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
            marker_id = message['session_id']
            if marker_id == 40:
                continue
            touch_x = message['x_pos']
            touch_y = message['y_pos']
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
                    try:
                        del self.brushes[i]
                    except IndexError:
                        pass


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
        # CAMERA_RES_X = 1280
        # CAMERA_RES_Y = 720
        # CANVAS_RES_X = 2560
        # CANVAS_RES_Y = 1440
        # global_pos = QPoint(int(self.x / CAMERA_RES_X * CANVAS_RES_X), int(self.y / CAMERA_RES_Y * CANVAS_RES_Y))
        global_pos = QPoint(self.x, self.y)
        local_pos = widget.mapFromGlobal(global_pos)

        return local_pos

    def __repr__(self):
        return 'PaintBrush: ' + str(self.marker_id)
