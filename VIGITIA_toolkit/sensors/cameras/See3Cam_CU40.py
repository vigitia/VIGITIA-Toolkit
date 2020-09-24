#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Based on: https://gist.github.com/bhive01/56b915ccc5118619fc19c71733f51d34

# Code for streaming video from the See3Cam CU40
# More info on the camera:
# https://www.e-consystems.com/OV4682-RGB-IR-USB3-camera.asp
# https://www.e-consystems.com/OV4682-4MP-MIPI-IR-camera-module-faq.asp#faq-1

# USE a USB 3.0 cable and port!

import os
import numpy as np
import cv2

FRAMES_TO_WAIT_WARM_UP = 5

DEBUG_MODE = True

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720


num_frame = 0

cap = cv2.VideoCapture(6)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
cap.set(cv2.CAP_PROP_CONVERT_RGB, False)  # turn off RGB conversion

while True:
    num_frame += 1
    print('Frame: ', num_frame)

    ret, frame = cap.read()

    if frame is not None:
        # get dimensions of image for later processing
        rows = frame.shape[0]
        cols = frame.shape[1]

        # convert from 10 bit (1024 levels) to 8 bit (255) 255/104 = 0.249023
        bf8 = cv2.convertScaleAbs(frame, 0.249023)

        bayerRGGB = np.copy(bf8)

        IR = np.zeros([rows // 2, cols // 2], np.uint8)
        #IRbig = np.zeros([dimx, dimy], np.uint8)

        for x in range(0, rows, 2):
            for y in range(0, cols, 2):

                # Replace IR data with nearest Green
                # Bayer Matrix setup:
                #     0      1
                # 0  Blue  Green
                # 1  IR     Red

                # TODO: Reduce intensity of all green pixels here
                green_value = int(1 * frame[x, y + 1])

                bayerRGGB[x + 1, y] = green_value

                #bayerRGGB[x, y + 1] = green_value


                # Print values of pixel in the center of the image
                if x == rows // 2 and y == cols // 2:
                    print('B:', bayerRGGB[x, y])
                    print('G:', bayerRGGB[x, y + 1])
                    print('R:', bayerRGGB[x + 1, y + 1])
                    print('IR:', bayerRGGB[x + 1, y])

                # Copy IR data into new array
                ir_data = frame[x + 1, y]
                IR[x // 2, y // 2] = ir_data

        BGRim = cv2.cvtColor(bayerRGGB, cv2.COLOR_BayerRG2BGR)

        # Prevent color problems and set to same size as IR image. Only taking every fourth pixel
        small_BGR_img = np.zeros([rows // 2, cols // 2, 3], np.uint8)
        
        for x in range(0, rows, 2):
            for y in range(0, cols, 2):
                small_BGR_img[x // 2, y // 2] = BGRim[x + 0, y + 1]
        
        
        #BGRim = cv2.resize(BGRim, (int(BGRim.shape[1] / 2), int(BGRim.shape[0] / 2)))
        
        #cv2.circle(BGRim, (int(BGRim.shape[1] / 2), int(BGRim.shape[0] / 2)), 20, (0, 0, 255))

        if DEBUG_MODE:
            cv2.imshow('new', small_BGR_img)
            cv2.imshow('See3Cam_CU40_RGB_large.png', BGRim)
            cv2.imshow('See3Cam_CU40_IR.png', IR)
        else:
            if num_frame == FRAMES_TO_WAIT_WARM_UP:
                cv2.imwrite('See3Cam_CU40_RGB.png', small_BGR_img)
                cv2.imwrite('See3Cam_CU40_RGB_large.png', BGRim)
                cv2.imwrite('See3Cam_CU40_IR.png', IR)
                break

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
