#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time

import cv2

from VIGITIA_toolkit.data_transportation.VIGITIAVideoStreamer import VIGITIAVideoStreamer
from VIGITIA_toolkit.sensors.cameras.realsense_D435_camera import RealsenseD435Camera
from VIGITIA_toolkit.sensors.cameras.GenericWebcam import GenericWebcam

from VIGITIA_toolkit.data_transportation.TUIOServer import TUIOServer  # Import TUIO Server

from VIGITIA_toolkit.sensor_processing_services.TableExtractionService import TableSurfaceExtractor

from VIGITIA_toolkit.utility.get_ip import get_ip_address

# Import Sensor Processing Services:
from VIGITIA_toolkit.sensor_processing_services.FiducialsDetectionService import FiducialsDetectionService
from VIGITIA_toolkit.sensor_processing_services.BackgroundSubstractionService import ForegroundMaskExtractor
from VIGITIA_toolkit.sensor_processing_services.TouchDetectionService import TouchDetectionService
from VIGITIA_toolkit.sensor_processing_services.ObjectDetectionService import ObjectDetectionService
from VIGITIA_toolkit.sensor_processing_services.HandLandmarkDetectionService import HandLandmarkDetectionService

# TODO: Allow multiple
TARGET_COMPUTER_IP = get_ip_address()
print(TARGET_COMPUTER_IP)

TARGET_COMPUTER_PORT = 8000

DEBUG_MODE = False

FLIP_IMAGE = True  # Necessary if the camera is upside down

ENABLE_MARKER_DETECTOR = True
ENABLE_OBJECT_DETECTOR = False
ENABLE_TOUCH_DETECTOR = False


