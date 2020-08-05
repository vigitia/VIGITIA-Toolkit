
# Inspired by https://towardsdatascience.com/object-detection-with-less-than-10-lines-of-code-using-python-2d28eebc5b11

from cvlib import detect_common_objects
from cvlib.object_detection import draw_bbox


class GenericObjectDetector:

    def __init__(self):
        print('[Generic Object Detector] Service Ready')

    def detect_generic_objects(self, frame):
        # bbox, label, conf = detect_common_objects(frame, confidence=0.75)
        # bbox, label, conf = detect_common_objects(frame, confidence=0.75, enable_gpu=True)
        bbox, label, conf = detect_common_objects(frame, confidence=0.75, model='yolov3-tiny')

        output_image = draw_bbox(frame, bbox, label, conf)

        detected_objects = []

        for i in range(len(bbox)):
            detected_objects.append({
                'label': label[i],
                'bbox': bbox[i],
                'conf': conf[i]
            })

        #print(detected_objects)

        return output_image, detected_objects