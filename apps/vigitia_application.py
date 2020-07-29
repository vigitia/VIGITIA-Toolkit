
# Parent class for all Toolkit applications


class VIGITIAApplication:
    print('Main class')

    def __init__(self):
        self.x = 0
        self.y = 0
        self.width = 500
        self.height = 500
        self.rotation = 0

    def get_x(self):
        print('Get X')
        return self.x

    def get_y(self):
        return self.y

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_rotation(self):
        return self.rotation

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

    def on_new_pointer_messages(self, data):
        pass

    def on_new_token_messages(self, data):
        pass
