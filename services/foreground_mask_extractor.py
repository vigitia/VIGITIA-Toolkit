#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://docs.opencv.org/master/de/df4/tutorial_js_bg_subtraction.html

import cv2


class ForegroundMaskExtractor:

    def __init__(self):
        self.fgbg = cv2.createBackgroundSubtractorMOG2(history=1000, detectShadows=True)
        print('Foreground Mask Extractor ready')

    def get_foreground_mask(self, frame):
        blur = cv2.GaussianBlur(frame, (7, 7), 0)

        foreground_mask = self.fgbg.apply(blur, learningRate=0.001)

        # Filter out the shadows
        _, foreground_mask = cv2.threshold(foreground_mask, 254, 255, cv2.THRESH_BINARY)

        # Remove small black regions
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
        foreground_mask = cv2.morphologyEx(foreground_mask, cv2.MORPH_CLOSE, kernel, 2)

        return foreground_mask
