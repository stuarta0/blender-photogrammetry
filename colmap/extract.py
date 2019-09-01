import bpy
import os
import shutil
import subprocess
from configparser import ConfigParser
from math import pi
from mathutils import Quaternion, Vector, Matrix, Euler
from collections import namedtuple
from .read_model import read_model
from ..utils import get_image_size


""" https://colmap.github.io/
    https://colmap.github.io/format.html

    CameraModel = collections.namedtuple(
        "CameraModel", ["model_id", "model_name", "num_params"])
    Camera = collections.namedtuple(
        "Camera", ["id", "model", "width", "height", "params"])
    BaseImage = collections.namedtuple(
        "Image", ["id", "qvec", "tvec", "camera_id", "name", "xys", "point3D_ids"])
    Point3D = collections.namedtuple(
        "Point3D", ["id", "xyz", "rgb", "error", "image_ids", "point2D_idxs"])
"""
def extract(properties, *args, **kargs):
    dirpath = bpy.path.abspath(properties.dirpath)

    # find the requisite files in either format
    requisites = ['cameras', 'images', 'points3D']
    extensions = ['.bin', '.txt', None]
    
    for ext in extensions:
        if not ext:
            raise Exception('COLMAP sparse reconstruction must contain a cameras, images and points3D file in .BIN or .TXT format')
        elif len([f for f in os.listdir(dirpath) for c in requisites if f == f'{c}{ext}']) == 3:
            # found the correct set of files with this extension
            break

    # check for a project.ini as it may contain an alternate image path setting
    try:
        # https://stackoverflow.com/a/25493615
        with open(os.path.join(dirpath, 'project.ini'), 'r') as f:
            config_string = f'[DEFAULT]\n{f.read()}'
        config = ConfigParser()
        config.read_string(config_string)
        image_path = config['DEFAULT']['image_path']
    except:
        image_path = os.path.join(dirpath, '..', 'images')

    cameras = {}
    trackers = {}
    data = {
        'trackers': trackers,
        'cameras': cameras
    }

    # https://colmap.github.io/format.html
    ccameras, images, points3D = read_model(dirpath, ext=ext)
    model = list(ccameras.values())[0]
    resolution = (model.width, model.height)
    data.setdefault('resolution', resolution)
    
    for idx, i in images.items():
        camera = ccameras[i.camera_id]
        f, cx, cy = parse_camera_param_list(camera)
        filename = i.name.strip()
        if not os.path.isabs(filename) or not os.path.isfile(filename):
            filename = os.path.join(image_path, filename)

        # The coordinates of the projection/camera center are given by -R^t * T, 
        # where R^t is the inverse/transpose of the 3x3 rotation matrix composed
        # from the quaternion and T is the translation vector. The local camera
        # coordinate system of an image is defined in a way that the X axis points
        # to the right, the Y axis to the bottom, and the Z axis to the front as
        # seen from the image.
        R = Quaternion(i.qvec).to_matrix()
        R.transpose()

        # c = -R^T t
        T = Vector(i.tvec)
        c = -1 * R @ T

        # t = -R * c
        R.transpose()
        R.rotate(Euler((pi, 0, 0)))
        t = -1 * R @ c

        cameras.setdefault(idx, {
            'filename': filename,
            'f': f,
            'k': (0, 0, 0),
            't': tuple(t),
            'principal': (cx, cy),
            'R': tuple(map(tuple, tuple(R))),
            'trackers': {},
        })

    for idx, p in points3D.items():
        trackers.setdefault(idx, {
            'co': tuple(p.xyz),
            'rgb': tuple(p.rgb)
        })

        # COLMAP uses the convention that the upper left image corner has coordinate (0, 0)
        # and the center of the upper left most pixel has coordinate (0.5, 0.5).
        for image_idx, image_id in enumerate(p.image_ids):
            # COLMAP db format allows more dimensions, but sparse file format may not reperesent it
            # to be safe, truncated coords to 2 dimensions
            co = list(images[image_id].xys[p.point2D_idxs[image_idx]])[:2]
            co[0] = co[0] - resolution[0] / 2.0 + 0.5
            co[1] = co[1] - resolution[1] / 2.0 + 0.5
            cameras[p.image_ids[0]]['trackers'].setdefault(idx, co)

    return data


# https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer/blob/4145f821b292b4cfae805c7cc1bdd5fc5af299d0/photogrammetry_importer/file_handler/colmap_file_handler.py#L37
def parse_camera_param_list(cam):
    name = cam.model
    params = cam.params 
    f, fx, fy, cx, cy = None, None, None, None, None
    if name == "SIMPLE_PINHOLE":
        f, cx, cy = params
    elif name == "PINHOLE":
        fx, fy, cx, cy = params
    elif name == "SIMPLE_RADIAL":
        f, cx, cy, _ = params
    elif name == "RADIAL":
        f, cx, cy, _, _ = params
    elif name == "OPENCV":
        fx, fy, cx, cy, _, _, _, _ = params
    elif name == "OPENCV_FISHEYE":
        fx, fy, cx, cy, _, _, _, _ = params
    elif name == "FULL_OPENCV":
        fx, fy, cx, cy, _, _, _, _, _, _, _, _ = params
    elif name == "FOV":
        fx, fy, cx, cy, _ = params
    elif name == "SIMPLE_RADIAL_FISHEYE":
        f, cx, cy, _ = params
    elif name == "RADIAL_FISHEYE":
        f, cx, cy, _, _ = params
    elif name == "THIN_PRISM_FISHEYE":
        fx, fy, cx, cy, _, _, _, _, _, _, _, _ = params
    if f is None:
        f = (fx + fy) * 0.5
    return f, cx, cy
