#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import threading

from data_transportation.VIGITIAVideoStreamReceiver import VIGITIAVideoStreamReceiver
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
    """ This class functions as a TUIO 2.0 client and decodes recieved TUIO messages using the python-osc library
        (https://github.com/attwad/python-osc).
        It also bundles incoming gstreamer video streams and provides a convenient way of applications

    """

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

        self.camera_resolution = None
        self.screen_resolution = None

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
        dispatcher.map("/tuio2/ctl", self.on_new_control_message, needs_reply_address=True)
        dispatcher.map("/tuio2/alv", self.on_new_alive_message, needs_reply_address=True)

        osc_udp_server = ThreadingOSCUDPServer((self.ip, PORT), dispatcher)

        print('[SensorDataInterface]: Listening on {} for incoming TUIO messages'.format(osc_udp_server.server_address))

        server_thread = threading.Thread(target=osc_udp_server.serve_forever)
        server_thread.start()

    # Init a new video stream receiver and subscribe to it to receive new video streams
    def init_video_stream_receiver(self, name, origin_ip, port):
        receiver = VIGITIAVideoStreamReceiver(name, origin_ip, port=port)
        receiver.register_subscriber(self)
        receiver.start()

    # Forward a received video frame to all subscribers
    def on_new_video_frame(self, frame, name, origin_ip, port):
        # Directly forward frame to subscribers
        for subscriber in self.subscribers:
            subscriber.on_new_video_frame(frame, name, origin_ip, port)

    # Translate the dimension attribute from the TUIO protocoll into readable x and y coordinates
    def set_camera_resolution(self, dimension):
        dimension_split = dimension.split('x')
        self.camera_resolution = (int(dimension_split[0]), int(dimension_split[1]))

    def on_new_frame_message(self, *messages):

        if self.camera_resolution is None:
            self.set_camera_resolution(messages[4])

        #print('New frame arrived:', messages)
        origin_ip = messages[0][0]

        self.bundles[origin_ip] = {
            'origin_ip': origin_ip,
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

    # If the Sensor Data Interface does not know the output screen resolution, a toolkit application is asked for it
    def get_screen_resolution(self):
        if len(self.subscribers) > 0:
            self.screen_resolution = list(self.subscribers)[0].get_screen_resolution()

    # Translate coordinates from the camera resolution to the screen resolution
    def translate_coordinates(self, x, y):
        if self.camera_resolution is not None:

            x_translated = int(x / self.camera_resolution[0] * self.screen_resolution[0])
            y_translated = int(y / self.camera_resolution[1] * self.screen_resolution[1])

            return x_translated, y_translated

        else:
            return x, y

    def translate_x_coordinate(self, x):
        if self.camera_resolution is not None and self.screen_resolution is not None:
            return int(x / self.camera_resolution[0] * self.screen_resolution[0])
        else:
            return x

    def translate_y_coordinate(self, y):
        if self.camera_resolution is not None and self.screen_resolution is not None:
            return int(y / self.camera_resolution[1] * self.screen_resolution[1])
        else:
            return y

    def on_new_token_message(self, *messages):

        if self.screen_resolution is None or self.screen_resolution[0] <= 0 or self.screen_resolution[1] <= 0:
            self.get_screen_resolution()

        # Translate coordinates from camera space to screen space
        #x_translated, y_translated = self.translate_coordinates(messages[5], messages[6])

        origin_ip = messages[0][0]
        token_message = {
            'session_id': messages[2],
            'tuio_id': messages[3],
            'component_id': messages[4],
            'x_pos': self.translate_x_coordinate(messages[5]),
            'y_pos': self.translate_y_coordinate(messages[6]),
            'angle': messages[7]
        }
        self.bundles[origin_ip]['tokens'].append(token_message)

    def on_new_pointer_message(self, *messages):

        if self.screen_resolution is None or self.screen_resolution[0] <= 0 or self.screen_resolution[1] <= 0:
            self.get_screen_resolution()

        origin_ip = messages[0][0]
        pointer_message = {
            'session_id': messages[2],
            'tuio_id': messages[3],
            'component_id': messages[4],
            'x_pos': self.translate_x_coordinate(messages[5]),
            'y_pos': self.translate_y_coordinate(messages[6]),
            'angle': messages[7],
            'shear': messages[8],
            'radius': messages[9],
            'press': messages[10]
        }
        self.bundles[origin_ip]['pointers'].append(pointer_message)

    def on_new_bounding_box_message(self, *messages):
        origin_ip = messages[0][0]
        bounding_box_message = {
            'session_id': messages[2],
            'x_pos': self.translate_x_coordinate(messages[3]),
            'y_pos': self.translate_y_coordinate(messages[4]),
            'angle': messages[5],
            'width': self.translate_x_coordinate(messages[6]),
            'height': self.translate_x_coordinate(messages[7]),
            'area': messages[8]
        }
        self.bundles[origin_ip]['bounding_boxes'].append(bounding_box_message)

    def on_new_data_message(self, *messages):
        # print(messages)
        origin_ip = messages[0][0]
        self.bundles[origin_ip]['data'].append(messages[2:])

        message_type = messages[3]
        # Messages of type video indicate the presence of a video stream
        if message_type == 'video':
            stream_name = messages[4]
            stream_port = messages[7]

            stream_info = [stream_name, origin_ip, stream_port]
            stream_already_registered = False
            for entry in self.available_video_streams:
                if set(entry) == set(stream_info):
                    stream_already_registered = True

            if not stream_already_registered:
                print('[SensorDataInterface]: New video stream available:', stream_name, origin_ip, stream_port)
                self.available_video_streams.append(stream_info)
                self.init_video_stream_receiver(stream_name, origin_ip, stream_port)

    def on_new_control_message(self, *messages):
        #print(messages)
        # Send control messages directly because they are currently not in a bundle (sent from a smartphone)
        for subscriber in self.subscribers:
            subscriber.on_new_control_messages(messages)

    def on_new_alive_message(self, *messages):
        origin_ip = messages[0][0]
        active_session_ids = messages[2:]
        self.bundles[origin_ip]['active_session_ids'].append(active_session_ids)

        #print(self.bundles[origin_ip])

        # Send new data to all subscribers
        try:
            for subscriber in self.subscribers:
                # The entire bundle
                subscriber.on_new_tuio_bundle(self.bundles[origin_ip])

                # Just certain components for quicker data access
                subscriber.on_new_token_messages(self.bundles[origin_ip]['tokens'])
                subscriber.on_new_pointer_messages(self.bundles[origin_ip]['pointers'])
                subscriber.on_new_bounding_box_messages(self.bundles[origin_ip]['bounding_boxes'])
        except RuntimeError as error:
            # Handle rare cases when the self.subscribers set changes while it is read
            print(error)

    # Applications can call this function to ask what video streams are available
    def get_available_video_streams(self):
        return self.available_video_streams


def main():
    VIGITIASensorDataInterface.Instance()
    sys.exit()


if __name__ == '__main__':
    main()
