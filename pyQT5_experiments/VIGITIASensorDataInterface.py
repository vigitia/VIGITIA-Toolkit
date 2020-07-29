#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The TUIO 2.0 client decodes recieved TUIO messages
# using the python-osc library: https://github.com/attwad/python-osc

# Based upon the TUIO 2.0 C++ Library by Martin Kaltebrunner
# https://github.com/mkalten/TUIO20_CPP/blob/b3fc7998670200091e5768747c3e04ac758084e3/TUIO2/TuioServer.cpp
# and the TUIO 2.0 Protocol Specification by Martin Kaltenbrunner
# http://www.tuio.org/?tuio20

# Using the Observer Pattern
# Using the Singleton Pattern ()


import sys
import threading
from urllib import request, error

from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.dispatcher import Dispatcher

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
        self.ip = self.get_ip_address()

        self.subscribers = set()

        self.tokens = []

        self.init_tuio_interface()

    def get_ip_address(self):
        try:
            # Try to get the public IP address of the computer
            ip = request.urlopen('https://ident.me').read().decode('utf8')
        except error.URLError as e:
            # If no Internet connection is available, use the local IP address instead
            import socket
            ip = socket.gethostbyname(socket.gethostname())

        return ip

    def register_subscriber(self, new_subscriber):
        print('New Subscriber:', new_subscriber.__class__.__name__)
        self.subscribers.add(new_subscriber)

    def unregister_subscriber(self, subscriber):
        self.subscribers.discard(subscriber)

    def init_tuio_interface(self):
        dispatcher = Dispatcher()
        dispatcher.map("/tuio2/frm", self.on_new_frame_message)
        dispatcher.map("/tuio2/ptr", self.on_new_pointer_message)
        dispatcher.map("/tuio2/tok", self.on_new_token_message)
        dispatcher.map("/tuio2/bnd", self.on_new_bounding_box_message)
        dispatcher.map("/tuio2/alv", self.on_new_alive_message)

        osc_udp_server = ThreadingOSCUDPServer((self.ip, PORT), dispatcher)

        print("Listening on {}".format(osc_udp_server.server_address))

        server_thread = threading.Thread(target=osc_udp_server.serve_forever)
        server_thread.start()

        print('Initialized TUIO interface')

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
        #     # print('Sending message to subscriber:', subscriber.__class__.__name__)
        #     subscriber.on_new_token_message(messages)

    def on_new_alive_message(self, *messages):
        #print(messages)

        for subscriber in self.subscribers:
            # print('Sending message to subscriber:', subscriber.__class__.__name__)
            subscriber.on_new_token_messages(self.tokens)


def main():
    data_interface = VIGITIASensorDataInterface.Instance()
    sys.exit()


if __name__ == '__main__':
    main()
