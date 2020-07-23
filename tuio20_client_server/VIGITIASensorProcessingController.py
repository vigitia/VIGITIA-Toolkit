#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import cv2
from sensors.cameras.realsenseD435.realsense_D435_camera import RealsenseD435Camera
from tuio20_client_server.tuio_server import TUIOServer
from calibration.table_surface_extractor import TableSurfaceExtractor
from services.fiducials_detector import FiducialsDetector
from services.movement_detector import MovementDetector
from services.foreground_mask_extractor import ForegroundMaskExtractor
from services.touch_detector import TouchDetector


class VIGITIASensorProcessingController:

    def __init__(self):
        self.init_tuio_server()

        self.camera = RealsenseD435Camera()
        self.camera.start()

        self.table_surface_extractor = TableSurfaceExtractor()
        self.fiducials_detector = FiducialsDetector()
        self.movement_detector = MovementDetector()
        self.foreground_mask_extractor = ForegroundMaskExtractor()
        self.touch_detector = TouchDetector()

        self.table_border = self.table_surface_extractor.get_table_border()

        self.loop()

    def init_tuio_server(self):
        target_computer_ip = '132.199.130.68'  # '132.199.117.19'
        self.tuio_server = TUIOServer(target_computer_ip)

        # The dimension attribute encodes the sensor dimension with two 16bit unsigned integer values embedded into a 32bit
        # integer value. The first two bytes represent the sensor width, while the final two bytes represent the sensor
        # height
        self.dimension = 0
        self.source = os.uname()[1]

    def loop(self):
        while True:
            color_image, depth_image = self.camera.get_frames()

            if color_image is not None:
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
                    # TODO: SEND ALSO BOUNDING BOX

                for movement in movements:
                    cv2.rectangle(color_image, (movement['bounding_rect_x'], movement['bounding_rect_y']), (
                    movement['bounding_rect_x'] + movement['bounding_rect_width'],
                    movement['bounding_rect_y'] + movement['bounding_rect_height']), (0, 255, 0), 2)

                for touch_point in touch_points:
                    print(touch_point)

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
