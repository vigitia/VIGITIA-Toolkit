#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The TUIO 2.0 server endcodes and sends TUIO messages via UDP to the defined IP address and port
# using the python-osc library: https://github.com/attwad/python-osc

# Based upon the TUIO 2.0 C++ Library by Martin Kaltenbrunner
# https://github.com/mkalten/TUIO20_CPP/blob/b3fc7998670200091e5768747c3e04ac758084e3/TUIO2/TuioServer.cpp
# and the TUIO 2.0 Protocol Specification by Martin Kaltenbrunner
# http://www.tuio.org/?tuio20

import sys
import time
from pythonosc import udp_client
from pythonosc import osc_bundle_builder
from pythonosc import osc_message_builder

IP = "132.199.130.68"
PORT = 8000


class TUIOServer:

    current_tuio_frame_bundle = None
    current_frame_id = 0

    def __init__(self):
        self.udp_client = udp_client.SimpleUDPClient(IP, PORT)
        self.start_time_ms = int(round(time.time() * 1000))
        #self.send_test()
        #self.start_tuio_bundle()

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

    # /tuio2/tok {s_id} {tu_id} {c_id} {x_pos} {y_pos} {angle}
    def add_token_message(self, s_id, tu_id, c_id, x_pos, y_pos, angle):
        pointer_message = osc_message_builder.OscMessageBuilder(address="/tuio2/tok")
        pointer_message.add_arg(s_id)
        pointer_message.add_arg(tu_id)  # tu_id refers to type/user and can be 0 for now
        pointer_message.add_arg(c_id)  # c_id for touch points and hands refers to the individual finger (index, ring, thumb, …) or hand (left/right)
        pointer_message.add_arg(x_pos)
        pointer_message.add_arg(y_pos)
        pointer_message.add_arg(angle)
        self.current_tuio_frame_bundle.add_content(pointer_message.build())

    # /tuio2/ptr s_id tu_id c_id x_pos y_pos angle shear radius press [x_vel y_vel p_vel m_acc p_acc]
    # /tuio2/ptr int32 int32 int32 float float float float float [float float float float float]
    def add_pointer_message(self, s_id, tu_id, c_id, x_pos, y_pos, angle, shear, radius, press):
        pointer_message = osc_message_builder.OscMessageBuilder(address="/tuio2/ptr")
        pointer_message.add_arg(s_id)
        pointer_message.add_arg(tu_id)  # tu_id refers to type/user and can be 0 for now
        pointer_message.add_arg(c_id)  # c_id for touch points and hands refers to the individual finger (index, ring, thumb, …) or hand (left/right)
        pointer_message.add_arg(x_pos)
        pointer_message.add_arg(y_pos)
        pointer_message.add_arg(angle)
        pointer_message.add_arg(shear)
        pointer_message.add_arg(radius)
        pointer_message.add_arg(press)
        self.current_tuio_frame_bundle.add_content(pointer_message.build())

    def add_bounds_message(self):
        pass

    def add_symbol_message(self):
        pass

    ''' f_id ->   Frame ID (int32)
        time ->   OSC 64bit time tag (ttag)
        dim  ->   Dimension encodes the sensor dimension with two 16bit unsigned integer values embedded into a 32bit
                  integer value. The first two bytes represent the sensor width, while the final two bytes represent
                  the sensor height. (int32)
        source -> e.g. 'REAC' (string) '''
    def start_tuio_bundle(self, dimension, source):
        self.current_tuio_frame_bundle = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)

        self.current_frame_id += 1
        time_now_ms = int(round(time.time() * 1000))
        frame_time_tag = time_now_ms - self.start_time_ms

        frame_message = osc_message_builder.OscMessageBuilder(address="/tuio2/frm")
        frame_message.add_arg(self.current_frame_id)  # f_id
        frame_message.add_arg(frame_time_tag)
        frame_message.add_arg(dimension)
        frame_message.add_arg(source)
        self.current_tuio_frame_bundle.add_content(frame_message.build())

    def send_tuio_bundle(self):
        alive_message = osc_message_builder.OscMessageBuilder(address="/tuio2/alv")
        # TODO: Add a list of all active session IDs to the alive message
        alive_message.add_arg(0)
        self.current_tuio_frame_bundle.add_content(alive_message.build())

        self.udp_client.send(self.current_tuio_frame_bundle.build())

        self.current_tuio_frame_bundle = None


# def main():
#     tuioServer = TUIOServer()
#     sys.exit()
#
#
# if __name__ == '__main__':
#     main()
