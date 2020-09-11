
# Inspired by https://towardsdatascience.com/object-detection-with-less-than-10-lines-of-code-using-python-2d28eebc5b11
import cv2
from cvlib import detect_common_objects
from cvlib.object_detection import draw_bbox

import numpy as np

DEBUG_MODE = True


class GenericObjectDetector:

    def __init__(self):
        print('[Generic Object Detector] Service Ready')

    def detect_generic_objects(self, frame, mask):

        detected_objects = []

        extracted_objects = self.extract_objects(frame, mask)

        for i, extracted_object in enumerate(extracted_objects):
            if i > 9:
                break
            label, confidence = self.detect_extracted_object(extracted_object['extracted_object'])
            print(label)
            cv2.rectangle(frame, (extracted_object['x'], extracted_object['y']), (extracted_object['width'], extracted_object['height']), (0, 0, 255), 2)

            cv2.putText(img=frame, text=str(label), org=(int(extracted_object['x']), int(extracted_object['y'])),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=2, color=(0, 0, 0))


        cv2.imshow('labels', frame)


        # print(frame.shape)
        #
        # # bbox, label, conf = detect_common_objects(frame, confidence=0.25)
        # # bbox, label, conf = detect_common_objects(frame, confidence=0.75, enable_gpu=True)
        # bbox, label, conf = detect_common_objects(frame, confidence=0.3, model='yolov3-tiny')
        #
        # if DEBUG_MODE:
        #     output_image = draw_bbox(frame, bbox, label, conf)
        #
        # for i in range(len(bbox)):
        #     detected_objects.append({
        #         'label': label[i],
        #         'bbox': bbox[i],
        #         'conf': conf[i]
        #     })
        #
        # print(detected_objects)

        return detected_objects

    def detect_extracted_object(self, extracted_object):

        label = ''
        confidence = 0

        # bbox, label, conf = detect_common_objects(frame, confidence=0.25)
        # bbox, label, conf = detect_common_objects(frame, confidence=0.75, enable_gpu=True)
        bbox, label, conf = detect_common_objects(extracted_object, confidence=0.3, model='yolov3-tiny')

        if len(label) > 0:
            label = label
            confidence = conf[0]

        return label, confidence

    def extract_objects(self, frame, mask):

        kernel = np.ones((5, 5), np.uint8)
        frame = cv2.erode(frame, kernel, iterations=2)
        frame = cv2.dilate(frame, kernel, iterations=2)

        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        contours_filtered = []

        MIN_CONTOUR_SIZE = 100

        for i, contour in enumerate(contours):
            if hierarchy[0, i, 3] <= 1:
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

        EXPAND_BOX = 20
        MIN_LENGTH = 50

        objects_extracted = []

        for i in range(len(contours_filtered)):
            color = (200, 100, 50)
            x = int(boundRect[i][0]) - EXPAND_BOX
            y = int(boundRect[i][1]) - EXPAND_BOX
            width = int(boundRect[i][0] + boundRect[i][2] + EXPAND_BOX)
            height = int(boundRect[i][1] + boundRect[i][3]) + EXPAND_BOX

            extracted_object = frame.copy()[y:y + height, x:x + width]

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