
# Based on https://answers.opencv.org/question/202017/how-to-use-gstreamer-pipeline-in-opencv/

import cv2

from sensors.cameras.realsenseD435.realsense_D435_camera import RealsenseD435Camera


def send():
    camera = RealsenseD435Camera()
    camera.start()

    out_send = cv2.VideoWriter('appsrc ! videoconvert ! x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! rtph264pay ! udpsink host=127.0.0.1 port=5000',cv2.CAP_GSTREAMER, 0, 30, (1280, 720), True)

    if not out_send.isOpened():
        print('VideoCapture or VideoWriter not opened')
        exit(0)

    while True:
        color_image, depth_image = camera.get_frames()

        if color_image is None:
            print('empty frame')
        else:
            out_send.write(color_image)

            cv2.imshow('send', color_image)
        if cv2.waitKey(1)&0xFF == ord('q'):
            break

    out_send.release()


send()
