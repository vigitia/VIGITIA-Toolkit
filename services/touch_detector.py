#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import cv2
import imutils
import configparser
from scipy.spatial import distance

from services.foreground_mask_extractor import ForegroundMaskExtractor
# from calibration.table_surface_extractor import TableSurfaceExtractor

MIN_DIST_TOUCH = 3  # mm
DIST_HOVERING = 20  # mm
MAX_DIST_TOUCH = 50  # mm

MIN_FINGER_DISTANCE_FROM_TABLE_BORDER = 20  # Ignore touch points closer than X pixels to table border

NUM_FRAMES_FOR_BACKGROUND_MODEL = 50

COLOR_TOUCH = [113, 204, 46]
COLOR_HOVER = [18, 156, 243]
COLOR_NO_TOUCH = [60, 76, 231]
COLOR_PALM_CENTER = [80, 80, 80]
COLOR_REMOVED_BACKGROUND = [64, 177, 0]  # Chroma Green

DEBUG_MODE = True


# Class representing a single finger touch
# Implementation inspired by the paper "DIRECT: Making Touch Tracking on Ordinary Surfaces Practical with
# Hybrid Depth-Infrared Sensing." by Xiao, R., Hudson, S., & Harrison, C. (2016).
# See https://github.com/nneonneo/direct-handtracking/blob/master/ofx/apps/handTracking/direct/src/Touch.h
class TouchPoint:

    def __init__(self, x, y, hand_id, distance_to_table_mm, palm_center_x, palm_center_y):
        self.id = -1
        self.x = x
        self.y = y
        self.hand_id = hand_id
        self.distance_to_table_mm = distance_to_table_mm
        self.palm_center_x = palm_center_x
        self.palm_center_y = palm_center_y
        self.is_touching = int(distance_to_table_mm <= DIST_HOVERING)

        self.missing = False
        self.num_frames_missing = 0

    def get_touch_coordinates(self):
        return tuple([self.x, self.y])

    def get_palm_center_coordinates(self):
        return tuple([self.palm_center_x, self.palm_center_y])

    def __repr__(self):
        return 'TouchPoint {} at ({}, {}). Distance to the table: {}mm.'.format(str(self.id), str(self.x), str(self.y),
                                                                                str(self.distance_to_table_mm))


