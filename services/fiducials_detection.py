#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import cv2
import cv2.aruco as aruco
import numpy as np
from sensors.cameras.realsenseD435.realsense_D435_camera import RealsenseD435Camera

DEBUG_MODE = True

class FiducialsDetection:

    aruco_dictionary = None
    aruco_detector_parameters = None

    marker_frame = None

    def __init__(self):
        self.camera = RealsenseD435Camera()
        self.camera.start()

        self.init_aruco_tracking()

        self.loop()

    def init_aruco_tracking(self):
        self.aruco_dictionary = aruco.Dictionary_get(aruco.DICT_4X4_100)
        self.aruco_detector_parameters = aruco.DetectorParameters_create()
        self.aruco_detector_parameters.adaptiveThreshConstant = 10  # TODO: Tweak value

    # Streaming loop
    def loop(self):
        while True:
            color_image, depth_image = self.camera.get_frames()

            if color_image is not None:
                aruco_markers = self.track_aruco_markers(color_image)
                tuio_messages = self.to_tuio_messages(aruco_markers)

            key = cv2.waitKey(1)
            # Press esc or 'q' to close the image window
            if key & 0xFF == ord('q') or key == 27:
                cv2.destroyAllWindows()
                break

        self.camera.stop()
        cv2.destroyAllWindows()
        sys.exit(0)

    # Code for tracking Aruco markers taken from https://github.com/njanirudh/Aruco_Tracker
    def track_aruco_markers(self, frame_color):

        gray = cv2.cvtColor(frame_color, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected_points = aruco.detectMarkers(gray, self.aruco_dictionary,
                                                            parameters=self.aruco_detector_parameters)

        aruco_markers = []

        # check if the ids list is not empty
        if np.all(ids is not None):
            if DEBUG_MODE:
                frame = np.zeros((frame_color.shape[0], frame_color.shape[1], 3), np.uint8)
                # Draw a square around the markers
                aruco.drawDetectedMarkers(frame, corners, ids)

            for i in range(len(ids)):
                aruco_marker = {'id': ids[i][0],
                                'angle': self.calculate_aruco_marker_rotation(corners[i][0], frame),
                                'corners': corners[i][0],
                                'centroid': self.centroid(corners[i][0])}

                aruco_markers.append(aruco_marker)

                if DEBUG_MODE:
                    cv2.putText(img=frame, text=str(aruco_marker['angle']) + ' Grad',
                                org=(int(frame.shape[1] / 6), int(frame.shape[0] / 4)),
                                fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=2, color=(255, 255, 255))

        if DEBUG_MODE:
            cv2.imshow('marker', frame)

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

    def to_tuio_messages(self, aruco_markers):
        tuio_messages = []

        for marker in aruco_markers:
            #print(marker)
            blank_tuio_message = '/tuio2/tok {s_id} {tu_id} {c_id} {x_pos} {y_pos} {angle}'
            tuio_message = blank_tuio_message.format(s_id=marker['id'], tu_id=0, c_id=marker['id'], x_pos=marker['centroid'][0], y_pos=marker['centroid'][0], angle=marker['angle'])
            print(tuio_message)

            tuio_messages.append(tuio_message)

        return tuio_messages


def main():
    FiducialsDetection()
    sys.exit()


if __name__ == '__main__':
    main()
