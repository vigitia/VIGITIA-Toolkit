
import cv2
import numpy as np


class TableDetector:

    def __init__(self):
        print('Table Detector ready')

    def get_table_border(self, color_image, depth_image):

        black_image = np.zeros(shape=(color_image.shape[0], color_image.shape[1], 1), dtype=np.uint8)

        table_min_dist_mm = 0
        table_max_dist_mm = 2000
        depth_filtered = cv2.inRange(depth_image, np.array([table_min_dist_mm], dtype="uint16"),
                                     np.array([table_max_dist_mm], dtype="uint16"))

        # Based on https://www.tutorialspoint.com/line-detection-in-python-with-opencv
        edges = cv2.Canny(depth_filtered, 75, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 30, maxLineGap=250)
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(black_image, (x1, y1), (x2, y2), (255), 1)


        # black_image = cv2.GaussianBlur(black_image, (7, 7), 0)

        cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        im, contours, hierarchy = cv2.findContours(black_image, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            rect = cv2.boundingRect(cnt)
            x, y, w, h = rect
            if w * h > 40000:
                mask = np.zeros(color_image.shape, np.uint8)
                mask[y:y + h, x:x + w] = color_image[y:y + h, x:x + w]
                brightness = np.sum(mask)
                if brightness > max_brightness:
                    brightest_rectangle = rect
                    max_brightness = brightness
                cv2.imshow("mask", mask)

        return black_image