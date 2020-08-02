
# Parent class for all Toolkit applications


class VIGITIABaseApplication:

    def __init__(self):

        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.rotation = 0

        self.rendering_manager = None

        # TODO: Flags to implement
        self.force_fullscreen = False
        self.force_aspect_ratio = False

    """
    Getter Functions
    """

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    def get_position(self):
        return self.x, self.y

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_rotation(self):
        return self.rotation

    def get_force_fullscreen(self):
        return self.force_fullscreen

    """
    Setter Functions
    """

    def set_rendering_manager(self, rendering_manager):
        self.rendering_manager = rendering_manager
        print('Rendering Manager set')

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def set_dimensions(self, width, height):
        self.width = width
        self.height = height

    def set_width(self, width):
        self.width = width

    def set_height(self, height):
        self.height = height

    def set_rotation(self, rotation):
        self.rotation = rotation

    """
    Functions for receiving data from the VIGITIA Sensor Data Interface
    """

    def on_new_bounding_box_message(self, data):
        pass

    def on_new_pointer_messages(self, data):
        pass

    def on_new_token_messages(self, data):
        pass

    def on_new_video_frame(self, frame, name):
        pass
