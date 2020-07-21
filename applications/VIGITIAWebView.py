

import os
from PyQt5.QtCore import Qt, QUrl, QCoreApplication, QPoint, QEvent, QObject, QVariant, pyqtSlot
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import *

from pyQT5_experiments.demo_tuio_inteface import DataInterface

from apps.vigitia_application import VIGITIAApplication

# Communication between javascript and Python based on https://gist.github.com/mphuie/63e964e9ff8ae25d16a949389392e0d7
# and https://doc.qt.io/qt-5/qtwebengine-webenginewidgets-contentmanipulation-example.html

class CallHandler(QObject):

    @pyqtSlot(result=QVariant)
    def test(self):
        print('call received')
        return QVariant({"abc": "def", "ab": 22})

    # take an argument from javascript - JS:  handler.test1('hello!')
    @pyqtSlot(QVariant, result=QVariant)
    def message_from_javascript(self, args):
        print('Message from JavaScript to Python:', args)
        return "ok"


#class BrowserWidget(QWebEngineView):
class BrowserWidget(QWebEngineView, VIGITIAApplication):
    def __init__(self):
        super().__init__()

        self.x = 500
        self.y = 600
        self.width = 800
        self.height = 600

        self.setGeometry(0, 0, self.width, self.height)


        self.channel = QWebChannel()
        self.handler = CallHandler()
        self.channel.registerObject('handler', self.handler)
        self.page().setWebChannel(self.channel)

        self.loadFinished.connect(self.loadFinishedHandler)

        web_url = QUrl('https://maps.google.com')
        #local_html_url = QUrl.fromLocalFile(os.path.abspath(os.path.join(os.path.dirname(__file__), "index.html")))

        self.load(web_url)

        #layout = QVBoxLayout()
        #self.setLayout(layout)
        #layout.addWidget(self.web)

        #data_interface = DataInterface()
        #data_interface.register_subscriber(self)

    @pyqtSlot()
    def loadFinishedHandler(self):
        print("load finished")
        js_code = 'pythonToJS("I am a message from python");'
        self.page().runJavaScript(js_code, self.js_callback)

    def js_callback(self, result):
        print('Python called back:', result)

    def on_new_data(self, data):
        print('Data arrived:', data)

        global_pos = QPoint(int(data[4] / 1280 * 2560), int(data[5] / 720 * 1440))
        local_pos = self.mapFromGlobal(global_pos)

        target = self.focusProxy()

        print(global_pos)

        #self.emulate_mouse_event(QEvent.MouseMove, local_pos, global_pos, target)
        #self.emulate_mouse_event(QEvent.MouseButtonPress, local_pos, global_pos, target)

    def emulate_mouse_event(self, event_type, local_pos, global_pos, target):
        mouse_event = QMouseEvent(event_type, local_pos, global_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QCoreApplication.sendEvent(target, mouse_event)

    # def keyPressEvent(self, event):
    #     if event.key() == Qt.Key_Escape:
    #         self.close()


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = BrowserWidget()
#     window.show()
#     sys.exit(app.exec_())
