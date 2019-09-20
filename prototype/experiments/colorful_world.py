# See https://www.youtube.com/watch?v=PtCQH93GucA&

import cv2
import numpy as np

# See "ls /dev/video*" to get the ID
CAMERA_ID = 6

# Constants
CAMERA_FRAME_WIDTH = 672
CAMERA_FRAME_HEIGHT = 380

# Coordinates for 672x380px camera resolution
CORNER_TOP_LEFT = (39, 123)
CORNER_TOP_RIGHT = (598, 128)
CORNER_BOTTOM_LEFT = (37, 408)
CORNER_BOTTOM_RIGHT = (599, 402)

# Output image
OUTPUT_IMAGE_WIDTH = 1920
OUTPUT_IMAGE_HEIGHT = 1080

cap = cv2.VideoCapture(CAMERA_ID)

cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("window", cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)

while True:

    _, frame = cap.read()
    #hsv = cv2.cvtColor((frame, cv2))

    # Code for Perspective Transformation: https://www.youtube.com/watch?v=PtCQH93GucA
    # Draw circles to mark the screen corners
    cv2.circle(frame, CORNER_TOP_LEFT, 3, (0, 0, 255), -1)
    cv2.circle(frame, CORNER_TOP_RIGHT, 3, (0, 0, 255), -1)
    cv2.circle(frame, CORNER_BOTTOM_LEFT, 3, (0, 0, 255), -1)
    cv2.circle(frame, CORNER_BOTTOM_RIGHT, 3, (0, 0, 255), -1)

    pts1 = np.float32([list(CORNER_TOP_LEFT), list(CORNER_TOP_RIGHT), list(CORNER_BOTTOM_LEFT), list(CORNER_BOTTOM_RIGHT)])
    pts2 = np.float32([[0, 0], [OUTPUT_IMAGE_WIDTH, 0], [0, OUTPUT_IMAGE_HEIGHT], [OUTPUT_IMAGE_WIDTH, OUTPUT_IMAGE_HEIGHT]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    result = cv2.warpPerspective(frame, matrix, (OUTPUT_IMAGE_WIDTH, OUTPUT_IMAGE_HEIGHT))

    cv2.imshow("window", result)

    key = cv2.waitKey(1)
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()