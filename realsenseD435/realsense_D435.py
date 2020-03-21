# Built upon: https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/examples/align-depth2color.py

import pyrealsense2 as rs
import numpy as np
import cv2
import sys

DISTANCE_CAMERA_TABLE = 1.20  # m

# Camera Settings
DEPTH_RES_X = 1280
DEPTH_RES_Y = 720
RGB_RES_X = 1280
RGB_RES_Y = 720

DEPTH_FPS = 30
RGB_FPS = 30

COLOR_REMOVED_BACKGROUND = [64, 177, 0]  # Chroma Green

class RealsenseD435Camera():

    depth_scale = -1
    clipping_distance = -1

    pipeline = None
    align = None
    colorizer = None

    def __init__(self):
        # Create a pipeline
        self.pipeline = rs.pipeline()

        # Create a config and configure the pipeline to stream
        #  different resolutions of color and depth streams
        config = rs.config()
        config.enable_stream(rs.stream.depth, DEPTH_RES_X, DEPTH_RES_Y, rs.format.z16, DEPTH_FPS)
        config.enable_stream(rs.stream.color, RGB_RES_X, RGB_RES_Y, rs.format.bgr8, RGB_FPS)

        # Start streaming
        profile = self.pipeline.start(config)

        # Getting the depth sensor's depth scale (see rs-align example for explanation)
        depth_sensor = profile.get_device().first_depth_sensor()
        self.depth_scale = depth_sensor.get_depth_scale()

        # TODO: Tweak camera settings
        depth_sensor.set_option(rs.option.laser_power, 360)
        depth_sensor.set_option(rs.option.depth_units, 0.0001)

        # Create an align object
        # rs.align allows us to perform alignment of depth frames to others frames
        # The "align_to" is the stream type to which we plan to align depth frames.
        align_to = rs.stream.color
        self.align = rs.align(align_to)

        # We will be removing the background of objects more than
        #  clipping_distance_in_meters meters away
        self.clipping_distance = DISTANCE_CAMERA_TABLE / self.depth_scale

        self.init_colorizer()
        self.init_opencv()

        self.loop()

    def init_opencv(self):
        #cv2.namedWindow("realsense", cv2.WND_PROP_FULLSCREEN)
        #cv2.setWindowProperty("window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.namedWindow('realsense', cv2.WINDOW_AUTOSIZE)

        # Set mouse callbacks to extract the coordinates of clicked spots in the image
        cv2.setMouseCallback('window', self.on_mouse_click)

    # Log mouse click positions to the console
    def on_mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print((x, y))

    def init_colorizer(self):
        self.colorizer = rs.colorizer()
        self.colorizer.set_option(rs.option.color_scheme, 0)   # Define the color scheme
        # Auto histogram color selection (0 = off, 1 = on)
        self.colorizer.set_option(rs.option.histogram_equalization_enabled, 0)
        self.colorizer.set_option(rs.option.min_distance, 0.5)  # meter
        self.colorizer.set_option(rs.option.max_distance, 1.4)  # meter

    def loop(self):
        # Streaming loop
        try:
            while True:
                # Get frameset of color and depth
                frames = self.pipeline.wait_for_frames()

                # Align the depth frame to color frame
                aligned_frames = self.align.process(frames)

                # Get aligned frames
                aligned_depth_frame = aligned_frames.get_depth_frame()
                color_frame = aligned_frames.get_color_frame()

                # Validate that both frames are valid
                if not aligned_depth_frame or not color_frame:
                    continue

                color_image = np.asanyarray(color_frame.get_data())
                depth_image = np.asanyarray(aligned_depth_frame.get_data())

                bg_removed = self.remove_background(color_image, depth_image)

                # Render images
                #depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
                depth_colormap = np.asanyarray(self.colorizer.colorize(aligned_depth_frame).get_data())

                #cv2.imshow('realsense', bg_removed)
                cv2.imshow('realsense', depth_colormap)

                key = cv2.waitKey(1)
                # Press esc or 'q' to close the image window
                if key & 0xFF == ord('q') or key == 27:
                    cv2.destroyAllWindows()
                    break
        finally:
            self.pipeline.stop()

    def remove_background(self, color_image, depth_image):
        # Remove background - Set pixels further than clipping_distance to grey
        depth_image_3d = np.dstack((depth_image, depth_image, depth_image))  # depth image is 1 channel, color is 3 channels
        # TODO Replace color here in one step
        bg_removed = np.where((depth_image_3d > self.clipping_distance) | (depth_image_3d <= 0), 0, color_image)
        # https://answers.opencv.org/question/97416/replace-a-range-of-colors-with-a-specific-color-in-python/
        bg_removed[np.where((bg_removed == [0, 0, 0]).all(axis=2))] = COLOR_REMOVED_BACKGROUND

        return bg_removed

def main():
    realsenseCamera = RealsenseD435Camera()
    sys.exit()


if __name__ == '__main__':
    main()
