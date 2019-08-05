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


def find_layer_collection(layer_collection, collection_name, parent_name=None):
    found = layer_collection.children.get(collection_name)
    if found:
        # found it, does it have the right parent?
        if parent_name:
            if layer_collection.name == parent_name:
                return found
        else:
            return found
    else:
        # check all child layer collections for this collection
        for child in layer_collection.children.values():
            found = find_layer_collection(child, collection_name, parent_name)
            if found:
                return found
    return None


def set_active_layer_collection(view_layers, collection_name, parent_name=None):
    for view_layer in view_layers:
        found = find_layer_collection(view_layer.layer_collection, collection_name, parent_name)
        if found:
            view_layer.active_layer_collection = found
            return found
    return None


def set_active_collection(name='Photogrammetry', parent=None, **kwargs):
    scene = kwargs.get('scene', None)
    if scene:
        col = (parent or scene.collection).children.get(name)
        if not col:
            col = bpy.data.collections.new(name)
            (parent or scene.collection).children.link(col)
        set_active_layer_collection(scene.view_layers, col.name, parent.name if parent else None)
        return col
    return None


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
        p = os.path.join(module_binary_path, f'{binary_name}{ext}')
        if os.path.exists(p):
            return p
    return None
