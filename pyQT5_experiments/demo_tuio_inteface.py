#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The TUIO 2.0 client decodes recieved TUIO messages
# using the python-osc library: https://github.com/attwad/python-osc

# Based upon the TUIO 2.0 C++ Library by Martin Kaltebrunner
# https://github.com/mkalten/TUIO20_CPP/blob/b3fc7998670200091e5768747c3e04ac758084e3/TUIO2/TuioServer.cpp
# and the TUIO 2.0 Protocol Specification by Martin Kaltenbrunner
# http://www.tuio.org/?tuio20

# Using the ObserverPattern

import sys

from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.dispatcher import Dispatcher

IP = "132.199.130.68"
PORT = 8000


class DataInterface:

    def __init__(self):
        self.subscribers = set()

        self.init_tuio_interface()

    def register_subscriber(self, new_subscriber):
        print('New Subscriber:', new_subscriber)
        self.subscribers.add(new_subscriber)

    def unregister_subscriber(self, subscriber):
        self.subscribers.discard(subscriber)

    def init_tuio_interface(self):
        dispatcher = Dispatcher()
        # dispatcher.map("/tuio2/*", self.dispatch)
        dispatcher.map("/tuio2/tok", self.on_new_token_message)

        osc_udp_server = BlockingOSCUDPServer((IP, PORT), dispatcher)
        print("Listening on {}".format(osc_udp_server.server_address))
        osc_udp_server.serve_forever()

    def on_new_token_message(self, *messages):
        print(messages)
        for subscriber in self.subscribers:
            print('Sending message to subscriber:', subscriber)
            subscriber.update(messages)

def main():
    data_interface = DataInterface()
    sys.exit()


if __name__ == '__main__':
    main()
