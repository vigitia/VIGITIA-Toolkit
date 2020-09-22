#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Code parts for asynchronous video capture taken from
# http://blog.blitzblit.com/2017/12/24/asynchronous-video-capture-in-python-with-opencv/

# Code parts for the RealSense Camera taken from
# https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/examples/align-depth2color.py
import sys

import pyrealsense2 as rs
import numpy as np
import threading

# Camera Settings
from apps.VIGITIACameraBase import VIGITIACameraBase

DEPTH_RES_X = 1280
DEPTH_RES_Y = 720
RGB_RES_X = 1280
RGB_RES_Y = 720
DEPTH_FPS = 30
RGB_FPS = 30

COLORIZER_MIN_DISTANCE = 0.5  # m
COLORIZER_MAX_DISTANCE = 1.5  # m

NUM_FRAMES_WAIT_INITIALIZING = 100  # Let the camera warm up and let the auto white balance adjust

DEBUG_MODE = False
# TODO: Add Debug mode


class RealsenseD435Camera(VIGITIACameraBase):

    num_frame = 0

    pipeline = None
    align = None
    colorizer = None

    color_image = None
    depth_image = None

    def __init__(self):

        super().__init__('Intel RealSense D435')

        self.add_video_stream('color', 'bgr8', RGB_RES_X, RGB_RES_Y, RGB_FPS,
                              'Color Stream of the Intel RealSense D435 camera')
        self.add_video_stream('depth', 'z16', DEPTH_RES_X, DEPTH_RES_Y, DEPTH_FPS,
                              'Depth Stream of the Intel RealSense D435 camera. Each pixel corresponds to the measured '
                              'distance in mm.')

    def init_video_capture(self):
        try:
            # Create a pipeline
            self.pipeline = rs.pipeline()

            # Create a config and configure the pipeline to stream
            #  different resolutions of color and depth streams
            config = rs.config()
            config.enable_stream(rs.stream.depth, DEPTH_RES_X, DEPTH_RES_Y, rs.format.z16, DEPTH_FPS)
            config.enable_stream(rs.stream.color, RGB_RES_X, RGB_RES_Y, rs.format.bgr8, RGB_FPS)
            # config.enable_stream(rs.stream.infrared, 1, DEPTH_RES_X, DEPTH_RES_Y, rs.format.y8, DEPTH_FPS)
            # config.enable_stream(rs.stream.infrared, 2, DEPTH_RES_X, DEPTH_RES_Y, rs.format.y8, DEPTH_FPS)

            # Start streaming
            profile = self.pipeline.start(config)

            # Getting the depth sensor's depth scale (see rs-align example for explanation)
            depth_sensor = profile.get_device().first_depth_sensor()
            self.depth_scale = depth_sensor.get_depth_scale()
            # print("[RealSense D435]: Depth scale", self.depth_scale)

            # TODO: Allow settings to be changed on initializing the function
            depth_sensor.set_option(rs.option.laser_power, 360)  # 0 - 360
            depth_sensor.set_option(rs.option.depth_units, 0.001)  # Number of meters represented by a single depth unit

            # Create an align object
            # rs.align allows us to perform alignment of depth frames to others frames
            # The "align_to" is the stream type to which we plan to align depth frames.
            align_to = rs.stream.color
            self.align = rs.align(align_to)

            self.hole_filling_filter = rs.hole_filling_filter()
            self.decimation_filter = rs.decimation_filter()
            self.temporal_filter = rs.temporal_filter()
        except Exception as e:
            print('[RealSense D435]: ERROR:', e, file=sys.stderr)
            print('[RealSense D435]: Could not initialize camera. If the resource is busy, check if any other script '
                  'is currently accessing the camera. If this is not the case, replug the camera and try again.',
                  file=sys.stderr)
            sys.exit(0)

        self.init_colorizer()

        self.started = False
        self.read_lock = threading.Lock()

    # The colorizer can colorize depth images
    def init_colorizer(self):
        self.colorizer = rs.colorizer()
        self.colorizer.set_option(rs.option.color_scheme, 0)  # Define the color scheme
        # Auto histogram color selection (0 = off, 1 = on)
        self.colorizer.set_option(rs.option.histogram_equalization_enabled, 0)
        self.colorizer.set_option(rs.option.min_distance, COLORIZER_MIN_DISTANCE)  # meter
        self.colorizer.set_option(rs.option.max_distance, COLORIZER_MAX_DISTANCE)  # meter

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
        print('[RealSense D435]: Skip first ' + str(NUM_FRAMES_WAIT_INITIALIZING) +
              ' frames to allow Auto White Balance to adjust')

        while self.started:
            self.num_frame += 1
            if DEBUG_MODE:
                print('[RealSense D435]: Frame ', self.num_frame)

            # Get frameset of color and depth
            frames = self.pipeline.wait_for_frames()

            # Align the depth frame to color frame
            aligned_frames = self.align.process(frames)

            # Get aligned frames
            aligned_depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()
            # ir_left_frame = frames.get_infrared_frame(1)
            # ir_right_frame = frames.get_infrared_frame(2)

            # Validate that both frames are valid
            if not aligned_depth_frame or not color_frame:
                continue

            if self.num_frame < NUM_FRAMES_WAIT_INITIALIZING:
                continue
            elif self.num_frame == NUM_FRAMES_WAIT_INITIALIZING:
                print('[RealSense D435]: Ready')

            # Apply Filters
            # aligned_depth_frame = self.hole_filling_filter.process(aligned_depth_frame)
            # aligned_depth_frame = self.decimation_filter.process(aligned_depth_frame)
            # aligned_depth_frame = self.temporal_filter.process(aligned_depth_frame)

            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.array(aligned_depth_frame.get_data(), dtype=np.uint16)
            depth_image = self.get_depth_image_mm(depth_image)
            depth_colormap = np.asanyarray(self.colorizer.colorize(aligned_depth_frame).get_data())

            # ir_left_frame = np.asanyarray(ir_left_frame.get_data())
            # ir_right_frame = np.asanyarray(ir_right_frame.get_data())

            with self.read_lock:
                self.color_image = color_image
                self.depth_image = depth_image

    # Convert the depth image into a numpy array where each pixel value corresponds to the measured distance in mm
    # This conversion only works if the depth units are set to 0.001
    def get_depth_image_mm(self, depth_image):
        depth_image_mm = depth_image.copy() * self.depth_scale * 1000
        depth_image_mm = np.array(depth_image_mm, dtype=np.uint16)

        return depth_image_mm

    # Returns the requested camera frames
    # TODO: Return only the frames that are requested via params
    def get_frames(self):
        with self.read_lock:
            if self.color_image is not None and self.depth_image is not None:
                return self.color_image.copy(), self.depth_image.copy()
            else:
                return None, None

    def get_resolution(self):
        return RGB_RES_X, RGB_RES_Y


    def stop(self):
        self.started = False
        self.thread.join()

    def __exit__(self, exec_type, exc_value, traceback):
        self.pipeline.stop()
