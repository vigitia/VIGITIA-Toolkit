
# Based on https://answers.opencv.org/question/202017/how-to-use-gstreamer-pipeline-in-opencv/

import cv2
import threading


class VIGITIAVideoStreamReceiver:

    frame = None

    def __init__(self, name='Video Stream', origin_ip='', port=5000):
        self.name = name
        self.origin_ip = origin_ip
        self.port = str(port)
        self.pipeline = 'udpsrc port={} caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, ' \
                   'encoding-name=(string)H264, payload=(int)96" ! rtph264depay ! decodebin ! videoconvert ! ' \
                   'appsink'.format(self.port)

        self.subscribers = set()

        self.started = False

    def register_subscriber(self, new_subscriber):
        # print('[VIGITIAVideoStreamReceiver]: New Subscriber:', new_subscriber.__class__.__name__)
        self.subscribers.add(new_subscriber)

    def unregister_subscriber(self, subscriber):
        self.subscribers.discard(subscriber)

    def start(self):
        if self.started:
            print('[VIGITIAVideoStreamReceiver]: Already running')
            return None
        else:
            self.started = True
            self.thread = threading.Thread(target=self.update, args=())
            self.thread.start()
            return self

    def update(self):
        self.capture_receive = cv2.VideoCapture(self.pipeline, cv2.CAP_GSTREAMER)

        if not self.capture_receive.isOpened():
            print('[VIGITIAVideoStreamReceiver]: Error: VideoCapture not opened')
            exit(0)

        while True:
            ret, frame = self.capture_receive.read()
            print('New frame received')

            if frame is not None:
                for subscriber in self.subscribers:
                    subscriber.on_new_video_frame(frame, self.name, self.origin_ip, self.port)

    def stop(self):
        self.started = False
        self.thread.join()

    def __exit__(self, exec_type, exc_value, traceback):
        self.capture_receive.release()
