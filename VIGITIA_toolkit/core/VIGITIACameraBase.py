

class VIGITIACameraBase:

    def __init__(self, camera_name):
        self.camera_name = camera_name
        self.available_video_streams = []

    def add_video_stream(self, type, format, res_x, res_y, fps, description=''):
        """
        Add information about an available video stream

        Parameters:
            type (str): Description of arg1
            format (str): Description of arg1
            res_x (str): Description of arg1
            res_y (str): Description of arg1
            fps (str): Description of arg1
            description (str): Description of arg1

        """
        self.available_video_streams.append([type, format, res_x, res_y, fps, description])

    def get_name(self):
        return self.camera_name

    def get_available_video_streams(self):
        return self.available_video_streams
