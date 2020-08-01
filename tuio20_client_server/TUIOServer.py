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


class TUIOServer:

    current_tuio_frame_bundle = None
    current_frame_id = 0

    def __init__(self, ip, port=8000):
        self.udp_client = udp_client.SimpleUDPClient(ip, port)
        self.start_time_ms = int(round(time.time() * 1000))

    ''' f_id ->   Frame ID (int32)
            time ->   OSC 64bit time tag (ttag)
            dim  ->   Dimension encodes the sensor dimension with two 16bit unsigned integer values embedded into a 32bit
                      integer value. The first two bytes represent the sensor width, while the final two bytes represent
                      the sensor height. (int32)
            source -> e.g. 'REAC' (string) '''
    def init_tuio_frame(self, dimension, source):
        self.current_frame_id += 1
        time_now_ms = int(round(time.time() * 1000))
        frame_time_tag = time_now_ms - self.start_time_ms

        frame_message = osc_message_builder.OscMessageBuilder(address="/tuio2/frm")
        frame_message.add_arg(self.current_frame_id)  # f_id
        frame_message.add_arg(frame_time_tag)
        frame_message.add_arg(dimension)
        frame_message.add_arg(source)

        return frame_message

    # /tuio2/tok {s_id} {tu_id} {c_id} {x_pos} {y_pos} {angle}
    def add_token_message(self, s_id, tu_id, c_id, x_pos, y_pos, angle):
        token_message = osc_message_builder.OscMessageBuilder(address="/tuio2/tok")
        token_message.add_arg(s_id)
        token_message.add_arg(tu_id)  # tu_id refers to type/user and can be 0 for now
        token_message.add_arg(c_id)  # c_id for touch points and hands refers to the individual finger (index, ring, thumb, …) or hand (left/right)
        token_message.add_arg(x_pos)
        token_message.add_arg(y_pos)
        token_message.add_arg(angle)
        self.current_tuio_frame_bundle.add_content(token_message.build())

    # /tuio2/ptr s_id tu_id c_id x_pos y_pos angle shear radius press [x_vel y_vel p_vel m_acc p_acc]
    # /tuio2/ptr int32 int32 int32 float float float float float [float float float float float]
    def add_pointer_message(self, s_id, tu_id, c_id, x_pos, y_pos, angle, shear, radius, press):
        pointer_message = osc_message_builder.OscMessageBuilder(address="/tuio2/ptr")
        pointer_message.add_arg(int(s_id))
        pointer_message.add_arg(int(tu_id))  # tu_id refers to type/user and can be 0 for now
        pointer_message.add_arg(int(c_id))  # c_id for touch points and hands refers to the individual finger (index, ring, thumb, …) or hand (left/right)
        pointer_message.add_arg(int(x_pos))
        pointer_message.add_arg(int(y_pos))
        pointer_message.add_arg(int(angle))
        pointer_message.add_arg(int(shear))
        pointer_message.add_arg(int(radius))
        pointer_message.add_arg(int(press))
        self.current_tuio_frame_bundle.add_content(pointer_message.build())

    # /tuio2/ocg s_id x_p0 y_p0 ... x_pN y_pN
    def add_outer_contour_geometry_message(self, s_id):
        pass

    # /tuio2/bnd s_id x_pos y_pos angle width height area
    def add_bounding_box_message(self, s_id, x_pos, y_pos, angle, width, height, area):
        bounding_box_message = osc_message_builder.OscMessageBuilder(address="/tuio2/bnd")
        bounding_box_message.add_arg(s_id)
        bounding_box_message.add_arg(x_pos)
        bounding_box_message.add_arg(y_pos)
        bounding_box_message.add_arg(angle)
        bounding_box_message.add_arg(width)
        bounding_box_message.add_arg(height)
        bounding_box_message.add_arg(area)
        self.current_tuio_frame_bundle.add_content(bounding_box_message.build())

    # /tuio2/sym s_id tu_id c_id group data
    def add_symbol_message(self, s_id, tu_id, c_id, group, data):
        symbol_message = osc_message_builder.OscMessageBuilder(address="/tuio2/sym")
        symbol_message.add_arg(s_id)
        symbol_message.add_arg(tu_id)
        symbol_message.add_arg(c_id)
        symbol_message.add_arg(group)
        symbol_message.add_arg(data)
        self.current_tuio_frame_bundle.add_content(symbol_message.build())

    # /tuio2/skg s_id x_p0 y_p0 x_p1 y_p1 node ... x_pN y_pN
    def add_skeleton_message(self):
        skeleton_message = osc_message_builder.OscMessageBuilder(address="/tuio2/skg")
        self.current_tuio_frame_bundle.add_content(skeleton_message.build())

    """ DAT (data message)
    
    /tuio2/dat s_id mime data
    /tuio2/dat s_id string string/blob

    The DAT message allows the association of arbitrary data content to any present TUIO component. Apart from the 
    common session ID, this message only contains an initial OSC string that defines the MIME type of the following 
    data attribute, which can be either transmitted using an OSC string or OSC blob data type. Therefore this message 
    is capable of encoding and transmitting textural or binary data such as business cards, XML data, images or sounds 
    etc. The DAT message can be for example also used to transmit the actual data content of an RFID tag that has been 
    referenced within a previous SYM message. Due to the likely limited bandwidth resources of the used OSC channel, 
    this infrastructure is not suitable for the transmission of larger data sets. In this case the use of alternative 
    transport methods is recommended.
    
    (Source: http://www.tuio.org/?tuio20)
    
    """
    def add_data_message(self, s_id, mime, *data):
        data_message = osc_message_builder.OscMessageBuilder(address="/tuio2/data")
        data_message.add_arg(s_id)
        data_message.add_arg(mime)
        for arg in data:
            data_message.add_arg(arg)

        self.current_tuio_frame_bundle.add_content(data_message.build())

    """ CTL (control message)
    
    /tuio2/ctl s_id c0 ... cN
    /tuio2/ctl int32 bool/float ... bool/float
    
    The CTL message can be used to transmit additional control dimensions that can be associated to an existing 
    component instance, such as a token with an incorporated pressure sensor or for example. This (open length) 
    list of variable float or boolean values, encodes each individual control dimension as discrete 0/1 bool or 
    continuous floats in the normalized range from -1.0f ... 1.0f. A simple 3-button wheel mouse for example could be 
    encoded using a CTL message with three boolean values for the discrete buttons and one additional float value for 
    the continuous wheel after the initial session ID.
    
    An array of 12 float attributes can for example encode the keys of a full octave in a small piano keyboard 
    including key velocity. The association of the according CTL message to a previous TKN consequently allows the 
    identification and localization of that physical keyboard component.
    
    (Source: http://www.tuio.org/?tuio20)
    """
    def add_control_message(self, s_id, *cN):
        control_message = osc_message_builder.OscMessageBuilder(address="/tuio2/ctl")
        control_message.add_arg(s_id)
        for arg in cN:
            control_message.add_arg(arg)

        self.current_tuio_frame_bundle.add_content(control_message.build())

    def start_tuio_bundle(self, dimension, source):
        self.current_tuio_frame_bundle = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)

        frame_message = self.init_tuio_frame(dimension, source)

        self.current_tuio_frame_bundle.add_content(frame_message.build())

    def send_tuio_bundle(self):
        alive_message = osc_message_builder.OscMessageBuilder(address="/tuio2/alv")
        # TODO: Add a list of all active session IDs to the alive message
        alive_message.add_arg(0)
        self.current_tuio_frame_bundle.add_content(alive_message.build())

        self.udp_client.send(self.current_tuio_frame_bundle.build())

        self.current_tuio_frame_bundle = None
