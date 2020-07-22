#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
from sensors.cameras.realsenseD435.realsense_D435_camera import RealsenseD435Camera
from tuio20_client_server.tuio_server import TUIOServer
from calibration.table_surface_extractor import TableSurfaceExtractor
from services.fiducials_detector import FiducialsDetector
from services.movement_detector import MovementDetector
from services.foreground_mask_extractor import ForegroundMaskExtractor
from services.touch_detector import TouchDetector


def send_tuio_bundle(tuio_server, aruco_markers):
    # The dimension attribute encodes the sensor dimension with two 16bit unsigned integer values embedded into a 32bit
    # integer value. The first two bytes represent the sensor width, while the final two bytes represent the sensor
    # height
    dimension = 0
    source = 'VIGITIA'

    tuio_server.start_tuio_bundle(dimension=dimension, source=source)
    
    for marker in aruco_markers:
        # TODO: Correct IDs
        tuio_server.add_token_message(s_id=int(marker['id']), tu_id=0, c_id=int(marker['id']), x_pos=int(marker['centroid'][0]), y_pos=int(marker['centroid'][1]), angle=marker['angle'])
        # TODO: SEND ALSO BOUNDING BOX
    tuio_server.send_tuio_bundle()


def tuio_send_fiducials():
    target_computer_ip = '132.199.130.68'  # '132.199.117.19'
    tuio_server = TUIOServer(target_computer_ip)

    camera = RealsenseD435Camera()
    camera.start()

    table_surface_extractor = TableSurfaceExtractor()
    fiducials_detector = FiducialsDetector()
    movement_detector = MovementDetector()
    foreground_mask_extractor = ForegroundMaskExtractor()
    touch_detector = TouchDetector()

    table_border = table_surface_extractor.get_table_border()

    while True:
        color_image, depth_image = camera.get_frames()

        if color_image is not None:
            color_image_table = table_surface_extractor.extract_table_area(color_image)

            aruco_markers = fiducials_detector.detect_fiducials(color_image_table)
            movements = movement_detector.detect_movement(color_image_table)
            #touch_points = touch_detector.get_touch_points_final(color_image, depth_image, table_border)

            print(movements)
            #print('Touch Points:', touch_points)


            if len(aruco_markers) > 0:
                print('found marker')
                send_tuio_bundle(tuio_server, aruco_markers)

            for movement in movements:
                cv2.rectangle(color_image, (movement['bounding_rect_x'], movement['bounding_rect_y']), (movement['bounding_rect_x'] + movement['bounding_rect_width'], movement['bounding_rect_y'] + movement['bounding_rect_height']), (0, 255, 0), 2)

            foreground_mask = foreground_mask_extractor.get_foreground_mask(color_image)

            cv2.imshow('frame', foreground_mask)

        key = cv2.waitKey(1)
        # Press esc or 'q' to close the image window
        if key & 0xFF == ord('q') or key == 27:
            cv2.destroyAllWindows()
            break

tuio_send_fiducials()
