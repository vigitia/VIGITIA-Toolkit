
# Based on https://answers.opencv.org/question/202017/how-to-use-gstreamer-pipeline-in-opencv/

import sys
import cv2
import threading


class VIGITIAVideoStreamReceiver:

    frame = None

    def __init__(self, port=5000):
        pipeline = 'udpsrc port={} caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96" ! rtph264depay ! decodebin ! videoconvert ! appsink'.format(str(port))
        self.capture_receive = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

        self.started = False
        self.read_lock = threading.Lock()

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

        if not self.capture_receive.isOpened():
            print('VideoCapture not opened')
            exit(0)

        while True:
            ret, frame = self.capture_receive.read()

            if frame is not None:
                with self.read_lock:
                    self.frame = frame

                cv2.imshow('receive', frame)
                if cv2.waitKey(1)&0xFF == ord('q'):
                    break

    def get_frame(self):
        with self.read_lock:
            return self.frame

    def stop(self):
        self.started = False
        self.thread.join()

    def __exit__(self, exec_type, exc_value, traceback):
        self.pipeline.stop()


def main():
    receiver = VIGITIAVideoStreamReceiver()
    receiver.start()
    sys.exit()


if __name__ == '__main__':
    main()
