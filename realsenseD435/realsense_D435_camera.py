#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Code parts for asynchronous video capture taken from
# http://blog.blitzblit.com/2017/12/24/asynchronous-video-capture-in-python-with-opencv/

import pyrealsense2 as rs
import numpy as np
import threading

# Camera Settings
DEPTH_RES_X = 848
DEPTH_RES_Y = 480
RGB_RES_X = 848
RGB_RES_Y = 480
DEPTH_FPS = 60
RGB_FPS = 60

NUM_FRAMES_WAIT_INITIALIZING = 100  # Let the camera warm up and let the auto white balance adjust


class RealsenseD435Camera():

    num_frame = 0

    pipeline = None
    align = None
    colorizer = None

    hole_filling_filter = None
    decimation_filter = None
    spacial_filter = None
    temporal_filter = None
    disparity_to_depth_filter = None
    depth_to_disparity_filter = None

    color_image = None
    depth_image = None

    def __init__(self):

        # Create a pipeline
        self.pipeline = rs.pipeline()

        # Create a config and configure the pipeline to stream
        #  different resolutions of color and depth streams
        config = rs.config()
        config.enable_stream(rs.stream.depth, DEPTH_RES_X, DEPTH_RES_Y, rs.format.z16, DEPTH_FPS)
        config.enable_stream(rs.stream.color, RGB_RES_X, RGB_RES_Y, rs.format.bgr8, RGB_FPS)

        # Start streaming
        profile = self.pipeline.start(config)

        # Getting the depth sensor's depth scale (see rs-align example for explanation)
        depth_sensor = profile.get_device().first_depth_sensor()
        self.depth_scale = depth_sensor.get_depth_scale()
        print("Depth scale", self.depth_scale)

        # TODO: Tweak camera settings
        depth_sensor.set_option(rs.option.laser_power, 360)
        depth_sensor.set_option(rs.option.depth_units, 0.001)  # Number of meters represented by a single depth unit

        # Create an align object
        # rs.align allows us to perform alignment of depth frames to others frames
        # The "align_to" is the stream type to which we plan to align depth frames.
        align_to = rs.stream.color
        self.align = rs.align(align_to)

        self.hole_filling_filter = rs.hole_filling_filter()
        self.decimation_filter = rs.decimation_filter()
        self.temporal_filter = rs.temporal_filter()

        self.init_colorizer()

        self.started = False
        self.read_lock = threading.Lock()

        print('Finished INIT')

    # The colorizer can colorize depth images
    def init_colorizer(self):
        self.colorizer = rs.colorizer()
        self.colorizer.set_option(rs.option.color_scheme, 0)  # Define the color scheme
        # Auto histogram color selection (0 = off, 1 = on)
        self.colorizer.set_option(rs.option.histogram_equalization_enabled, 0)
        self.colorizer.set_option(rs.option.min_distance, 0.5)  # meter
        self.colorizer.set_option(rs.option.max_distance, 1.3)  # meter

    def start(self):
        if self.started:
            print('Already running')
            return None
        else:
            self.started = True
            thread = threading.Thread(target=self.update, args=())
            # thread.daemon = True
            thread.start()
            return self

    def update(self):
        while self.started:
            self.num_frame += 1
            print('Frame: ', self.num_frame)

            # Get frameset of color and depth
            frames = self.pipeline.wait_for_frames()

            # Align the depth frame to color frame
            aligned_frames = self.align.process(frames)

            # Get aligned frames
            aligned_depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            # Validate that both frames are valid
            if not aligned_depth_frame or not color_frame:
                continue

            if self.num_frame < NUM_FRAMES_WAIT_INITIALIZING:
                continue

            # Apply Filters
            # aligned_depth_frame = self.hole_filling_filter.process(aligned_depth_frame)
            # aligned_depth_frame = self.decimation_filter.process(aligned_depth_frame)
            # aligned_depth_frame = self.temporal_filter.process(aligned_depth_frame)

            color_image = np.asanyarray(color_frame.get_data())
            # depth_image = np.asanyarray(aligned_depth_frame.get_data())
            depth_image = np.array(aligned_depth_frame.get_data(), dtype=np.int16)

            # depth_image = self.moving_average_filter(depth_image)

            # depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
            # depth_colormap = np.asanyarray(self.colorizer.colorize(aligned_depth_frame).get_data())

            with self.read_lock:
                self.color_image = color_image
                self.depth_image = depth_image

    def get_frames(self):
        with self.read_lock:
            if self.color_image is not None and self.depth_image is not None:
                return self.color_image.copy(), self.depth_image.copy()
            else:
                return None, None

    def stop(self):
        self.started = False
        self.thread.join()

    def __exit__(self, exec_type, exc_value, traceback):
        self.pipeline.stop()