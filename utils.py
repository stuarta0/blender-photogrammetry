import os
import bpy
import platform


osname = platform.system().lower()


class PhotogrammetryModule(object):
    def __init__(self, name, description, property_group, func):
        self.name = name
        self.description = description
        self.property_group = property_group
        self.func = func
    
    def __unicode__(self):
        return self.name


def get_binpath_for_module(module_name):
    module_root = module_name
    if os.path.isfile(module_name):
        module_root = os.path.dirname(module_name)
    if not os.path.isabs(module_root) or not os.path.exists(module_root):
        module_root = os.path.join(os.path.dirname(os.path.realpath(__file__)), module_name)
    paths = [
        os.path.join(module_root, 'bin'), # packaged release for each platform
        os.path.join(module_root, osname), # development; github clone
    ]

    for p in paths:
        if os.path.exists(p):
            return p
    return None


def get_binary_path(module_binary_path, binary_name):
    if not module_binary_path:
        return None
    for ext in ['', '.exe']:
        p = os.path.join(module_binary_path, '{binary_name}{ext}'.format(binary_name=binary_name, ext=ext))
        if os.path.exists(p):
            return p
    return None
