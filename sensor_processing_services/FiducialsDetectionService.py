#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import cv2.aruco as aruco
import numpy as np


ADAPTIVE_THRESH_CONSTANT = 10  # TODO: Find best value
ARUCO_DICT = aruco.DICT_4X4_100


class FiducialsDetector:

    aruco_dictionary = None
    aruco_detector_parameters = None

    marker_frame = None

    def __init__(self):
        self.init_aruco_tracking()
        print('[FiducialsDetector]: Ready')

    def init_aruco_tracking(self):
        self.aruco_dictionary = aruco.Dictionary_get(ARUCO_DICT)
        self.aruco_detector_parameters = aruco.DetectorParameters_create()
        self.aruco_detector_parameters.adaptiveThreshConstant = ADAPTIVE_THRESH_CONSTANT

    # Code for tracking Aruco markers based on https://github.com/njanirudh/Aruco_Tracker
    def detect_fiducials(self, frame_color):
        gray = cv2.cvtColor(frame_color, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected_points = aruco.detectMarkers(gray, self.aruco_dictionary,
                                                            parameters=self.aruco_detector_parameters)

        aruco_markers = []

        # check if the ids list is not empty
        if np.all(ids is not None):
            for i in range(len(ids)):
                aruco_marker = {'id': ids[i][0],
                                'angle': self.calculate_aruco_marker_rotation(corners[i][0], frame_color),
                                'corners': corners[i][0],
                                'centroid': self.centroid(corners[i][0])}

                aruco_markers.append(aruco_marker)

        return aruco_markers

    # Calculate the rotation of an aruco marker relative to the frame
    # Returns the angle in the range from 0° to 360°
    def calculate_aruco_marker_rotation(self, aruco_marker_corners, frame):
        tracker_point_one = aruco_marker_corners[0]
        tracker_point_two = aruco_marker_corners[1]
        v1 = np.array([frame.shape[0], 0])
        v2 = np.array([tracker_point_two[0] - tracker_point_one[0], tracker_point_two[1] - tracker_point_one[1]])

        angle = self.calculate_angle(v1, v2)
        return angle

    # Calculate the angle between the two given vectors
    def calculate_angle(self, v1, v2):
        # https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python
        angle = np.math.atan2(np.linalg.det([v1, v2]), np.dot(v1, v2))
        angle = np.degrees(angle)
        if angle < 0:
            angle = angle + 360
        return int(angle)

    # Get the centroid of a polygon
    # https://progr.interplanety.org/en/python-how-to-find-the-polygon-center-coordinates/
    def centroid(self, vertexes):
        _x_list = [vertex[0] for vertex in vertexes]
        _y_list = [vertex[1] for vertex in vertexes]
        _len = len(vertexes)
        _x = sum(_x_list) / _len
        _y = sum(_y_list) / _len
        return (_x, _y)
