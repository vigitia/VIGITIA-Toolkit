
import cv2
import numpy as np


class TableDetector:

    def __init__(self):
        print('[Table Detector]: Ready')

    # Based on https://theailearner.com/2019/11/22/simple-shape-detection-using-contour-approximation/
    # and https://answers.opencv.org/question/94845/python-opencv-extracting-xy-coordinates-of-point-features-on-an-image/
    def get_table_border(self, color_image, depth_image):

        # Set to relevant range
        table_min_dist_mm = 0
        table_max_dist_mm = 2000
        depth_filtered = cv2.inRange(depth_image, np.array([table_min_dist_mm], dtype="uint16"),
                                     np.array([table_max_dist_mm], dtype="uint16"))

        gray = cv2.GaussianBlur(depth_filtered, (5, 5), 0)
        binary_image = cv2.dilate(gray, None)  # fill some holes
        binary_image = cv2.dilate(binary_image, None)
        binary_image = cv2.erode(binary_image, None)  # dilate made our shape larger, revert that
        binary_image = cv2.erode(binary_image, None)

        contours, _ = cv2.findContours(binary_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        epsilon = 0.05 * cv2.arcLength(contours[0], True)
        approx = cv2.approxPolyDP(contours[0], epsilon, True)
        cv2.drawContours(color_image, [approx], 0, (255, 255, 0), 3)

        rc = cv2.minAreaRect(contours[0])
        box = cv2.boxPoints(rc)
        for p in box:
            pt = (p[0], p[1])
            cv2.circle(color_image, pt, 5, (0, 0, 255), 2)

        return color_image


        # black_image = np.zeros(shape=(color_image.shape[0], color_image.shape[1], 3), dtype=np.uint8)
        #
        # table_min_dist_mm = 0
        # table_max_dist_mm = 2000
        # depth_filtered = cv2.inRange(depth_image, np.array([table_min_dist_mm], dtype="uint16"),
        #                              np.array([table_max_dist_mm], dtype="uint16"))
        #
        # # Based on https://www.tutorialspoint.com/line-detection-in-python-with-opencv
        # edges = cv2.Canny(depth_filtered, 75, 150)
        # lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 30, maxLineGap=250)
        # for line in lines:
        #     x1, y1, x2, y2 = line[0]
        #     cv2.line(black_image, (x1, y1), (x2, y2), (255, 255, 255), 1)
        #
        # black_image = cv2.cvtColor(black_image, cv2.COLOR_BGR2GRAY)
        #
        # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        # black_image = cv2.dilate(black_image, kernel)

        #black_image = cv2.GaussianBlur(black_image, (11, 11), 0)

        contours, hierarchy = cv2.findContours(black_image, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

        # for cnt in contours:
        #     rect = cv2.boundingRect(cnt)
        #     cv2.polylines(black_image, rect, is_closed=1, thickness=1, lineType=8, shift=0)
        #     x, y, w, h = rect
        #     if w * h > 1:
        #         mask = np.zeros(color_image.shape, np.uint8)
        #         mask[y:y + h, x:x + w] = color_image[y:y + h, x:x + w]
        #         cv2.imshow("mask", mask)

        # return black_image