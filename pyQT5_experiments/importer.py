#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from os import listdir
from pathlib import Path
from os.path import isfile, join
from importlib import import_module
import pyclbr

APPLICATIONS_BASE_FOLDER = 'applications'


applications_path = os.path.join(Path(__file__).resolve().parent.parent, APPLICATIONS_BASE_FOLDER)
files = [f for f in listdir(applications_path) if isfile(join(applications_path, f)) and f != '__init__.py']

print('Searching for applications in', applications_path)

print('Found files in {}:', files)

for file in files:
    module_name = f"{'applications'}.{file[:-3]}"
    print(module_name)
    module_info = pyclbr.readmodule(module_name)
    print(module_info)

    module = import_module(module_name)
    for item in module_info.values():
        print(item.name)
        if item.name == 'PaintExample':
            my_class = getattr(module, 'PaintExample')
            my_instance = my_class()

            my_instance.hello()
