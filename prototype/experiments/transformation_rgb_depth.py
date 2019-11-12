import sys
import pyrealsense2 as rs
import cv2
import cv2.aruco as aruco
import numpy as np
import time
import configparser
# https://stackoverflow.com/questions/9763116/parse-a-tuple-from-a-string
from ast import literal_eval as make_tuple  # Needed to convert strings stored in config file back to tuples

from hand_tracker import HandTracker

# Built upon: https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/examples/align-depth2color.py
# Code for Hand Tracking and Models from https://github.com/metalwhale/hand_tracking

# TODO: M = cv2.getRotationMatrix2D(center, angle, scale)

# Current distance between camera and table in cm
# TODO: Should be calculated automatically later and saved to config file
DISTANCE_CAMERA_TABLE = 110  # cm

DEFAULT_DISPLAY_MODE = 'memory'

# Camera Settings
DEPTH_RES_X = 1280
DEPTH_RES_Y = 720
RGB_RES_X = 1280
RGB_RES_Y = 720

DEPTH_FPS = 30
RGB_FPS = 30

# Output image (currently needs to be 16x9 because the projector can project this)
OUTPUT_IMAGE_WIDTH = 3840
OUTPUT_IMAGE_HEIGHT = 2160

# Since the projection field of the projector is larger than the table,
# we need to add black borders on at least two sides
BORDER_TOP = 38  # px
BORDER_BOTTOM = 0  # px
BORDER_LEFT = 0  # px
BORDER_RIGHT = 50  # px

# Paths to the Models needed for hand tracking
PALM_MODEL_PATH = "./palm_detection_without_custom_op.tflite"
LANDMARK_MODEL_PATH = "./hand_landmark.tflite"
ANCHORS_PATH = "./anchors.csv"

# Constants for drawing of the hand
POINT_COLOR = (0, 255, 0)
CONNECTION_COLOR = (255, 255, 0)
THICKNESS = 2

# Connections for the hand tracking model
#        8   12  16  20
#        |   |   |   |
#        7   11  15  19
#    4   |   |   |   |
#    |   6   10  14  18
#    3   |   |   |   |
#    |   5---9---13--17
#    2    \         /
#     \    \       /
#      1    \     /
#       \    \   /
#        ------0-
CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (2, 5), (3, 4),
    (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12),
    (13, 14), (14, 15), (15, 16),
    (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17), (0, 17)
]

# Coordinates of marker points for the fabric pattern "T-shirt"
FABRIC_PATTERN_T_SHIRT = np.array([[597, 95], [961, 95], [959, 107], [961, 116], [963, 127], [967, 138], [957, 167],
                                   [924, 163], [907, 163], [897, 164], [887, 171], [878, 180], [870, 188], [861, 196],
                                   [815, 184], [785, 181], [767, 179], [750, 178], [733, 178], [710, 181], [679, 185],
                                   [661, 187], [635, 190], [616, 195], [598, 196]])


# IDs of the used Aruco Marker IDs of the demo applications
ARUCO_MARKER_SHIRT_S = 0
ARUCO_MARKER_SHIRT_M = 4
ARUCO_MARKER_SHIRT_L = 8
ARUCO_MARKER_TIMELINE_CONTROLLER = 42

# Time until a marker is declared absent by the system (we wait a little to make sure it is not just obstructed by
# something
ARUCO_MARKER_MISSING_TIMEOUT = 2  # seconds

# Number of stored frames for the rewind function
TIMELINE_NUM_FRAMES = 120

# interval for storing frames for the rewind function
TIMELINE_FRAME_SAVING_INTERVAL = 1  # seconds


