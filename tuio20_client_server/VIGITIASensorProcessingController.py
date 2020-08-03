#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import cv2
import numpy as np
from sensors.cameras.realsenseD435.realsense_D435_camera import RealsenseD435Camera

# Import TUIO Server
from tuio20_client_server.TUIOServer import TUIOServer

from calibration.table_surface_extractor import TableSurfaceExtractor

from gstreamer.VIGITIAVideoStreamer import VIGITIAVideoStreamer

from utility.get_ip import get_ip_address

# Import Sensor data processing services
from services.fiducials_detector import FiducialsDetector
from services.movement_detector import MovementDetector
from services.foreground_mask_extractor import ForegroundMaskExtractor
from services.touch_detector import TouchDetector
from services.table_detector import TableDetector
from services.generic_object_detector import GenericObjectDetector
from services.hand_tracker import HandTracker

TARGET_COMPUTER_PORT = 8000

class VIGITIASensorProcessingController:

    def __init__(self):
        self.init_tuio_server()

        self.camera = RealsenseD435Camera()
        self.camera.start()

        #self.video_streamer = VIGITIAVideoStreamer('132.199.199.67', 5000)
        self.video_streamer = VIGITIAVideoStreamer(get_ip_address(), 5000)
        self.video_streamer_two = VIGITIAVideoStreamer(get_ip_address(), 5001)

        self.table_surface_extractor = TableSurfaceExtractor()

        self.init_sensor_data_processing_services()

        self.table_border = self.table_surface_extractor.get_table_border()

        self.loop()

    def init_tuio_server(self):

        self.tuio_server = TUIOServer(get_ip_address(), TARGET_COMPUTER_PORT)

        # The dimension attribute encodes the sensor dimension with two 16bit unsigned integer values embedded into a 32bit
        # integer value. The first two bytes represent the sensor width, while the final two bytes represent the sensor
        # height
        self.dimension = '1280x720'
        self.source = os.uname()[1]

    def init_sensor_data_processing_services(self):
        self.fiducials_detector = FiducialsDetector()
        self.movement_detector = MovementDetector()
        self.foreground_mask_extractor = ForegroundMaskExtractor()
        self.touch_detector = TouchDetector()
        self.table_detector = TableDetector()
        self.generic_object_detector = GenericObjectDetector()
        self.hand_tracker = HandTracker()

    def loop(self):
        while True:
            color_image, depth_image = self.camera.get_frames()

            if color_image is not None:

                color_image_table = self.table_surface_extractor.extract_table_area(color_image)

                self.experiments(color_image, color_image_table, depth_image)

                aruco_markers, movements, touch_points = self.process_sensor_data(color_image, color_image_table,
                                                                                  depth_image)

                self.tuio_server.start_tuio_bundle(dimension=self.dimension, source=self.source)

                # Send a message for every video stream
                # TODO: Automate, count up ID, ...
                self.tuio_server.add_data_message(0, 'video', 'Intel Realsense D435 RGB', 1280, 720, 5000)
                self.tuio_server.add_data_message(1, 'video', 'Intel Realsense D435 Depth', 1280, 720, 5001)

                for marker in aruco_markers:
                    # TODO: Correct IDs
                    self.tuio_server.add_token_message(s_id=int(marker['id']), tu_id=0, c_id=int(marker['id']),
                                                       x_pos=int(marker['centroid'][0]),
                                                       y_pos=int(marker['centroid'][1]),
                                                       angle=marker['angle'])
                    # TODO: Fill out
                    self.tuio_server.add_bounding_box_message(s_id=int(marker['id']), x_pos=0,
                                                              y_pos=0, angle=0,
                                                              width=0,
                                                              height=0, area=0)
                    # TODO: SEND ALSO BOUNDING BOX

                for movement in movements:
                    # TODO: Correct IDs
                    # TODO: How to identify them as movement areas client side?
                    self.tuio_server.add_bounding_box_message(s_id=0, x_pos=movement['bounding_rect_x'],
                                                              y_pos=movement['bounding_rect_y'], angle=0,
                                                              width=movement['bounding_rect_width'],
                                                              height=movement['bounding_rect_height'], area=0)

                for touch_point in touch_points:
                    #print(touch_point)
                    # TODO: Correct IDs
                    self.tuio_server.add_pointer_message(s_id=touch_point.id, tu_id=0, c_id=0, x_pos=touch_point.x,
                                                         y_pos=touch_point.y, angle=0, shear=0, radius=0,
                                                         press=touch_point.is_touching)

                self.tuio_server.send_tuio_bundle()

            key = cv2.waitKey(1)
            # Press esc or 'q' to close the image window
            if key & 0xFF == ord('q') or key == 27:
                cv2.destroyAllWindows()
                break

    def experiments(self, color_image, color_image_table, depth_image):
        pass
        # depth_filtered = cv2.convertScaleAbs(depth_image, alpha=(255/2000))
        # depth_foreground = self.foreground_mask_extractor.get_foreground_mask_depth(depth_filtered)

        #table = self.table_detector.get_table_border(color_image, depth_image)
        #cv2.imshow('table', table)

        self.video_streamer.stream_frame(color_image_table)
        self.video_streamer_two.stream_frame(color_image)

        #detected_objects, detected_objects_dict = self.generic_object_detector.detect_generic_objects(color_image_table)
        #cv2.imshow('objects', detected_objects)

        #if len(detected_objects_dict) > 0:
        #    print(detected_objects_dict)
                
    def process_sensor_data(self, color_image, color_image_table, depth_image):
        aruco_markers = self.fiducials_detector.detect_fiducials(color_image_table)
        movements = self.movement_detector.detect_movement(color_image_table)

        # TODO: Find solution for this temporary fix of ghost hands
        self.hand_tracker.reset()
        detected_hands = self.hand_tracker(cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB))
        hands, hand_regions = self.hand_tracker.add_hand_tracking_points(color_image.copy(), detected_hands)
        cv2.imshow('hands', hands)

        touch_points = self.touch_detector.get_touch_points(color_image, depth_image, self.table_border, hand_regions)

        return aruco_markers, movements, touch_points


def main():
    VIGITIASensorProcessingController()
    sys.exit()


if __name__ == '__main__':
    main()
