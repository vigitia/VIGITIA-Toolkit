
import cv2
from realsenseD435.realsense_D435_camera import RealsenseD435Camera

realsense = RealsenseD435Camera()
realsense.start()

while True:
    color_image, depth_image = realsense.get_frames()

    if color_image is not None and depth_image is not None:
        cv2.imshow('frame', color_image)

    key = cv2.waitKey(1)
    # Press 'ESC' or 'Q' to close the image window
    if key & 0xFF == ord('q') or key == 27:
        break

realsense.stop()
cv2.destroyAllWindows()
