#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import numpy as np
import cv2

CAMERA_ID = 1


class VigitiaTableStudy:

    capture = None
    last_frame = None

    def __init__(self):
        self.capture = cv2.VideoCapture(CAMERA_ID)
        #self.capture.set(3, 1920)
        #self.capture.set(4, 1080)
        #self.capture.set(cv2.CAP_PROP_FPS, 1)
        self.loop()

    def loop(self):
        while True:
            # Capture frame-by-frame
            ret, frame = self.capture.read()

            if ret:
                self.check_save_frame(frame)


            key = cv2.waitKey(1)
            # Press 'ESC' or 'Q' to close the image window
            if key & 0xFF == ord('q') or key == 27:
                break

        # When everything done, release the capture
        self.capture.release()
        cv2.destroyAllWindows()

    def check_save_frame(self, frame):
        if self.last_frame is None:
            self.last_frame = frame
            return

        cv2.imshow('frame', frame)
        #cv2.imwrite('test.png', frame)




def main():
    vigitiaTableStudy = VigitiaTableStudy()
    sys.exit()


if __name__ == '__main__':
    main()
