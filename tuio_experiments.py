#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from tuio20_client_server.tuio_server import TUIOServer


def tuio_experiment():
    tuio_server = TUIOServer()

    # The dimension attribute encodes the sensor dimension with two 16bit unsigned integer values embedded into a 32bit
    # integer value. The first two bytes represent the sensor width, while the final two bytes represent the sensor
    # height
    dimension = 0
    source = 'VIGITIA'

    for i in range(5):
        tuio_server.start_tuio_bundle(dimension=dimension, source=source)
        tuio_server.add_pointer_message(s_id=0, tu_id=0, c_id=0, x_pos=200, y_pos=300, angle=0, shear=0, radius=0, press=1)
        tuio_server.send_tuio_bundle()
        time.sleep(3)


tuio_experiment()
