# Code for Hand Tracking and Models from https://github.com/metalwhale/hand_tracking

import sys
import cv2
from hand_tracking.hand_tracker import HandTracker


# Paths to the Models needed for hand tracking
PALM_MODEL_PATH = "./hand_tracking/models/palm_detection.tflite"
LANDMARK_MODEL_PATH = "./hand_tracking/models/hand_landmark.tflite"
ANCHORS_PATH = "./hand_tracking/models/anchors.csv"

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
    (0, 1), (1, 2), (2, 3), (2, 5), (3, 4),
    (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12),
    (13, 14), (14, 15), (15, 16),
    (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17), (0, 17)
]


class HandTrackingController:
    def __init__(self):
        self.detector = HandTracker(PALM_MODEL_PATH, LANDMARK_MODEL_PATH, ANCHORS_PATH)

    def detect_hands(self, color_image, aligned_depth_frame):
        # TODO: Find solution for this temporary fix of ghost hands
        #self.detector.reset()

        detected_hands = self.detector(cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB))
        color_image = self.add_hand_tracking_points(detected_hands, color_image, aligned_depth_frame)

        return color_image

    # Draw circles on the frame for all detected coordinates of the hand
    def add_hand_tracking_points(self, detected_hands, color_image, aligned_depth_frame):
        if detected_hands is not None:
            for hand in detected_hands:
                # Only look at the joints right now
                # TODO: Check bounding boxes, etc later
                points = hand['joints']
                print(hand['bbox'][0])
                point_id = 0
                for point in points:
                    x, y = point
                    if point_id == 8:  # Id of index finger -> draw in different color
                        cv2.circle(color_image, (int(x), int(y)), THICKNESS * 2, (255, 0, 0), -1)
                    else:
                        cv2.circle(color_image, (int(x), int(y)), THICKNESS * 2, POINT_COLOR, -1)
                    point_id += 1

                for connection in CONNECTIONS:  # Draw connections of the points
                    x0, y0 = points[connection[0]]
                    x1, y1 = points[connection[1]]
                    cv2.line(color_image, (int(x0), int(y0)), (int(x1), int(y1)), CONNECTION_COLOR, THICKNESS)

                    cv2.rectangle(color_image, tuple(hand['bbox'][0]), tuple(hand['bbox'][2]), CONNECTION_COLOR, THICKNESS)


        return color_image

def main():
    handTrackingController = HandTrackingController()
    sys.exit()

if __name__ == '__main__':
    main()