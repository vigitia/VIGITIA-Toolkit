#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The TUIO 2.0 server endcodes and sends TUIO messages via UDP to the defined IP address and port
# Using the python-osc library: https://github.com/attwad/python-osc

# Based upon the TUIO 2.0 C++ Library by Martin Kaltebrunner
# https://github.com/mkalten/TUIO20_CPP/blob/b3fc7998670200091e5768747c3e04ac758084e3/TUIO2/TuioServer.cpp
# and the TUIO 2.0 Protocol Specification by Martin Kaltenbrunner
# http://www.tuio.org/?tuio20

import sys
import time
from pythonosc import udp_client
from pythonosc import osc_bundle_builder
from pythonosc import osc_message_builder

IP = "192.168.178.81"
PORT = 8000

class TUIOServer:

    def __init__(self):
        self.udp_client = udp_client.SimpleUDPClient(IP, PORT)

    # Get sample points for testing
    def get_hand_point(self):
        # /tuio2/ptr s_id tu_id c_id x_pos y_pos angle shear radius press
        s_id = 0
        t_id = 1
        c_id = 2
        x_pos = 100
        y_pos = 200
        angle = 0
        shear = 0
        radius = 0
        press = 1
        return [s_id, t_id, c_id, x_pos, y_pos, angle, shear, radius, press]

    def create_tuio_pointer(self, x_pos, y_pos, angle, shear, radius, pressure):

        return None

    def send_test(self):
        for x in range(5):
            print('send test message')

            hand_point_args = self.get_hand_point()
            self.udp_client.send_message("/tuio2/ptr", hand_point_args)
            time.sleep(1)

    def init_tuio_frame(self):
        # frameTimeTag = TuioTime::getSystemTimeTag();
        # currentFrameTime = TuioTime(ttime);
        # currentFrame++;
        # if (currentFrame==UINT_MAX) currentFrame = 1;
        pass

    # Commits the current frame.
    # Generates and sends TUIO messages of all currently active and updated TuioTokens and TuioPointers.
    def commit_tuio_frame(self):
        pass

    def send_tuio_bundle(self):
        pass

    def start_tuio_bundle(self):
        # f_id -> Frame ID (int32)
        # time -> OSC 64bit time tag (ttag)
        # dim  -> Dimension encodes the sensor dimension with two 16bit unsigned integer values embedded into a 32bit
        #         integer value. The first two bytes represent the sensor width, while the final two bytes represent
        #         the sensor height. (int32)
        # source -> e.g. 'REAC' (string)
        tuio_bundle = osc_message_builder.OscMessageBuilder(address="/tuio2/frm")
        tuio_bundle.add_arg(4.0)



def main():
    tuioServer = TUIOServer()
    sys.exit()


if __name__ == '__main__':
    main()
