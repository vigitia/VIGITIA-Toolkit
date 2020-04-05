# Built upon: https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/examples/align-depth2color.py

import pyrealsense2 as rs
import numpy as np
import cv2
import imutils
import sys


DISTANCE_CAMERA_TABLE = 1.22  # m

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
NUM_FRAMES_FOR_BACKGROUND_MODEL = 10

COLOR_REMOVED_BACKGROUND = [64, 177, 0]  # Chroma Green

class RealsenseD435Camera():

    depth_scale = -1
    clipping_distance = -1

    num_frame = 0

    stored_background_values = np.zeros(shape=(DEPTH_RES_Y, DEPTH_RES_X, NUM_FRAMES_FOR_BACKGROUND_MODEL), dtype=np.int16)
    background_average = np.zeros(shape=(DEPTH_RES_Y, DEPTH_RES_X), dtype=np.int16)
    background_standard_deviation = np.zeros(shape=(DEPTH_RES_Y, DEPTH_RES_X), dtype=np.int16)

    stored_color_frame = None
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

    fgbg = cv2.createBackgroundSubtractorMOG2()

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

        self.init_opencv()

        self.loop()

    def init_opencv(self):
        #cv2.namedWindow("realsense", cv2.WND_PROP_FULLSCREEN)
        #cv2.setWindowProperty("window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.namedWindow('realsense', cv2.WINDOW_AUTOSIZE)

    def create_background_model(self, depth_image, color_image):
        pos = self.num_frame - NUM_FRAMES_WAIT_INITIALIZING - 1
        print('Storing frame ' + str(pos+1) + '/' + str(NUM_FRAMES_FOR_BACKGROUND_MODEL))
        self.store_depth_values(depth_image, pos)

        if pos == (NUM_FRAMES_FOR_BACKGROUND_MODEL - 1):
            gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            self.stored_color_frame = gray
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
                #depth_colormap = np.asanyarray(self.colorizer.colorize(aligned_depth_frame).get_data())

                if NUM_FRAMES_WAIT_INITIALIZING < self.num_frame <= NUM_FRAMES_FOR_BACKGROUND_MODEL + NUM_FRAMES_WAIT_INITIALIZING:
                    self.create_background_model(depth_image, color_image)
                    continue
                else:

                    #output_image = self.remove_background_advanced(color_image, depth_image)
                    output_image = self.detect_movement(color_image)

                    cv2.imshow('realsense', output_image)
                    #cv2.imwrite('average_background.png', self.average_background)

                key = cv2.waitKey(1)
                # Press esc or 'q' to close the image window
                if key & 0xFF == ord('q') or key == 27:
                    cv2.destroyAllWindows()
                    break
        finally:
            self.pipeline.stop()

    # https://www.pyimagesearch.com/2015/05/25/basic-motion-detection-and-tracking-with-python-and-opencv/
    def detect_movement(self, color_image):

        if self.stored_color_frame is None:
            return color_image

        fgmask = self.fgbg.apply(color_image)
        fgmask = np.where(fgmask == 255, 0, fgmask)
        shadow_mask = np.where(fgmask > 0, 255, fgmask)
        shadow_mask = np.dstack((shadow_mask, shadow_mask, shadow_mask))


        MIN_AREA = 100

        gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # compute the absolute difference between the current frame and
        # first frame
        frameDelta = cv2.absdiff(self.stored_color_frame, gray)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
        # dilate the thresholded image to fill in holes, then find contours
        # on thresholded image
        thresh = cv2.dilate(thresh, None, iterations=3)
        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        # loop over the contours

        black_image = np.zeros(shape=(RGB_RES_Y, RGB_RES_X, 3), dtype=np.uint8)

        for c in contours:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < MIN_AREA:
                continue
            # compute the bounding box for the contour, draw it on the frame,
            # and update the text
            #(x, y, w, h) = cv2.boundingRect(c)
            #cv2.rectangle(color_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            #cv2.rectangle(black_image, (x, y), (x + w, y + h), (255, 255, 255), -1)
            print("Bewegung gefunden")

        black_image = cv2.drawContours(black_image, contours, -1, (255, 255, 255), -1)
        color_image = np.where(black_image == 255, color_image, black_image)
        # color_image[np.where((shadow_mask == [255, 255, 255]).all(axis=2))] = [0, 0, 0]

        return color_image

    def moving_average_filter(self, image):
        if self.stored_depth_frame is None:
            self.stored_depth_frame = image
            return image
        else:
            combined_images = self.stored_depth_frame + image
            averaged_image = combined_images/2
            self.stored_depth_frame = image
            return averaged_image


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

        return image

    def remove_background_advanced(self, color_image, depth_image):
        difference_to_background = self.background_average - depth_image
        difference_to_background = np.where(difference_to_background < 0, 0, difference_to_background)

        remove_uncertain_pixels = difference_to_background - self.background_standard_deviation
        remove_uncertain_pixels = np.where(remove_uncertain_pixels < 0, 0, difference_to_background)
        remove_uncertain_pixels = np.where((remove_uncertain_pixels < MIN_DIST_TOUCH / self.depth_scale), 0,
                                           remove_uncertain_pixels)

        depth_holes = np.where(depth_image == 0, 0, 65535)
        remove_uncertain_pixels = np.where(depth_holes == 0, 0, remove_uncertain_pixels)


        ...

        small_regions = self.remove_small_connected_regions(remove_uncertain_pixels, 10000, True)

        remove_uncertain_pixels -= small_regions

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



# Crop depth data:
#depth = depth[xmin_depth:xmax_depth,ymin_depth:ymax_depth].astype(float)
