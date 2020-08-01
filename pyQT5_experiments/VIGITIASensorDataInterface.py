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

        self.tokens = []
        self.pointers = []
        self.outer_contour_geometries = []
        self.bounding_boxes = []
        self.symbols = []

        self.init_tuio_interface()
        self.init_video_stream_receivers()

    def register_subscriber(self, new_subscriber):
        print('New Subscriber:', new_subscriber.__class__.__name__)
        self.subscribers.add(new_subscriber)

    def unregister_subscriber(self, subscriber):
        self.subscribers.discard(subscriber)

    def init_tuio_interface(self):
        dispatcher = Dispatcher()
        dispatcher.map("/tuio2/frm", self.on_new_frame_message)
        dispatcher.map("/tuio2/ptr", self.on_new_pointer_message)
        dispatcher.map("/tuio2/bnd", self.on_new_bounding_box_message)
        dispatcher.map("/tuio2/tok", self.on_new_token_message)
        dispatcher.map("/tuio2/alv", self.on_new_alive_message)

        osc_udp_server = ThreadingOSCUDPServer((self.ip, PORT), dispatcher)

        print("Listening on {} for incoming TUIO messages".format(osc_udp_server.server_address))

        server_thread = threading.Thread(target=osc_udp_server.serve_forever)
        server_thread.start()

    #
    def init_video_stream_receivers(self):

        ports = [5000]

        for port in ports:
            receiver = VIGITIAVideoStreamReceiver('RealSense D435 RGB', port=port)
            receiver.register_subscriber(self)
            receiver.start()

    def on_new_video_frame(self, frame, name):
        print('New frame received of type', name)

        for subscriber in self.subscribers:
            subscriber.on_new_video_frame(frame, name)

    def on_new_frame_message(self, *message):
        #print('New frame arrived:', message)
        self.tokens = []
        pass

    def on_new_pointer_message(self, *messages):
        # print(messages)
        for subscriber in self.subscribers:
            subscriber.on_new_pointer_messages(messages)

    def on_new_bounding_box_message(self, *messages):
        pass
        # print(messages)

    def on_new_token_message(self, *messages):
        self.tokens.append(messages)
        # print(messages)
        # for subscriber in self.subscribers:
        #     subscriber.on_new_token_message(messages)

    def on_new_alive_message(self, *messages):
        #print(messages)

        for subscriber in self.subscribers:
            subscriber.on_new_token_messages(self.tokens)


def main():
    data_interface = VIGITIASensorDataInterface.Instance()
    sys.exit()


if __name__ == '__main__':
    main()
