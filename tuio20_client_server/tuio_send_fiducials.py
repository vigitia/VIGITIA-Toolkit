#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from sensors.cameras.realsenseD435.realsense_D435_camera import RealsenseD435Camera
from tuio20_client_server.tuio_server import TUIOServer
from calibration.table_surface_extractor import TableSurfaceExtractor
from services.fiducials_detector import FiducialsDetector


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
    tuio_server = TUIOServer()

    camera = RealsenseD435Camera()
    camera.start()

    table_surface_extractor = TableSurfaceExtractor()
    fiducials_detector = FiducialsDetector()

    while True:
        color_image, depth_image = camera.get_frames()

        if color_image is not None:
            color_image = table_surface_extractor.extract_table_area(color_image)
            aruco_markers = fiducials_detector.detect_fiducials(color_image)
            if len(aruco_markers) > 0:
                print('found marker')
                send_tuio_bundle(tuio_server, aruco_markers)


tuio_send_fiducials()
