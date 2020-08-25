#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from pythonosc import udp_client
from pythonosc import osc_bundle_builder
from pythonosc import osc_message_builder


class TUIOServer:
    """ Basic python implementation of a TUIO 2.0 server

        The TUIO 2.0 server endcodes and sends TUIO messages via UDP to the defined IP address and port
        using the python-osc library: https://github.com/attwad/python-osc

        Based upon the TUIO 2.0 C++ Library by Martin Kaltenbrunner
        https://github.com/mkalten/TUIO20_CPP/blob/b3fc7998670200091e5768747c3e04ac758084e3/TUIO2/TuioServer.cpp

        Documentation of this class mainly taken from the TUIO 2.0 Protocol Specification by Martin Kaltenbrunner
        http://www.tuio.org/?tuio20
    """

    # Global variable to store the current TUIO Bundle
    current_tuio_frame_bundle = None
    current_frame_id = 0

    def __init__(self, ip, port=8000):
        """ Create a new instance of the TUIO server.

            With the current implementation, one instance is needed per target computer

            Parameters:
                ip (str): IP address of the target computer
                port: Port of the target computer that should be used
        """
        self.udp_client = udp_client.SimpleUDPClient(ip, port)
        self.start_time_ms = int(round(time.time() * 1000))

    def init_tuio_frame(self, dimension, source):
        """ FRM (frame message)

            Parameters:
                dimension (int): Dimension encodes the sensor dimension with two 16bit unsigned integer values embedded
                                 into a 32bit integer value. The first two bytes represent the sensor width, while the
                                 final two bytes represent the sensor height.
                source (str): e.g. 'REAC'

            (Source: http://www.tuio.org/?tuio20)
        """

        self.current_frame_id += 1
        time_now_ms = int(round(time.time() * 1000))
        frame_time_tag = time_now_ms - self.start_time_ms

        frame_message = osc_message_builder.OscMessageBuilder(address="/tuio2/frm")
        frame_message.add_arg(self.current_frame_id)  #
        frame_message.add_arg(frame_time_tag)  # OSC 64bit time tag
        frame_message.add_arg(dimension)
        frame_message.add_arg(source)

        return frame_message

    # /tuio2/tok {s_id} {tu_id} {c_id} {x_pos} {y_pos} {angle}
    def add_token_message(self, s_id, tu_id, c_id, x_pos, y_pos, angle):
        """ TOK (token message)

            /tuio2/tok s_id tu_id c_id x_pos y_pos angle [x_vel y_vel a_vel m_acc r_acc]
            /tuio2/tok int32 int32 int32 float float float [float float float float float]

            The TOK message is the equivalent to the 2Dobj SET message of the TUIO 1.* specification, which encodes the
            common attributes of tagged physical objects. The Session ID (s_id) and Component ID (c_id) as well as the
            general X & Y position and angle attributes remain unchanged, while a combined Type/User ID (tu_id) allows
            the multiplexing of various symbol types within the same session as well as the association of an additional
            user ID. The first two bytes of the type/user attribute are therefore encoding the User ID, while the second
            half of the attribute encode the actual Type ID resulting in two 16bit unsigned integer values. This allows
            a possible range of 65535 Type and User IDs. The User ID can be used to determine if a token is currently
            being held by a user, therefore the ID 0 is reserved for the "no user" state. A TUIO implementation has to
            consider this special usage of the int32 tu_id attribute with an according encoding/decoding step. Speed and
            acceleration parameters are optional and the client implementation has to consider the two possible message
            lengths.

            (Source: http://www.tuio.org/?tuio20)
        """

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
        # TODO: Implement if needed
        pass

    # /tuio2/bnd s_id x_pos y_pos angle width height area
    def add_bounding_box_message(self, s_id, x_pos, y_pos, angle, width, height, area):
        """ BND (bounds message)

            /tuio2/bnd s_id x_pos y_pos angle width height area [x_vel y_vel a_vel m_acc r_acc]
            /tuio2/bnd int32 float float float float float float [float float float float float]

            The BND message is the equivalent to the 2Dblb SET message of the TUIO 1.1 specification, which encodes the
            basic geometry information of untagged generic objects (blobs). The message format describes the inner
            ellipse of an oriented bounding box, with its center point, the angle of the major axis, the dimensions of
            the major and minor axis as well as the region area. Therefore this compact format carries information about
            the approximate elliptical region enclosure, but also allows the reconstruction of the oriented bounding
            box. The region area is normalized in pixels/width*height, providing quick access to the overall region
            size.

            The BND message usually identifies the boundaries of any generic untagged physical object, and can be also
            used to transmit the basic geometry information such as the angle and dimensions of finger blobs or physical
            tokens that have been already identified by a previous PTR or TOK message. The session ID has to be equal in
            both messages in order to match the component with the corresponding bounds.

        """

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
        """ SYM (symbol message)

            /tuio2/sym s_id tu_id c_id group data
            /tuio2/sym int32 int32 int32 string string

            The SYM message allows the transmission of the type and data contents of a marker symbol. Since this
            information can be redundant, and does not necessarily apply to all symbol types, it is represented by a
            dedicated message, which can be omitted or sent at a lower rate if desired. The Session ID, Type/User ID and
            Component ID are identical to the values used in the corresponding TOK message. Therefore the actual symbol
            code and the meta-information about the marker type and symbol description only needs to be received once by
            the client. The group attribute is a string describing the symbol type, such as fiducial markers, barcodes,
            or RFID tags. The code attribute is alternatively an OSC string or an OSC blob data field that transmits the
            symbol code or contents: such as the fidtrack left heavy depth sequence, an EAN barcode number, or an RFID
            UID. Since the possibly symbol space may often exceed the range of component IDs, a TUIO implementation
            needs to maintain its internal mapping of Symbols to Component IDs. In case a TUIO tracker such as an RFID
            reader, is not capable to determine the symbol position or orientation, the SYM message can be sent
            individually without any association to a previous TOK component.

            (Source: http://www.tuio.org/?tuio20)

        """

        symbol_message = osc_message_builder.OscMessageBuilder(address="/tuio2/sym")
        symbol_message.add_arg(s_id)
        symbol_message.add_arg(tu_id)
        symbol_message.add_arg(c_id)
        symbol_message.add_arg(group)
        symbol_message.add_arg(data)
        self.current_tuio_frame_bundle.add_content(symbol_message.build())

    # /tuio2/skg s_id x_p0 y_p0 x_p1 y_p1 node ... x_pN y_pN
    def add_skeleton_message(self):
        """ SKG (skeleton geometry)

            /tuio2/skg s_id x_p0 y_p0 x_p1 y_p1 node ... x_pN y_pN

            The SKG message represents the skeleton structure of a blob. In contrary to the list of contour points this
            needs to be represented as a tree structure. After the session ID the message begins with an arbitrary leaf
            of that tree structure and continues the point list until it reaches the next leaf point. The integer node
            number directs the tree back to the last node point.

            (Source: http://www.tuio.org/?tuio20)

        """
        skeleton_message = osc_message_builder.OscMessageBuilder(address="/tuio2/skg")
        self.current_tuio_frame_bundle.add_content(skeleton_message.build())

    def add_data_message(self, s_id, mime, *data):
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
        data_message = osc_message_builder.OscMessageBuilder(address="/tuio2/dat")
        data_message.add_arg(s_id)
        data_message.add_arg(mime)
        for arg in data:
            data_message.add_arg(arg)

        self.current_tuio_frame_bundle.add_content(data_message.build())

    def add_control_message(self, s_id, *cN):
        """ CTL (control message)

            /tuio2/ctl s_id c0 ... cN
            /tuio2/ctl int32 bool/float ... bool/float

            The CTL message can be used to transmit additional control dimensions that can be associated to an existing
            component instance, such as a token with an incorporated pressure sensor or for example. This (open length)
            list of variable float or boolean values, encodes each individual control dimension as discrete 0/1 bool or
            continuous floats in the normalized range from -1.0f ... 1.0f. A simple 3-button wheel mouse for example
            could be encoded using a CTL message with three boolean values for the discrete buttons and one additional
            float value for the continuous wheel after the initial session ID.

            An array of 12 float attributes can for example encode the keys of a full octave in a small piano keyboard
            including key velocity. The association of the according CTL message to a previous TKN consequently allows
            the identification and localization of that physical keyboard component.

            (Source: http://www.tuio.org/?tuio20)
        """
        control_message = osc_message_builder.OscMessageBuilder(address="/tuio2/ctl")
        control_message.add_arg(s_id)
        for arg in cN:
            control_message.add_arg(arg)

        self.current_tuio_frame_bundle.add_content(control_message.build())

    def start_tuio_bundle(self, dimension, source):
        """ Start building a new TUIO bundle"""
        self.current_tuio_frame_bundle = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)

        frame_message = self.init_tuio_frame(dimension, source)

        self.current_tuio_frame_bundle.add_content(frame_message.build())

    def send_tuio_bundle(self):
        alive_message = osc_message_builder.OscMessageBuilder(address="/tuio2/alv")
        # TODO: Add a list of all active session IDs to the alive message
        # This also means that components that are still present -> 'alive' but have not updated at the current frame
        # should be included in the alive message but no other TUIO messages need to be sent.
        alive_message.add_arg(0)
        self.current_tuio_frame_bundle.add_content(alive_message.build())

        self.udp_client.send(self.current_tuio_frame_bundle.build())

        self.current_tuio_frame_bundle = None
