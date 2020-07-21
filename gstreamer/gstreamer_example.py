# #!/usr/bin/python3

# Source: https://gist.github.com/NBonaparte/89fb1b645c99470bc0f6

# python3 test.py --rtsp --uri rtsp://admin:abcd@1234@113.22.74.74:1554
# gst-launch-1.0 rtspsrc location=rtsp://admin:abcd@1234@113.22.74.74:1554 ! rtph264depay ! h264parse ! omxh264dec ! nveglglessink


import sys
import argparse
import cv2


WINDOW_NAME = 'CameraDemo'


def parse_args():
    # Parse input arguments
    desc = 'Capture and display live camera video on Jetson TX2/TX1'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--rtsp', dest='use_rtsp',
                        help='use IP CAM (remember to also set --uri)',
                        action='store_true')
    parser.add_argument('--uri', dest='rtsp_uri',
                        help='RTSP URI, e.g. rtsp://192.168.1.64:554',
                        default=None, type=str)
    parser.add_argument('--latency', dest='rtsp_latency',
                        help='latency in ms for RTSP [200]',
                        default=200, type=int)
    parser.add_argument('--usb', dest='use_usb',
                        help='use USB webcam (remember to also set --vid)',
                        action='store_true')
    parser.add_argument('--vid', dest='video_dev',
                        help='device # of USB webcam (/dev/video?) [1]',
                        default=1, type=int)
    parser.add_argument('--width', dest='image_width',
                        help='image width [1920]',
                        default=1920, type=int)
    parser.add_argument('--height', dest='image_height',
                        help='image height [1080]',
                        default=1080, type=int)
    args = parser.parse_args()
    return args


def open_cam_rtsp(uri, width, height, latency):
    gst_str = ('rtspsrc location={} latency={} ! '
               'rtph264depay ! h264parse ! omxh264dec ! '
               'nvvidconv ! '
               'video/x-raw, width=(int){}, height=(int){}, '
               'format=(string)BGRx ! '
               'videoconvert ! appsink').format(uri, latency, width, height)
    return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)


def open_cam_usb(dev, width, height):
    # We want to set width and height here, otherwise we could just do:
    #     return cv2.VideoCapture(dev)
    gst_str = ('v4l2src device=/dev/video{} ! '
               'video/x-raw, width=(int){}, height=(int){} ! '
               'videoconvert ! appsink').format(dev, width, height)
    return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)


def open_cam_onboard(width, height):
    # On versions of L4T prior to 28.1, add 'flip-method=2' into gst_str
    gst_str = ('nvcamerasrc ! '
               'video/x-raw(memory:NVMM), '
               'width=(int)2592, height=(int)1458, '
               'format=(string)I420, framerate=(fraction)30/1 ! '
               'nvvidconv ! '
               'video/x-raw, width=(int){}, height=(int){}, '
               'format=(string)BGRx ! '
               'videoconvert ! appsink').format(width, height)
    return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)


def open_window(width, height):
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, width, height)
    cv2.moveWindow(WINDOW_NAME, 0, 0)
    cv2.setWindowTitle(WINDOW_NAME, 'Camera Demo for Jetson TX2/TX1')


def read_cam(cap):
    show_help = True
    full_scrn = False
    help_text = '"Esc" to Quit, "H" for Help, "F" to Toggle Fullscreen'
    font = cv2.FONT_HERSHEY_PLAIN
    while True:
        if cv2.getWindowProperty(WINDOW_NAME, 0) < 0:
            # Check to see if the user has closed the window
            # If yes, terminate the program
            break
        _, img = cap.read() # grab the next image frame from camera
        if show_help:
            cv2.putText(img, help_text, (11, 20), font,
                        1.0, (32, 32, 32), 4, cv2.LINE_AA)
            cv2.putText(img, help_text, (10, 20), font,
                        1.0, (240, 240, 240), 1, cv2.LINE_AA)
        cv2.imshow(WINDOW_NAME, img)
        key = cv2.waitKey(10)
        if key == 27: # ESC key: quit program
            break
        elif key == ord('H') or key == ord('h'): # toggle help message
            show_help = not show_help
        elif key == ord('F') or key == ord('f'): # toggle fullscreen
            full_scrn = not full_scrn
            if full_scrn:
                cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN,
                                      cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN,
                                      cv2.WINDOW_NORMAL)


def main():

    cap = open_cam_usb(4, 1280, 70)

    if not cap.isOpened():
        sys.exit('Failed to open camera!')

    open_window(1280, 70)
    read_cam(cap)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()



