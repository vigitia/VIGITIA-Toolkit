import sys
import pyrealsense2 as rs
import cv2
import numpy as np

from hand_tracker import HandTracker

# Built upon: https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/examples/align-depth2color.py
# Code for Hand Tracking and Models from https://github.com/metalwhale/hand_tracking

'''
Current distance between camera and table: 121.5cm
'''

DEPTH_RES_X = 1280
DEPTH_RES_Y = 720
RGB_RES_X = 1280
RGB_RES_Y = 720

DEPTH_FPS = 30
RGB_FPS = 30

# Coordinates of table corners
CORNER_TOP_LEFT = (42, 135)
CORNER_TOP_RIGHT = (1191, 138)
CORNER_BOTTOM_LEFT = (37, 707)
CORNER_BOTTOM_RIGHT = (1192, 714)

BORDER_TOP = 0  # px
BORDER_BOTTOM = 115  # px
BORDER_LEFT = 60  # px
BORDER_RIGHT = 0  # px

# Output image (currently needs to be 16x9 because the projector can project this)
OUTPUT_IMAGE_WIDTH = 1920
OUTPUT_IMAGE_HEIGHT = 1080

CALIBRATE = False

PALM_MODEL_PATH = "./palm_detection_without_custom_op.tflite"
LANDMARK_MODEL_PATH = "./hand_landmark.tflite"
ANCHORS_PATH = "./anchors.csv"

POINT_COLOR = (0, 255, 0)
CONNECTION_COLOR = (255, 255, 0)
THICKNESS = 2

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
connections = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12),
    (13, 14), (14, 15), (15, 16),
    (17, 18), (18, 19), (19, 20),
    (0, 5), (5, 9), (9, 13), (13, 17), (0, 17)
]