class VigitiaDemo:
    table_corner_top_left = (0, 0)
    table_corner_top_right = (0, 0)
    table_corner_bottom_left = (0, 0)
    table_corner_bottom_right = (0, 0)

    last_mouse_click_coordinates = []

    pipeline = None
    align = None
    colorizer = None
    last_color_frames = []
    stored_image = None
    hand_detector = None

    aruco_dictionary = None
    aruco_detector_parameters = None

    display_mode = DEFAULT_DISPLAY_MODE
    hand_tracking_enabled = False
    aruco_markers_enabled = False
    outline_enabled = False
    show_hand_model = False

    frame = 0
    depth_scale = 0
    hand_points = None
    last_distance = None

    last_saved_frame_timestamp = time.time()
    last_time_marker_present = None
    marker_origin = None
    last_aruco_timeline_controller_data = None

    last_fabric_pattern_angle = None
    last_tracker_centroid_pos = None

    #fgbg = cv2.cv2.createBackgroundSubtractorMOG2()
    fgbg = cv2.cv2.createBackgroundSubtractorKNN()

    def __init__(self):
        # Create a pipeline
        self.pipeline = rs.pipeline()

        # Create a config and configure the pipeline to stream different resolutions of color and depth streams
        config = rs.config()
        config.enable_stream(rs.stream.depth, DEPTH_RES_X, DEPTH_RES_Y, rs.format.z16, DEPTH_FPS)
        config.enable_stream(rs.stream.color, RGB_RES_X, RGB_RES_Y, rs.format.bgr8, RGB_FPS)

        # Start streaming
        profile = self.pipeline.start(config)

        # TODO: Wait for a few frames to make sure the camera is ready

        # TODO: Make this code work to set ROI for Auto exposure on the table surface
        # Set ROI (https://github.com/IntelRealSense/librealsense/issues/3427)
        dev = profile.get_device()
        for sensor in dev.sensors:
            if not sensor.is_depth_sensor():
                break
        roi_sensor = sensor.as_roi_sensor()
        sensor_roi = roi_sensor.get_region_of_interest()
        #sensor_roi.min_x, sensor_roi.max_x = CORNER_TOP_LEFT[0], CORNER_TOP_RIGHT[0]
        #sensor_roi.min_y, sensor_roi.max_y = CORNER_TOP_LEFT[1], CORNER_BOTTOM_RIGHT[1]
        #roi_sensor.set_region_of_interest(sensor_roi)
        print(sensor_roi.min_x, sensor_roi.max_x, sensor_roi.min_y, sensor_roi.max_y)

        # Getting the depth sensor's depth scale (see rs-align example for explanation)
        depth_sensor = profile.get_device().first_depth_sensor()
        self.depth_scale = depth_sensor.get_depth_scale()
        depth_sensor.set_option(rs.option.laser_power, 360)

        # TODO: Tweak camera settings
        depth_sensor.set_option(rs.option.depth_units, 0.0001)

        # Create an align object
        # rs.align allows us to perform alignment of depth frames to others frames
        # The "align_to" is the stream type to which we plan to align depth frames.
        align_to = rs.stream.color
        self.align = rs.align(align_to)

        # Set to fullscreen
        cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        # Set mouse callbacks to extract the coordinates of clicked spots in the image
        cv2.setMouseCallback('window', self.on_mouse_click)

        self.read_config_file()
        self.init_colorizer()
        self.init_hand_detector()
        self.init_aruco_tracking()
        self.loop()

    def read_config_file(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        print(config.sections())

        # Coordinates of table corners for perspective transformation
        self.table_corner_top_left = make_tuple(config['CORNERS']['CornerTopLeft'])
        self.table_corner_top_right = make_tuple(config['CORNERS']['CornerTopRight'])
        self.table_corner_bottom_left = make_tuple(config['CORNERS']['CornerBottomLeft'])
        self.table_corner_bottom_right = make_tuple(config['CORNERS']['CornerBottomRight'])

        print(self.table_corner_top_left)

    # Log mouse click positions to the console
    def on_mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print((x, y))
            self.last_mouse_click_coordinates.append((x, y))
            if len(self.last_mouse_click_coordinates) > 4:
                self.last_mouse_click_coordinates = []

    def init_colorizer(self):
        self.colorizer = rs.colorizer()
        self.colorizer.set_option(rs.option.color_scheme, 0)   # Define the color scheme
        # Auto histogram color selection (0 = off, 1 = on)
        self.colorizer.set_option(rs.option.histogram_equalization_enabled, 0)
        self.colorizer.set_option(rs.option.min_distance, 1.0)  # meter
        self.colorizer.set_option(rs.option.max_distance, 1.3)  # meter

    def init_hand_detector(self):
        self.detector = HandTracker(PALM_MODEL_PATH, LANDMARK_MODEL_PATH, ANCHORS_PATH, box_shift=0.2, box_enlarge=1.3)

    def init_aruco_tracking(self):
        self.aruco_dictionary = aruco.Dictionary_get(aruco.DICT_4X4_100)
        self.aruco_detector_parameters = aruco.DetectorParameters_create()
        self.aruco_detector_parameters.adaptiveThreshConstant = 10  # TODO: Tweak value

    # Main application loop
    def loop(self):
        try:
            while True:
                self.frame += 1
                frames = self.pipeline.wait_for_frames()  # Get frameset of color and depth
                color_image, depth_colormap, aligned_depth_frame = self.align_frames(frames)

                # skip the first few frames to make sure the camera is ready
                if self.frame < 30:
                    continue

                # depth_data = aligned_depth_frame.get_data()
                # np_image = np.asanyarray(depth_data)
                #distance = np_image[int(len(np_image) / 2)][int(len(np_image[0]) / 2)] * self.depth_scale * 100
                #print(str("%.2f" % distance) + ' cm')

                #distance = cv2.mean(np_image * self.depth_scale)
                #print(distance)

                # for i in range(color_image.shape[0]):
                #     for j in range(color_image.shape[1]):
                #         distance = np_image[i][j] * self.depth_scale
                #         if distance > 1.08:
                #             color_image[i, j] = (0, 0, 0)

                #color_image = self.remove_background(color_image, depth_colormap, 100)

                self.detect_hands(color_image, aligned_depth_frame)

                # Available modes of demo application
                if self.display_mode == "default":
                    self.display_mode_rgb(color_image)
                elif self.display_mode == "RGB":
                    self.display_mode_rgb(color_image)
                elif self.display_mode == "depth":
                    self.display_mode_depth(depth_colormap)
                elif self.display_mode == "off":
                    self.display_mode_black_background(color_image)
                elif self.display_mode == 'memory':
                    self.display_mode_memory(color_image)
                elif self.display_mode == 'calibration':
                    self.display_mode_calibration(color_image)

                key = cv2.waitKey(1)
                if key & 0xFF == ord('q') or key == 27:  # Press esc or 'q' to close the image window
                    cv2.destroyAllWindows()
                    break
                else:
                    self.check_key_inputs(key, color_image, depth_colormap)
        finally:
            self.pipeline.stop()

    # https://dev.intelrealsense.com/docs/rs-align-advanced
    def remove_background(self, color_frame, depth_frame, clipping_distance):
        height = color_frame.shape[1]
        width = color_frame.shape[0]
        for y in range(height):
            depth_pixel_index = y * width
            for x in range(width):
                depth_pixel_index += 1
                # Get the depth value of the current pixel
                pixels_distance = depth_frame[x][y] * self.depth_scale
                # Check if the depth value is invalid (<=0) or greater than the threshold
                if pixels_distance <= 0 or pixels_distance > clipping_distance:
                    # Set pixel to "background" color
                    color_frame[x, y] = (0, 0, 0)

        return color_frame

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Available display modes
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def display_mode_default(self, color_image):
        color_image = self.perspective_transformation(color_image)
        black_image = np.zeros((color_image.shape[0], color_image.shape[1], 3), np.uint8)
        aruco_markers = self.track_aruco_markers(black_image, color_image)
        current_time = time.time()

        if len(aruco_markers) > 0:
            if ARUCO_MARKER_TIMELINE_CONTROLLER in aruco_markers.keys():
                pass

    def display_mode_rgb(self, color_image):
        color_image = self.add_hand_tracking_points(color_image, self.hand_points)
        # Perspective Transformation on images
        color_image = self.perspective_transformation(color_image)

        if self.outline_enabled:
            color_image = self.highlight_objects(color_image, False)
        if self.aruco_markers_enabled:
            color_image, angle, tracker_centroid = self.track_aruco_markers(color_image, color_image)

        # Invert image
        # copy = cv2.bitwise_not(copy)

        # Canny Edge Detection
        # https://www.pyimagesearch.com/2014/04/21/building-pokedex-python-finding-game-boy-screen-step-4-6/
        # color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        # color_image = cv2.bilateralFilter(color_image, 11, 17, 17)
        # color_image = cv2.Canny(color_image, 100, 200)

        # mask_img = self.fgbg.apply(color_image)
        # color_image = cv2.bitwise_and(color_image, color_image, mask=mask_img)

        # Add black border on top to fill the missing pixels from 2:1 (16:8) to 16:9 aspect ratio
        color_image = self.add_border(color_image)
        cv2.imshow('window', color_image)

    def display_mode_calibration(self, color_image):
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
                    org=(int(color_image.shape[1] / 30), int(color_image.shape[0] / 20)),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(0, 0, 255))

        if len(self.last_mouse_click_coordinates) == 4:
            print('Calibrated')
            self.update_table_corner_calibration()

        cv2.imshow('window', color_image)

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
            self.table_corner_top_left = coordinates[2]
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
        self.display_mode = DEFAULT_DISPLAY_MODE



    def display_mode_depth(self, depth_colormap):
        depth_colormap = self.add_hand_tracking_points(depth_colormap, self.hand_points)
        # Perspective Transformation on images
        depth_colormap = self.perspective_transformation(depth_colormap)
        depth_colormap = self.add_border(depth_colormap)

        cv2.imshow('window', depth_colormap)

    def display_mode_black_background(self, color_image):
        black_image = np.zeros((color_image.shape[0], color_image.shape[1], 3), np.uint8)
        black_image = self.add_hand_tracking_points(black_image, self.hand_points)
        black_image = self.perspective_transformation(black_image)

        if self.outline_enabled:
            black_image = self.highlight_objects(self.perspective_transformation(color_image), True)
        if self.aruco_markers_enabled:
            aruco_markers = self.track_aruco_markers(black_image, self.perspective_transformation(color_image), True)

        black_image = self.add_border(black_image)
        if self.last_distance is not None:
            cv2.putText(img=black_image, text=str(self.last_distance) + " cm",
                        org=(int(color_image.shape[1] / 6), int(color_image.shape[0] / 4)),
                        fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=2, color=(255, 255, 255))

        cv2.imshow('window', black_image)

    def display_mode_memory(self, color_image):
        color_image = self.perspective_transformation(color_image)
        black_image = np.zeros((color_image.shape[0], color_image.shape[1], 3), np.uint8)
        aruco_markers = self.track_aruco_markers(black_image, color_image)
        current_time = time.time()

        if len(aruco_markers) > 0:
            self.display_fabric_pattern(black_image, FABRIC_PATTERN_T_SHIRT, aruco_markers)

        # If marker is present, show timeline. Otherwise, just show a black screen
        if len(aruco_markers) > 0 and ARUCO_MARKER_TIMELINE_CONTROLLER in aruco_markers.keys():

            # Check if it it the starting position of the marker
            if self.last_time_marker_present is None \
                    or (current_time - self.last_time_marker_present) > ARUCO_MARKER_MISSING_TIMEOUT:
                self.marker_origin = aruco_markers[ARUCO_MARKER_TIMELINE_CONTROLLER]['centroid']

            self.last_time_marker_present = current_time
            self.last_aruco_timeline_controller_data = aruco_markers[ARUCO_MARKER_TIMELINE_CONTROLLER]
            self.show_scrollable_timeline(color_image, self.last_aruco_timeline_controller_data)
        # If marker was present within the last X seconds
        elif self.last_time_marker_present is not None \
                and current_time - self.last_time_marker_present < ARUCO_MARKER_MISSING_TIMEOUT:
            self.show_scrollable_timeline(color_image, self.last_aruco_timeline_controller_data)
        else:
            time_since_last_saved_frame = current_time - self.last_saved_frame_timestamp
            if time_since_last_saved_frame > TIMELINE_FRAME_SAVING_INTERVAL:
                self.last_saved_frame_timestamp = current_time
                color_image = self.add_border(color_image)

                self.last_color_frames.append(color_image)
                if len(self.last_color_frames) == TIMELINE_NUM_FRAMES:
                    self.last_color_frames.pop(0)  # Remove oldest frame

            black_image = self.add_border(black_image)
            cv2.imshow('window', black_image)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Helper functions
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # Put a white circle around all objects on the table, like a spotlight
    def highlight_objects(self, frame, draw_on_black=True):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # TODO: Tweak values and implement cutoff and moving average filter
        frame = cv2.bilateralFilter(frame, 11, 17, 17)
        ret, thresh = cv2.threshold(frame, 100, 255, 0)  # Define treshold here. Still needs tweaking
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if draw_on_black:
            frame = np.zeros((frame.shape[0], frame.shape[1], 3), np.uint8)  # draw the contours on a black canvas
        # cv2.drawContours(copy, contours, -1, (0, 255, 0), 1)
        for contour in contours:
            (x, y), radius = cv2.minEnclosingCircle(contour)
            center = (int(x), int(y))
            radius = int(radius * 1.5)

            MIN_CIRCLE_SIZE = 30

            if frame.shape[0] / 2 > radius > MIN_CIRCLE_SIZE:
                frame = cv2.circle(frame, center, radius, (255, 255, 255), cv2.FILLED)

        return frame

    # Rotate a list of points around their centroid
    def rotate_points(self, points, angle):
        rotation_matrix = self.get_rotation_matrix(angle)
        centroid = self.centroid(points)  # Get centroid
        points = points - centroid  # Move points to origin for rotation
        #print(points.astype(int).tolist())

        # Rotate (see: https://scipython.com/book/chapter-6-numpy/examples/creating-a-rotation-matrix-in-numpy/)
        points = np.dot(points, rotation_matrix.T)
        points = points + centroid  # Move points back to original position
        points = points.astype(int)  # Convert all floats to int because coordinates are expected to be Integers
        return points

    # Get the rotation matrix for a specific angle
    # https://scipython.com/book/chapter-6-numpy/examples/creating-a-rotation-matrix-in-numpy/
    def get_rotation_matrix(self, angle):
        theta = np.radians(angle)
        c, s = np.cos(theta), np.sin(theta)
        rotation_matrix = np.array(((c, -s), (s, c)))
        return rotation_matrix

    # Get the centroid of a polygon
    # https://progr.interplanety.org/en/python-how-to-find-the-polygon-center-coordinates/
    def centroid(self, vertexes):
        _x_list = [vertex[0] for vertex in vertexes]
        _y_list = [vertex[1] for vertex in vertexes]
        _len = len(vertexes)
        _x = sum(_x_list) / _len
        _y = sum(_y_list) / _len
        return (_x, _y)

    # Change display modes and options depending on pressed keys
    def check_key_inputs(self, key, color_image, depth_colormap):
        if key == 49:  # Key 1
            if self.display_mode == 'RGB':
                self.display_mode = 'depth'
            else:
                self.display_mode = 'RGB'
        elif key == 50:  # Key 2
            self.display_mode = 'off'
        elif key == 51:  # Key 3
            #self.stored_image = self.perspective_transformation(self.last_color_frame.copy())
            self.display_mode = 'memory'
        elif key == 52:  # Key 4
            cv2.imwrite('depth.png', self.perspective_transformation(depth_colormap))
            cv2.imwrite('color.png', self.perspective_transformation(color_image))
        elif key == 97:  # A as in Aruco Markers
            self.aruco_markers_enabled = not self.aruco_markers_enabled
        elif key == 99:  # C as in Calibrate
            self.last_mouse_click_coordinates = []  # Reset list
            self.display_mode = 'calibration'
        elif key == 104:  # H as in Hand
            if not self.hand_tracking_enabled:
                self.hand_tracking_enabled = True
            else:
                if not self.show_hand_model:
                    self.show_hand_model = True
                else:
                    self.show_hand_model = False
                    self.hand_tracking_enabled = False
                    self.hand_points = None
                    self.last_distance = None
        elif key == 111:  # O as in Outline:
            self.outline_enabled = not self.outline_enabled

    # Adds black borders to the given frame
    def add_border(self, frame):
        frame = cv2.copyMakeBorder(frame, top=BORDER_TOP, bottom=BORDER_BOTTOM,
                                   left=BORDER_LEFT, right=BORDER_RIGHT,
                                   borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0])

        return frame

    # Align the depth frame to color frame
    def align_frames(self, frames):
        aligned_frames = self.align.process(frames)

        # Get aligned frames
        aligned_depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()

        # Validate that both frames are valid
        if not aligned_depth_frame or not color_frame:
            return None, None

        # Generate color image
        color_image = np.asanyarray(color_frame.get_data())

        # Transform the depth map into a RGB image
        depth_colormap = np.asanyarray(self.colorizer.colorize(aligned_depth_frame).get_data())

        # Also return the aligned depth frame. It is needed to calculate distances
        return color_image, depth_colormap, aligned_depth_frame

    # Based on: https://www.youtube.com/watch?v=PtCQH93GucA
    def perspective_transformation(self, frame):
        x = frame.shape[1]

        pts1 = np.float32([list(self.table_corner_top_left), list(self.table_corner_top_right),
                           list(self.table_corner_bottom_left), list(self.table_corner_bottom_right)])
        pts2 = np.float32([[0, 0], [x, 0], [0, x / 2], [x, x / 2]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)

        frame = cv2.warpPerspective(frame, matrix, (x, int(x / 2)))

        return frame

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Functions for hand tracking
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # Detect hand position using the google mediapipe framework
    def detect_hands(self, color_image, aligned_depth_frame):
        # Hand detection (current implementation is far from real time). To reduce lag, the detection only
        # takes place only once in 8 frames
        if self.hand_tracking_enabled and self.frame % 8 == 0:
            self.hand_points, _ = self.detector(cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB))
            if self.hand_points is not None:
                # The fingertip in the google mediapipe handtracking model has the ID 8.
                distance_camera_fingertip = int(aligned_depth_frame.get_distance(int(self.hand_points[8][0]),
                                                                                 int(self.hand_points[8][1])) * 100)
                distance_fingertip_table = DISTANCE_CAMERA_TABLE - distance_camera_fingertip
                if distance_fingertip_table < 0:
                    self.last_distance = 0
                else:
                    self.last_distance = distance_fingertip_table
            else:
                self.last_distance = None  #

    # Draw circles on the frame for all detected coordinates of the hand
    def add_hand_tracking_points(self, frame, points):
        if points is not None:
            point_id = 0
            for point in points:
                x, y = point
                if point_id == 8:  # Id of index finger -> draw in different color
                    cv2.circle(frame, (int(x), int(y)), THICKNESS * 5, (255, 0, 0), -1)
                else:
                    if self.show_hand_model:
                        cv2.circle(frame, (int(x), int(y)), THICKNESS * 2, POINT_COLOR, -1)
                point_id += 1
            if self.show_hand_model:
                for connection in CONNECTIONS:  # Draw connections of the points
                    x0, y0 = points[connection[0]]
                    x1, y1 = points[connection[1]]
                    cv2.line(frame, (int(x0), int(y0)), (int(x1), int(y1)), CONNECTION_COLOR, THICKNESS)

        return frame

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Functions for tracking of aruco markers
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # Code for tracking Aruco markers taken from https://github.com/njanirudh/Aruco_Tracker
    def track_aruco_markers(self, frame, frame_color, draw_detected_markers=False):
        gray = cv2.cvtColor(frame_color, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected_points = aruco.detectMarkers(gray, self.aruco_dictionary,
                                                            parameters=self.aruco_detector_parameters)

        aruco_markers = {}

        # check if the ids list is not empty
        if np.all(ids is not None):
            for i in range(len(ids)):
                aruco_marker = {'angle': self.calculate_aruco_marker_rotation(corners[i][0], frame),
                                'corners': corners[i][0],
                                'centroid': self.centroid(corners[i][0])}

                aruco_markers[ids[i][0]] = aruco_marker

                # angle = self.calculate_aruco_marker_rotation(corners[i][0], frame)
                # tracker_centroid = self.centroid(corners[i][0])
                # tracker_relative_x, tracker_relative_y = self.calculate_aruco_marker_relative_pos(tracker_centroid, frame)

                # cv2.circle(frame, (int(tracker_centroid[0]), int(tracker_centroid[1])), 5, (0, 0, 255), -1)

                # Display info. ONLY FOR TESTING PURPOSES
                # cv2.putText(img=frame, text=str(int(angle)) + ' Grad' +
                #             ' Rel X: ' + str(int(tracker_relative_x * 100)) + '%' +
                #             ' Rel Y: ' + str(int(tracker_relative_y * 100)) + '%',
                #             org=(int(frame.shape[1] / 6), int(frame.shape[0] / 4)),
                #             fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=2, color=(255, 255, 255))

            if draw_detected_markers:
                # draw a square around the markers
                aruco.drawDetectedMarkers(frame, corners, ids)

        return aruco_markers

    # Calculate the rotation of an aruco marker relative to the frame
    # Returns the angle in the range from 0° to 360°
    def calculate_aruco_marker_rotation(self, aruco_marker_corners, frame):
        tracker_point_one = aruco_marker_corners[0]
        tracker_point_two = aruco_marker_corners[1]
        v1 = np.array([frame.shape[0], 0])
        v2 = np.array([tracker_point_two[0] - tracker_point_one[0], tracker_point_two[1] - tracker_point_one[1]])

        angle = self.calculate_angle(v1, v2)
        return angle

    # Calculates the relative position of the given marker on the frame
    # Returns a percentage for the x and the y pos of the marker
    def calculate_aruco_marker_relative_pos(self, tracker_centroid, frame):
        tracker_relative_x = (tracker_centroid[0] / frame.shape[1])
        tracker_relative_y = (tracker_centroid[1] / frame.shape[0])
        return tracker_relative_x, tracker_relative_y

    # Calculate the angle between the two given vectors
    def calculate_angle(self, v1, v2):
        # https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python
        angle = np.math.atan2(np.linalg.det([v1, v2]), np.dot(v1, v2))
        angle = np.degrees(angle)
        if angle < 0:
            angle = angle + 360
        return angle

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Functions for the MEMORY FUNCTION example
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def show_scrollable_timeline(self, color_image, tracker):
        if len(self.last_color_frames) > 0:  # Check if there is at least one stored image to show
            timeline_length = color_image.shape[1] / 4  # TODO: Save as constant
            interval_size = timeline_length / TIMELINE_NUM_FRAMES

            # Check if tracker is close to the displayed timeline
            if self.marker_origin[0] <= tracker['centroid'][0] <= self.marker_origin[0] + timeline_length and \
                    self.marker_origin[1] - 100 < tracker['centroid'][1] < self.marker_origin[1] + 100:
                current_interval_pos = int((tracker['centroid'][0] - self.marker_origin[0]) / interval_size)

                # if the array is not full yet with saved frames, always show the last frame present
                if current_interval_pos > len(self.last_color_frames):
                    current_interval_pos = len(self.last_color_frames) - 1

                if current_interval_pos == 0:
                    frame = self.last_color_frames[0].copy()
                else:
                    # Invert array position (take elements from the back by adding a minus)
                    frame = self.last_color_frames[-current_interval_pos].copy()

                if self.marker_origin is not None:
                    frame = self.draw_timeline(frame, timeline_length)

                cv2.imshow('window', frame)

    def draw_timeline(self, frame, timeline_length):

        black_image = np.ones((frame.shape[0], frame.shape[1], 3), np.uint8)

        # TODO: Correct offset (magic numbers here are just a placeholder)
        cv2.line(frame,
                 (int(self.marker_origin[0] - 20),
                  int(self.marker_origin[1]) + 50),
                 (int(self.marker_origin[0] + timeline_length),
                  int(self.marker_origin[1]) + 50), (30, 30, 30), 10)
        cv2.putText(img=black_image, text='- 0s',
                    org=(int(abs((self.marker_origin[0]) - black_image.shape[1])),
                         int(abs(self.marker_origin[1] - black_image.shape[0] + 80))),
                    fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=0.5, color=(30, 30, 30))
        cv2.putText(img=black_image, text='- 60s',
                    org=(int(abs((self.marker_origin[0] + timeline_length / 2) - black_image.shape[1])),
                         int(abs((self.marker_origin[1]) - black_image.shape[0] + 80))),
                    fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=0.5, color=(30, 30, 30))
        cv2.putText(img=black_image, text='- 120s',
                    org=(int(abs((self.marker_origin[0] + timeline_length) - black_image.shape[1])),
                         int(abs((self.marker_origin[1]) - black_image.shape[0] + 80))),
                    fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=0.5, color=(30, 30, 30))

        black_image = cv2.flip(black_image, -1)

        # https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_core/py_image_arithmetics/py_image_arithmetics.html
        # I want to put logo on top-left corner, So I create a ROI
        rows, cols, channels = black_image.shape
        roi = frame[0:rows, 0:cols]
        # Now create a mask of logo and create its inverse mask also
        img2gray = cv2.cvtColor(black_image, cv2.COLOR_BGR2GRAY)
        ret, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        # Now black-out the area of logo in ROI
        img1_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
        # Take only region of logo from logo image.
        img2_fg = cv2.bitwise_and(black_image, black_image, mask=mask)
        # Put logo in ROI and modify the main image
        dst = cv2.add(img1_bg, img2_fg)
        frame[0:rows, 0:cols] = dst

        return frame

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Functions for the FABRIC PATTERN example
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def display_fabric_pattern(self, frame, pattern_points, aruco_markers):
        # Move the pattern to the desired spot on the table. Take the marker pos on the frame to calculate a good
        # position for the Polygon

        ids = aruco_markers.keys()

        if ARUCO_MARKER_SHIRT_S in ids and ARUCO_MARKER_SHIRT_M in ids and ARUCO_MARKER_SHIRT_L in ids:
            tracker_centroid = aruco_markers[ARUCO_MARKER_SHIRT_M]['centroid']
            angle = aruco_markers[ARUCO_MARKER_SHIRT_M]['angle']
            pattern_points = self.scale_fabric(pattern_points, 1.5)
        elif ARUCO_MARKER_SHIRT_S in ids and ARUCO_MARKER_SHIRT_L in ids:
            tracker_centroid = self.calculate_obscured_marker_centroid(aruco_markers[ARUCO_MARKER_SHIRT_S]['centroid'],
                                                                       None,
                                                                       aruco_markers[ARUCO_MARKER_SHIRT_L]['centroid'])
            angle = aruco_markers[ARUCO_MARKER_SHIRT_S]['angle']
            pattern_points = self.scale_fabric(pattern_points, 1.5)
        elif ARUCO_MARKER_SHIRT_S in ids and ARUCO_MARKER_SHIRT_M in ids:
            tracker_centroid = self.calculate_obscured_marker_centroid(aruco_markers[ARUCO_MARKER_SHIRT_S]['centroid'],
                                                                       aruco_markers[ARUCO_MARKER_SHIRT_M]['centroid'],
                                                                       None)
            angle = aruco_markers[ARUCO_MARKER_SHIRT_M]['angle']
            pattern_points = self.scale_fabric(pattern_points, 1.7)
        elif ARUCO_MARKER_SHIRT_M in ids and ARUCO_MARKER_SHIRT_L in ids:
            tracker_centroid = self.calculate_obscured_marker_centroid(None,
                                                                       aruco_markers[ARUCO_MARKER_SHIRT_M]['centroid'],
                                                                       aruco_markers[ARUCO_MARKER_SHIRT_L]['centroid'])
            angle = aruco_markers[ARUCO_MARKER_SHIRT_M]['angle']
            pattern_points = self.scale_fabric(pattern_points, 1.2)
        else:
            return

        # Threshold for rotation
        if self.last_fabric_pattern_angle is None:
            self.last_fabric_pattern_angle = angle
        if abs(self.last_fabric_pattern_angle - angle) > 3:
            pattern_points = self.rotate_points(pattern_points, angle)
            self.last_fabric_pattern_angle = angle
        else:
            pattern_points = self.rotate_points(pattern_points, self.last_fabric_pattern_angle)

        # Threshold for position
        if self.last_tracker_centroid_pos is None:
            self.last_tracker_centroid_pos = tracker_centroid
        if abs(self.last_tracker_centroid_pos[0] - tracker_centroid[0]) > 3 \
                or abs(self.last_tracker_centroid_pos[1] - tracker_centroid[1]) > 3:  # Threshold for rotation
            pattern_points = self.calculate_fabric_pos_offset(tracker_centroid, pattern_points, frame)
            # Draw a circle to mark the selected pattern size
            cv2.circle(frame, (int(tracker_centroid[0]), int(tracker_centroid[1])), 30, (0, 0, 255), 3)
            self.last_tracker_centroid_pos = tracker_centroid
        else:
            pattern_points = self.calculate_fabric_pos_offset(self.last_tracker_centroid_pos, pattern_points, frame)
            # Draw a circle to mark the selected pattern size
            cv2.circle(frame, (int(self.last_tracker_centroid_pos[0]), int(self.last_tracker_centroid_pos[1])), 30,
                       (0, 0, 255), 3)

        centroid_of_pattern = self.centroid(pattern_points)
        # Draw line to connect tracker and pattern
        cv2.line(frame, (int(tracker_centroid[0]), int(tracker_centroid[1])), (int(centroid_of_pattern[0]),
                 int(centroid_of_pattern[1])), (0, 0, 255), 2)

        # Draw the selected pattern
        cv2.polylines(frame, [pattern_points], 1, (255, 255, 255), thickness=2)

    def calculate_fabric_pos_offset(self, tracker_centroid, pattern_points, frame):
        tracker_relative_x, tracker_relative_y = self.calculate_aruco_marker_relative_pos(tracker_centroid, frame)
        if tracker_relative_x <= 0.5:   # If the tracker is on the left half of the table
            x = int(tracker_centroid[0] + frame.shape[1] / 2)
        else:  # If the tracker is on the right side of the table
            x = int(tracker_centroid[0] - frame.shape[1] / 2)

        #y = abs(int(tracker_centroid[1] - frame.shape[0]))
        y = abs(int(tracker_centroid[1]))
        offset = [x, y]
        pattern_points = pattern_points + offset
        pattern_points = pattern_points.astype(int)  # Convert all floats to int because coordinates are expected to be Integers

        # Make sure the pattern is not displayed outside the table
        x = 0
        y = 0
        fabric_bounding_rect = cv2.boundingRect(pattern_points)
        #cv2.rectangle(frame, fabric_bounding_rect, (255, 0, 0), 3)
        if fabric_bounding_rect[0] < 0:
            x = abs(fabric_bounding_rect[0])
        if fabric_bounding_rect[0] + fabric_bounding_rect[2] > frame.shape[1]:
            x = -1 * (fabric_bounding_rect[0] + fabric_bounding_rect[2] - frame.shape[1])

        if fabric_bounding_rect[1] < 0:
            y = abs(fabric_bounding_rect[1])
        if fabric_bounding_rect[1] + fabric_bounding_rect[3] > frame.shape[0]:
            y = -1 * (fabric_bounding_rect[1] + fabric_bounding_rect[3] - frame.shape[0])

        offset = [x, y]
        pattern_points = pattern_points + offset

        return pattern_points

    # Calculated the center of the obscured aruco marker
    def calculate_obscured_marker_centroid(self, marker_left, marker_middle, marker_right):
        if marker_left is None:
            x = marker_middle[0] - (marker_right[0] - marker_middle[0])
            y = marker_middle[1] - (marker_right[1] - marker_middle[1])
        elif marker_middle is None:
            x = (marker_left[0] + marker_right[0]) / 2
            y = (marker_left[1] + marker_right[1]) / 2
        elif marker_right is None:
            x = marker_middle[0] + (marker_middle[0] - marker_left[0])
            y = marker_middle[1] + (marker_middle[1] - marker_left[1])

        return [x, y]

    def scale_fabric(self, points, scale_factor):
        # Get centroid
        centroid = self.centroid(points)

        # Move to origin
        points = points - centroid

        for point in points:
            point[0] *= scale_factor
            point[1] *= scale_factor

        return points


def main():
    transformation = VigitiaDemo()
    sys.exit()


if __name__ == '__main__':
    main()