# # This program is licensed under GPLv3.
# # Source: https://gist.github.com/NBonaparte/89fb1b645c99470bc0f6
#
# from os import path
# import gi
# gi.require_version('Gst', '1.0')
# gi.require_version('Gtk', '3.0')
# gi.require_version('GdkX11', '3.0')
# gi.require_version('GstVideo', '1.0')
# from gi.repository import GObject, Gst, Gtk
#
# # Needed for get_xid(), set_window_handle()
# from gi.repository import GdkX11, GstVideo
#
# # Needed for timestamp on file output
# from datetime import datetime
# GObject.threads_init()
# Gst.init(None)
# location = '/dev/video4'
#
# class Player(Gtk.Window):
#     def __init__(self):
#         Gtk.Window.__init__(self, title="Liveview")
#         self.connect('destroy', self.quit)
#         self.set_default_size(800, 450)
#
#         # Create DrawingArea for video widget
#         self.drawingarea = Gtk.DrawingArea()
#
#         # Create a grid for the DrawingArea and buttons
#         grid = Gtk.Grid()
#         self.add(grid)
#         grid.attach(self.drawingarea, 0, 1, 2, 1)
#         # Needed or else the drawing area will be really small (1px)
#         self.drawingarea.set_hexpand(True)
#         self.drawingarea.set_vexpand(True)
#
#         # Quit button
#         quit = Gtk.Button(label="Quit")
#         quit.connect("clicked", Gtk.main_quit)
#         grid.attach(quit, 0, 0, 1, 1)
#
#         # Record/Stop button
#         self.record = Gtk.Button(label="Record")
#         self.record.connect("clicked", self.record_button)
#         grid.attach(self.record, 1, 0, 1, 1)
#
#         # Create GStreamer pipeline
#         self.pipeline = Gst.parse_launch("v4l2src device=" + location + " ! tee name=tee ! queue name=videoqueue ! deinterlace ! xvimagesink")
#
#         # Create bus to get events from GStreamer pipeline
#         bus = self.pipeline.get_bus()
#         bus.add_signal_watch()
#         bus.connect('message::eos', self.on_eos)
#         bus.connect('message::error', self.on_error)
#
#         # This is needed to make the video output in our DrawingArea:
#         bus.enable_sync_message_emission()
#         bus.connect('sync-message::element', self.on_sync_message)
#
#     def run(self):
#         self.show_all()
#         self.xid = self.drawingarea.get_property('window').get_xid()
#         self.pipeline.set_state(Gst.State.PLAYING)
#         Gtk.main()
#
#     def quit(self, window):
#         self.pipeline.set_state(Gst.State.NULL)
#         Gtk.main_quit()
#
#     def on_sync_message(self, bus, msg):
#         if msg.get_structure().get_name() == 'prepare-window-handle':
#             print('prepare-window-handle')
#             msg.src.set_window_handle(self.xid)
#
#     def on_eos(self, bus, msg):
#         print('on_eos(): seeking to start of video')
#         self.pipeline.seek_simple(
#             Gst.Format.TIME,
#             Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
#             0
#         )
#
#     def on_error(self, bus, msg):
#         print('on_error():', msg.parse_error())
#
#     def start_record(self):
#         # Filename (current time)
#         filename = datetime.now().strftime("%Y-%m-%d_%H.%M.%S") + ".avi"
#         print(filename)
#         self.recordpipe = Gst.parse_bin_from_description("queue name=filequeue ! jpegenc ! avimux ! filesink location=" + filename, True)
#         self.pipeline.add(self.recordpipe)
#         self.pipeline.get_by_name("tee").link(self.recordpipe)
#         self.recordpipe.set_state(Gst.State.PLAYING)
#
#     def stop_record(self):
#         filequeue = self.recordpipe.get_by_name("filequeue")
#         filequeue.get_static_pad("src").add_probe(Gst.PadProbeType.BLOCK_DOWNSTREAM, self.probe_block)
#         self.pipeline.get_by_name("tee").unlink(self.recordpipe)
#         filequeue.get_static_pad("sink").send_event(Gst.Event.new_eos())
#         print("Stopped recording")
#
#     def record_button(self, widget):
#         if self.record.get_label() == "Record":
#             self.record.set_label("Stop")
#             self.start_record()
#         else:
#             self.stop_record()
#             self.record.set_label("Record")
#
#     def probe_block(self, pad, buf):
#         print("blocked")
#         return True
#
# p = Player()
# p.run()