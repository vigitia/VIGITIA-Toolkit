#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The TUIO 2.0 client decodes recieved TUIO messages
# using the python-osc library: https://github.com/attwad/python-osc

# Based upon the TUIO 2.0 C++ Library by Martin Kaltebrunner
# https://github.com/mkalten/TUIO20_CPP/blob/b3fc7998670200091e5768747c3e04ac758084e3/TUIO2/TuioServer.cpp
# and the TUIO 2.0 Protocol Specification by Martin Kaltenbrunner
# http://www.tuio.org/?tuio20

import sys

from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.dispatcher import Dispatcher

IP = "192.168.178.81"
PORT = 8000


class TUIOClient:

    def __init__(self):
        dispatcher = Dispatcher()
        dispatcher.map("/tuio2/*", print)

        osc_udp_server = BlockingOSCUDPServer((IP, PORT), dispatcher)
        print("Listening on {}".format(osc_udp_server.server_address))
        osc_udp_server.serve_forever()


def main():
    tuioclient = TUIOClient()
    sys.exit()


if __name__ == '__main__':
    main()
