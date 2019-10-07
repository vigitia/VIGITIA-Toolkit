import sys
import pyrealsense2 as rs
import cv2
import cv2.aruco as aruco
import numpy as np

from hand_tracker import HandTracker

# Built upon: https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/examples/align-depth2color.py
# Code for Hand Tracking and Models from https://github.com/metalwhale/hand_tracking

# Current distance between camera and table in cm
DISTANCE_CAMERA_TABLE = 110  # cm

# Camera Settings
DEPTH_RES_X = 1280
DEPTH_RES_Y = 720
RGB_RES_X = 1280
RGB_RES_Y = 720

DEPTH_FPS = 30
RGB_FPS = 30

# Output image (currently needs to be 16x9 because the projector can project this)
OUTPUT_IMAGE_WIDTH = 1920
OUTPUT_IMAGE_HEIGHT = 1080

# Coordinates of table corners for perspective transformation
CORNER_TOP_LEFT = (85, 45)
CORNER_TOP_RIGHT = (1269, 94)
CORNER_BOTTOM_LEFT = (67, 641)
CORNER_BOTTOM_RIGHT = (1248, 675)

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

FABRIC_PATTERN_ONE = np.array([[-77, -56], [-41, -56], [116, -63], [191, -17], [156, 23], [85, -19], [96, 94],
                                [-83, 102], [-77, -11], [-174, 28], [-188, -24]])


