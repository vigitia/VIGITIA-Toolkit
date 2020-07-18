#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The TUIO 2.0 client decodes recieved TUIO messages
# using the python-osc library: https://github.com/attwad/python-osc

# Based upon the TUIO 2.0 C++ Library by Martin Kaltebrunner
# https://github.com/mkalten/TUIO20_CPP/blob/b3fc7998670200091e5768747c3e04ac758084e3/TUIO2/TuioServer.cpp
# and the TUIO 2.0 Protocol Specification by Martin Kaltenbrunner
# http://www.tuio.org/?tuio20

# Using the Observer Pattern
# Using the Singleton Pattern (https://www.tutorialspoint.com/python_design_patterns/python_design_patterns_singleton.htm)

import sys
import threading

from pythonosc.osc_server import BlockingOSCUDPServer, ThreadingOSCUDPServer
from pythonosc.dispatcher import Dispatcher

IP = "132.199.130.68"
PORT = 8000


class DataInterface:
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if DataInterface.__instance is None:
            DataInterface()
        return DataInterface.__instance

    def __init__(self):
        if DataInterface.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            print('Initialized DataInterface')
            DataInterface.__instance = self

        self.subscribers = set()

        self.init_tuio_interface()

    def register_subscriber(self, new_subscriber):
        print('New Subscriber:', new_subscriber.__class__.__name__)
        self.subscribers.add(new_subscriber)

    def unregister_subscriber(self, subscriber):
        self.subscribers.discard(subscriber)

    def init_tuio_interface(self):
        dispatcher = Dispatcher()
        # dispatcher.map("/tuio2/*", self.dispatch)
        dispatcher.map("/tuio2/tok", self.on_new_token_message)

        osc_udp_server = ThreadingOSCUDPServer((IP, PORT), dispatcher)
        print("Listening on {}".format(osc_udp_server.server_address))

        server_thread = threading.Thread(target=osc_udp_server.serve_forever)
        server_thread.start()

        print('Initialized TUIO interface')

    def on_new_token_message(self, *messages):
        for subscriber in self.subscribers:
            # print('Sending message to subscriber:', subscriber.__class__.__name__)
            subscriber.on_new_data(messages)


def main():
    data_interface = DataInterface()
    sys.exit()


if __name__ == '__main__':
    main()
