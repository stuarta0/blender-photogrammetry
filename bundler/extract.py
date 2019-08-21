import bpy
import os
import shutil
import subprocess
from mathutils import Vector, Matrix
from collections import namedtuple


def extract(properties, *args, **kargs):
    dirpath = bpy.path.abspath(properties.dirpath)

    with open(os.path.join(dirpath, 'bundle.out'), 'r') as f:
        lines = f.readlines()

    with open(os.path.join(dirpath, 'list.txt'), 'r') as f:
        images = f.readlines()  # TODO: make sure focal length is removed if present

    cameras = {}
    trackers = {}

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
    
    for i in range(int(total_points)):
        # each point uses 3 lines
        idx = 2 + int(total_cameras) * 5 + i * 3
        trackers.setdefault(i, {
            'co': map(float, lines[idx].split()),
            'rgb': tuple(map(int, lines[idx + 1].split())),
        })
        # TODO: read 2d view list and update camera collection
    
    i = bpy.data.images.load(next(v for v in cameras.values())['filename'])
    resolution = tuple(i.size)
    bpy.data.images.remove(i)

    return {
        'trackers': trackers,
        'cameras': cameras,
        'resolution': resolution
    }