#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Based on: https://google.github.io/mediapipe/solutions/hands.html

import sys
import cv2
import numpy as np
import mediapipe as mp

CAMERA_ID = 4

MAX_NUM_HANDS = 4
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5


class HandDetectionService:

    def __init__(self):
        self.capture = cv2.VideoCapture(CAMERA_ID)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.capture.set(cv2.CAP_PROP_FPS, 60)

        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands

        self.hands = self.mp_hands.Hands(max_num_hands=MAX_NUM_HANDS, min_detection_confidence=MIN_DETECTION_CONFIDENCE,
                                         min_tracking_confidence=MIN_TRACKING_CONFIDENCE)
        self.loop()

    def loop(self):
        while self.capture.isOpened():
            success, image = self.capture.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            results_formatted = self.__analyse_frame(image)
            print(results_formatted)

            if cv2.waitKey(1) & 0xFF == 27:
                break
        self.capture.release()

    def __analyse_frame(self, image):

        # Debug image to draw translated points
        black_image = np.zeros(shape=image.shape, dtype=np.uint8)

        image_width = image.shape[1]
        image_height = image.shape[0]

        # Flip the image horizontally for a later selfie-view display, and convert the BGR image to RGB for the detection
        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
        # To improve performance, optionally mark the image as not writeable to pass by reference.
        image.flags.writeable = False

        results = self.hands.process(image)

        # Draw the hand annotations on the image.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        results_formatted = []

        # If hands found
        if results.multi_hand_landmarks:

            # Iterate over each found hand
            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                hand_index = results.multi_handedness[i].classification[0].index
                hand_label = results.multi_handedness[i].classification[0].label
                hand_score = results.multi_handedness[i].classification[0].score

                # New easier and clearer data structure
                hand = {
                    'index': hand_index,
                    'hand_label': hand_label,
                    'hand_score': float("{:.2f}".format(hand_score)),
                    'hand_points': [],
                    'z_values': []
                }

                # A list of 21 Hand landmark points (x,y,z)
                for point in hand_landmarks.landmark:
                    # Translate to image coordinate system and convert to int
                    hand['hand_points'].append((int(point.x * image_width), int(point.y * image_height)))
                    # TODO: z-value should be in same scale as x-value. Maybe translate
                    hand['z_values'].append(point.z)

                results_formatted.append(hand)

                # Draw hand on image
                self.mp_drawing.draw_landmarks(image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

        # Iterate over each hand
        for hand in results_formatted:
            # Iterate over each of the 21 points of the hand
            for i, point in enumerate(hand['hand_points']):
                # ID of index finger tip
                if i == 8:
                    black_image = cv2.circle(black_image, point, 10, (0, 0, 255), -1)
                else:
                    black_image = cv2.circle(black_image, point, 10, (255, 0, 0), -1)

        cv2.imshow('MediaPipe Hands', image)
        cv2.imshow('black', black_image)

        return results_formatted


def main():
    HandDetectionService()
    sys.exit()


if __name__ == '__main__':
    main()
