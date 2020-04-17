# The TUIO 2.0 server endcodes and sends TUIO messages via UDP to the defined IP address and port
# Using the python-osc library: https://github.com/attwad/python-osc


import time
from pythonosc import udp_client
from pythonosc import osc_bundle_builder
from pythonosc import osc_message_builder

IP = "192.168.178.81"
PORT = 8000

# Get sample points for testing
def get_hand_point():
    # /tuio2/ptr s_id tu_id c_id x_pos y_pos angle shear radius press
    s_id = 0
    t_id = 1
    c_id = 2
    x_pos = 100
    y_pos = 200
    angle = 0
    shear = 0
    radius = 0
    press = 1
    return [s_id, t_id, c_id, x_pos, y_pos, angle, shear, radius, press]

if __name__ == "__main__":

  client = udp_client.SimpleUDPClient(IP, PORT)

  for x in range(5):
    print('send test message')

    #msg = osc_message_builder.OscMessageBuilder(address="/tuio2/ptr")
    #msg.add_arg(4.0)
    hand_point_args = get_hand_point()
    client.send_message("/tuio2/ptr", hand_point_args)
    time.sleep(1)