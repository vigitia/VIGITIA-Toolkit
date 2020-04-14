#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import numpy as np
import cv2
import configparser
# https://stackoverflow.com/questions/9763116/parse-a-tuple-from-a-string
from ast import literal_eval as make_tuple  # Needed to convert strings stored in config file back to tuples

# General constants
WINDOW_NAME = 'VIGITIA_TABLE_STUDY'

# Constants to fill out by the user
CAMERA_ID = 1
TABLE_NAME = 'Esstisch'
TABLE_LENGTH_CM = 42
TABLE_DEPTH_CM = 59
FLIP_IMAGE_VERTICALLY = True
FLIP_IMAGE_HORIZONTALLY = True


class VigitiaTableStudy:

    capture = None
    last_frame = None

    last_mouse_click_coordinates = []

    table_corner_top_left = (0, 0)
    table_corner_top_right = (0, 0)
    table_corner_bottom_left = (0, 0)
    table_corner_bottom_right = (0, 0)

    calibration_mode = False

    def __init__(self):

        self.read_config_file()
        self.init_opencv()
        self.init_video_capture()

        self.loop()

    # In the config file, info like the table corner coordinates are stored
    def read_config_file(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        print(config.sections())

        if len(config.sections()) > 0:
            # Coordinates of table corners for perspective transformation
            self.table_corner_top_left = make_tuple(config['CORNERS']['CornerTopLeft'])
            self.table_corner_top_right = make_tuple(config['CORNERS']['CornerTopRight'])
            self.table_corner_bottom_left = make_tuple(config['CORNERS']['CornerBottomLeft'])
            self.table_corner_bottom_right = make_tuple(config['CORNERS']['CornerBottomRight'])

            print('Successfully read data from config file')
            self.calibration_mode = False
        else:
            print('Error reading data from config file')
            self.calibration_mode = True

    def init_opencv(self):
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
        # Set mouse callbacks to extract the coordinates of clicked spots in the image
        cv2.setMouseCallback(WINDOW_NAME, self.on_mouse_click)

    # Process mouse click events
    def on_mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print((x, y))
            self.last_mouse_click_coordinates.append((x, y))
            if len(self.last_mouse_click_coordinates) > 4:
                self.last_mouse_click_coordinates = []

    def init_video_capture(self):
        self.capture = cv2.VideoCapture(CAMERA_ID)
        # self.capture.set(3, 1920)
        # self.capture.set(4, 1080)
        # self.capture.set(cv2.CAP_PROP_FPS, 1)

    def loop(self):
        while True:
            # Capture frame-by-frame
            ret, frame = self.capture.read()

            if ret:
                if self.calibration_mode:
                    self.display_mode_calibration(frame)
                else:
                    self.check_save_frame(frame)

            key = cv2.waitKey(1)
            # Press 'ESC' or 'Q' to close the image window
            if key & 0xFF == ord('q') or key == 27:
                break
            elif key == 99:  # C as in Calibrate
                self.last_mouse_click_coordinates = []  # Reset list
                self.calibration_mode = not self.calibration_mode

        # When everything done, release the capture
        self.capture.release()
        cv2.destroyAllWindows()

    def display_mode_calibration(self, frame):
        print('In calibration mode')
        # Show circles of previous coordinates
        cv2.circle(frame, self.table_corner_top_left, 2, (0, 0, 255), -1)
        cv2.circle(frame, self.table_corner_top_right, 2, (0, 0, 255), -1)
        cv2.circle(frame, self.table_corner_bottom_left, 2, (0, 0, 255), -1)
        cv2.circle(frame, self.table_corner_bottom_right, 2, (0, 0, 255), -1)

        # Draw circles for clicks in a different color to mark the new points
        for coordinate in self.last_mouse_click_coordinates:
            cv2.circle(frame, coordinate, 2, (0, 255, 0), -1)

        cv2.putText(img=frame, text='Calibration Mode - Press on each of the four corners of the table (' +
                                    str(len(self.last_mouse_click_coordinates)) + '/4)',
                    org=(int(frame.shape[1] / 6), int(frame.shape[0] / 2)),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(0, 0, 255))

        if len(self.last_mouse_click_coordinates) == 4:
            print('Calibrated')
            self.update_table_corner_calibration()

        cv2.imshow(WINDOW_NAME, frame)

    def update_table_corner_calibration(self):
        # Order coordinates by x value
        coordinates = sorted(self.last_mouse_click_coordinates)

        if coordinates[0][1] > coordinates[1][1]:
            self.table_corner_top_left = coordinates[1]
            self.table_corner_bottom_left = coordinates[0]
        else:
            self.table_corner_top_left = coordinates[0]
            self.table_corner_bottom_left = coordinates[1]

        if coordinates[2][1] > coordinates[3][1]:
            self.table_corner_top_right = coordinates[3]
            self.table_corner_bottom_right = coordinates[2]
        else:
            self.table_corner_top_right = coordinates[2]
            self.table_corner_bottom_right = coordinates[3]

        # Update config
        config = configparser.ConfigParser()
        config['CORNERS'] = {'CornerTopLeft': str(self.table_corner_top_left),
                             'CornerTopRight': str(self.table_corner_top_right),
                             'CornerBottomLeft': str(self.table_corner_bottom_left),
                             'CornerBottomRight': str(self.table_corner_bottom_right)}

        with open('config.ini', 'w') as configfile:
            config.write(configfile)

        # Go back to default display mode
        self.calibration_mode = False

    def check_save_frame(self, frame):
        if self.last_frame is None:
            self.last_frame = frame
            return

        frame = self.perspective_transformation(frame)
        cv2.imshow(WINDOW_NAME, frame)
        #cv2.imwrite('test.png', frame)

    # Based on: https://www.youtube.com/watch?v=PtCQH93GucA
    def perspective_transformation(self, frame):
        x = frame.shape[1]

        pts1 = np.float32([list(self.table_corner_top_left), list(self.table_corner_top_right),
                           list(self.table_corner_bottom_left), list(self.table_corner_bottom_right)])
        pts2 = np.float32([[0, 0], [x, 0], [0, x / 2], [x, x / 2]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)

        frame = cv2.warpPerspective(frame, matrix, (x, int(x / 2)))

        frame = self.resize_frame_to_table(frame)

        return frame

    def resize_frame_to_table(self, frame):
        x, y = self.calculate_aspect_ratio(TABLE_LENGTH_CM, TABLE_DEPTH_CM)
        new_width = int(frame.shape[1])
        new_height = int((frame.shape[1] / x) * y)
        frame = cv2.resize(frame, (new_height, new_width), interpolation=cv2.INTER_AREA)

        if FLIP_IMAGE_HORIZONTALLY:
            frame = cv2.flip(frame, 1)
        if FLIP_IMAGE_VERTICALLY:
            frame = cv2.flip(frame, 0)

        return frame


    # Function taken from: https://gist.github.com/Integralist/4ca9ff94ea82b0e407f540540f1d8c6c
    def calculate_aspect_ratio(self, width: int, height: int):
        temp = 0

        def gcd(a, b):
            """The GCD (greatest common divisor) is the highest number that evenly divides both width and height."""
            return a if b == 0 else gcd(b, a % b)

        if width == height:
            return "1:1"

        if width < height:
            temp = width
            width = height
            height = temp

        divisor = gcd(width, height)

        x = int(width / divisor) if not temp else int(height / divisor)
        y = int(height / divisor) if not temp else int(width / divisor)

        return x, y




def main():
    vigitiaTableStudy = VigitiaTableStudy()
    sys.exit()


if __name__ == '__main__':
    main()