class TouchDetector:

    num_frame = 0

    stored_background_values = None
    background_average = None
    background_standard_deviation = None
    background_model_available = False

    table_border = None
    table_mask = None

    active_touch_points = []

    highest_touch_id = 1  # Keep track of the currently highest present ID

    def __init__(self):
        self.init_background_model()
        self.foreground_mask_extractor = ForegroundMaskExtractor()
        # self.table_surface_extractor = TableSurfaceExtractor()
        print('Touch Detector service ready')

    # TODO: Generate backround model during runtime of the last X frames
    def init_background_model(self):
        background_temp = None
        deviation_temp = None
        try:
            background_temp = np.load('background_average.npy')
            deviation_temp = np.load('background_standard_deviation.npy')
        except FileNotFoundError:
            print("No stored background")

        if background_temp is not None and deviation_temp is not None:
            print('Found stored background model')
            self.background_average = background_temp
            self.background_standard_deviation = deviation_temp
            self.background_model_available = True

    def get_touch_points(self, color_image, depth_image, hand_regions, detected_hands):
        # self.table_border = table_border
        self.table_border = np.array([(0, 0), (color_image.shape[1], 0),
                                      (color_image.shape[1], color_image.shape[0]), (0, color_image.shape[1])])

        self.num_frame += 1

        self.depth_res_x = depth_image.shape[1]
        self.depth_res_y = depth_image.shape[0]

        if not self.background_model_available and self.num_frame <= NUM_FRAMES_FOR_BACKGROUND_MODEL:
            self.create_background_model(depth_image)
            return []
        else:
            new_touch_points = self.find_touch_points(color_image, depth_image)
            new_touch_points = self.compare_with_cnn_points(new_touch_points, hand_regions, detected_hands)
            self.active_touch_points = self.merge_touch_points(new_touch_points)

            self.draw_touch_points(color_image, self.active_touch_points, hand_regions)

            # Experiment
            # self.extract_arms_in_depth_image(depth_image)

            return self.active_touch_points

    def compare_with_cnn_points(self, new_touch_points, hand_regions, detected_hands):
        points_inside = []

        if len(hand_regions) > 0:

            for hand_region in hand_regions:
                points_inside_region = []
                for point in new_touch_points:
                    if point.distance_to_table_mm > DIST_HOVERING:
                        continue
                    if hand_region[0][0] <= point.x <= hand_region[1][0]:
                        if hand_region[0][1] <= point.y <= hand_region[1][1]:
                            points_inside_region.append(point)

                for hand in detected_hands:

                    index_finger = hand['joints'][8]
                    x, y = index_finger

                    smallest_distance = -1
                    index_finger_candidate = None
                    for point in points_inside_region:
                        distance_between_points = distance.euclidean((point.x, point.y), index_finger)
                        print('Distance between random finger and index finger: ', distance_between_points, 'px')

                        if smallest_distance == -1 or distance_between_points < smallest_distance:
                            smallest_distance = distance_between_points
                            index_finger_candidate = point

                    if index_finger_candidate is not None:
                        points_inside.append(index_finger_candidate)



            # for point in new_touch_points:
            #     point_inside = False
            #     for hand_region in hand_regions:
            #         if hand_region[0][0] <= point.x <= hand_region[1][0]:
            #             if hand_region[0][1] <= point.y <= hand_region[1][1]:
            #                 point_inside = True
            #
            #     if point_inside:
            #         points_inside.append(point)




        return points_inside




    def create_background_model(self, depth_image):
        pos = self.num_frame - 1
        print('Storing frame ' + str(pos+1) + '/' + str(NUM_FRAMES_FOR_BACKGROUND_MODEL))

        # TODO: Get dimensions from current frame
        if self.stored_background_values is None:
            self.stored_background_values = np.zeros(shape=(self.depth_res_y, self.depth_res_x, NUM_FRAMES_FOR_BACKGROUND_MODEL), dtype=np.int16)
            self.background_average = np.zeros(shape=(self.depth_res_y, self.depth_res_x), dtype=np.int16)
            self.background_standard_deviation = np.zeros(shape=(self.depth_res_y, self.depth_res_x), dtype=np.int16)

        self.store_depth_values(depth_image, pos)

        if pos == (NUM_FRAMES_FOR_BACKGROUND_MODEL - 1):
            self.calculate_background_model_statistics(self.depth_res_x, self.depth_res_y)

    def store_depth_values(self, depth_image, pos):
        for y in range(self.depth_res_y):
            for x in range(self.depth_res_x):
                current_depth_px = depth_image[y][x]
                self.stored_background_values[y][x][pos] = current_depth_px

    def calculate_background_model_statistics(self, depth_res_x, depth_res_y):
        print('Calculating background model statistics')
        # TODO: Improve performance
        for y in range(depth_res_y):
            for x in range(depth_res_x):
                stored_values_at_pixel = self.stored_background_values[y][x]
                #stored_values_at_pixel = stored_values_at_pixel[stored_values_at_pixel != 0]
                #if len(stored_values_at_pixel) == 0:
                #    stored_values_at_pixel = [0]
                # Calculate average depth value for all values stored for the specific pixel
                self.background_average[y][x] = np.mean(stored_values_at_pixel)
                # Implemented like in the paper "DIRECT"
                self.background_standard_deviation[y][x] = 3 * np.std(stored_values_at_pixel)

        # Write the background info to permanent storage.
        # If conditions dont change, it does not need to be created every time
        np.save('background_average.npy', self.background_average)
        np.save('background_standard_deviation.npy', self.background_standard_deviation)

        print('Finished calculating background model statistics')

    # Inspired by https://webnautes.tistory.com/m/1378
    def find_touch_points(self, color_image, depth_image):

        # List to be filled by this method:
        touch_points = []

        # foreground_mask = self.foreground_mask_extractor.get_foreground_mask_basic(color_image)
        foreground_mask = self.foreground_mask_extractor.get_foreground_mask(color_image)
        cv2.imshow('mask', foreground_mask)

        #foreground_mask = self.remove_pixels_outside_table_border(foreground_mask)

        black_image = np.dstack((foreground_mask, foreground_mask, foreground_mask))

        # TODO: Fill holes if needed

        arm_candidates = self.get_arm_candidates(foreground_mask)

        if len(arm_candidates) > 0:

            # Check each arm candidate
            for index, arm_candidate in enumerate(arm_candidates):

                center_point_palm, palm_radius = self.find_palm_in_hand(foreground_mask, arm_candidate)

                if DEBUG_MODE:
                    # Draw a circle where the palm is estimated to be
                    cv2.circle(black_image, center_point_palm, palm_radius, [80, 80, 80], 3)

                hull, center_point, finger_candidates, inner_points, starts, ends = self.get_finger_points(arm_candidate)

                if DEBUG_MODE:
                    # Draw the contour
                    cv2.drawContours(black_image, [hull], 0, (0, 255, 255), 2)
                    # Draw the center point of the contour
                    cv2.circle(black_image, center_point, 5, [255, 255, 255], -1)

                # Check each finger candidate
                for finger_candidate in finger_candidates:

                    # Check distance between point and table surface to get touch state and the corresponding color
                    max_distance_mm, touch_state = self.get_touch_state(finger_candidate, depth_image)
                    distance_between_points = distance.euclidean(center_point_palm, finger_candidate)
                    if distance_between_points > 2 * palm_radius:
                        if DEBUG_MODE:
                            cv2.line(black_image, finger_candidate, center_point_palm, [0, 255, 0], 2)
                            cv2.circle(black_image, finger_candidate, 10, touch_state, 2)
                        if max_distance_mm < MAX_DIST_TOUCH:
                            touch_points.append(TouchPoint(finger_candidate[0], finger_candidate[1], index,
                                                           max_distance_mm, center_point_palm[0],
                                                           center_point_palm[1]))
                    continue
                    if max_distance_mm < MAX_DIST_TOUCH:
                        distance_between_points = distance.euclidean(center_point_palm, finger_candidate)
                        if distance_between_points > 1.7 * palm_radius:
                            if DEBUG_MODE:
                                cv2.line(black_image, finger_candidate, center_point_palm, [0, 255, 0], 2)
                            cv2.circle(black_image, finger_candidate, 10, touch_state, 2)
                            touch_points.append(TouchPoint(finger_candidate[0], finger_candidate[1], index,
                                                           max_distance_mm, center_point_palm[0],
                                                           center_point_palm[1]))
                        #else:
                            #cv2.line(black_image, finger_candidate, center_point_palm, [255, 0, 0], 2)

                        # TODO: Check if distance between points is realistic

        # black_image = self.table_surface_extractor.extract_table_area(black_image)
        #black_image = cv2.flip(black_image, -1)
        cv2.imshow('Detected hands', black_image)

        #print(touch_points)
        return touch_points

    def remove_pixels_outside_table_border(self, foreground_mask):
        # Store table border coordinates in an array and create a mask for the table

        self.table_mask = np.zeros(shape=foreground_mask.shape, dtype=np.uint8)
        cv2.fillPoly(self.table_mask, pts=[self.table_border], color=255)

        # Remove all points outside of the border
        foreground_mask = np.where(self.table_mask == 0, 0, foreground_mask)

        return foreground_mask

    def get_arm_candidates(self, foreground_mask):
        contours, hierarchy = cv2.findContours(foreground_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Extract the 10 largest contours (more should never be needed)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        # TODO: Fill holes if needed

        arm_candidates = []

        if len(contours) > 0:
            for contour in contours:

                connected_to_table_border = False

                # Check all points in the contour if the lie on or within the table area
                for point in contour:
                    if cv2.pointPolygonTest(self.table_border, tuple(point[0]), False) <= 0:
                        connected_to_table_border = True

                # If they are connected to the table border, they are considered as a hand candidate.
                if connected_to_table_border:
                    arm_candidates.append(contour)

        return arm_candidates

    def find_palm_in_hand(self, foreground_mask, arm_candidate):
        contour_mask = np.zeros(shape=foreground_mask.shape, dtype=np.uint8)
        cv2.fillPoly(contour_mask, pts=[arm_candidate], color=255)

        # Find maximum inscribing circle for Hand detection
        # See: https://stackoverflow.com/questions/53646022/opencv-c-find-inscribing-circle-of-a-contour
        # See: https://www.youtube.com/watch?v=xML2S6bvMwI
        dist = cv2.distanceTransform(contour_mask, cv2.DIST_L2, 3)
        minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(dist)
        center_point_palm = maxLoc
        palm_radius = int(maxVal)

        return center_point_palm, palm_radius

    # Inspired by https://webnautes.tistory.com/m/1378
    def get_finger_points(self, arm_candidate):

        arm_candidate = cv2.approxPolyDP(arm_candidate, 0.02 * cv2.arcLength(arm_candidate, True), True)
        hull = cv2.convexHull(arm_candidate, returnPoints=False)
        # https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_contours/py_contours_more_functions/py_contours_more_functions.html

        defects = None
        try:
            defects = cv2.convexityDefects(arm_candidate, hull)
        except cv2.error as e:
            # print(e)
            pass

        inner_points = []
        starts = []
        ends = []

        if defects is not None:
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(arm_candidate[s][0])
                end = tuple(arm_candidate[e][0])
                far = tuple(arm_candidate[f][0])
                inner_points.append(far)
                starts.append(start)
                ends.append(end)

        hull = cv2.convexHull(arm_candidate, returnPoints=True)

        center_point = (0, 0)
        finger_candidates = []

        try:
            # Find center of contour
            moments = cv2.moments(arm_candidate)
            cx = int(moments['m10'] / moments['m00'])
            cy = int(moments['m01'] / moments['m00'])
            center_point = (cx, cy)
        except ZeroDivisionError:
            pass

        for point in hull:
            distance_to_table_border = abs(cv2.pointPolygonTest(self.table_border, tuple(point[0]), True))
            # TODO Remove points close to the table border

            if distance_to_table_border > MIN_FINGER_DISTANCE_FROM_TABLE_BORDER:
                finger_candidates.append(tuple(point[0]))

        return hull, center_point, finger_candidates, inner_points, starts, ends

    # Implemented like described in paper "DIRECT: Making Touch Tracking on Ordinary Surfaces Practical with
    # Hybrid Depth-Infrared Sensing." by Xiao, R., Hudson, S., & Harrison, C. (2016).
    def get_touch_state(self, point, depth_image):
        point_x = point[1]
        point_y = point[0]
        # Check the neighboring pixels in a 5x5 area
        neighboring_pixels_stored = self.background_average[point_x - 2:point_x + 3, point_y - 2:point_y + 3]
        neighboring_pixels_current = depth_image[point_x - 2:point_x + 3, point_y - 2:point_y + 3]
        try:
            highest_point = np.amin(neighboring_pixels_current)
            # Compare the highest point in the area with the mean of the 5x5 pixel area
            max_distance_mm = int(abs(np.mean(neighboring_pixels_stored) - highest_point))
            if max_distance_mm <= DIST_HOVERING:
                return max_distance_mm, COLOR_TOUCH
            elif max_distance_mm <= MAX_DIST_TOUCH:
                return max_distance_mm, COLOR_HOVER
            else:
                return max_distance_mm, COLOR_NO_TOUCH
        except ValueError:
            return -1, COLOR_NO_TOUCH

    # Implemented like described in paper "DIRECT: Making Touch Tracking on Ordinary Surfaces Practical with
    # Hybrid Depth-Infrared Sensing." by Xiao, R., Hudson, S., & Harrison, C. (2016).
    def merge_touch_points(self, new_touch_points):

        distances = []
        for i in range(len(self.active_touch_points)):
            for j in range(len(new_touch_points)):
                distance_between_points = distance.euclidean(self.active_touch_points[i].get_touch_coordinates(),
                                                             new_touch_points[j].get_touch_coordinates())

                # If distance is large enough, there is no need to check if the touch point already exists
                DISTANCE_MOVEMENT_BETWEEN_FRAMES_THRESHOLD = 100
                if distance_between_points > DISTANCE_MOVEMENT_BETWEEN_FRAMES_THRESHOLD:
                    continue
                distances.append([i, j, distance_between_points])

        # Sort list of lists by third element
        # https://stackoverflow.com/questions/4174941/how-to-sort-a-list-of-lists-by-a-specific-index-of-the-inner-list
        distances.sort(key=lambda x: x[2])

        for entry in distances:
            active_touch_point = self.active_touch_points[entry[0]]
            new_touch_point = new_touch_points[entry[1]]

            if active_touch_point.id < 0 or new_touch_point.id >= 0:
                continue

            # Move the ID from the active touch point into the new touch point
            new_touch_point.id = active_touch_point.id
            active_touch_point.id = -1

            # Simple Smoothing
            SMOOTHING_FACTOR = 0.3  # Value between 0 and 1, depending if the old or the new value should count more.

            new_touch_point.x = int(SMOOTHING_FACTOR * (new_touch_point.x - active_touch_point.x) + active_touch_point.x)
            new_touch_point.y = int(SMOOTHING_FACTOR * (new_touch_point.y - active_touch_point.y) + active_touch_point.y)
            new_touch_point.distance_to_table_mm = (new_touch_point.distance_to_table_mm -
                                                    active_touch_point.distance_to_table_mm) + \
                                                   active_touch_point.distance_to_table_mm

            new_touch_point.palm_center_x = int(SMOOTHING_FACTOR * (new_touch_point.palm_center_x - active_touch_point.palm_center_x) + active_touch_point.palm_center_x)
            new_touch_point.palm_center_y = int(SMOOTHING_FACTOR * (new_touch_point.palm_center_y - active_touch_point.palm_center_y) + active_touch_point.palm_center_y)

        for touch_point in new_touch_points:
            touch_point.missing = False
            touch_point.num_frames_missing = 0

        for touch_point in self.active_touch_points:
            NUM_FRAMES_TOUCH_POINT_MISSING_THRESHOLD = 3
            if touch_point.id >= 0 and (not touch_point.missing or touch_point.num_frames_missing < NUM_FRAMES_TOUCH_POINT_MISSING_THRESHOLD):
                if touch_point.missing:
                    touch_point.num_frames_missing += 1
                else:
                    touch_point.num_frames_missing = 0

                touch_point.missing = True
                new_touch_points.append(touch_point)

        final_touch_points = []
        for touch_point in new_touch_points:
            if touch_point.id < 0:
                touch_point.id = self.highest_touch_id
                self.highest_touch_id += 1

            final_touch_points.append(touch_point)

        return final_touch_points

    def draw_touch_points(self, color_image, touch_points, hand_regions):

        #black_image = np.zeros(shape=(self.depth_res_y, self.depth_res_x, 3), dtype=np.uint8)
        black_image = color_image

        for region in hand_regions:
            cv2.rectangle(black_image, region[0], region[1], (0, 255, 0), 3)

        for touch_point in touch_points:
            cv2.circle(black_image, touch_point.get_touch_coordinates(), 8,
                       self.get_touch_color(touch_point.distance_to_table_mm), -1)
            cv2.circle(black_image, touch_point.get_palm_center_coordinates(), 5, COLOR_PALM_CENTER, -1)
            cv2.putText(black_image, text='{}: {}mm'.format(str(touch_point.id), str(touch_point.distance_to_table_mm)),
                        org=touch_point.get_touch_coordinates(),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=2, color=(0, 0, 0))

        #black_image = self.table_surface_extractor.extract_table_area(black_image)
        #black_image = cv2.flip(black_image, -1)
        cv2.imshow('touch points', black_image)

    @staticmethod
    def get_touch_color(distance_to_table_mm):
        if distance_to_table_mm <= DIST_HOVERING:
            return COLOR_TOUCH
        elif distance_to_table_mm <= MAX_DIST_TOUCH:
            return COLOR_HOVER
        else:
            return COLOR_NO_TOUCH

    '''
    Old methods and examples below
    '''

    def coordinates_to_full_hd(self, low_res_tuple):
        tuple_as_list = list(low_res_tuple)
        tuple_as_list[0] = int(tuple_as_list[0] / 848 * 1920)
        tuple_as_list[1] = int(tuple_as_list[1] / 480 * 1080)
        return tuple(tuple_as_list)

    def moving_average_filter(self, image):
        pass
        #     if self.stored_depth_frame is None:
        #         self.stored_depth_frame = image
        #         return image
        #     else:
        #         combined_images = self.stored_depth_frame + image
        #         averaged_image = combined_images/2
        #         self.stored_depth_frame = image
        #         return averaged_image

    def extract_arms_in_depth_image(self, depth_image):

        #hand_area = self.get_touch_points(color_image, depth_image)
        #return None

        depth_image_table = self.table_surface_extractor.extract_table_area(depth_image)
        background_average_table = self.table_surface_extractor.extract_table_area(self.background_average)
        background_standard_deviation_table = self.table_surface_extractor.extract_table_area(self.background_standard_deviation)

        # Compare the current depth image with the stored average of the background
        #difference_to_background = background_average_table - depth_image_table
        difference_to_background = background_average_table - depth_image_table

        # Make sure that there are no negative values in the array
        difference_to_background = np.where(difference_to_background < 0, 0, difference_to_background)

        # Ignore pixels that are too close to the table surface
        remove_uncertain_pixels = difference_to_background - background_standard_deviation_table
        remove_uncertain_pixels = np.where(remove_uncertain_pixels < 0, 0, difference_to_background)
        remove_uncertain_pixels = np.where((remove_uncertain_pixels < MIN_DIST_TOUCH), 0, remove_uncertain_pixels)

        #depth_holes = np.where(depth_image_table == 0, 0, 65535)
        #remove_uncertain_pixels = np.where(depth_holes == 0, 0, remove_uncertain_pixels)

        # Arm pixels are pixels at least MAX_DIST_TOUCH away from the the background mean
        mark_arm_pixels = np.where((remove_uncertain_pixels > MAX_DIST_TOUCH), 65535, 0)
        mark_arm_pixels = cv2.convertScaleAbs(mark_arm_pixels, alpha=(255.0 / 65535.0))

        mark_touch_pixels = np.where((remove_uncertain_pixels >= MAX_DIST_TOUCH), 0, remove_uncertain_pixels)
        mark_touch_pixels = np.where(mark_touch_pixels != 0, 65535, 0)
        mark_touch_pixels = cv2.convertScaleAbs(mark_touch_pixels, alpha=(255.0 / 65535.0))

        remove_uncertain_pixels = np.where((remove_uncertain_pixels >= MIN_DIST_TOUCH), 65535, 0)
        remove_uncertain_pixels = cv2.convertScaleAbs(remove_uncertain_pixels, alpha=(255.0/65535.0))

        small_regions = self.remove_small_connected_regions(remove_uncertain_pixels, 10000, True)
        remove_uncertain_pixels -= small_regions
        mark_arm_pixels -= small_regions
        mark_touch_pixels -= small_regions

        significant_pixels = cv2.cvtColor(remove_uncertain_pixels, cv2.COLOR_GRAY2BGR)
        mark_arm_pixels = cv2.cvtColor(mark_arm_pixels, cv2.COLOR_GRAY2BGR)
        mark_touch_pixels = cv2.cvtColor(mark_touch_pixels, cv2.COLOR_GRAY2BGR)

        significant_pixels[np.where((mark_touch_pixels == [255, 255, 255]).all(axis=2))] = [0, 0, 255]
        significant_pixels[np.where((mark_arm_pixels == [255, 255, 255]).all(axis=2))] = [0, 255, 0]

        cv2.imshow('hands_depth', significant_pixels)


        #unique, counts = np.unique(significant_pixels, return_counts=True)
        #print(dict(zip(unique, counts)))

        #significant_pixels_color = cv2.cvtColor(significant_pixels, cv2.COLOR_GRAY2BGR)

        #hand_area = self.get_touch_points(color_image, depth_image)

        #hand_area = cv2.cvtColor(hand_area, cv2.COLOR_GRAY2BGR)
        #significant_pixels[np.where((hand_area == [0, 0, 0]).all(axis=2))] = [0, 0, 0]

        #edge_map = self.get_edge_map(color_image)
        #edge_map = cv2.cvtColor(edge_map, cv2.COLOR_GRAY2BGR)

        #output_image = significant_pixels + edge_map
        output_image = significant_pixels

        #unique, counts = np.unique(output_image, return_counts=True)
        #print(dict(zip(unique, counts)))

        # TODO: Get extreme Points: https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_contours/py_contour_properties/py_contour_properties.html#contour-properties

        return output_image

    def remove_small_connected_regions(self, image, min_size, get_only_regions_to_remove):
        # https://stackoverflow.com/questions/42798659/how-to-remove-small-connected-objects-using-opencv
        nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(image, connectivity=8)
        sizes = stats[1:, -1]
        nb_components = nb_components - 1

        output_image = np.zeros(shape=image.shape, dtype=np.uint8)
        # for every component in the image, you keep it only if it's above min_size
        for i in range(0, nb_components):
            if get_only_regions_to_remove:
                if sizes[i] < min_size:
                    output_image[output == i + 1] = 255
            else:
                if sizes[i] >= min_size:
                    output_image[output == i + 1] = 255

        return output_image

    def get_edge_map_old(self, image):

        # https://www.pyimagesearch.com/2014/04/21/building-pokedex-python-finding-game-boy-screen-step-4-6/
        #image = cv2.bilateralFilter(image, 11, 17, 17)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = cv2.bilateralFilter(image, 7, 50, 50)
        image = cv2.Canny(image, 30, 400, 7)

        black_image = np.zeros(shape=(self.depth_res_y, self.depth_res_x), dtype=np.uint8)


        #https://www.pyimagesearch.com/2014/04/21/building-pokedex-python-finding-game-boy-screen-step-4-6/
        # find contours in the edged image, keep only the largest
        # ones, and initialize our screen contour
        #cnts = cv2.findContours(image.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = cv2.findContours(image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contours = imutils.grab_contours(contours)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        print("Num Contours: ", len(contours))

        for contour in contours:
            print('')

            points_inside = []

            for point in contour:
                modified_point = (point[0][0], point[0][1])
                if cv2.pointPolygonTest(self.table_border, modified_point, False) == 1:
                    points_inside.append(point)

            result = np.asarray(points_inside)

            cv2.drawContours(black_image, result, -1, (255, 255, 255), 3)



            # approximate the contour
            #peri = cv2.arcLength(c, True)
            #approx = cv2.approxPolyDP(c, 0.015 * peri, True)
            #print("Length of contour: ", len(approx))

        #image = self.remove_small_connected_regions(image, 10, False)

        # TODO: See:
        # https://stackoverflow.com/questions/35847990/detect-holes-ends-and-beginnings-of-a-line-using-opencv

        # Also: Remove points outside the boundries of the table

        return black_image

    def remove_background(self, color_image, depth_image, clipping_distance):
        # Remove background - Set pixels further than clipping_distance to grey
        depth_image_3d = np.dstack((depth_image, depth_image, depth_image))  # depth image is 1 channel, color is 3 channels
        bg_removed = np.where((depth_image_3d > clipping_distance) | (depth_image_3d <= 0), 0, color_image)
        # https://answers.opencv.org/question/97416/replace-a-range-of-colors-with-a-specific-color-in-python/
        bg_removed[np.where((bg_removed == [0, 0, 0]).all(axis=2))] = COLOR_REMOVED_BACKGROUND

        return bg_removed
