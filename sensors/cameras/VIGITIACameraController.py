#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import cv2
from sensors.cameras.kinect2.kinectV2 import KinectV2

class VIGITIACameraController:

    def __init__(self):
        print('init camera controller')
        self.kinectV2 = KinectV2()
        self.listener = self.kinectV2.get_listener()

        self.loop()

    def loop(self):

        while True:
            print('loop')
            self.listener.waitForNewFrame()
            print('new frame arrived')

            color_frame, depth_frame, ir_frame,  registered_frame, bigdepth_frame = self.kinectV2.get_frames()
            #print('loop', color_frame, depth_frame, ir_frame,  registered_frame, bigdepth_frame)

            if color_frame is not None:
                cv2.imshow("kinectv2_color", color_frame)

                key = cv2.waitKey(delay=1)
                if key == ord('q'):
                    break





def main():
    VIGITIACameraController()
    #sys.exit()


if __name__ == '__main__':
    main()
