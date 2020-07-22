# coding: utf-8

# Based on: https://github.com/r9y9/pylibfreenect2/blob/master/examples/multiframe_listener.py

# Before starting:  export LD_LIBRARY_PATH=$HOME/freenect2/lib


import numpy as np
import cv2
import sys
from pylibfreenect2 import Freenect2, SyncMultiFrameListener
from pylibfreenect2 import FrameType, Registration, Frame
from pylibfreenect2 import createConsoleLogger, setGlobalLogger
from pylibfreenect2 import LoggerLevel

try:
    from pylibfreenect2 import OpenGLPacketPipeline
    pipeline = OpenGLPacketPipeline()
except:
    try:
        from pylibfreenect2 import OpenCLPacketPipeline
        pipeline = OpenCLPacketPipeline()
    except:
        from pylibfreenect2 import CpuPacketPipeline
        pipeline = CpuPacketPipeline()
print("Packet pipeline:", type(pipeline).__name__)


FRAMES_TO_WAIT_WARM_UP = 100

DEBUG_MODE = True


class KinectV2:

    # Optional parameters for registration. Set True if you need
    need_color_depth_map = False

    current_frame = 0

    def __init__(self):

        # Create and set logger
        logger = createConsoleLogger(LoggerLevel.Debug)
        setGlobalLogger(logger)

        fn = Freenect2()
        num_devices = fn.enumerateDevices()
        if num_devices == 0:
            print("No device connected!")
            sys.exit(1)

        serial = fn.getDeviceSerialNumber(0)
        self.device = fn.openDevice(serial, pipeline=pipeline)

        self.listener = SyncMultiFrameListener(FrameType.Color | FrameType.Ir | FrameType.Depth)

        # Register listeners
        self.device.setColorFrameListener(self.listener)
        self.device.setIrAndDepthFrameListener(self.listener)

        self.device.start()

        # NOTE: must be called after device.start()
        self.registration = Registration(self.device.getIrCameraParams(),
                                         self.device.getColorCameraParams())

        self.undistorted = Frame(512, 424, 4)
        self.registered = Frame(512, 424, 4)
        self.bigdepth = Frame(1920, 1082, 4)

        self.color_depth_map = np.zeros((424, 512), np.int32).ravel() \
            if self.need_color_depth_map else None

        self.take_picture()

    def take_picture(self):
        while True:
            self.current_frame += 1
            print('Frame:', self.current_frame)

            frames = self.listener.waitForNewFrame()

            color = frames["color"]
            ir = frames["ir"]
            depth = frames["depth"]

            # print(depth.asarray()[212][256] /10, "cm")

            self.registration.apply(color, depth, self.undistorted, self.registered, bigdepth=self.bigdepth,
                                    color_depth_map=self.color_depth_map)

            print(depth.asarray()[200, 200])
            print(self.bigdepth.asarray(np.float32)[200, 200])

            if DEBUG_MODE:
                cv2.imshow("kinectv2_ir.png", ir.asarray() / 65535.)
                cv2.imshow("kinectv2_depth.png", depth.asarray() / 4500.)
                cv2.imshow("kinectv2_color.png", cv2.resize(color.asarray(),
                                                            (int(1920 / 3), int(1080 / 3))))
                cv2.imshow("kinectv2_registered.png", self.registered.asarray(np.uint8))
                cv2.imshow("kinectv2_bigdepth.png", cv2.resize(self.bigdepth.asarray(np.float32),
                                                               (int(1920 / 3), int(1082 / 3))))
                if self.need_color_depth_map:
                    cv2.imshow("kinectv2_color_depth_map.png", self.color_depth_map.reshape(424, 512))

                key = cv2.waitKey(delay=1)
                if key == ord('q'):
                    break
            else:
                if self.current_frame == FRAMES_TO_WAIT_WARM_UP:

                    cv2.imwrite("kinectv2_ir.png", ir.asarray() / 65535.)
                    cv2.imwrite("kinectv2_depth.png", depth.asarray() / 4500.)
                    cv2.imwrite("kinectv2_color.png", color.asarray())
                    cv2.imwrite("kinectv2_registered.png", self.registered.asarray(np.uint8))
                    cv2.imwrite("kinectv2_bigdepth.png", self.bigdepth.asarray(np.float32))

                    if self.need_color_depth_map:
                        cv2.imwrite("kinectv2_color_depth_map.png", self.color_depth_map.reshape(424, 512))

                    print('[Kinect V2]: Pictures taken')

                    return True

            self.listener.release(frames)

        self.device.stop()
        self.device.close()

        return False


if __name__ == '__main__':
    KinectV2()
