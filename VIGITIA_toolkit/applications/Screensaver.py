import os

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from VIGITIA_toolkit.core.VIGITIABaseApplication import VIGITIABaseApplication


class Screensaver(QVideoWidget, VIGITIABaseApplication):

    # It needs to receive the rendering manager as an argument
    def __init__(self, rendering_manager):
        super().__init__()  # Init the super class
        self.set_name(self.__class__.__name__)  # Register the application with their name
        self.set_rendering_manager(rendering_manager)  # Register the rendering manager

        self.x = 2500
        self.y = 1000
        self.width = 1920
        self.height = 1080
        self.z_index = 10000

        self.setStyleSheet('border: 1px solid #0000FF;')

        self.init_video_player()

    def init_video_player(self):
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.mediaPlayer.setVideoOutput(self)
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__), "earth.mp4"))
        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))

        self.mediaPlayer.play()

    # def init_video_player(self):
    #     self.layout = QVBoxLayout()
    #     self.setLayout(self.layout)
    #
    #     self.videoWidget = QVideoWidget()
    #     self.layout.addWidget(self.videoWidget)
    #
    #     self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
    #     self.mediaPlayer.setVideoOutput(self.videoWidget)
    #     filename = os.path.abspath(os.path.join(os.path.dirname(__file__), "earth.mp4"))
    #     self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))

        #self.mediaPlayer.play()

    def on_key_pressed(self, event):
        if event.key() == Qt.Key_P:
            print('Play')
            self.mediaPlayer.play()
