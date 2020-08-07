
from pyQT5_experiments.VIGITIASensorDataInterface import VIGITIASensorDataInterface


class VIGITIABaseApplication:
    """ Parent class for all Toolkit applications.

        All toolkit applications need to inherit this class.

        It prepares getter and setter functions, manages basic info about the application and communicates changes
        to the rendering manager.

        The empty methods are the input points for incoming data from the sensor data interface and can easily be
        overwritten by any class that inherits from this class

    """

    def __init__(self):

        self.name = ''
        self.x = 0  # x-pos of top-left corner on canvas
        self.y = 0  # y-pos of top-left corner in canvas
        self.width = 0  # If set to 0, the application will be shown fullscreen
        self.height = 0  # If set to 0, the application will be shown fullscreen
        self.rotation = 0  # 0 - 360

        self.rendering_manager = None

        self.z_index = 0

        self.data_interface = VIGITIASensorDataInterface.Instance()
        self.data_interface.register_subscriber(self)

    """
    Getter Functions
    """

    def get_name(self):
        return self.name

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    def get_screen_resolution(self):
        return self.rendering_manager.get_screen_resolution()

    def get_position(self):
        return self.x, self.y

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_rotation(self):
        return self.rotation

    def get_z_index(self):
        return self.z_index

    """
    Setter Functions
    """

    def set_name(self, name):
        self.name = name

    def set_rendering_manager(self, rendering_manager):
        self.rendering_manager = rendering_manager

        # If width or height is set to 0, make the application fullscreen. Also handle value <0 or larger than canvas
        if self.get_width() <= 0 or self.get_width() > self.rendering_manager.get_screen_resolution()[0]:
            self.set_width(self.rendering_manager.get_screen_resolution()[0])
        if self.get_height() <= 0 or self.get_height() > self.rendering_manager.get_screen_resolution()[1]:
            self.set_height(self.rendering_manager.get_screen_resolution()[1])

    def set_x(self, x):
        self.x = x
        self.rendering_manager.on_application_updated(self.get_name())

    def set_y(self, y):
        self.y = y
        self.rendering_manager.on_application_updated(self.get_name())

    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.rendering_manager.on_application_updated(self.get_name())

    def set_dimensions(self, width, height):
        self.width = width
        self.height = height
        self.rendering_manager.on_application_updated(self.get_name())

    def set_width(self, width):
        self.width = width
        self.rendering_manager.on_application_updated(self.get_name())

    def set_height(self, height):
        self.height = height
        self.rendering_manager.on_application_updated(self.get_name())

    def set_rotation(self, rotation):
        self.rotation = rotation
        self.rendering_manager.on_application_updated(self.get_name())

    def set_z_index(self, z_index):
        self.z_index = z_index
        self.rendering_manager.on_application_updated(self.get_name())

    """
    Functions for receiving data from the VIGITIA Sensor Data Interface
    """

    def on_new_tuio_bundle(self, data):
        pass

    def on_new_token_messages(self, data):
        pass

    def on_new_pointer_messages(self, data):
        pass

    def on_new_bounding_box_messages(self, data):
        pass

    def on_new_data_messages(self, data):
        pass

    def on_new_control_messages(self, data):
        pass

    def on_new_video_frame(self, frame, name, origin_ip, port):
        pass
