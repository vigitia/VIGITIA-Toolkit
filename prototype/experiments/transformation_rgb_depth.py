import sys
import pyrealsense2 as rs
import cv2
import numpy as np

from hand_tracker import HandTracker

# Built upon: https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/examples/align-depth2color.py
# Code for Hand Tracking and Models from https://github.com/metalwhale/hand_tracking

# Current distance between camera and table in cm
DISTANCE_CAMERA_TABLE = 112  # cm

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
CORNER_TOP_LEFT = (92, 33)
CORNER_TOP_RIGHT = (1243, 55)
CORNER_BOTTOM_LEFT = (85, 608)
CORNER_BOTTOM_RIGHT = (1231, 627)

# Since the projection field of the projector is larger than the table,
# we need to add black borders on at least two sides
BORDER_TOP = 100  # px
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
    (0, 1), (1, 2), (2, 3), (3, 4),
    (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12),
    (13, 14), (14, 15), (15, 16),
    (17, 18), (18, 19), (19, 20),
    (0, 5), (5, 9), (9, 13), (13, 17), (0, 17)
]


class TransformationRGBDepth:

    pipeline = None
    align = None
    colorizer = None
    last_color_frame = None
    stored_image = None
    hand_detector = None

    # If calibration mode is on, the user can select the table corners
    calibration_mode = False
    display_mode = "off"
    hand_tracking_enabled = False
    show_hand_model = False

    frame = 0
    depth_scale = 0
    hand_points = None
    last_distance = -1

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
        # dev = profile.get_device()
        # for sensor in dev.sensors:
        #     if not sensor.is_depth_sensor():
        #         break
        # roi_sensor = sensor.as_roi_sensor()
        # sensor_roi = roi_sensor.get_region_of_interest()
        # sensor_roi.min_x, sensor_roi.max_x = CORNER_TOP_LEFT[0], CORNER_TOP_RIGHT[0]
        # sensor_roi.min_y, sensor_roi.max_y = CORNER_TOP_LEFT[1], CORNER_BOTTOM_RIGHT[1]
        # roi_sensor.set_region_of_interest(sensor_roi)
        # print(sensor_roi.min_x, sensor_roi.max_x, sensor_roi.min_y, sensor_roi.max_y)

        # Getting the depth sensor's depth scale (see rs-align example for explanation)
        depth_sensor = profile.get_device().first_depth_sensor()
        self.depth_scale = depth_sensor.get_depth_scale()

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
        self.loop()

    def mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print((x, y))

    def init_colorizer(self):
        self.colorizer = rs.colorizer()
        self.colorizer.set_option(rs.option.color_scheme, 0)   # Define the color scheme
        self.colorizer.set_option(rs.option.histogram_equalization_enabled, 0)
        self.colorizer.set_option(rs.option.min_distance, 0.9)  # meter
        self.colorizer.set_option(rs.option.max_distance, 1.6)  # meter

    def init_hand_detector(self):
        self.detector = HandTracker(
            PALM_MODEL_PATH,
            LANDMARK_MODEL_PATH,
            ANCHORS_PATH,
            box_shift=0.2,
            box_enlarge=1.3
        )

    # Streaming loop
    def loop(self):
        try:
            while True:
                self.frame += 1
                # Get frameset of color and depth
                frames = self.pipeline.wait_for_frames()
                color_image, depth_colormap, aligned_depth_frame = self.align_frames(frames)

                self.last_color_frame = color_image

                # Hand detection
                if self.hand_tracking_enabled and self.frame % 4 == 0:
                    self.hand_points, _ = self.detector(cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB))
                    if self.hand_points is not None:
                        self.last_distance = aligned_depth_frame.get_distance(int(self.hand_points[8][0]), int(self.hand_points[8][1]))
                    else:
                        self.last_distance = -1

                # Flip image vertically and horizontally (instead of rotating the camera 180° on the current setup)
                #color_image = cv2.flip(color_image, -1)
                #depth_colormap = cv2.flip(depth_colormap, -1)

                if self.display_mode == "RGB":
                    if not self.calibration_mode:
                        color_image = self.add_hand_tracking_points(color_image, self.hand_points)
                        # Perspective Transformation on images
                        color_image = self.perspective_transformation(color_image)
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
                    #black_image = cv2.flip(black_image, -1)
                    black_image = self.perspective_transformation(black_image)
                    black_image = self.add_border(black_image)
                    if not self.last_distance == -1:
                        cv2.putText(img=black_image, text=str(int(self.last_distance * 100)) + " cm",
                                    org=(int(color_image.shape[1]/6), int(color_image.shape[0]/4)),
                                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=2, color=(255, 255, 255))
                    cv2.imshow('window', black_image)
                elif self.display_mode == 'memory':
                    copy = self.stored_image.copy()

                    # Invert image
                    #copy = cv2.bitwise_not(copy)

                    # Canny Edge Detection
                    # https://www.pyimagesearch.com/2014/04/21/building-pokedex-python-finding-game-boy-screen-step-4-6/
                    # copy = cv2.cvtColor(copy, cv2.COLOR_BGR2GRAY)
                    # copy = cv2.bilateralFilter(copy, 11, 17, 17)
                    # copy = cv2.Canny(copy, 100, 200)

                    # Contours
                    copy = cv2.cvtColor(copy, cv2.COLOR_BGR2GRAY)
                    copy = cv2.bilateralFilter(copy, 11, 17, 17)
                    ret, thresh = cv2.threshold(copy, 100, 255, 0)
                    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                    copy = np.zeros((copy.shape[0], copy.shape[1], 3), np.uint8)
                    cv2.drawContours(copy, contours, -1, (0, 255, 0), 1)


                    copy = self.add_border(copy)
                    cv2.imshow('window', copy)

                key = cv2.waitKey(1)
                # Press esc or 'q' to close the image window
                if key & 0xFF == ord('q') or key == 27:
                    cv2.destroyAllWindows()
                    break
                else:
                    self.check_key_inputs(key, color_image, depth_colormap)
        finally:
            self.pipeline.stop()

    def check_key_inputs(self, key, color_image, depth_colormap):
        if key == 49:  # Key 1:
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
                    self.last_distance = -1

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
            cv2.circle(frame, CORNER_TOP_LEFT, 1, (0, 0, 255), -1)
            cv2.circle(frame, CORNER_TOP_RIGHT, 1, (0, 0, 255), -1)
            cv2.circle(frame, CORNER_BOTTOM_LEFT, 1, (0, 0, 255), -1)
            cv2.circle(frame, CORNER_BOTTOM_RIGHT, 1, (0, 0, 255), -1)

        pts1 = np.float32([list(CORNER_TOP_LEFT), list(CORNER_TOP_RIGHT), list(CORNER_BOTTOM_LEFT), list(CORNER_BOTTOM_RIGHT)])
        pts2 = np.float32([[0, 0], [x, 0], [0, x / 2], [x, x / 2]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        # Only do the perspective transformation if calibration mode is off.
        if not self.calibration_mode:
            frame = cv2.warpPerspective(frame, matrix, (x, int(x / 2)))

        return frame


def main():
    transformation = TransformationRGBDepth()
    sys.exit()


if __name__ == '__main__':
    main()