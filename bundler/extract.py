import bpy
import os
import shutil
import subprocess
from mathutils import Vector, Matrix
from collections import namedtuple
from ..utils import get_image_size


def extract(properties, *args, **kargs):
    dirpath = bpy.path.abspath(properties.dirpath)

    with open(os.path.join(dirpath, 'bundle.out'), 'r') as f:
        lines = f.readlines()

    with open(os.path.join(dirpath, 'list.txt'), 'r') as f:
        images = f.readlines()  # TODO: make sure focal length is removed if present

    cameras = {}
    trackers = {}
    data = {
        'trackers': trackers,
        'cameras': cameras
    }

    total_cameras, total_points = map(int, lines[1].split())
    for i in range(int(total_cameras)):
        # each camera uses 5 lines
        idx = 2 + i * 5
        # read data
        focal, k1, k2 = list(map(float, lines[idx].split()))
        rotation = []
        rotation.append(map(float, lines[idx + 1].split()))
        rotation.append(map(float, lines[idx + 2].split()))
        rotation.append(map(float, lines[idx + 3].split()))
        translation = Vector(map(float, lines[idx + 4].split()))
        
        filename = images[i].strip()
        if not os.path.isabs(filename) or not os.path.isfile(filename):
            filename = os.path.join(dirpath, filename)

        # create cameras
        cameras.setdefault(i, {
            'filename': filename,
            'f': focal,
            'k': (k1, k2, 0),
            't': tuple(translation),
            'R': tuple(map(tuple, tuple(rotation))),
            'trackers': {},
        })
        
        if 'resolution' not in data:
            data.setdefault('resolution', get_image_size(filename))
    
    for i in range(int(total_points)):
        # each point uses 3 lines
        idx = 2 + int(total_cameras) * 5 + i * 3
        trackers.setdefault(i, {
            'co': tuple(map(float, lines[idx].split())),
            'rgb': tuple(map(int, lines[idx + 1].split())),
        })
        
        # for m in range(int(match.group('num_measurements'))):
        #     measurement_match = measurement_re.match(cur)
        #     if not measurement_match:
        #         raise Exception(f'Marker {i} did not match measurement {m} format specification')
        #     cameras[int(measurement_match.group('image_idx'))]['trackers'].setdefault(i, tuple(map(float, (measurement_match.group('X'), measurement_match.group('Y')))))
        #     cur = cur[measurement_match.end(len(measurement_match.groups())):].strip()
    
    return data