class VIGITIASensorProcessingController:
    """ VIGITIASensorProcessingController


    """

    frame_id = 0

    hand_regions = []
    detected_hands = []

    def __init__(self):
        self.init_cameras()
        self.init_tuio_server()
        # self.init_video_streamers()
        self.init_sensor_data_processing_services()

        self.loop()

    def init_cameras(self):
        # TODO: Select camera via GUI
        #self.camera = GenericWebcam()
        self.camera = RealsenseD435Camera()
        self.camera.init_video_capture()
        self.camera.start()

    def init_tuio_server(self):
        self.tuio_server = TUIOServer(TARGET_COMPUTER_IP, TARGET_COMPUTER_PORT)

        camera_res_x, camera_res_y = self.camera.get_resolution()
        self.dimension = str(camera_res_x) + 'x' + str(camera_res_y)
        print('[SensorProcessingController]: Dimension of main sensor: ', self.dimension)

        self.source = os.uname()[1]  # TODO: Not working on windows

    def init_video_streamers(self):
        # TODO: Let user select in GUI what video should be streamed
        self.video_streamer = VIGITIAVideoStreamer(TARGET_COMPUTER_IP, 5000)

    # Init all Sensor Processing Services here
    def init_sensor_data_processing_services(self):
        self.table_surface_extractor = TableSurfaceExtractor()
        self.fiducials_detector = FiducialsDetectionService()
        #self.movement_detector = MovementDetector()
        self.foreground_mask_extractor = ForegroundMaskExtractor()
        self.touch_detector = TouchDetectionService()
        #self.table_detector = TableDetector()
        self.generic_object_detector = ObjectDetectionService()
        self.hand_tracker = HandLandmarkDetectionService()

    # The main application loop. Code parts for fps counter from
    # https://stackoverflow.com/questions/43761004/fps-how-to-divide-count-by-time-function-to-determine-fps
    def loop(self):
        # Variables for fps counter
        start_time = 0
        counter = 0

        while True:
            # Get frames from cameras
            color_image, depth_image = self.camera.get_frames()

            if FLIP_IMAGE:
                color_image = cv2.flip(color_image, -1)
                # TODO: Flip depth image

            # Only continue if needed frames are available
            if color_image is not None:
                self.frame_id += 1

                # Pre-process camera frames
                color_image_table = self.table_surface_extractor.extract_table_area(color_image)
                if depth_image is not None:
                    depth_image_table = self.table_surface_extractor.extract_table_area(depth_image)
                else:
                    depth_image_table = None

                if DEBUG_MODE:
                    # Preview frames
                    cv2.imshow('color_image_table', color_image_table)

                # Start a new TUIO Bundle for the current frame
                self.tuio_server.start_tuio_bundle(dimension=self.dimension, source=self.source)

                # Stream Frames
                # self.stream_frames(color_image, color_image_table, depth_image)

                # Run Sensor Processing Services. They all add their data to the TUIO Bundle
                self.run_sensor_processing_services(color_image, color_image_table, depth_image, depth_image_table)

                # Send the TUIO Bundle
                self.tuio_server.send_tuio_bundle()

                # FPS Counter
                counter += 1
                if (time.time() - start_time) > 1:  # displays the frame rate every 1 second
                    if DEBUG_MODE:
                        print("[SensorProcessingController]: FPS: ", round(counter / (time.time() - start_time), 1))
                    counter = 0
                    start_time = time.time()

            key = cv2.waitKey(1)
            # Press esc or 'q' to close the image window
            if key & 0xFF == ord('q') or key == 27:
                cv2.destroyAllWindows()
                break

    # Call all selected sensor processing services for the current frame
    def run_sensor_processing_services(self, color_image, color_image_table, depth_image, depth_image_table):

        foreground_mask = None
        if ENABLE_OBJECT_DETECTOR or ENABLE_TOUCH_DETECTOR:
            foreground_mask = self.get_foreground_mask(color_image_table)
            if DEBUG_MODE:
                cv2.imshow('Binary Mask of the foreground', foreground_mask)

        if ENABLE_MARKER_DETECTOR:
            self.get_aruco_markers(color_image_table)
        if ENABLE_OBJECT_DETECTOR:
            self.get_detected_objects(color_image_table.copy(), foreground_mask)
        if ENABLE_TOUCH_DETECTOR:
            self.get_touch_points(color_image_table, depth_image_table, foreground_mask)

    # This function handles the streaming of all video frames
    def stream_frames(self, color_image, color_image_table, depth_image):
        # Send TUIO data messages to let the SensorDataInterface on the Target Computer know that new frames are coming
        self.tuio_server.add_data_message(0, 'video', 'Intel Realsense D435 RGB table local', 1280, 720, 5000)
        # self.tuio_server.add_data_message(0, 'video', 'Intel Realsense D435 RGB full local', 1280, 720, 5001)

        # Stream the frames using the correct instance of the sensor processing controller
        self.video_streamer.stream_frame(color_image_table)
        # self.video_streamer_two.stream_frame(color_image)

    # Some SensorProcessingServices need the foreground mask. Request it here and pass it over to them.
    def get_foreground_mask(self, color_image_table):
        return self.foreground_mask_extractor.get_foreground_mask_otsu(color_image_table)

    # Get data from the GenericObjectDetectionService and convert it to TUIO messages
    def get_detected_objects(self, color_image_table, foreground_mask):
        detected_objects = self.generic_object_detector.detect_generic_objects(color_image_table, foreground_mask)

        # Give each object an ID
        for detected_object in detected_objects:
            if detected_object['label'] == 'orange':
                component_id = 10000
            elif detected_object['label'] == 'banana':
                component_id = 10001
            elif detected_object['label'] == 'carrot':
                component_id = 10002
            elif detected_object['label'] == 'cell phone':
                component_id = 10003
            elif detected_object['label'] == 'apple':
                component_id = 10004
            elif detected_object['label'] == 'donut':
                component_id = 10005
            else:
                component_id = 10006

            # Send out information as TUIO Messages
            self.tuio_server.add_token_message(s_id=component_id, tu_id=0, c_id=component_id,
                                               x_pos=detected_object['center_x'],
                                               y_pos=detected_object['center_y'],
                                               angle=0)

            self.tuio_server.add_bounding_box_message(s_id=component_id, x_pos=detected_object['x'],
                                                      y_pos=detected_object['y'], angle=0,
                                                      width=detected_object['width'],
                                                      height=detected_object['height'], area=0)

    def get_aruco_markers(self, color_image_table):
        aruco_markers = self.fiducials_detector.detect_fiducials(color_image_table)

        for marker in aruco_markers:

            print(marker)

            # TODO: Correct IDs
            self.tuio_server.add_token_message(s_id=int(marker['id']), tu_id=0, c_id=int(marker['id']),
                                               x_pos=int(marker['centroid'][0]),
                                               y_pos=int(marker['centroid'][1]),
                                               angle=marker['angle'])

            # TODO: SEND ALSO BOUNDING BOX:
            self.tuio_server.add_bounding_box_message(s_id=int(marker['id']), x_pos=0,
                                                      y_pos=0, angle=0,
                                                      width=0,
                                                      height=0, area=0)

    # Call the MovementDetectionService that finds areas where movement is happening above the table
    def get_movements(self, color_image_table):
        movements = self.movement_detector.detect_movement(color_image_table)

        for movement in movements:
            # TODO: Correct IDs
            # TODO: How to identify them as movement areas client side?
            self.tuio_server.add_bounding_box_message(s_id=0, x_pos=movement['bounding_rect_x'],
                                                      y_pos=movement['bounding_rect_y'], angle=0,
                                                      width=movement['bounding_rect_width'],
                                                      height=movement['bounding_rect_height'], area=0)

    # Find touch points on the table
    def get_touch_points(self, color_image_table, depth_image_table, foreground_mask):
        touch_points = []

        # Use the CNN Hand tracker only every other frame to improve performance
        if self.frame_id % 2 == 0:
            # TODO: Find solution for this temporary fix of ghost hands
            self.hand_tracker.reset()
            detected_hands = self.hand_tracker(cv2.cvtColor(color_image_table, cv2.COLOR_BGR2RGB))
            hands, hand_regions = self.hand_tracker.add_hand_tracking_points(color_image_table.copy(), detected_hands)
            if DEBUG_MODE:
                cv2.imshow('hands', hands)

            self.detected_hands = detected_hands
            self.hand_regions = hand_regions

        # Find the touch points using the TouchDetectionService
        touch_points = self.touch_detector.get_touch_points(color_image_table, depth_image_table, self.hand_regions, self.detected_hands, foreground_mask)

        # Send out a TUIO pointer message for each touch point
        for touch_point in touch_points:
            # TODO: Add correct Type/User and Component ID
            self.tuio_server.add_pointer_message(s_id=touch_point.id, tu_id=0, c_id=0, x_pos=touch_point.x,
                                                 y_pos=touch_point.y, angle=0, shear=0, radius=0,
                                                 press=touch_point.is_touching)

    # Use the calibration data to extract the table area from the camera frame
    def get_table_border(self):
        table_border = self.table_surface_extractor.get_table_border()
        return table_border


def main():
    VIGITIASensorProcessingController()
    sys.exit()


if __name__ == '__main__':
    main()
