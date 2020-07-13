import sys
from PyQt5 import uic
from PyQt5.QtCore import Qt, QUrl, QCoreApplication, QPoint, QEvent
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout

from pyQT5_experiments.demo_tuio_inteface import DataInterface


class BrowserWidget(QMainWindow):
    def __init__(self):
        super().__init__()  # Call the inherited classes __init__ method

        self.left = 0
        self.top = 0
        self.width = 2000
        self.height = 1000

        self.setGeometry(self.left, self.top, self.width, self.height)

        self.web = QWebEngineView()
        self.web.load(QUrl('https://maps.google.de'))

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.web)

        data_interface = DataInterface()
        data_interface.register_subscriber(self)

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BrowserWidget()
    window.show()
    sys.exit(app.exec_())
