
# Based on https://answers.opencv.org/question/202017/how-to-use-gstreamer-pipeline-in-opencv/
import sys

import cv2


class VIGITIAVideoStreamReceiver:

    def __init__(self, port=5000):
        pipeline = 'udpsrc port={} caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96" ! rtph264depay ! decodebin ! videoconvert ! appsink'.format(str(port))
        self.capture_receive = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

        self.receive()

    def receive(self):

        if not self.capture_receive.isOpened():
            print('VideoCapture not opened')
            exit(0)

        while True:
            ret, frame = self.capture_receive.read()

            if not ret:
                print('empty frame')
                break

            cv2.imshow('receive', frame)
            if cv2.waitKey(1)&0xFF == ord('q'):
                break

        self.capture_receive.release()


def main():
    VIGITIAVideoStreamReceiver()
    sys.exit()


if __name__ == '__main__':
    main()
