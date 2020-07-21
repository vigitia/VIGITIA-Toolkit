#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import cv2
import numpy as np
import configparser
from ast import literal_eval as make_tuple  # Needed to convert strings stored in config file back to tuples

CONFIG_FILE_NAME = 'config.ini'

class TableSurfaceExtractor:

    table_corner_top_left = (0, 0)
    table_corner_top_right = (0, 0)
    table_corner_bottom_left = (0, 0)
    table_corner_bottom_right = (0, 0)

    def __init__(self):
        print('Init TableSurfaceExtractor')

        print(os.path.join(os.path.dirname(__file__), CONFIG_FILE_NAME))

        self.read_config_file()

    # In the config file, info like the table corner coordinates are stored
    def read_config_file(self):
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), CONFIG_FILE_NAME))
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

    # TODO: Check differences between camera and table aspect ratio
    # Based on: https://www.youtube.com/watch?v=PtCQH93GucA
    def extract_table_area(self, frame):
        x = frame.shape[1]
        y = frame.shape[0]

        pts1 = np.float32([list(self.table_corner_top_left),
                           list(self.table_corner_top_right),
                           list(self.table_corner_bottom_left),
                           list(self.table_corner_bottom_right)])

        pts2 = np.float32([[0, 0], [x, 0], [0, y], [x, y]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)

        frame = cv2.warpPerspective(frame, matrix, (x, y))

        return frame
