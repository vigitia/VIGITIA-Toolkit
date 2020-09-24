# Source: https://stackoverflow.com/questions/58020983/rotate-the-widget-for-some-degree

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QUrl, QRect, QPoint, QSize
from PyQt5.QtGui import QPixmap, QRegion
from PyQt5.QtWebEngineWidgets import QWebEngineView


from PyQt5 import QtCore, QtGui, QtWidgets

from applications.pyqt_paint_example import PaintExample
from applications.BrowserWidget import BrowserWidget


def main():
    import sys

    app = QtWidgets.QApplication(sys.argv)

    graphicsview = QtWidgets.QGraphicsView()
    scene = QtWidgets.QGraphicsScene(graphicsview)
    graphicsview.setScene(scene)

    application = BrowserWidget()

    proxy = QtWidgets.QGraphicsProxyWidget()
    proxy.setWidget(application)
    proxy.setTransformOriginPoint(proxy.boundingRect().center())
    scene.addItem(proxy)

    slider = QtWidgets.QSlider(minimum=0, maximum=359, orientation=QtCore.Qt.Horizontal)
    slider.valueChanged.connect(proxy.setRotation)

    label_text = QtWidgets.QLabel(
        "{}°".format(slider.value()), alignment=QtCore.Qt.AlignCenter
    )
    slider.valueChanged.connect(
        lambda value: label_text.setText("{}°".format(slider.value()))
    )

    slider.setValue(45)

    w = QtWidgets.QWidget()
    lay = QtWidgets.QVBoxLayout(w)
    lay.addWidget(graphicsview)
    lay.addWidget(slider)
    lay.addWidget(label_text)
    w.resize(1500, 1000)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()