class TransformationRGBDepth():

    pipeline = None
    align = None
    colorizer = None

    display_mode = "off"
    stored_image = None
    hand_detector = None
    show_hand_model = False

    def __init__(self):
        # Create a pipeline
        self.pipeline = rs.pipeline()

        # Create a config and configure the pipeline to stream different resolutions of color and depth streams
        config = rs.config()
        config.enable_stream(rs.stream.depth, DEPTH_RES_X, DEPTH_RES_Y, rs.format.z16, DEPTH_FPS)
        config.enable_stream(rs.stream.color, RGB_RES_X, RGB_RES_Y, rs.format.bgr8, RGB_FPS)

        # Start streaming
        profile = self.pipeline.start(config)

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
        depth_scale = depth_sensor.get_depth_scale()
        print("Depth Scale is: ", depth_scale)

        # Create an align object
        # rs.align allows us to perform alignment of depth frames to others frames
        # The "align_to" is the stream type to which we plan to align depth frames.
        align_to = rs.stream.color
        self.align = rs.align(align_to)

        # Set to fullscreen
        cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        cv2.setMouseCallback('window', self.mouse_click)

        self.init_colorizer()
        self.init_hand_detector()
        self.loop()

    def init_hand_detector(self):
        self.detector = HandTracker(
            PALM_MODEL_PATH,
            LANDMARK_MODEL_PATH,
            ANCHORS_PATH,
            box_shift=0.2,
            box_enlarge=1.3
        )

    def mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print((x, y))

    def init_colorizer(self):
        self.colorizer = rs.colorizer()
        self.colorizer.set_option(rs.option.color_scheme, 0)
        self.colorizer.set_option(rs.option.histogram_equalization_enabled, 0)
        self.colorizer.set_option(rs.option.min_distance, 0.9)  # meter
        self.colorizer.set_option(rs.option.max_distance, 1.6)  # meter

    # Streaming loop
    def loop(self):
        try:
            while True:
                # Get frameset of color and depth
                frames = self.pipeline.wait_for_frames()
                color_image, depth_colormap = self.align_frames(frames)

                color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)

                # Flip image vertically and horizontally (instead of rotating the camera 180° on the current setup)
                color_image = cv2.flip(color_image, -1)
                depth_colormap = cv2.flip(depth_colormap, -1)

                # Perspective Transformation on images
                color_image = self.perspective_transformation(color_image)
                depth_colormap = self.perspective_transformation(depth_colormap)

                # Hand detection
                points, _ = self.detector(color_image)

                if self.display_mode == "RGB":
                    if not CALIBRATE:
                        color_image = self.add_hand_tracking_points(color_image, points, depth_colormap)
                        color_image = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)
                        # Add black border on top to fill the missing pixels from 2:1 (16:8) to 16:9 aspect ratio
                        color_image = cv2.copyMakeBorder(color_image, top=BORDER_TOP, bottom=BORDER_BOTTOM,
                                                         left=BORDER_LEFT, right=BORDER_RIGHT,
                                                         borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0])
                    cv2.imshow('window', color_image)
                elif self.display_mode == "depth":
                    # Add black border on top to fill the missing pixels from 2:1 (16:8) to 16:9 aspect ratio
                    if not CALIBRATE:
                        depth_colormap = self.add_hand_tracking_points(depth_colormap, points, depth_colormap)
                        depth_colormap = cv2.copyMakeBorder(depth_colormap, top=BORDER_TOP, bottom=BORDER_BOTTOM,
                                                            left=BORDER_LEFT, right=BORDER_RIGHT,
                                                            borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0])

                    cv2.imshow('window', depth_colormap)
                elif self.display_mode == "off":
                    black_image = np.zeros((color_image.shape[0], color_image.shape[1], 3), np.uint8)
                    black_image = self.add_hand_tracking_points(black_image, points, depth_colormap)
                    black_image = cv2.copyMakeBorder(black_image, top=BORDER_TOP, bottom=BORDER_BOTTOM,
                                                     left=BORDER_LEFT, right=BORDER_RIGHT,
                                                     borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0])
                    cv2.imshow('window', black_image)
                elif self.display_mode == 'memory':
                    cv2.imshow('window', self.stored_image)

                key = cv2.waitKey(1)
                # Press esc or 'q' to close the image window
                if key & 0xFF == ord('q') or key == 27:
                    cv2.destroyAllWindows()
                    break
                elif key == 49:  # Key 1:
                    if self.display_mode == "RGB":
                        self.display_mode = "depth"
                    else:
                        self.display_mode = "RGB"
                elif key == 50:  # Key 2
                    self.display_mode = "off"
                elif key == 51:  # Key 3
                    self.display_mode = 'memory'
                    #self.stored_image = cv2.bitwise_not(color_image)
                    self.stored_image = color_image
                elif key == 52:
                    cv2.imwrite('depth.png', depth_colormap)
                    cv2.imwrite('color.png', color_image)
                elif key == 104:  # H
                    self.show_hand_model = not self.show_hand_model
        finally:
            self.pipeline.stop()

    def add_hand_tracking_points(self, frame, points, depth_image):
        if points is not None:
            point_id = 0
            for point in points:
                x, y = point
                if point_id == 8:
                    cv2.circle(frame, (int(x), int(y)), THICKNESS * 5, (255, 0, 0), -1)
                    #depth = depth_image.get_distance(int(x), int(y))
                    #print(depth)
                else:
                    if self.show_hand_model:
                        cv2.circle(frame, (int(x), int(y)), THICKNESS * 2, POINT_COLOR, -1)
                point_id += 1
            if self.show_hand_model:
                for connection in connections:
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
        #depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        return color_image, depth_colormap

    # Based on: https://www.youtube.com/watch?v=PtCQH93GucA
    def perspective_transformation(self, frame):
        x = frame.shape[1]
        y = frame.shape[0]

        # Draw circles to mark the screen corners
        cv2.circle(frame, CORNER_TOP_LEFT, 1, (0, 0, 255), -1)
        cv2.circle(frame, CORNER_TOP_RIGHT, 1, (0, 0, 255), -1)
        cv2.circle(frame, CORNER_BOTTOM_LEFT, 1, (0, 0, 255), -1)
        cv2.circle(frame, CORNER_BOTTOM_RIGHT, 1, (0, 0, 255), -1)

        pts1 = np.float32([list(CORNER_TOP_LEFT), list(CORNER_TOP_RIGHT), list(CORNER_BOTTOM_LEFT), list(CORNER_BOTTOM_RIGHT)])
        pts2 = np.float32([[0, 0], [x, 0], [0, x / 2], [x, x / 2]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        if not CALIBRATE:
            frame = cv2.warpPerspective(frame, matrix, (x, int(x / 2)))

        return frame


def main():
    transformation = TransformationRGBDepth()
    sys.exit()


if __name__ == '__main__':
    main()