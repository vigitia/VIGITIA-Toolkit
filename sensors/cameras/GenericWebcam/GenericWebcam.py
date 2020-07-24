#!/usr/bin/env
# coding: utf-8

# Code parts for asynchronous video capture taken from
# http://blog.blitzblit.com/2017/12/24/asynchronous-video-capture-in-python-with-opencv/

import cv2
import threading


class GenericWebcam:

    frame = None

    def __init__(self, camera_id=0, resolution_x=1920, resolution_y=720, fps=30):
        self.init_opencv_video_capture(camera_id, resolution_x, resolution_y, fps)

        self.started = False
        self.read_lock = threading.Lock()

    def init_opencv_video_capture(self, camera_id, resolution_x, resolution_y, fps):
        self.capture = cv2.VideoCapture(camera_id)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, resolution_x)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution_y)
        self.capture.set(cv2.CAP_PROP_FPS, fps)

    def start(self):
        if self.started:
            print('Already running')
            return None
        else:
            self.started = True
            self.thread = threading.Thread(target=self.update, args=())
            # thread.daemon = True
            self.thread.start()
            return self

    def update(self):

        while self.started:
            ret, frame = self.capture.read()

            if frame is not None:
                with self.read_lock:
                    self.frame = frame

    def get_frames(self):
        with self.read_lock:
            return self.frame

    def stop(self):
        self.started = False
        self.thread.join()

    def __exit__(self, exec_type, exc_value, traceback):
        self.capture.release()



# webcam = GenericWebcam()
# webcam.start()
#
# while True:
#     frame = webcam.get_frames()
#     if frame is not None:
#         cv2.imshow('webcam', frame)
#
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
# cv2.destroyAllWindows()