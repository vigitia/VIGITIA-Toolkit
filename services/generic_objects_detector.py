
# Based on https://towardsdatascience.com/object-detection-with-less-than-10-lines-of-code-using-python-2d28eebc5b11

import cv2
import matplotlib.pyplot as plt
import cvlib as cv
from cvlib.object_detection import draw_bbox
im = cv2.imread('table.jpeg')
bbox, label, conf = cv.detect_common_objects(im)
# bbox, label, conf = cv.detect_common_objects(img, confidence=0.25, model='yolov3-tiny')
output_image = draw_bbox(im, bbox, label, conf)
plt.imshow(output_image)
plt.show()