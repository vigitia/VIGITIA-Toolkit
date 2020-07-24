#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import cv2
from sensors.cameras.realsenseD435.realsense_D435_camera import RealsenseD435Camera

# Import TUIO Server
from tuio20_client_server.TUIOServer import TUIOServer

from calibration.table_surface_extractor import TableSurfaceExtractor

from gstreamer.VIGITIAVideoStreamer import VIGITIAVideoStreamer

# Import Sensor data processing services
from services.fiducials_detector import FiducialsDetector
from services.movement_detector import MovementDetector
from services.foreground_mask_extractor import ForegroundMaskExtractor
from services.touch_detector import TouchDetector

TARGET_COMPUTER_IP = '132.199.130.68'
TARGET_COMPUTER_PORT = 8000

class VIGITIASensorProcessingController:

    def __init__(self):
        self.init_tuio_server()

        self.camera = RealsenseD435Camera()
        self.camera.start()

        self.video_streamer = VIGITIAVideoStreamer()

        self.table_surface_extractor = TableSurfaceExtractor()

        self.init_sensor_data_processing_services()

        self.table_border = self.table_surface_extractor.get_table_border()

        self.loop()

    def init_tuio_server(self):

        self.tuio_server = TUIOServer(TARGET_COMPUTER_IP, TARGET_COMPUTER_PORT)

        # The dimension attribute encodes the sensor dimension with two 16bit unsigned integer values embedded into a 32bit
        # integer value. The first two bytes represent the sensor width, while the final two bytes represent the sensor
        # height
        self.dimension = 0
        self.source = os.uname()[1]

    def init_sensor_data_processing_services(self):
        self.fiducials_detector = FiducialsDetector()
        self.movement_detector = MovementDetector()
        self.foreground_mask_extractor = ForegroundMaskExtractor()
        self.touch_detector = TouchDetector()

    def loop(self):
        while True:
            color_image, depth_image = self.camera.get_frames()

            if color_image is not None:

                self.video_streamer.stream_frame(color_image)

                self.tuio_server.start_tuio_bundle(dimension=self.dimension, source=self.source)

                color_image_table = self.table_surface_extractor.extract_table_area(color_image)

                aruco_markers, movements, touch_points = self.process_sensor_data(color_image, color_image_table,
                                                                                  depth_image)

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
                    print(touch_point)
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
                
    def process_sensor_data(self, color_image, color_image_table, depth_image):
        aruco_markers = self.fiducials_detector.detect_fiducials(color_image_table)
        movements = self.movement_detector.detect_movement(color_image_table)
        touch_points = self.touch_detector.get_touch_points(color_image, depth_image, self.table_border)

        return aruco_markers, movements, touch_points


def main():
    VIGITIASensorProcessingController()
    sys.exit()


if __name__ == '__main__':
    main()
