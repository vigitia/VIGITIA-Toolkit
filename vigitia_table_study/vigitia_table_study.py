#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup procedure:

1. Mount a camera above the table so that the entire table is within the frame of the camera
2. Modify the user constants below (some tweaks later might be necessary, too)
3. Start the script. if no previous config file is found, the application will launch directly to calibration mode.
   Click on the four corners of the table.
4. Now the script is ready. If the table is moved, the four corner calibration needs to be done again (Just press 'C'
   to enter calibration mode)
"""

# TODO: Only rectangle tables are currently supported. Support more shapes
# TODO: Changes in brightness can also trigger

import os
import sys
import time
import datetime
import numpy as np
import cv2
import configparser
# https://stackoverflow.com/questions/9763116/parse-a-tuple-from-a-string
from ast import literal_eval as make_tuple  # Needed to convert strings stored in config file back to tuples
from skimage.measure import compare_ssim
from pathlib import Path
import imutils

from sensors.cameras.realsenseD435.realsense_D435_camera import RealsenseD435Camera

# General constants
WINDOW_NAME = 'VIGITIA_TABLE_STUDY'

# Constants to fill out by the user
USE_REALSENSE_D435_CAMERA = True  # Select whether the INTEL REALSENSE D435 camera or a generic webcam should be used
CAMERA_ID = 1  # IF USE_REALSENSE_D435_CAMERA == False, select the camera ID for Opencv video capture
CAMERA_RESOLUTION_X = 1280
CAMERA_RESOLUTION_Y = 720
CAMERA_FPS = 30
TABLE_NAME = 'Esstisch'  # This name is used for the filenames of the saved images
TABLE_LENGTH_CM = 41  # Length and depth of the table are used to store the images distortion free in the correct aspect
TABLE_DEPTH_CM = 57   # ratio after perspective transformation
FLIP_IMAGE_VERTICALLY = False  # If images are not saved in the correct orientation, this can be fixed here
FLIP_IMAGE_HORIZONTALLY = False
MIN_TIME_BETWEEN_SAVED_FRAMES_SEC = 30  # Minimum distance between two saved frames in seconds
MIN_TIME_WAIT_AFTER_MOVEMENT_SEC = 10  # Minimum time to wait
MIN_DIFFERENCE_PERCENT_TO_SAVE = 5  # If the current image is at least X % different from the last saved image -> save
MIN_AREA_FOR_MOVEMENT_PX = 100  # An area where movement is detected needs to be at least XXX pixels in size
MOVEMENT_THRESHOLD = 30  # Cutoff threshold for the difference image of two frames for movement detection
MIN_BRIGHTNESS = 50  # Overall brightness of the image from 0 (completely black) to 255 (completely white)
DEBUG_MODE = True  # If Debug mode is on, more data is displayed
DIFFERCENCE_CUTOFF_VALUE = 220


class VigitiaTableStudy:

    capture = None
    last_frame = None
    last_check_saving_frame_timestamp = None
    last_saved_frame = None
    last_movement_timestamp = None

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

    # Either the INTEL REALSENSE D435 or a generic (web)cam is used
    def init_video_capture(self):
        if USE_REALSENSE_D435_CAMERA:
            self.realsense = RealsenseD435Camera()
            self.realsense.start()
        else:
            self.capture = cv2.VideoCapture(CAMERA_ID)
            self.capture.set(3, CAMERA_RESOLUTION_X)
            self.capture.set(4, CAMERA_RESOLUTION_Y)
            self.capture.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

    # The main application loop
    def loop(self):
        while True:

            # Get frames
            if USE_REALSENSE_D435_CAMERA:
                frame, depth_image = self.realsense.get_frames()
            else:
                ret, frame = self.capture.read()

            # If a new frame has arrived
            if frame is not None:
                if self.calibration_mode:
                    self.display_mode_calibration(frame)
                else:
                    frame_full = frame.copy()  # The entire picture the camera sees
                    frame_table = self.perspective_transformation(frame)  # Just the table area

                    # If all criteria are fulfilled, save the two frames to the hard drive
                    if self.check_save_frame(frame_table):
                        self.save_frame(frame_table, frame_full)

            key = cv2.waitKey(1)
            # Press 'ESC' or 'Q' to close the image window
            if key & 0xFF == ord('q') or key == 27:
                break
            elif key == 99:  # C as in Calibrate to activate calibration mode
                self.last_mouse_click_coordinates = []  # Reset list
                self.calibration_mode = not self.calibration_mode

        if USE_REALSENSE_D435_CAMERA:
            self.realsense.stop()
        else:
            self.capture.release()
        cv2.destroyAllWindows()

    # Code for when the calibration mode is acitve
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

    # Check if the current frame fulfills all criteria to be saved
    def check_save_frame(self, frame):
        now = time.time()

        # Init values at the beginning
        if self.last_frame is None:
            self.last_frame = frame
            self.last_saved_frame = frame
            self.last_check_saving_frame_timestamp = now
            self.last_movement_timestamp = now
            return False

        time_since_last_check_saving_frame = now - self.last_check_saving_frame_timestamp
        time_since_last_movement = now - self.last_movement_timestamp

        # Don't save images at all if the room is too dark
        brightness = self.get_brightness_value(frame)
        if brightness < MIN_BRIGHTNESS:
            print('Too Dark')
            return False

        # Check the image for current movement
        movement = self.detect_movement(frame)
        if movement:
            self.last_movement_timestamp = now

        # Set the last stored frame to the current frame (needed the next time the code checks for movement)
        self.last_frame = frame

        # If enough time has passed since last movement and last saved frame
        if time_since_last_movement > MIN_TIME_WAIT_AFTER_MOVEMENT_SEC and \
                time_since_last_check_saving_frame > MIN_TIME_BETWEEN_SAVED_FRAMES_SEC:

            self.last_check_saving_frame_timestamp = now

            # Compare the difference between the last saved frame and the current frame
            difference = self.frame_difference(frame)
            if difference >= MIN_DIFFERENCE_PERCENT_TO_SAVE:
                return True  # All criteria are fulfulled

            return False

        cv2.imshow(WINDOW_NAME, frame)

    # Get an value for the overall brightness of the image. We dont want to save images that are too dark to be useful
    # https://stackoverflow.com/questions/14243472/estimate-brightness-of-an-image-opencv
    @staticmethod
    def get_brightness_value(frame):
        hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hue, saturation, value = cv2.split(hsv_image)
        brightness = np.mean(value)
        return brightness

    # Based onhttps://www.pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/
    def detect_movement(self, frame):
        grey_new = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        grey_old = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2GRAY)
        grey_new = cv2.GaussianBlur(grey_new, (21, 21), 0)
        grey_old = cv2.GaussianBlur(grey_old, (21, 21), 0)

        # compute the absolute difference between the current frame and first frame
        frame_delta = cv2.absdiff(grey_old, grey_new)
        thresh = cv2.threshold(frame_delta, MOVEMENT_THRESHOLD, 255, cv2.THRESH_BINARY)[1]
        # dilate the thresholded image to fill in holes, then find contours on thresholded image
        thresh = cv2.dilate(thresh, None, iterations=2)

        if DEBUG_MODE:
            cv2.imshow('thresh', thresh)

        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)

        movement = False

        frame_show_movement = frame.copy()

        # loop over the contours
        for contour in contours:
            # if the contour is too small, ignore it
            if cv2.contourArea(contour) >= MIN_AREA_FOR_MOVEMENT_PX:
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(frame_show_movement, (x, y), (x + w, y + h), (0, 255, 0), 2)
                movement = True

        if DEBUG_MODE:
            if movement:
                print('Movement detected')
            cv2.imshow('movement', frame_show_movement)

        return movement

    # Calculate the difference between the current and the last frame in percent
    # Based on https://www.pyimagesearch.com/2017/06/19/image-difference-with-opencv-and-python/
    def frame_difference(self, frame):
        # Convert frame to grey and blur them to reduce noise
        grey_new = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        grey_old = cv2.cvtColor(self.last_saved_frame, cv2.COLOR_BGR2GRAY)
        grey_new = cv2.GaussianBlur(grey_new, (21, 21), 0)
        grey_old = cv2.GaussianBlur(grey_old, (21, 21), 0)

        # compute the Structural Similarity Index (SSIM) between the two images,
        # ensuring that the difference image is returned
        (score, diff) = compare_ssim(grey_new, grey_old, full=True)
        diff = (diff * 255).astype("uint8")
        diff = np.where(diff > DIFFERCENCE_CUTOFF_VALUE, 255, diff)
        diff = np.where(diff < 255, 0, diff)
        diff = cv2.bitwise_not(diff)

        if DEBUG_MODE:
            cv2.imshow('Areas of detected difference', diff)

        difference = int((np.sum(diff == 255) / diff.size) * 100)
        print('Difference:', difference, '%')

        return difference

    # Write the two frames to the hard drive
    def save_frame(self, frame_table, frame_full):
        print('SAVING FRAME!')

        self.last_saved_frame = frame_table

        # The full sensor image has not been flipped yet like the table image. This is done now here
        frame_full = self.flip_image(frame_full)

        now = datetime.datetime.now()
        folder_name = str(now.date())

        # Create two folders if they not exist yet (main folder is the name of the table, subfolder is the current date)
        Path(os.path.join(TABLE_NAME, folder_name)).mkdir(parents=True, exist_ok=True)

        # Save the frames
        time_string = now.strftime('%Y-%m-%d_%H-%M-%S-%f')[:-4]
        file_name_table = TABLE_NAME + '_' + time_string + '_table.png'
        file_name_full = TABLE_NAME + '_' + time_string + '_full.png'

        cv2.imwrite(os.path.join(os.path.join(TABLE_NAME, folder_name), file_name_table), frame_table)
        cv2.imwrite(os.path.join(os.path.join(TABLE_NAME, folder_name), file_name_full), frame_full)

    # Do a perspective transformation to extract the table surface
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

    # Resize the image after perspective transformation so that the table aspect ratio is preserved
    def resize_frame_to_table(self, frame):
        x, y = self.calculate_aspect_ratio(TABLE_LENGTH_CM, TABLE_DEPTH_CM)
        new_width = int(frame.shape[1])
        new_height = int((frame.shape[1] / x) * y)
        frame = cv2.resize(frame, (new_height, new_width), interpolation=cv2.INTER_AREA)

        frame = self.flip_image(frame)

        return frame

    # To save the image in the correct orientation (even if the camera is rotated)
    @staticmethod
    def flip_image(frame):
        if FLIP_IMAGE_HORIZONTALLY:
            frame = cv2.flip(frame, 1)
        if FLIP_IMAGE_VERTICALLY:
            frame = cv2.flip(frame, 0)

        return frame

    # Calculate the aspect ratio of the table to save images after perspective transformation without distortion
    # Method taken from: https://gist.github.com/Integralist/4ca9ff94ea82b0e407f540540f1d8c6c
    @staticmethod
    def calculate_aspect_ratio(width: int, height: int):
        temp = 0

        def gcd(a, b):
            # The GCD (greatest common divisor) is the highest number that evenly divides both width and height.
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
    vigitia_table_study = VigitiaTableStudy()
    sys.exit()


if __name__ == '__main__':
    main()
