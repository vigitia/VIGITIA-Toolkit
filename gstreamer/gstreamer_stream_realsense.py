import cv2
from sensors.cameras.realsenseD435.realsense_D435_camera import RealsenseD435Camera




def send():
    camera = RealsenseD435Camera()
    camera.start()

    #cap_send = cv2.VideoCapture('videotestsrc ! video/x-raw,framerate=20/1 ! videoscale ! videoconvert ! appsink', cv2.CAP_GSTREAMER)
    # videotestsrc pattern=smpte ! "video/x-raw,format=BGRx,width=1280,height=720" ! jpegenc ! rtpgstpay config-interval=1 ! udpsink host=127.0.0.1 port=5000
    # gst-launch-1.0 -e v4l2src device=/dev/video0 ! image/jpeg,width=1280,height=720,framerate=30/1 ! rtpgstpay config-interval=1 ! udpsink host=127.0.0.1 port=5001
    out_send = cv2.VideoWriter('appsrc ! videoconvert ! x264enc tune=zerolatency bitrate=500 speed-preset=superfast ! rtph264pay ! udpsink host=127.0.0.1 port=5000',cv2.CAP_V4L2,0, 20, (320,240), True)

    if not out_send.isOpened():
        print('VideoCapture or VideoWriter not opened')
        exit(0)

    while True:
        color_image, depth_image = camera.get_frames()

        if color_image is None:
            print('empty frame')
        else:

            cv2.imshow('send', color_image)
            out_send.write(color_image)

        if cv2.waitKey(1)&0xFF == ord('q'):
            break

    #cap_send.release()
    out_send.release()

send()