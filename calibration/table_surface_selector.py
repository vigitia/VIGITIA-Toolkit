#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import cv2
import configparser
# https://stackoverflow.com/questions/9763116/parse-a-tuple-from-a-string
from ast import literal_eval as make_tuple  # Needed to convert strings stored in config file back to tuples
from sensors.cameras.realsenseD435.realsense_D435_camera import RealsenseD435Camera


class TableSurfaceSelector:

    last_mouse_click_coordinates = []

    # TODO: Add support for differently shaped tables (not just rectangles)
    table_corner_top_left = (0, 0)
    table_corner_top_right = (0, 0)
    table_corner_bottom_left = (0, 0)
    table_corner_bottom_right = (0, 0)

    def __init__(self):
        self.camera = RealsenseD435Camera()
        self.camera.start()

        self.read_config_file()
        self.init_opencv()
        self.loop()

    def init_opencv(self):
        cv2.namedWindow('realsense', cv2.WINDOW_AUTOSIZE)

        # Set mouse callbacks to extract the coordinates of clicked spots in the image
        cv2.setMouseCallback('realsense', self.on_mouse_click)

    # Log mouse click positions to the console
    def on_mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print((x, y))
            self.last_mouse_click_coordinates.append((x, y))
            if len(self.last_mouse_click_coordinates) > 4:
                self.last_mouse_click_coordinates = []

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
        else:
            print('Error reading data from config file')

    # Streaming loop
    def loop(self):
        while True:
            color_image, depth_image = self.camera.get_frames()

            if color_image is not None:
                self.display_mode_calibration(color_image)
            else:
                print("No color image")

            key = cv2.waitKey(1)
            # Press esc or 'q' to close the image window
            if key & 0xFF == ord('q') or key == 27:
                cv2.destroyAllWindows()
                break

    def display_mode_calibration(self, color_image):
        print("In calibration mode")
        # Show circles of previous coordinates

        cv2.circle(color_image, self.table_corner_top_left, 2, (0, 0, 255), -1)
        cv2.circle(color_image, self.table_corner_top_right, 2, (0, 0, 255), -1)
        cv2.circle(color_image, self.table_corner_bottom_left, 2, (0, 0, 255), -1)
        cv2.circle(color_image, self.table_corner_bottom_right, 2, (0, 0, 255), -1)

        # Draw circles for clicks in a different color to mark the new points
        for coordinate in self.last_mouse_click_coordinates:
            cv2.circle(color_image, coordinate, 2, (0, 255, 0), -1)

        cv2.putText(img=color_image, text='Calibration Mode - Press on each of the four corners of the table (' +
                                          str(len(self.last_mouse_click_coordinates)) + '/4)',
                    org=(int(color_image.shape[1] / 6), int(color_image.shape[0] / 2)),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(0, 0, 255))

        if len(self.last_mouse_click_coordinates) == 4:
            print('Calibrated')
            self.update_table_corner_calibration()

        cv2.imshow('realsense', color_image)

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

        self.camera.stop()
        cv2.destroyAllWindows()
        sys.exit(0)


    def project_targets_on_table(self):
        # TODO: Project Targets on table and let a user click them. Then we have points that lie for sure on the table surface
        pass


def main():
    TableSurfaceSelector()
    sys.exit()


if __name__ == '__main__':
    main()
