#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random

from PyQt5.QtCore import Qt, QUrl, QCoreApplication, QPoint, QObject, QVariant, pyqtSlot, QEvent
from PyQt5.QtGui import QMouseEvent, QKeySequence
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import QShortcut

from VIGITIA_toolkit.core.VIGITIABaseApplication import VIGITIABaseApplication

# Communication between javascript and Python based on https://gist.github.com/mphuie/63e964e9ff8ae25d16a949389392e0d7
# and https://doc.qt.io/qt-5/qtwebengine-webenginewidgets-contentmanipulation-example.html


# Exampe class to demonstrate connection between python and javascript code
class CallHandler(QObject):

    @pyqtSlot(result=QVariant)
    def sent_message_to_javascript(self):
        print('call received')
        return QVariant({"abc": "def", "ab": 22})

    # take an argument from javascript - JS:  handler.test1('hello!')
    @pyqtSlot(QVariant, result=QVariant)
    def message_from_javascript(self, args):
        print('Message from JavaScript to Python:', args)
        return "ok"


class BrowserWidget(QWebEngineView, VIGITIABaseApplication):
    """ BrowserWidget

        Example application demonstrating how to display Webpages and local HTML Files on the table

    """

    # Flag to toggle visibility
    is_hidden = False

    def __init__(self, rendering_manager):
        super().__init__()
        self.set_name(self.__class__.__name__)
        self.set_rendering_manager(rendering_manager)

        self.x = 2500
        self.y = 1000
        self.width = 1920
        self.height = 1080
        self.rotation = 0
        self.z_index = 100

        # Prevent ESC from beeing blocked by BrowserWidget
        # https://stackoverflow.com/questions/56890831/qwidget-cannot-catch-escape-backspace-or-c-x-key-press-events
        QShortcut(QKeySequence("Escape"), self, activated=self.on_Escape)

        self.initUI()

        # Uncomment this line to establish connection to js code
        # self.connect_to_javascript_code()

        # Define url or local index.html path here
        url = QUrl('https://maps.google.com')
        # Explanation on how to load a local HTML page
        # url = QUrl.fromLocalFile(os.path.abspath(os.path.join(os.path.dirname(__file__), "index.html")))

        self.load(url)

    def connect_to_javascript_code(self):
        self.channel = QWebChannel()
        self.handler = CallHandler()
        self.channel.registerObject('handler', self.handler)
        self.page().setWebChannel(self.channel)
        self.loadFinished.connect(self.loadFinishedHandler)

    def initUI(self):
        pass
        #self.setGeometry(0, 0, self.width, self.height)

    @pyqtSlot()
    def loadFinishedHandler(self):
        # Example on how to call a function in the javascript code of a website
        js_code = 'pythonToJS("I am a message from python");'
        self.page().runJavaScript(js_code, self.js_callback)

    def js_callback(self, result):
        print('Python called back:', result)

    def on_new_token_messages(self, data):
        # print('Tokens:', data)
        for token in data:
            if token['component_id'] == 4:
                angle = token['angle']
                self.set_rotation(angle)
                #self.set_position(token['x_pos'], token['y_pos'])
                #self.set_x(token['x_pos'])
                #self.set_y(token['y_pos'])

    def on_key_pressed(self, event):
        if event.key() == Qt.Key_F1:
            #self.set_rotation(self.rotation + 10)
            self.set_rotation(random.randint(0, 359))
        if event.key() == Qt.Key_F2:
            #self.set_position(self.get_x() - 10, self.get_y())
            self.set_position(1845, 750)

    # Use Touch events in the application: Convert the pointer messages to mouse click events
    def on_new_pointer_messages(self, messages):
        for message in messages:

            global_pos = QPoint(message['x_pos'], message['y_pos'])
            local_pos = self.mapFromGlobal(global_pos)

            #target = self.focusProxy()
            target = self

            self.emulate_mouse_event(QEvent.MouseMove, local_pos, global_pos, target)
            self.emulate_mouse_event(QEvent.MouseButtonPress, local_pos, global_pos, target)

    def on_new_control_messages(self, data):
        pass
        # Show/hide video
        # if data[2] == 3 and data[3] == 1:
        #     self.is_hidden = not self.is_hidden
        #
        # if self.is_hidden:
        #     self.hide()
        # else:
        #     self.show()

    #
    def emulate_mouse_event(self, event_type, local_pos, global_pos, target):
        mouse_event = QMouseEvent(event_type, local_pos, global_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        try:
            QCoreApplication.sendEvent(target, mouse_event)
        except:
            print('[BrowserWidget]: Error on injecting Touch Event in BrowserWidget')

    @pyqtSlot()
    def on_Escape(self):
        self.rendering_manager.close_window()
