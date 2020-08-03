#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from os import listdir
from pathlib import Path
from os.path import isfile, join
from importlib import import_module
import pyclbr

CAMERA_FOLDER = 'cameras'
BASE_FOLDER = 'sensors'
CAMERA_BASE_CLASS = 'VIGITIACAMERABASE'


class VIGITIACameraController:

    def __init__(self):
        self.find_available_cameras()

    # Checking the folder CAMERA_BASE_FOLDER for all classes that inherit from the superclass CAMERA_BASE_CLASS
    # These are the applications that are currently available for display
    def find_available_cameras(self):
        available_cameras = []

        # Searching for available cameras in the following directory
        # TODO: Also allow for searching in subdirectories and add support for Git Repositories
        cameras_path = os.path.join(Path(__file__).resolve().parent.parent, BASE_FOLDER, CAMERA_FOLDER)

        # Inspired by https://stackoverflow.com/questions/1057431/how-to-load-all-modules-in-a-folder
        files = [f for f in listdir(cameras_path) if isfile(join(cameras_path, f)) and f != '__init__.py']
        for file in files:
            file_type = os.path.splitext(file)[1]
            if file_type == '.py':
                module_name = f"{BASE_FOLDER}.{CAMERA_FOLDER}.{file[:-3]}"
                module_info = pyclbr.readmodule(module_name)
                module = import_module(module_name)
                print(module_name, module_info, module)

                for item in module_info.values():
                    class_name = item.name  # The name of the found class
                    print(class_name)
                    my_class = getattr(module, class_name)
                    superclasses = my_class.mro()
                    # Check if the class has the required superclass
                    for superclass in superclasses:
                        if superclass.__name__ == CAMERA_BASE_CLASS:
                            print('"{}" in Module "{}" is a known camera'.format(class_name, module_name))

        print(available_cameras)

        return available_cameras


def main():
    VIGITIACameraController()
    sys.exit()


if __name__ == '__main__':
    main()