class TransformationRGBDepth:

    pipeline = None
    align = None
    colorizer = None
    last_color_frame = None
    stored_image = None
    hand_detector = None

    aruco_dictionary = None
    aruco_detector_parameters = None

    # If calibration mode is on, the user can select the table corners
    calibration_mode = False
    display_mode = "off"
    hand_tracking_enabled = False
    aruco_markers_enabled = False
    outline_enabled = False
    show_hand_model = False

    frame = 0
    depth_scale = 0
    hand_points = None
    last_distance = None

    last_fabric_pattern_angle = 0

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
        cv2.setMouseCallback('window', self.mouse_click)

        self.init_colorizer()
        self.init_hand_detector()
        self.init_aruco_tracking()
        self.loop()

    def mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print((x, y))

    def init_colorizer(self):
        self.colorizer = rs.colorizer()
        self.colorizer.set_option(rs.option.color_scheme, 0)   # Define the color scheme
        self.colorizer.set_option(rs.option.histogram_equalization_enabled, 0)
        self.colorizer.set_option(rs.option.min_distance, 1.0)  # meter
        self.colorizer.set_option(rs.option.max_distance, 1.3)  # meter

    def init_hand_detector(self):
        self.detector = HandTracker(PALM_MODEL_PATH, LANDMARK_MODEL_PATH, ANCHORS_PATH, box_shift=0.2, box_enlarge=1.3)

    def init_aruco_tracking(self):
        self.aruco_dictionary = aruco.Dictionary_get(aruco.DICT_4X4_100)
        self.aruco_detector_parameters = aruco.DetectorParameters_create()
        self.aruco_detector_parameters.adaptiveThreshConstant = 10

    # Streaming loop
    def loop(self):
        try:
            while True:
                self.frame += 1
                # Get frameset of color and depth
                frames = self.pipeline.wait_for_frames()
                color_image, depth_colormap, aligned_depth_frame = self.align_frames(frames)

                depth_data = aligned_depth_frame.get_data()
                np_image = np.asanyarray(depth_data)
                #distance = np_image[int(len(np_image) / 2)][int(len(np_image[0]) / 2)] * self.depth_scale * 100
                #print(str("%.2f" % distance) + ' cm')

                #distance = cv2.mean(np_image * self.depth_scale)
                #print(distance)

                # for i in range(color_image.shape[0]):
                #     for j in range(color_image.shape[1]):
                #         distance = np_image[i][j] * self.depth_scale
                #         if distance > 1.08:
                #             color_image[i, j] = (0, 0, 0)

                self.last_color_frame = color_image

                # Hand detection
                if self.hand_tracking_enabled and self.frame % 8 == 0:
                    self.hand_points, _ = self.detector(cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB))
                    if self.hand_points is not None:
                        # The fingertip in the google mediapipe handtracking model has the ID 8.
                        distance_camera_fingertip = int(aligned_depth_frame.get_distance(int(self.hand_points[8][0]), int(self.hand_points[8][1])) * 100)
                        distance_fingertip_table = DISTANCE_CAMERA_TABLE - distance_camera_fingertip
                        if distance_fingertip_table < 0:
                            self.last_distance = 0
                        else:
                            self.last_distance = distance_fingertip_table
                    else:
                        self.last_distance = None

                if self.display_mode == "RGB":
                    if not self.calibration_mode:
                        color_image = self.add_hand_tracking_points(color_image, self.hand_points)
                        # Perspective Transformation on images
                        color_image = self.perspective_transformation(color_image)
                        if self.outline_enabled:
                            color_image = self.highlight_objects(color_image, False)
                        if self.aruco_markers_enabled:
                            color_image, angle, tracker_centroid = self.track_aruco_markers(color_image, color_image)

                        # Canny Edge Detection
                        # https://www.pyimagesearch.com/2014/04/21/building-pokedex-python-finding-game-boy-screen-step-4-6/
                        # color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
                        # color_image = cv2.bilateralFilter(color_image, 11, 17, 17)
                        # color_image = cv2.Canny(color_image, 100, 200)

                        #mask_img = self.fgbg.apply(color_image)
                        #color_image = cv2.bitwise_and(color_image, color_image, mask=mask_img)

                        # Add black border on top to fill the missing pixels from 2:1 (16:8) to 16:9 aspect ratio
                        color_image = self.add_border(color_image)
                    cv2.imshow('window', color_image)
                elif self.display_mode == "depth":
                    # Add black border on top to fill the missing pixels from 2:1 (16:8) to 16:9 aspect ratio
                    if not self.calibration_mode:
                        depth_colormap = self.add_hand_tracking_points(depth_colormap, self.hand_points)
                        # Perspective Transformation on images
                        depth_colormap = self.perspective_transformation(depth_colormap)
                        depth_colormap = self.add_border(depth_colormap)

                    cv2.imshow('window', depth_colormap)
                elif self.display_mode == "off":
                    black_image = np.zeros((color_image.shape[0], color_image.shape[1], 3), np.uint8)
                    black_image = self.add_hand_tracking_points(black_image, self.hand_points)
                    black_image = self.perspective_transformation(black_image)

                    if self.outline_enabled:
                        black_image = self.highlight_objects(self.perspective_transformation(color_image), True)
                    if self.aruco_markers_enabled:
                        black_image, angle, tracker_centroid = self.track_aruco_markers(black_image,
                                                                                        self.perspective_transformation(color_image))

                    black_image = self.add_border(black_image)
                    if self.last_distance is not None:
                        cv2.putText(img=black_image, text=str(self.last_distance) + " cm",
                                    org=(int(color_image.shape[1]/6), int(color_image.shape[0]/4)),
                                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=2, color=(255, 255, 255))

                    cv2.imshow('window', black_image)
                elif self.display_mode == 'memory':
                    copy = self.stored_image.copy()

                    # Invert image
                    #copy = cv2.bitwise_not(copy)

                    # Canny Edge Detection
                    # https://www.pyimagesearch.com/2014/04/21/building-pokedex-python-finding-game-boy-screen-step-4-6/
                    copy = cv2.cvtColor(copy, cv2.COLOR_BGR2GRAY)
                    copy = cv2.bilateralFilter(copy, 11, 17, 17)
                    copy = cv2.Canny(copy, 40, 40)

                    copy = self.add_border(copy)
                    cv2.imshow('window', copy)
                elif self.display_mode == "pattern":
                    color_image = self.perspective_transformation(color_image)
                    black_image = np.zeros((color_image.shape[0], color_image.shape[1], 3), np.uint8)
                    self.pattern_example(black_image, color_image)

                    black_image = self.add_border(black_image)
                    cv2.imshow('window', black_image)

                key = cv2.waitKey(1)
                # Press esc or 'q' to close the image window
                if key & 0xFF == ord('q') or key == 27:
                    cv2.destroyAllWindows()
                    break
                else:
                    self.check_key_inputs(key, color_image, depth_colormap)
        finally:
            self.pipeline.stop()

    # Put a white circle around all objects on the table, like a spotlight
    def highlight_objects(self, frame, draw_on_black=True):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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
            if radius < frame.shape[0] / 2:
                frame = cv2.circle(frame, center, radius, (255, 255, 255), cv2.FILLED)

        return frame

    # https://scipython.com/book/chapter-6-numpy/examples/creating-a-rotation-matrix-in-numpy/
    def get_rotation_matrix(self, angle):
        theta = np.radians(angle)
        c, s = np.cos(theta), np.sin(theta)
        rotation_matrix = np.array(((c, -s), (s, c)))
        return rotation_matrix

    def rotate_points(self, points, angle):
        rotation_matrix = self.get_rotation_matrix(angle)
        # Get centroid
        centroid = self.centroid(points)

        # Move to origin
        points = points - centroid
        #print(points.astype(int).tolist())

        # Rotate (see: https://scipython.com/book/chapter-6-numpy/examples/creating-a-rotation-matrix-in-numpy/)
        points = np.dot(points, rotation_matrix.T)

        # Move back to original position
        points = points + centroid

        # Convert all floats to int
        points = points.astype(int)
        return points

    # https://progr.interplanety.org/en/python-how-to-find-the-polygon-center-coordinates/
    def centroid(self, vertexes):
        _x_list = [vertex[0] for vertex in vertexes]
        _y_list = [vertex[1] for vertex in vertexes]
        _len = len(vertexes)
        _x = sum(_x_list) / _len
        _y = sum(_y_list) / _len
        return (_x, _y)

        # Code for tracking Aruco markers taken from https://github.com/njanirudh/Aruco_Tracker
    def track_aruco_markers(self, frame, frame_color):
        gray = cv2.cvtColor(frame_color, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected_points = aruco.detectMarkers(gray, self.aruco_dictionary,
                                                            parameters=self.aruco_detector_parameters)
        angle = 0
        tracker_centroid = None

        # check if the ids list is not empty
        if np.all(ids is not None):
            for i in range(len(ids)):
                if ids[i] == 4:

                    angle = self.calculate_aruco_marker_rotation(corners[i][0], frame)
                    tracker_centroid = self.centroid(corners[i][0])
                    tracker_relative_x, tracker_relative_y = self.calculate_aruco_marker_relative_pos(tracker_centroid, frame)

                    cv2.circle(frame, (int(tracker_centroid[0]), int(tracker_centroid[1])), 5, (0, 0, 255), -1)

                    # Display info. ONLY FOR TESTING PURPOSES
                    # cv2.putText(img=frame, text=str(int(angle)) + ' Grad' +
                    #             ' Rel X: ' + str(int(tracker_relative_x * 100)) + '%' +
                    #             ' Rel Y: ' + str(int(tracker_relative_y * 100)) + '%',
                    #             org=(int(frame.shape[1] / 6), int(frame.shape[0] / 4)),
                    #             fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=2, color=(255, 255, 255))

            # draw a square around the markers
            aruco.drawDetectedMarkers(frame, corners, ids)

        return frame, angle, tracker_centroid

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

    def calculate_angle(self, v1, v2):
        # https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python
        angle = np.math.atan2(np.linalg.det([v1, v2]), np.dot(v1, v2))
        angle = np.degrees(angle)
        if angle < 0:
            angle = angle + 360
        return angle

    def check_key_inputs(self, key, color_image, depth_colormap):
        if key == 48:  # Key 0
            self.display_mode = 'pattern'
        elif key == 49:  # Key 1
            if self.display_mode == "RGB":
                self.display_mode = "depth"
            else:
                self.display_mode = "RGB"
        elif key == 50:  # Key 2
            self.display_mode = "off"
        elif key == 51:  # Key 3
            self.stored_image = self.perspective_transformation(self.last_color_frame.copy())
            self.display_mode = 'memory'
        elif key == 52:  # Key 4
            cv2.imwrite('depth.png', depth_colormap)
            cv2.imwrite('color.png', color_image)
        elif key == 97: # A as in Aruco Markers
            self.aruco_markers_enabled = not self.aruco_markers_enabled
        elif key == 99:  # C as in Calibrate
            self.calibration_mode = not self.calibration_mode
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

    def add_hand_tracking_points(self, frame, points):
        if points is not None:
            point_id = 0
            for point in points:
                x, y = point
                if point_id == 8:
                    cv2.circle(frame, (int(x), int(y)), THICKNESS * 5, (255, 0, 0), -1)
                else:
                    if self.show_hand_model:
                        cv2.circle(frame, (int(x), int(y)), THICKNESS * 2, POINT_COLOR, -1)
                point_id += 1
            if self.show_hand_model:
                for connection in CONNECTIONS:
                    x0, y0 = points[connection[0]]
                    x1, y1 = points[connection[1]]
                    cv2.line(frame, (int(x0), int(y0)), (int(x1), int(y1)), CONNECTION_COLOR, THICKNESS)

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

        # Draw circles to mark the screen corners. Only show them if calibration mode is on
        if self.calibration_mode:
            cv2.circle(frame, CORNER_TOP_LEFT, 2, (0, 0, 255), -1)
            cv2.circle(frame, CORNER_TOP_RIGHT, 2, (0, 0, 255), -1)
            cv2.circle(frame, CORNER_BOTTOM_LEFT, 2, (0, 0, 255), -1)
            cv2.circle(frame, CORNER_BOTTOM_RIGHT, 2, (0, 0, 255), -1)

        pts1 = np.float32([list(CORNER_TOP_LEFT), list(CORNER_TOP_RIGHT), list(CORNER_BOTTOM_LEFT), list(CORNER_BOTTOM_RIGHT)])
        pts2 = np.float32([[0, 0], [x, 0], [0, x / 2], [x, x / 2]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        # Only do the perspective transformation if calibration mode is off.
        if not self.calibration_mode:
            frame = cv2.warpPerspective(frame, matrix, (x, int(x / 2)))

        return frame

    def pattern_example(self, frame, frame_color):
        frame, angle, tracker_centroid = self.track_aruco_markers(frame, frame_color)

        if tracker_centroid is not None:
            self.display_fabric_pattern(frame, FABRIC_PATTERN_ONE, tracker_centroid, angle)

    def display_fabric_pattern(self, frame, pattern_points, tracker_centroid, angle):
        # Move the pattern to the desired spot on the table. Take the marker pos on the frame to calculate a good
        # position for the Polygon
        pattern_points = self.rotate_points(pattern_points, angle)
        pattern_points = self.calculate_fabric_pos_offset(tracker_centroid, pattern_points, frame)
        centroid_of_pattern = self.centroid(pattern_points)
        cv2.line(frame, (int(tracker_centroid[0]), int(tracker_centroid[1])), (int(centroid_of_pattern[0]),
                 int(centroid_of_pattern[1])), (255, 0, 0), 1)

        cv2.polylines(frame, [pattern_points], 1, (255, 255, 255), thickness=3)

    def calculate_fabric_pos_offset(self, tracker_centroid, pattern_points, frame):
        tracker_relative_x, tracker_relative_y = self.calculate_aruco_marker_relative_pos(tracker_centroid, frame)
        if tracker_relative_x <= 0.5:
            x = int(tracker_centroid[0] + frame.shape[1] / 2)
        else:
            x = int(tracker_centroid[0] - frame.shape[1] / 2)
        y = abs(int(tracker_centroid[1] - frame.shape[0]))
        offset = [x, y]
        pattern_points = pattern_points + offset

        x = 0
        y = 0
        fabric_bounding_rect = cv2.boundingRect(pattern_points)
        #cv2.rectangle(frame, fabric_bounding_rect, (255, 0, 0), 3)
        print(fabric_bounding_rect, frame.shape[0], frame.shape[1])
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


def main():
    transformation = TransformationRGBDepth()
    sys.exit()


if __name__ == '__main__':
    main()