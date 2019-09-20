import sys
import pyrealsense2 as rs
import cv2
import numpy as np

# Built upon: https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/examples/align-depth2color.py

'''
Current distance between camera and table: 105.5cm
'''

DEPTH_RES_X = 1280
DEPTH_RES_Y = 720
RGB_RES_X = 1280
RGB_RES_Y = 720

DEPTH_FPS = 30
RGB_FPS = 30

# Coordinates of table corners
CORNER_TOP_LEFT = (158, 60)
CORNER_TOP_RIGHT = (1211, 65)
CORNER_BOTTOM_LEFT = (157, 582)
CORNER_BOTTOM_RIGHT = (1203, 592)

BLACK_BORDER_HEIGHT = 80  # px

# Output image (currently needs to be 16x9 because the projector can project this)
OUTPUT_IMAGE_WIDTH = 1920
OUTPUT_IMAGE_HEIGHT = 1080


class TransformationRGBDepth():

    pipeline = None
    align = None
    clipping_distance = None
    colorizer = None

    def __init__(self):
        # Create a pipeline
        self.pipeline = rs.pipeline()

        # Create a config and configure the pipeline to stream different resolutions of color and depth streams
        config = rs.config()
        config.enable_stream(rs.stream.depth, DEPTH_RES_X, DEPTH_RES_Y, rs.format.z16, DEPTH_FPS)
        config.enable_stream(rs.stream.color, RGB_RES_X, RGB_RES_Y, rs.format.bgr8, RGB_FPS)

        # Start streaming
        profile = self.pipeline.start(config)

        # Getting the depth sensor's depth scale (see rs-align example for explanation)
        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale = depth_sensor.get_depth_scale()
        print("Depth Scale is: ", depth_scale)

        # We will be removing the background of objects more than
        #  clipping_distance_in_meters meters away
        clipping_distance_in_meters = 1.6  # 1 meter
        self.clipping_distance = clipping_distance_in_meters / depth_scale

        # Create an align object
        # rs.align allows us to perform alignment of depth frames to others frames
        # The "align_to" is the stream type to which we plan to align depth frames.
        align_to = rs.stream.color
        self.align = rs.align(align_to)

        # Set to fullscreen
        cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        self.init_colorizer()
        self.loop()

    def init_colorizer(self):
        self.colorizer = rs.colorizer()
        self.colorizer.set_option(rs.option.color_scheme, 0)
        self.colorizer.set_option(rs.option.histogram_equalization_enabled, 0)
        self.colorizer.set_option(rs.option.min_distance, 0.3)  # meter
        self.colorizer.set_option(rs.option.max_distance, 1.1)  # meter

    # Streaming loop
    def loop(self):
        try:
            while True:
                # Get frameset of color and depth
                frames = self.pipeline.wait_for_frames()
                # frames.get_depth_frame() is a 640x360 depth image

                color_image, depth_colormap = self.align_frames(frames)

                color_image = self.perspective_transformation(color_image)
                depth_colormap = self.perspective_transformation(depth_colormap)

                # print(depth_colormap.shape)

                # Add black border on top to fill the missing pixels from 2:1 (16:8) to 16:9 aspect ratio
                color_image = cv2.copyMakeBorder(color_image, top=0, bottom=BLACK_BORDER_HEIGHT, left=0, right=0, borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0])
                depth_colormap = cv2.copyMakeBorder(depth_colormap, top=0, bottom=BLACK_BORDER_HEIGHT, left=0, right=0, borderType=cv2.BORDER_CONSTANT, value=[0, 0, 0])

                # Upscale to 1920x1080 px
                color_image = cv2.resize(color_image, (OUTPUT_IMAGE_WIDTH, OUTPUT_IMAGE_HEIGHT), interpolation=cv2.INTER_AREA)
                depth_colormap = cv2.resize(depth_colormap, (OUTPUT_IMAGE_WIDTH, OUTPUT_IMAGE_HEIGHT), interpolation=cv2.INTER_AREA)

                #cv2.imshow('window', color_image)
                cv2.imshow('window', depth_colormap)

                key = cv2.waitKey(1)
                # Press esc or 'q' to close the image window
                if key & 0xFF == ord('q') or key == 27:
                    cv2.destroyAllWindows()
                    break
        finally:
            self.pipeline.stop()

    # Align the depth frame to color frame
    def align_frames(self, frames):
        aligned_frames = self.align.process(frames)

        # Get aligned frames
        aligned_depth_frame = aligned_frames.get_depth_frame()  # aligned_depth_frame is a 640x480 depth image
        color_frame = aligned_frames.get_color_frame()

        # Validate that both frames are valid
        if not aligned_depth_frame or not color_frame:
            return None, None

        # Generate color image
        color_image = np.asanyarray(color_frame.get_data())

        # Transform the deph map into a RGB image
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
        frame = cv2.warpPerspective(frame, matrix, (x, x / 2))

        return frame


def main():
    transformation = TransformationRGBDepth()
    sys.exit()


if __name__ == '__main__':
    main()