
# Inspired by https://towardsdatascience.com/object-detection-with-less-than-10-lines-of-code-using-python-2d28eebc5b11
import cv2
from cvlib import detect_common_objects
from cvlib.object_detection import draw_bbox

import numpy as np

DEBUG_MODE = True


class ObjectDetectionService:

    def __init__(self):
        print('[ObjectDetectionService]: Ready')

    def detect_objects_basic(self, frame, mask):

        detected_objects = []

        print(frame.shape)

        # bbox, label, conf = detect_common_objects(frame, confidence=0.25)
        # bbox, label, conf = detect_common_objects(frame, confidence=0.75, enable_gpu=True)
        bbox, label, conf = detect_common_objects(frame, confidence=0.3, model='yolov3-tiny')

        if DEBUG_MODE:
            output_image = draw_bbox(frame, bbox, label, conf)
            cv2.imshow('all objects', output_image)

        # for i in range(len(bbox)):
        #     detected_objects.append({
        #         'label': label[i],
        #         'bbox': bbox[i],
        #         'conf': conf[i],
        #         'x': extracted_object['x'],
        #         'y': extracted_object['y'],
        #         'width': extracted_object['width'],
        #         'height': extracted_object['height'],
        #         'center_x': int(extracted_object['x'] + extracted_object['width'] / 2),
        #         'center_y': int(extracted_object['y'] + extracted_object['height'] / 2)
        #     })

            print(detected_objects)

        return detected_objects

    def detect_generic_objects(self, frame, mask):

        detected_objects = []

        extracted_objects = self.extract_objects(frame, mask)

        for i, extracted_object in enumerate(extracted_objects):
            if i > 9:
                break
            label, confidence = self.detect_extracted_object(extracted_object['extracted_object'])

            cv2.rectangle(frame, (extracted_object['x'], extracted_object['y']),
                          (extracted_object['x'] + extracted_object['width'],
                           extracted_object['y'] + extracted_object['height']), (0, 0, 255), 2)

            if len(label) > 0:
                detected_objects.append({
                    'label': label,
                    'conf': confidence,
                    'x': extracted_object['x'],
                    'y': extracted_object['y'],
                    'width': extracted_object['width'],
                    'height': extracted_object['height'],
                    'center_x': int(extracted_object['x'] + extracted_object['width'] / 2),
                    'center_y': int(extracted_object['y'] + extracted_object['height'] / 2)
                })

                cv2.putText(img=frame, text=str(label), org=(int(extracted_object['x']), int(extracted_object['y'])),
                            fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=2, color=(0, 0, 0))

        cv2.imshow('labels', frame)

        return detected_objects

    def detect_extracted_object(self, extracted_object):

        label = ''
        confidence = 0

        # bbox, label, conf = detect_common_objects(extracted_object, confidence=0.25)
        # bbox, label, conf = detect_common_objects(extracted_object, confidence=0.75, enable_gpu=True)
        bbox, label, conf = detect_common_objects(extracted_object, confidence=0.25, model='yolov3-tiny')


        if len(label) > 0:
            print(label, conf)
            label = label[0]
            confidence = conf[0]

        return label, confidence

    def extract_objects(self, frame, foreground_mask):

        MIN_CONTOUR_SIZE = 1000
        MAX_HIERARCHY_DEPTH = 10

        #mask = cv2.bitwise_not(mask)

        kernel = np.ones((9, 9), np.uint8)
        foreground_mask = cv2.erode(foreground_mask, kernel, iterations=4)
        #mask = cv2.dilate(mask, kernel, iterations=3)
        cv2.imshow('mask', foreground_mask)

        contours, hierarchy = cv2.findContours(foreground_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        contours_filtered = []

        for i, contour in enumerate(contours):
            if hierarchy[0, i, 3] <= MAX_HIERARCHY_DEPTH:
                #print(hierarchy[0, i, 3])
                area = cv2.contourArea(contour)
                if area > MIN_CONTOUR_SIZE:
                    contours_filtered.append(contour)

        # https://docs.opencv.org/3.4/da/d0c/tutorial_bounding_rects_circles.html
        contours_poly = [None] * len(contours)
        boundRect = [None] * len(contours)
        for i, c in enumerate(contours_filtered):
            contours_poly[i] = cv2.approxPolyDP(c, 3, True)
            boundRect[i] = cv2.boundingRect(contours_poly[i])

        EXPAND_BOX = 50
        MIN_LENGTH = 50

        objects_extracted = []

        for i in range(len(contours_filtered)):
            x = boundRect[i][0] - EXPAND_BOX
            y = boundRect[i][1] - EXPAND_BOX
            width = boundRect[i][2] + 2 * EXPAND_BOX
            height = boundRect[i][3] + 2 * EXPAND_BOX

            if width > MIN_LENGTH and height > MIN_LENGTH:
                copy = frame.copy()
                extracted_object = copy[y:y+height, x:x+width]
                if i == 3:
                    print(extracted_object.shape)
                if extracted_object.shape[0] > MIN_LENGTH and extracted_object.shape[1] > MIN_LENGTH:

                    object_info = {
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height,
                        'extracted_object': extracted_object
                    }

                    objects_extracted.append(object_info)

        return objects_extracted
