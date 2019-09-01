import os
import bpy
import platform
from pprint import PrettyPrinter


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


def get_image_size(filename):
    img = bpy.data.images.load(filename)
    try:
        return tuple(img.size)
    finally:
        bpy.data.images.remove(img)


# https://stackoverflow.com/a/38534524
class CroppingPrettyPrinter(PrettyPrinter):
    def __init__(self, *args, **kwargs):
        self.maxlist = kwargs.pop('maxlist', 6)
        self.maxdict = kwargs.pop('maxdict', 4)
        PrettyPrinter.__init__(self, *args, **kwargs)

    def _format(self, obj, stream, indent, allowance, context, level):
        if isinstance(obj, list):
            # If object is a list, crop a copy of it according to self.maxlist
            # and append an ellipsis
            if len(obj) > self.maxlist:
                cropped_obj = obj[:self.maxlist] + [f'({len(obj) - self.maxlist} more)...']
                return PrettyPrinter._format(
                    self, cropped_obj, stream, indent,
                    allowance, context, level)

        # Let the original implementation handle anything else
        # Note: No use of super() because PrettyPrinter is an old-style class
        return PrettyPrinter._format(
            self, obj, stream, indent, allowance, context, level)

    def _format_dict_items(self, items, stream, indent, allowance, context,
                           level):
        write = stream.write
        indent += self._indent_per_level
        delimnl = ',\n' + ' ' * indent
        last_index = min([self.maxdict, len(items)]) - 1
        for i, (key, ent) in enumerate(items):
            last = i == last_index
            rep = self._repr(key, context, level)
            write(rep)
            write(': ')
            self._format(ent, stream, indent + len(rep) + 2,
                         allowance if last else 1,
                         context, level)
            if not last:
                write(delimnl)
            else:
                if self.maxdict < len(items):
                    write(delimnl)
                    write(f'({len(items) - self.maxdict} more)...')
                break


# def create_debug_svg(bpy_module, bundle_path):
#     list_path = listpath_from_bundle(bundle_path)
#     with open(list_path, 'r') as f:
#         images = [{'filename': os.path.join(os.path.dirname(list_path), imagepath.strip()), 'points': []} for imagepath in f.readlines()]
#     img = bpy_module.data.images.load(images[0]['filename'])
#     width, height = img.size

#     with open(bundle_path, 'r') as f:
#         lines = f.readlines()

#     total_cameras, total_points = map(int, lines[1].split())
#     for i in range(total_points):
#         # each point uses 3 lines (3d point, rgb, view list)
#         idx = 2 + total_cameras * 5 + i * 3
#         view_list = lines[idx + 2].split()
#         length = int(view_list[0])
#         for p in range(length):
#             # <camera> <sift> <x> <y>
#             pdx = 1 + p * 4
#             images[int(view_list[pdx])]['points'].append((float(view_list[pdx + 2]), float(view_list[pdx + 3])))
    
#     debug_path = os.path.join(os.path.dirname(bundle_path), 'debug')
#     if not os.path.exists(debug_path):
#         os.mkdir(debug_path)

#     for image in images:
#         points = ['<circle cx="{x}" cy="{y}" r="5" fill="none" stroke="#f00" stroke-width="1"/>'.format(x=p[0]+width/2, y=height/2-p[1]) for p in image['points']]
#         with open(os.path.join(debug_path, os.path.splitext(os.path.basename(image['filename']))[0] + '.svg'), 'w+') as svg:
#             svg.write('''<svg width="{width}" height="{height}" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
#     <image xlink:href="{filename}"/>
#     {points}
# </svg>'''.format(filename=image['filename'], width=width, height=height, points='\n\t'.join(points)))