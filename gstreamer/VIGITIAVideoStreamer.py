
# Based on https://answers.opencv.org/question/202017/how-to-use-gstreamer-pipeline-in-opencv/

import cv2

from sensors.cameras.realsenseD435.realsense_D435_camera import RealsenseD435Camera


class VIGITIAVideoStreamer:

    def __init__(self):

        host_ip = '132.199.130.68'
        port = 5000

        pipeline = 'appsrc ! videoconvert ! x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! rtph264pay ! udpsink host={} port={}'.format(host_ip, port)
        fps = 30
        res_x = 1280
        res_y = 720

        self.video_writer = cv2.VideoWriter(pipeline, cv2.CAP_GSTREAMER, fourcc=0, fps=fps, frameSize=(res_x, res_y), isColor=True)

    def stream_frame(self, frame):
        if not self.video_writer.isOpened():
            print('VideoWriter to opened')
        else:
            self.video_writer.write(frame)
