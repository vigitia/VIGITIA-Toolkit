# Source: https://stackoverflow.com/questions/58020983/rotate-the-widget-for-some-degree

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QUrl, QRect, QPoint, QSize
from PyQt5.QtGui import QPixmap, QRegion
from PyQt5.QtWebEngineWidgets import QWebEngineView


def main():
    import sys

    app = QtWidgets.QApplication(sys.argv)

    web = QWebEngineView()
    web.setMaximumWidth(1000)
    web.load(QUrl('https://maps.google.com'))

    graphics_view = QtWidgets.QGraphicsView()
    scene = QtWidgets.QGraphicsScene(graphics_view)
    graphics_view.setScene(scene)

    proxy = QtWidgets.QGraphicsProxyWidget()
    proxy.setWidget(web)
    proxy.setTransformOriginPoint(proxy.boundingRect().center())
    scene.addItem(proxy)

    proxy.setRotation(45)

    widget = QtWidgets.QWidget()
    layout = QtWidgets.QGridLayout(widget)
    layout.addWidget(graphics_view, 0, 0)
    widget.resize(1500, 1500)
    widget.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()