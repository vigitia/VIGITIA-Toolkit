#!/usr/bin/env
# coding: utf-8

# Open Issue: Class cant run as thread: https://github.com/r9y9/pylibfreenect2/issues/25

# Based on: https://github.com/r9y9/pylibfreenect2/blob/master/examples/multiframe_listener.py

LIBFREENECT2_LIBRARY_PATH = '/home/vigitia/freenect2/lib/libfreenect2.so'

import numpy as np
import cv2
import sys
import threading

from ctypes import *
lib = cdll.LoadLibrary(LIBFREENECT2_LIBRARY_PATH)

from pylibfreenect2 import Freenect2, SyncMultiFrameListener
from pylibfreenect2 import FrameType, Registration, Frame
from pylibfreenect2 import createConsoleLogger, setGlobalLogger
from pylibfreenect2 import LoggerLevel
try:
    from pylibfreenect2 import OpenGLPacketPipeline
    #pipeline = OpenGLPacketPipeline()
except:
    try:
        from pylibfreenect2 import OpenCLPacketPipeline
        #pipeline = OpenCLPacketPipeline()
    except:
        from pylibfreenect2 import CpuPacketPipeline
        #pipeline = CpuPacketPipeline()


FRAMES_TO_WAIT_WARM_UP = 100
DEBUG_MODE = True


class KinectV2:

    need_color_depth_map = False

    current_frame = 0

    color_frame = None
    depth_frame = None
    ir_frame = None
    registered_frame = None
    bigdepth_frame = None

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

        self.pipeline = OpenGLPacketPipeline()

        self.device = fn.openDevice(serial, pipeline=self.pipeline)

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

        self.color_depth_map = np.zeros((424, 512), np.int32).ravel() if self.need_color_depth_map else None

        #self.started = False
        #self.read_lock = threading.Lock()

        print('Finished init in kinect')

        #self.loop()

    def get_listener(self):
        return self.listener

    def start(self):
        if self.started:
            print('Already running')
            return None
        else:
            print('stared kinect thread')
            self.started = True
            self.thread = threading.Thread(target=self.update, args=())
            #self.thread.daemon = True
            self.thread.start()
            return self

    def loop(self):
        print('in kinect update')
        while self.started:
            self.current_frame += 1
            print('Frame:', self.current_frame)

            frames = self.listener.waitForNewFrame()
            print('Frames arrived')

            color = frames["color"]
            ir = frames["ir"]
            depth = frames["depth"]

            print('Distance measured at center: {} cm'.format(int(depth.asarray()[212][256] / 10)))

            self.registration.apply(color, depth, self.undistorted, self.registered, bigdepth=self.bigdepth,
                                    color_depth_map=self.color_depth_map)

            #print(depth.asarray()[200, 200])
            #print(self.bigdepth.asarray(np.float32)[200, 200])

            with self.read_lock:
                self.color_frame = color.asarray()
                self.depth_frame = depth.asarray() / 4500.
                self.ir_frame = ir.asarray() / 65535.
                self.registered_frame = self.registered.asarray(np.uint8)
                self.bigdepth_frame = self.bigdepth.asarray(np.float32)

            # if DEBUG_MODE:
            #     cv2.imshow("kinectv2_ir.png", ir.asarray() / 65535.)
            #     cv2.imshow("kinectv2_depth.png", depth.asarray() / 4500.)
            #     cv2.imshow("kinectv2_color.png", color.asarray())
            #     cv2.imshow("kinectv2_registered.png", self.registered.asarray(np.uint8))
            #     cv2.imshow("kinectv2_bigdepth.png", self.bigdepth.asarray(np.float32))
            #     if self.need_color_depth_map:
            #         cv2.imshow("kinectv2_color_depth_map.png", self.color_depth_map)
            #
            # key = cv2.waitKey(delay=1)
            # if key == ord('q'):
            #     break

            self.listener.release(frames)

        self.device.stop()
        self.device.close()

    def get_frames(self):
        with self.read_lock:
            return self.color_frame, self.depth_frame, self.ir_frame,  self.registered_frame, self.bigdepth_frame

    def stop(self):
        self.started = False
        self.thread.join()

    def __exit__(self, exec_type, exc_value, traceback):
        self.pipeline.stop()

#kinect = KinectV2()
#kinect.start()

# if __name__ == '__main__':
#     KinectV2()
