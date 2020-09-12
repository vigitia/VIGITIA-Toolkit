#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time

import cv2
from sensors.cameras.realsense_D435_camera import RealsenseD435Camera

from tuio20_client_server.TUIOServer import TUIOServer  # Import TUIO Server

from calibration.table_surface_extractor import TableSurfaceExtractor

from gstreamer.VIGITIAVideoStreamer import VIGITIAVideoStreamer  # Import VideoStreamer

from utility.get_ip import get_ip_address

# Import Sensor Processing Services:
from services.fiducials_detector import FiducialsDetector
from services.movement_detector import MovementDetector
from services.foreground_mask_extractor import ForegroundMaskExtractor
from services.touch_detector import TouchDetector
from services.table_detector import TableDetector
from services.generic_object_detector import GenericObjectDetector
from services.hand_tracker import HandTracker

# TODO: Allow multiple
TARGET_COMPUTER_IP = get_ip_address()
# TARGET_COMPUTER_IP = '132.199.199.67'
# TARGET_COMPUTER_IP = '127.0.0.1'

TARGET_COMPUTER_PORT = 8000

DEBUG_MODE = True


class VIGITIASensorProcessingController:
    """ VIGITIASensorProcessingController


    """

    frame_id = 0

    hand_regions = []
    detected_hands = []

    def __init__(self):
        self.init_cameras()
        self.init_tuio_server()
        self.init_video_streamers()
        self.init_sensor_data_processing_services()

        self.loop()

    def init_cameras(self):
        # TODO: Select camera via GUI
        self.camera = RealsenseD435Camera()
        self.camera.init_video_capture()
        self.camera.start()

    def init_tuio_server(self):
        self.tuio_server = TUIOServer(TARGET_COMPUTER_IP, TARGET_COMPUTER_PORT)

        camera_res_x, camera_res_y = self.camera.get_resolution()
        self.dimension = str(camera_res_x) + 'x' + str(camera_res_y)
        print('Dimension', self.dimension)

        self.source = os.uname()[1]  # TODO: Not working on windows

    def init_video_streamers(self):
        pass
        # TODO: Let user select in GUI what video should be streamed
        # self.video_streamer = VIGITIAVideoStreamer(TARGET_COMPUTER_IP, 5000)
        # self.video_streamer_two = VIGITIAVideoStreamer(TARGET_COMPUTER_IP, 5001)

    # Init all Sensor Processing Services here
    def init_sensor_data_processing_services(self):
        self.table_surface_extractor = TableSurfaceExtractor()
        self.fiducials_detector = FiducialsDetector()
        #self.movement_detector = MovementDetector()
        self.foreground_mask_extractor = ForegroundMaskExtractor()
        self.touch_detector = TouchDetector()
        #self.table_detector = TableDetector()
        self.generic_object_detector = GenericObjectDetector()
        self.hand_tracker = HandTracker()

    # The main application loop. Code parts for fps counter from
    # https://stackoverflow.com/questions/43761004/fps-how-to-divide-count-by-time-function-to-determine-fps
    def loop(self):
        # Variables for fps counter
        start_time = 0
        counter = 0

        while True:
            # Get frames from cameras
            color_image, depth_image = self.camera.get_frames()

            # Only continue if needed frames are available
            if color_image is not None:
                self.frame_id += 1

                # Preprocess camera frames
                color_image_table = self.table_surface_extractor.extract_table_area(color_image)
                depth_image_table = self.table_surface_extractor.extract_table_area(depth_image)

                if DEBUG_MODE:
                    # Preview frames
                    cv2.imshow('color_image_table', color_image_table)

                # Start TUIO Bundle
                self.tuio_server.start_tuio_bundle(dimension=self.dimension, source=self.source)

                # Stream Frames
                self.stream_frames(color_image, color_image_table, depth_image)

                # Run Sensor Processing Services. They all add their data to the TUIO Bundle
                foreground_mask = self.get_foreground_mask(color_image_table)

                #self.get_detected_objects(color_image_table, foreground_mask)
                self.get_aruco_markers(color_image_table)
                #self.get_movements(color_image_table)
                self.get_touch_points(color_image_table, depth_image_table)

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

    def stream_frames(self, color_image, color_image_table, depth_image):
        pass
        # self.tuio_server.add_data_message(0, 'video', 'Intel Realsense D435 RGB table local', 1280, 720, 5000)
        # self.tuio_server.add_data_message(0, 'video', 'Intel Realsense D435 RGB full local', 1280, 720, 5001)

        # self.video_streamer.stream_frame(color_image_table)
        # self.video_streamer_two.stream_frame(color_image)

    def get_foreground_mask(self, color_image_table):
        mask = self.foreground_mask_extractor.get_foreground_mask_otsu(color_image_table)
        # if DEBUG_MODE:
        #     cv2.imshow('otsu', mask)
        return mask

    def get_detected_objects(self, color_image_table, foreground_mask):
        detected_objects = self.generic_object_detector.detect_generic_objects(color_image_table, foreground_mask)

        for detected_object in detected_objects:
            if detected_object['label'] == 'orange':
                component_id = 1000
            elif detected_object['label'] == 'banana':
                component_id = 1001
            elif detected_object['label'] == 'carrot':
                component_id = 1002
            else:
                component_id = 1003

            print(detected_object['width'], detected_object['height'])

            self.tuio_server.add_token_message(s_id=component_id, tu_id=0, c_id=component_id,
                                               x_pos=detected_object['center_x'],
                                               y_pos=detected_object['center_y'],
                                               angle=0)

            self.tuio_server.add_bounding_box_message(s_id=component_id, x_pos=detected_object['center_x'],
                                                      y_pos=detected_object['center_y'], angle=0,
                                                      width=detected_object['width'],
                                                      height=detected_object['height'], area=0)

    def get_aruco_markers(self, color_image_table):
        aruco_markers = self.fiducials_detector.detect_fiducials(color_image_table)

        for marker in aruco_markers:
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

    def get_movements(self, color_image_table):
        movements = self.movement_detector.detect_movement(color_image_table)

        for movement in movements:
            # TODO: Correct IDs
            # TODO: How to identify them as movement areas client side?
            self.tuio_server.add_bounding_box_message(s_id=0, x_pos=movement['bounding_rect_x'],
                                                      y_pos=movement['bounding_rect_y'], angle=0,
                                                      width=movement['bounding_rect_width'],
                                                      height=movement['bounding_rect_height'], area=0)

    def get_touch_points(self, color_image_table, depth_image_table):
        touch_points = []
        # Only every other frame to improve performance
        if self.frame_id % 2 == 0:
            # TODO: Find solution for this temporary fix of ghost hands
            self.hand_tracker.reset()
            detected_hands = self.hand_tracker(cv2.cvtColor(color_image_table, cv2.COLOR_BGR2RGB))
            hands, hand_regions = self.hand_tracker.add_hand_tracking_points(color_image_table.copy(), detected_hands)
            cv2.imshow('hands', hands)

            self.detected_hands = detected_hands
            self.hand_regions = hand_regions

        touch_points = self.touch_detector.get_touch_points(color_image_table, depth_image_table, self.hand_regions, self.detected_hands)

        for touch_point in touch_points:
            # print(touch_point)
            # TODO: Correct IDs
            self.tuio_server.add_pointer_message(s_id=touch_point.id, tu_id=0, c_id=0, x_pos=touch_point.x,
                                                 y_pos=touch_point.y, angle=0, shear=0, radius=0,
                                                 press=touch_point.is_touching)

    def get_table_border(self):
        pass
        # self.table_border = self.table_surface_extractor.get_table_border()


def main():
    VIGITIASensorProcessingController()
    sys.exit()


if __name__ == '__main__':
    main()
