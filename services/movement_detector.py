#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import imutils
import numpy as np

MIN_AREA_FOR_MOVEMENT = 1000  # Min size in pixels of a area where movement has been detected to count
MOVEMENT_THRESH = 20

DEBUG_MODE = True


class MovementDetector:

    last_frame = None

    def __init__(self):
        print('Movement Detector ready')


# Check if movement was detected within the frame
    # Based on https://www.pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/
    def detect_movement(self, frame):

        # List where all areas of movement will be collected
        movements = []

        if self.last_frame is None:
            self.last_frame = frame.copy()
            return movements

        # The current and the last captured frame are compared to one another.
        # Convert both frames to grey and blur them generously to prevent noise in the image to cause an erroneously
        # detection.
        grey_new = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2GRAY)
        grey_old = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2GRAY)
        grey_new = cv2.GaussianBlur(grey_new, (21, 21), 0)
        grey_old = cv2.GaussianBlur(grey_old, (21, 21), 0)

        # Compute the absolute difference between the current frame and first frame
        frame_delta = cv2.absdiff(grey_old, grey_new)

        # Now threshold the difference image
        thresh = cv2.threshold(frame_delta,  MOVEMENT_THRESH, 255, cv2.THRESH_BINARY)[1]
        # dilate the thresholded image to fill in holes, then find contours on thresholded image
        kernel = np.ones((21, 21), np.uint8)
        dilate = cv2.dilate(thresh, kernel, iterations=5)

        # Find contours in the thresholded image (Those are areas where movement has been detected)
        contours = cv2.findContours(dilate.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)

        # Loop over the contours
        for contour in contours:
            # if the contour is too small, ignore it. Otherwise we accept it as an area where movement has been detected
            if cv2.contourArea(contour) >= MIN_AREA_FOR_MOVEMENT:
                (x, y, w, h) = cv2.boundingRect(contour)
                movement = {'bounding_rect_x': x,
                            'bounding_rect_y': y,
                            'bounding_rect_width': w,
                            'bounding_rect_height': h}

                movements.append(movement)

        self.last_frame = frame.copy()

        return movements
