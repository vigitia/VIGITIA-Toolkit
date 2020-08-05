#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://docs.opencv.org/master/de/df4/tutorial_js_bg_subtraction.html

import cv2


class ForegroundMaskExtractor:

    def __init__(self):
        self.fgbg = cv2.createBackgroundSubtractorMOG2(history=1000, detectShadows=1)
        self.fgbg_basic = cv2.createBackgroundSubtractorMOG2(varThreshold=200, detectShadows=0)
        print('[Foreground Mask Extractor]: Ready')

    def get_foreground_mask(self, frame):
        blur = cv2.GaussianBlur(frame, (7, 7), 0)

        foreground_mask = self.fgbg.apply(blur, learningRate=0.001)

        # Filter out the shadows
        _, foreground_mask = cv2.threshold(foreground_mask, 254, 255, cv2.THRESH_BINARY)

        # Remove small black regions
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
        foreground_mask = cv2.morphologyEx(foreground_mask, cv2.MORPH_CLOSE, kernel, 2)

        return foreground_mask

    def get_foreground_mask_depth(self, depth_frame):
        blur = cv2.GaussianBlur(depth_frame, (7, 7), 0)
        foreground_mask = self.fgbg_basic.apply(blur, learningRate=0)

        # Get rid of the small black regions in our mask by applying morphological closing
        # (dilation followed by erosion) with a small x by x pixel kernel
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        foreground_mask = cv2.morphologyEx(foreground_mask, cv2.MORPH_CLOSE, kernel, 2)

        return foreground_mask

    def get_foreground_mask_basic(self, frame):
        # Use the Hue channel on the test background for good detection results
        hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hue, saturation, value = cv2.split(hsv_image)

        blur = cv2.GaussianBlur(value, (7, 7), 0)
        foreground_mask = self.fgbg_basic.apply(blur, learningRate=0)

        # Get rid of the small black regions in our mask by applying morphological closing
        # (dilation followed by erosion) with a small x by x pixel kernel
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        foreground_mask = cv2.morphologyEx(foreground_mask, cv2.MORPH_CLOSE, kernel, 2)

        return foreground_mask
