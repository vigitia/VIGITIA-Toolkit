# See https://www.youtube.com/watch?v=PtCQH93GucA&

import cv2
import numpy as np

# See "ls /dev/video*" to get the ID
CAMERA_ID = 6

# Coordinates for 640x480px camera resolution (4x3)
CORNER_TOP_LEFT = (41, 128)
CORNER_TOP_RIGHT = (597, 123)
CORNER_BOTTOM_LEFT = (40, 408)
CORNER_BOTTOM_RIGHT = (602, 404)

# Output image (currently needs to be 16x9 because the Beamer can project this)
OUTPUT_IMAGE_WIDTH = 1920
OUTPUT_IMAGE_HEIGHT = 1080

cap = cv2.VideoCapture(CAMERA_ID)

# Set to fullscreen
cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

while True:

    _, frame = cap.read()

    # Camera image is 640x480 (4:3)
    x = frame.shape[1]
    y = frame.shape[0]

    # Code for Perspective Transformation: https://www.youtube.com/watch?v=PtCQH93GucA
    # Draw circles to mark the screen corners
    #cv2.circle(frame, CORNER_TOP_LEFT, 1, (0, 0, 255), -1)
    #cv2.circle(frame, CORNER_TOP_RIGHT, 1, (0, 0, 255), -1)
    #cv2.circle(frame, CORNER_BOTTOM_LEFT, 1, (0, 0, 255), -1)
    #cv2.circle(frame, CORNER_BOTTOM_RIGHT, 1, (0, 0, 255), -1)

    pts1 = np.float32([list(CORNER_TOP_LEFT), list(CORNER_TOP_RIGHT), list(CORNER_BOTTOM_LEFT), list(CORNER_BOTTOM_RIGHT)])
    pts2 = np.float32([[0, 0], [x, 0], [0, x/2], [x, x/2]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    frame = cv2.warpPerspective(frame, matrix, (x, x/2))

    # Add black border on top to fill the missing pixels from 2:1 (16:8) to 16:9 aspect ratio
    frame = cv2.copyMakeBorder(frame, top=40, bottom=0, left=0, right=0, borderType=cv2.BORDER_CONSTANT, value=[0,0,0])

    # Upscale to 1920x1080 px
    frame = cv2.resize(frame, (OUTPUT_IMAGE_WIDTH, OUTPUT_IMAGE_HEIGHT), interpolation=cv2.INTER_AREA)

    cv2.imshow("window", frame)

    key = cv2.waitKey(1)
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()