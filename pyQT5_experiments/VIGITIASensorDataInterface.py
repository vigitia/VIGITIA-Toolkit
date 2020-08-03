#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This class functions as a TUIO 2.0 client and decodes recieved TUIO messages using the python-osc library:
# https://github.com/attwad/python-osc


# Code parts for the TUIO client based on the TUIO 2.0 Protocol Specification (http://www.tuio.org/?tuio20) and the
# TUIO 2.0 C++ Library by Martin Kaltebrunner:
# https://github.com/mkalten/TUIO20_CPP/blob/b3fc7998670200091e5768747c3e04ac758084e3/TUIO2/TuioServer.cpp

import sys
import threading

from gstreamer.VIGITIAVideoStreamReceiver import VIGITIAVideoStreamReceiver
from utility.get_ip import get_ip_address

from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.dispatcher import Dispatcher

# Port where this application will listen for incoming TUIO messages
PORT = 8000


# The Singleton class is implemented like described here:
# https://medium.com/better-programming/singleton-in-python-5eaa66618e3d
class Singleton:

    def __init__(self, cls):
        self._cls = cls

    def Instance(self):
        try:
            return self._instance
        except AttributeError:
            self._instance = self._cls()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._cls)


@Singleton
class VIGITIASensorDataInterface:

    def __init__(self):
        # IP needs to be always the IP of the computer
        self.ip = get_ip_address()

        # Using the Observer pattern
        self.subscribers = set()

        self.bundles = {}

        self.tokens = []
        self.pointers = []
        self.outer_contour_geometries = []
        self.bounding_boxes = []
        self.symbols = []

        self.available_video_streams = []

        self.init_tuio_interface()

    def register_subscriber(self, new_subscriber):
        print('New Subscriber:', new_subscriber.__class__.__name__)
        self.subscribers.add(new_subscriber)

    def unregister_subscriber(self, subscriber):
        self.subscribers.discard(subscriber)

    def init_tuio_interface(self):
        dispatcher = Dispatcher()
        dispatcher.map("/tuio2/frm", self.on_new_frame_message, needs_reply_address=True)  # Also pass on the IP of the data origin
        dispatcher.map("/tuio2/ptr", self.on_new_pointer_message, needs_reply_address=True)
        dispatcher.map("/tuio2/bnd", self.on_new_bounding_box_message, needs_reply_address=True)
        dispatcher.map("/tuio2/tok", self.on_new_token_message, needs_reply_address=True)
        dispatcher.map("/tuio2/dat", self.on_new_data_message, needs_reply_address=True)
        dispatcher.map("/tuio2/alv", self.on_new_alive_message, needs_reply_address=True)

        osc_udp_server = ThreadingOSCUDPServer((self.ip, PORT), dispatcher)

        print("Listening on {} for incoming TUIO messages".format(osc_udp_server.server_address))

        server_thread = threading.Thread(target=osc_udp_server.serve_forever)
        server_thread.start()

    # Init a new video stream receiver and subscribe to it to receive new video streams
    def init_video_stream_receiver(self, name, origin_ip, port):
        receiver = VIGITIAVideoStreamReceiver(name, origin_ip, port=port)
        receiver.register_subscriber(self)
        receiver.start()

    # Forward a received video frame to all subscribers
    def on_new_video_frame(self, frame, name, origin_ip, port):
        # print('New frame received of type', name)

        for subscriber in self.subscribers:
            subscriber.on_new_video_frame(frame, name)

    def on_new_frame_message(self, *messages):
        #print('New frame arrived:', messages)
        origin_ip = messages[0][0]

        self.bundles[origin_ip] = {
            'frame_id': messages[2],
            'time_tag': messages[3],
            'dimension': messages[4],
            'source': messages[5],
            'tokens': [],
            'pointers': [],
            'bounding_boxes': [],
            'outer_contour_geometries': [],
            'symbols': [],
            'data': [],
            'active_session_ids': []
        }

    def on_new_token_message(self, *messages):
        origin_ip = messages[0][0]
        self.bundles[origin_ip]['tokens'].append(messages[2:])

    def on_new_pointer_message(self, *messages):
        origin_ip = messages[0][0]
        self.bundles[origin_ip]['pointers'].append(messages[2:])

    def on_new_bounding_box_message(self, *messages):
        origin_ip = messages[0][0]
        self.bundles[origin_ip]['bounding_boxes'].append(messages[2:])

    def on_new_data_message(self, *messages):
        origin_ip = messages[0][0]
        self.bundles[origin_ip]['data'].append(messages[2:])

        message_type = messages[3]
        if message_type == 'video':
            session_id = messages[2]
            if len(self.available_video_streams) > session_id:
                pass
            else:
                print('New video stream')
                stream_name = messages[4]
                stream_port = messages[7]
                self.available_video_streams.append(stream_name)
                self.init_video_stream_receiver(stream_name, origin_ip, stream_port)

    def on_new_alive_message(self, *messages):
        origin_ip = messages[0][0]
        active_session_ids = messages[2:]
        self.bundles[origin_ip]['active_session_ids'].append(active_session_ids)

        print(self.bundles[origin_ip])

        # Send bundle to all subscribers
        for subscriber in self.subscribers:
            subscriber.on_new_tuio_bundle(self.bundles[origin_ip])

    # Applications can call this function to ask what video streams are available
    def get_available_video_streams(self):
        return self.available_video_streams


def main():
    data_interface = VIGITIASensorDataInterface.Instance()
    sys.exit()


if __name__ == '__main__':
    main()
