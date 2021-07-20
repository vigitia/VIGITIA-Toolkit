#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import cv2
from VIGITIA_toolkit.sensors.cameras.realsense_D435_camera import RealsenseD435Camera
from VIGITIA_toolkit.sensors.cameras.GenericWebcam import GenericWebcam

from VIGITIA_toolkit.sensor_processing_services.TableExtractionService import TableSurfaceExtractor

FLIP_IMAGE = True
DEBUG_MODE = True

CAMERA_ID = -1
RES_X = 1920
RES_Y = 720
FPS = 30


class VideoRecorder:

    def __init__(self):

        self.table_surface_extractor = TableSurfaceExtractor()

        self.camera = RealsenseD435Camera()
        self.camera.init_video_capture()
        self.camera.start()

        # 'self.camera = GenericWebcam()
        # self.camera.init_video_capture(camera_id=9, resolution_x=1920, resolution_y=1080, fps=30)
        # self.camera.start()'

        self.loop()

    def loop(self):
        # Variables for fps counter
        start_time = 0
        counter = 0

        fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        video_writer = cv2.VideoWriter('output.mp4', fourcc, 30.0, (1920, 1080))

        while True:
            frame, _ = self.camera.get_frames()

            if frame is not None:

                # Pre-process camera frames
                color_image_table = self.table_surface_extractor.extract_table_area(frame)

                if FLIP_IMAGE:
                    color_image_table = cv2.flip(color_image_table, -1)

                if DEBUG_MODE:
                    # Preview frames
                    cv2.imshow('color_image_table', color_image_table)

                video_writer.write(color_image_table)

                # FPS Counter
                counter += 1
                if (time.time() - start_time) > 1:  # displays the frame rate every 1 second
                    if DEBUG_MODE:
                        print("[SensorProcessingController]: FPS: ", round(counter / (time.time() - start_time), 1))
                    counter = 0
                    start_time = time.time()

            else:
                print('No Frame')

            key = cv2.waitKey(1)
            # Press esc or 'q' to close the image window
            if key & 0xFF == ord('q') or key == 27:
                cv2.destroyAllWindows()
                video_writer.release()
                break


def main():
    VideoRecorder()
    sys.exit()


if __name__ == '__main__':
    main()