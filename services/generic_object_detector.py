
# Inspired by https://towardsdatascience.com/object-detection-with-less-than-10-lines-of-code-using-python-2d28eebc5b11
import cv2
from cvlib import detect_common_objects
from cvlib.object_detection import draw_bbox

import numpy as np


class GenericObjectDetector:

    def __init__(self):
        print('[Generic Object Detector] Service Ready')

    def detect_generic_objects(self, frame, mask):

        self.extract_objects(frame, mask)

        # bbox, label, conf = detect_common_objects(frame, confidence=0.25)
        # bbox, label, conf = detect_common_objects(frame, confidence=0.75, enable_gpu=True)
        bbox, label, conf = detect_common_objects(frame, confidence=0.3, model='yolov3-tiny')

        output_image = draw_bbox(frame, bbox, label, conf)

        detected_objects = []

        for i in range(len(bbox)):
            detected_objects.append({
                'label': label[i],
                'bbox': bbox[i],
                'conf': conf[i]
            })

        print(detected_objects)

        return output_image, detected_objects

    def extract_objects(self, frame, mask):
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        contours_filtered = []
        hierarchy_filtered = []

        for i, contour in enumerate(contours):
            if hierarchy[0, i, 3] <= 1:
                print(hierarchy[0, i, 3])
                area = cv2.contourArea(contour)
                if area > 100:
                    contours_filtered.append(contour)
                    # hierarchy_filtered.append(hierarchy[0,i,3])

        print(hierarchy_filtered)

        # https://docs.opencv.org/3.4/da/d0c/tutorial_bounding_rects_circles.html
        contours_poly = [None] * len(contours)
        boundRect = [None] * len(contours)
        for i, c in enumerate(contours_filtered):
            contours_poly[i] = cv2.approxPolyDP(c, 3, True)
            boundRect[i] = cv2.boundingRect(contours_poly[i])

        drawing = frame.copy()

        EXPAND_BOX = 50

        objects_extracted = []

        for i in range(len(contours_filtered)):
            color = (200, 100, 50)
            x = int(boundRect[i][0]) - EXPAND_BOX
            y = int(boundRect[i][1]) - EXPAND_BOX
            width = int(boundRect[i][0] + boundRect[i][2] + EXPAND_BOX)
            height = int(boundRect[i][1] + boundRect[i][3]) + EXPAND_BOX

            cv2.rectangle(drawing, (x, y), (width, height), color, 2)
            object = frame.copy()[y:y + height, x:x + width]
            objects_extracted.append(object)

        cv2.imshow('Contours', drawing)