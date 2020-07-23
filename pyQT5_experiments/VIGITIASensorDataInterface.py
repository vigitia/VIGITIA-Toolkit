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

from pythonosc.osc_server import BlockingOSCUDPServer, ThreadingOSCUDPServer
from pythonosc.dispatcher import Dispatcher

IP = "132.199.130.68"
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
        self.subscribers = set()

        self.init_tuio_interface()

    def register_subscriber(self, new_subscriber):
        print('New Subscriber:', new_subscriber.__class__.__name__)
        self.subscribers.add(new_subscriber)

    def unregister_subscriber(self, subscriber):
        self.subscribers.discard(subscriber)

    def init_tuio_interface(self):
        dispatcher = Dispatcher()
        dispatcher.map("/tuio2/ptr", self.on_new_pointer_message)
        dispatcher.map("/tuio2/tok", self.on_new_token_message)
        dispatcher.map("/tuio2/bnd", self.on_new_bounding_box_message)

        osc_udp_server = ThreadingOSCUDPServer((IP, PORT), dispatcher)
        print("Listening on {}".format(osc_udp_server.server_address))

        server_thread = threading.Thread(target=osc_udp_server.serve_forever)
        server_thread.start()

        print('Initialized TUIO interface')

    def on_new_pointer_message(self, *messages):
        print(messages)

    def on_new_bounding_box_message(self, *messages):
        print(messages)

    def on_new_token_message(self, *messages):
        print(messages)
        for subscriber in self.subscribers:
            # print('Sending message to subscriber:', subscriber.__class__.__name__)
            subscriber.on_new_data(messages)


def main():
    data_interface = VIGITIASensorDataInterface.Instance()
    sys.exit()


if __name__ == '__main__':
    main()
