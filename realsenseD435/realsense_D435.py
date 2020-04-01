# Built upon: https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/examples/align-depth2color.py

import pyrealsense2 as rs
import numpy as np
import cv2
import imutils
import sys

from hand_tracking.hand_tracking_controller import HandTrackingController


DISTANCE_CAMERA_TABLE = 1.23  # m

MIN_DIST_TOUCH = 0.003  # m
MAX_DIST_TOUCH = 0.05  # m

# Camera Settings
DEPTH_RES_X = 848
DEPTH_RES_Y = 480
RGB_RES_X = 848
RGB_RES_Y = 480

DEPTH_FPS = 60
RGB_FPS = 60

NUM_FRAMES_WAIT_INITIALIZING = 50
NUM_FRAMES_FOR_BACKGROUND_MODEL = 50

COLOR_REMOVED_BACKGROUND = [64, 177, 0]  # Chroma Green

class RealsenseD435Camera():

    depth_scale = -1
    clipping_distance = -1

    num_frame = 0

    stored_background_values = np.zeros(shape=(DEPTH_RES_Y, DEPTH_RES_X, NUM_FRAMES_FOR_BACKGROUND_MODEL), dtype=np.int16)
    background_average = np.zeros(shape=(DEPTH_RES_Y, DEPTH_RES_X), dtype=np.int16)
    background_standard_deviation = np.zeros(shape=(DEPTH_RES_Y, DEPTH_RES_X), dtype=np.int16)

    stored_depth_frame = None

    pipeline = None
    align = None
    colorizer = None

    hole_filling_filter = None
    decimation_filter = None
    spacial_filter = None
    temporal_filter = None
    disparity_to_depth_filter = None
    depth_to_disparity_filter = None

    hand_tracking_contoller = None

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
        print("Depth scale", self.depth_scale)

        # TODO: Tweak camera settings
        depth_sensor.set_option(rs.option.laser_power, 360)
        depth_sensor.set_option(rs.option.depth_units, 0.001)

        # Create an align object
        # rs.align allows us to perform alignment of depth frames to others frames
        # The "align_to" is the stream type to which we plan to align depth frames.
        align_to = rs.stream.color
        self.align = rs.align(align_to)

        self.hole_filling_filter = rs.hole_filling_filter()
        self.decimation_filter = rs.decimation_filter()
        self.temporal_filter = rs.temporal_filter()

        # We will be removing the background of objects more than
        #  clipping_distance_in_meters meters away
        self.clipping_distance = DISTANCE_CAMERA_TABLE / self.depth_scale

        self.init_colorizer()
        self.init_opencv()

        self.hand_tracking_contoller = HandTrackingController()

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

    def create_background_model(self, depth_image):
        pos = self.num_frame - NUM_FRAMES_WAIT_INITIALIZING - 1
        print('Storing frame ' + str(pos+1) + '/' + str(NUM_FRAMES_FOR_BACKGROUND_MODEL))
        self.store_depth_values(depth_image, pos)

        if pos == (NUM_FRAMES_FOR_BACKGROUND_MODEL - 1):
            self.calculate_background_model_statistics()

    def store_depth_values(self, depth_image, pos):
        for y in range(DEPTH_RES_Y):
            for x in range(DEPTH_RES_X):
                current_depth_px = depth_image[y][x]
                self.stored_background_values[y][x][pos] = current_depth_px

    def calculate_background_model_statistics(self):
        print('Calculating background model statistics')
        for y in range(DEPTH_RES_Y):
            for x in range(DEPTH_RES_X):
                stored_values_at_pixel = self.stored_background_values[y][x]
                #stored_values_at_pixel = stored_values_at_pixel[stored_values_at_pixel != 0]
                #if len(stored_values_at_pixel) == 0:
                #    stored_values_at_pixel = [0]
                self.background_average[y][x] = np.mean(stored_values_at_pixel)
                self.background_standard_deviation[y][x] = 3 * np.std(stored_values_at_pixel)

        print('Finished calculating background model statistics')
        print(self.background_average[int(DEPTH_RES_Y/2)])
        print(self.background_standard_deviation[int(DEPTH_RES_Y/2)])

    def loop(self):
        # Streaming loop
        try:
            while True:
                self.num_frame += 1
                print('Frame:', self.num_frame)

                # Get frameset of color and depth
                frames = self.pipeline.wait_for_frames()

                if self.num_frame < NUM_FRAMES_WAIT_INITIALIZING:
                    continue

                # Align the depth frame to color frame
                aligned_frames = self.align.process(frames)

                # Get aligned frames
                aligned_depth_frame = aligned_frames.get_depth_frame()
                color_frame = aligned_frames.get_color_frame()

                # Apply Filters
                #aligned_depth_frame = self.hole_filling_filter.process(aligned_depth_frame)
                #aligned_depth_frame = self.decimation_filter.process(aligned_depth_frame)
                #aligned_depth_frame = self.temporal_filter.process(aligned_depth_frame)

                color_image = np.asanyarray(color_frame.get_data())
                # depth_image = np.asanyarray(aligned_depth_frame.get_data())
                depth_image = np.array(aligned_depth_frame.get_data(), dtype=np.int16)

                #depth_image = self.moving_average_filter(depth_image)

                # Validate that both frames are valid
                if not aligned_depth_frame or not color_frame:
                    continue

                # Render images
                # depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
                depth_colormap = np.asanyarray(self.colorizer.colorize(aligned_depth_frame).get_data())

                # color_image = self.hand_tracking_contoller.detect_hands(color_image, aligned_depth_frame)

                if NUM_FRAMES_WAIT_INITIALIZING < self.num_frame <= NUM_FRAMES_FOR_BACKGROUND_MODEL + NUM_FRAMES_WAIT_INITIALIZING:
                    self.create_background_model(depth_image)
                    continue
                else:
                    # Remove all pixels at defined cutoff value
                    # bg_removed = self.remove_background(color_image, depth_image)

                    output_image = self.extract_arms(depth_image, color_image)

                    cv2.imshow('realsense', output_image)
                    #cv2.imwrite('average_background.png', self.average_background)

                key = cv2.waitKey(1)
                # Press esc or 'q' to close the image window
                if key & 0xFF == ord('q') or key == 27:
                    cv2.destroyAllWindows()
                    break
        finally:
            self.pipeline.stop()

    def moving_average_filter(self, image):
        if self.stored_depth_frame is None:
            self.stored_depth_frame = image
            return image
        else:
            combined_images = self.stored_depth_frame + image
            averaged_image = combined_images/2
            self.stored_depth_frame = image
            return averaged_image


    def extract_arms(self, depth_image, color_image):

        if self.num_frame == 200:
            print("Writing files")
            cv2.imwrite('depth_image.png', depth_image)
            cv2.imwrite('color_image.png', color_image)

        difference_to_background = self.background_average - depth_image
        difference_to_background = np.where(difference_to_background < 0, 0, difference_to_background)

        remove_uncertain_pixels = difference_to_background - self.background_standard_deviation
        remove_uncertain_pixels = np.where(remove_uncertain_pixels < 0, 0, difference_to_background)
        remove_uncertain_pixels = np.where((remove_uncertain_pixels < MIN_DIST_TOUCH / self.depth_scale), 0, remove_uncertain_pixels)

        depth_holes = np.where(depth_image == 0, 0, 65535)
        remove_uncertain_pixels = np.where(depth_holes == 0, 0, remove_uncertain_pixels)

        mark_arm_pixels = np.where((remove_uncertain_pixels > MAX_DIST_TOUCH / self.depth_scale), 65535, 0)
        mark_arm_pixels = cv2.convertScaleAbs(mark_arm_pixels, alpha=(255.0 / 65535.0))

        mark_touch_pixels = np.where((remove_uncertain_pixels >= MAX_DIST_TOUCH / self.depth_scale), 0, remove_uncertain_pixels)
        mark_touch_pixels = np.where(mark_touch_pixels != 0, 65535, 0)
        mark_touch_pixels = cv2.convertScaleAbs(mark_touch_pixels, alpha=(255.0 / 65535.0))

        if self.num_frame == 200:
            print("Writing files")
            cv2.imwrite('mark_arm_pixels.png', mark_arm_pixels)
            cv2.imwrite('mark_touch_pixels.png', mark_touch_pixels)


        remove_uncertain_pixels = np.where((remove_uncertain_pixels >= MIN_DIST_TOUCH / self.depth_scale), 65535, 0)
        remove_uncertain_pixels = cv2.convertScaleAbs(remove_uncertain_pixels, alpha=(255.0/65535.0))

        small_regions = self.remove_small_connected_regions(remove_uncertain_pixels, 10000, True)

        if self.num_frame == 200:
            print("Writing files")
            cv2.imwrite('remove_uncertain_pixels.png', remove_uncertain_pixels)
            cv2.imwrite('small_regions.png', small_regions)

        remove_uncertain_pixels -=small_regions
        mark_arm_pixels -= small_regions
        mark_touch_pixels -= small_regions

        significant_pixels = cv2.cvtColor(remove_uncertain_pixels, cv2.COLOR_GRAY2BGR)
        mark_arm_pixels = cv2.cvtColor(mark_arm_pixels, cv2.COLOR_GRAY2BGR)
        mark_touch_pixels = cv2.cvtColor(mark_touch_pixels, cv2.COLOR_GRAY2BGR)

        significant_pixels[np.where((mark_touch_pixels == [255, 255, 255]).all(axis=2))] = [0, 0, 255]
        significant_pixels[np.where((mark_arm_pixels == [255, 255, 255]).all(axis=2))] = [0, 255, 0]

        unique, counts = np.unique(significant_pixels, return_counts=True)
        print(dict(zip(unique, counts)))

        #significant_pixels_color = cv2.cvtColor(significant_pixels, cv2.COLOR_GRAY2BGR)


        edge_map = self.get_edge_map(color_image)
        edge_map = cv2.cvtColor(edge_map, cv2.COLOR_GRAY2BGR)


        output_image = significant_pixels + edge_map
        #output_image = edge_map

        unique, counts = np.unique(output_image, return_counts=True)
        #print(dict(zip(unique, counts)))

        return output_image

    def remove_small_connected_regions(self, image, min_size, get_only_regions_to_remove):
        # https://stackoverflow.com/questions/42798659/how-to-remove-small-connected-objects-using-opencv
        nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(image, connectivity=8)
        sizes = stats[1:, -1]
        nb_components = nb_components - 1

        output_image = np.zeros(shape=(DEPTH_RES_Y, DEPTH_RES_X), dtype=np.uint8)
        # for every component in the image, you keep it only if it's above min_size
        for i in range(0, nb_components):
            if get_only_regions_to_remove:
                if sizes[i] < min_size:
                    output_image[output == i + 1] = 255
            else:
                if sizes[i] >= min_size:
                    output_image[output == i + 1] = 255

        return output_image

    def get_edge_map(self, image):
        # https://www.pyimagesearch.com/2014/04/21/building-pokedex-python-finding-game-boy-screen-step-4-6/
        #image = cv2.bilateralFilter(image, 11, 17, 17)
        image = cv2.bilateralFilter(image, 7, 50, 50)
        image = cv2.Canny(image, 30, 400, 7)

        #https://www.pyimagesearch.com/2014/04/21/building-pokedex-python-finding-game-boy-screen-step-4-6/
        # find contours in the edged image, keep only the largest
        # ones, and initialize our screen contour
        cnts = cv2.findContours(image.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:10]

        print("Num Contours: ", len(cnts))

        # loop over our contours
        for c in cnts:
            # approximate the contour
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.015 * peri, True)
            # if our approximated contour has four points, then
            # we can assume that we have found our screen
            #print("Length of contour: ", len(approx))

        #image = self.remove_small_connected_regions(image, 10, False)

        # See:
        # https://stackoverflow.com/questions/35847990/detect-holes-ends-and-beginnings-of-a-line-using-opencv

        return image





    def compare_to_background_model(self, depth_image):
        #depth_image = np.where((abs(self.average_background - depth_image) < 300, 0, depth_image))

        for y in range(DEPTH_RES_Y):
            for x in range(DEPTH_RES_X):
                depth_px = depth_image[y][x]
                bg_px = self.average_background[y][x]
                dist = bg_px - depth_px
                if abs(dist) < 100:
                    depth_image[y][x] = 0

        return depth_image

    def remove_background(self, color_image, depth_image):
        # Remove background - Set pixels further than clipping_distance to grey
        depth_image_3d = np.dstack((depth_image, depth_image, depth_image))  # depth image is 1 channel, color is 3 channels
        # TODO Replace color here in one step
        bg_removed = np.where((depth_image_3d > self.clipping_distance) | (depth_image_3d <= 0), 0, color_image)
        # https://answers.opencv.org/question/97416/replace-a-range-of-colors-with-a-specific-color-in-python/
        bg_removed[np.where((bg_removed == [0, 0, 0]).all(axis=2))] = COLOR_REMOVED_BACKGROUND

        return bg_removed

    def depth_distance(self, aligned_depth_frame):
        # Print a simple text-based representation of the image, by breaking it into 10x20 pixel regions and approximating the coverage of pixels within one meter
        coverage = [0] * 64
        for y in range(DEPTH_RES_Y):
            for x in range(DEPTH_RES_X):
                dist = aligned_depth_frame.get_distance(x, y)
                if 0 < dist and dist < 1:
                    coverage[x // 10] += 1

            if y % 20 is 19:
                line = ""
                for c in coverage:
                    line += " .:nhBXWW"[c // 25]
                coverage = [0] * 64
                print(line)

def main():
    realsenseCamera = RealsenseD435Camera()
    sys.exit()


if __name__ == '__main__':
    main()



# Crop depth data:
#depth = depth[xmin_depth:xmax_depth,ymin_depth:ymax_depth].astype(float)
