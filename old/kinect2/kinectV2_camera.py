#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Based on: https://github.com/limgm/PyKinect2/blob/master/examples/basic_2D.py

# Code parts for asynchronous video capture taken from
# http://blog.blitzblit.com/2017/12/24/asynchronous-video-capture-in-python-with-opencv/

import cv2
import numpy as np
import ctypes
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectV2
from pykinect2 import PyKinectRuntime
import threading


class KinectV2Camera:

    num_frame = 0

    color_image = None
    depth_image = None
    infrared_image = None

    def __init__(self):
        # Kinect runtime object ###
        self.kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color |
                                                      PyKinectV2.FrameSourceTypes_Depth |
                                                      PyKinectV2.FrameSourceTypes_Infrared)

        # Default depth image dimensions: 512, 424
        self.depth_width, self.depth_height = self.kinect.depth_frame_desc.Width, self.kinect.depth_frame_desc.Height
        # Default color image dimensions: 1920, 1080
        self.color_width, self.color_height = self.kinect.color_frame_desc.Width, self.kinect.color_frame_desc.Height

        self.started = False
        self.read_lock = threading.Lock()

        print('Finished INIT')

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

    # Source: https://github.com/limgm/PyKinect2/blob/master/examples/utils_PyKinectV2.py
    def get_align_color_image(self, color_img, color_height=1080, color_width=1920, depth_height=424, depth_width=512):
        CSP_Count = self.kinect._depth_frame_data_capacity  # Number of pixels in the depth image (ColorSpacePoint count)
        CSP_type = _ColorSpacePoint * CSP_Count.value
        CSP = ctypes.cast(CSP_type(), ctypes.POINTER(_ColorSpacePoint))
        print(CSP_Count)

        self.kinect._mapper.MapDepthFrameToColorSpace(self.kinect._depth_frame_data_capacity, self.kinect._depth_frame_data, CSP_Count, CSP)

        # Convert ctype pointer to array
        colorXYs = np.copy(np.ctypeslib.as_array(CSP, shape=(depth_height * depth_width,)))
        # Convert struct array to regular numpy array https://stackoverflow.com/questions/5957380/convert-structured-array-to-regular-numpy-array
        colorXYs = colorXYs.view(np.float32).reshape(colorXYs.shape + (-1,))
        colorXYs += 0.5
        colorXYs = colorXYs.reshape(depth_height, depth_width, 2).astype(np.int)
        colorXs = np.clip(colorXYs[:, :, 0], 0, color_width - 1)
        colorYs = np.clip(colorXYs[:, :, 1], 0, color_height - 1)

        align_color_img = np.zeros((depth_height, depth_width, 4), dtype=np.uint8)
        align_color_img[:, :] = color_img[colorYs, colorXs, :]

        return align_color_img

    def update(self):
        a = 0
        while self.started:
            # Get images from camera
            print('a')
            if self.kinect.has_new_color_frame() and self.kinect.has_new_depth_frame() and self.kinect.has_new_infrared_frame():
                self.num_frame += 1
                print('[Kinect V2] Frame: ', self.num_frame)

                color_frame = self.kinect.get_last_color_frame()
                depth_frame = self.kinect.get_last_depth_frame()
                infrared_frame = self.kinect.get_last_infrared_frame()

                # Reshape from 1D frame to 2D image
                #color_img = color_frame.reshape((self.color_height, self.color_width, 4)).astype(np.uint8)
                depth_img = depth_frame.reshape((self.depth_height, self.depth_width)).astype(np.uint16)
                infrared_img = infrared_frame.reshape((self.depth_height, self.depth_width)).astype(np.uint16)

                #aligned_color_img = self.get_align_color_image(color_img)
                # Remove alpha channel
                #aligned_color_img = cv2.cvtColor(aligned_color_img, cv2.COLOR_BGRA2BGR)

                #depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_img, alpha=255 / 700), cv2.COLORMAP_JET)  # Scale to display from 0 mm to 700 mm
                infrared_img = cv2.convertScaleAbs(infrared_img, alpha=255 / 65535)  # Scale from uint16 to uint8

                with self.read_lock:
                    #self.color_image = aligned_color_img
                    self.depth_image = depth_img
                    self.infrared_image = infrared_img


    # Returns the requested camera frames
    # TODO: Return only the frames that are requested via params
    def get_frames(self):
        with self.read_lock:
            if self.infrared_image is not None and self.depth_image is not None:
                return self.infrared_image.copy(), self.depth_image.copy()
            else:
                return None, None

    def stop(self):
        self.started = False
        self.thread.join()

    def __exit__(self, exec_type, exc_value, traceback):
        self.kinect.close()