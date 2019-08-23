import bpy
import os
import shutil
import subprocess
import re
from math import pi
from mathutils import Vector, Matrix, Quaternion, Euler
from collections import namedtuple
from ..utils import get_image_size


"""
http://ccwu.me/vsfm/doc.html#nvm
The output format: N-View Match (NVM)
VisualSFM saves SfM workspaces into NVM files, which contain input image paths and multiple 3D models. Below is the format description

NVM_V3 [optional calibration]                        # file version header
<Model1> <Model2> ...                                # multiple reconstructed models
<Empty Model containing the unregistered Images>     # number of camera > 0, but number of points = 0
<0>                                                  # 0 camera to indicate the end of model section
<Some comments describing the PLY section>
<Number of PLY files> <List of indices of models that have associated PLY>

The [optional calibration] exists only if you use "Set Fixed Calibration" Function
FixedK fx cx fy cy

Each reconstructed <model> contains the following
<Number of cameras>   <List of cameras>
<Number of 3D points> <List of points>

The cameras and 3D points are saved in the following format
<Camera> = <File name> <focal length> <quaternion WXYZ> <camera center> <radial distortion> 0
<Point>  = <XYZ> <RGB> <number of measurements> <List of Measurements>
<Measurement> = <Image index> <Feature Index> <xy>

Check the LoadNVM function in util.h of Multicore bundle adjustment code for more details.  The LoadNVM function reads only the first model, and you should repeat to get all. Note the whitespaces in <file name> are replaced by '\"'.
"""

def extract(properties, *args, **kargs):
    filepath = bpy.path.abspath(properties.filepath)
    imagepaths = list(filter(None, bpy.path.abspath(properties.imagepath).split(';')))

    # # TODO: read list.txt to get image paths to detect image size
    # resolution_x = int(scene.render.resolution_x * (scene.render.resolution_percentage / 100))

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # TODO: read optional calibration from file
    if len(lines) == 0 or not lines[0].startswith('NVM_V3'):
        raise Exception('Not a valid NVM file')

    cameras = {}
    trackers = {}
    data = {
        'trackers': trackers,
        'cameras': cameras,
    }

    total_cameras = int(lines[2])
    total_points = int(lines[4 + total_cameras])

    # numbers: optional negative, digit(s), optional decimal point and following digit(s), optional scientific notation "e-0"
    num = r'-?\d+(?:\.\d+)?(?:e[+-]\d+)?'
    camera_re = re.compile(rf'^(?P<name>.*?)\s+(?P<f>{num})\s+(?P<QW>{num})\s+(?P<QX>{num})\s+(?P<QY>{num})\s+(?P<QZ>{num})\s+(?P<X>{num})\s+(?P<Y>{num})\s+(?P<Z>{num})\s+(?P<k1>{num})\s+{num}\s*$')
    for i in range(int(total_cameras)):
        # each camera uses 1 line
        match = camera_re.match(lines[3 + i])
        if not match:
            raise Exception(f'Camera {i} did not match the format specification')
        
        # find any filename that exists
        filenames = [fp for fp in [os.path.join(*parts) for parts in zip(imagepaths, [match.group('name'),] * len(imagepaths))] if os.path.exists(fp)]
        if not filenames:
            # wasn't in a root path, do we search sub directories?
            if properties.subdirs:
                for imagepath in imagepaths:
                    for root, dirs, files in os.walk(imagepath):
                        if match.group('name') in files:
                            filenames = [os.path.join(root, match.group('name'))]

            # still didn't find file?
            if not filenames:
                raise Exception(f'Image not found for camera {i}: {match.group("name")}')

        # create cameras
        q = Quaternion(tuple(map(float, [match.group('QW'), match.group('QX'), match.group('QY'), match.group('QZ')])))

        """
        https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer/blob/75189215dffde50dad106144111a48f29b1fed32/photogrammetry_importer/file_handler/nvm_file_handler.py#L55
        VisualSFM CAMERA coordinate system is the standard CAMERA coordinate system in computer vision (not the same
        as in computer graphics like in bundler, blender, etc.)
        That means
              the y axis in the image is pointing downwards (not upwards)
              the camera is looking along the positive z axis (points in front of the camera show a positive z value)
        The camera coordinate system in computer vision VISUALSFM uses camera matrices,
        which are rotated around the x axis by 180 degree
        i.e. the y and z axis of the CAMERA MATRICES are inverted
        """
        R = q.to_matrix()
        R.rotate(Euler((pi, 0, 0)))
        R.transpose()
        c = Vector(tuple(map(float, [match.group('X'), match.group('Y'), match.group('Z')])))
        t = -1 * R @ c
        R.transpose()

        # TODO: confirm whether the distortion coefficient needs inverting
        cameras.setdefault(i, {
            'filename': filenames[0],
            'f': float(match.group('f')),
            'k': (float(match.group('k1')), 0, 0),
            't': tuple(t),
            'R': tuple(map(tuple, tuple(R))),
            'trackers': {},
        })
        
        if 'resolution' not in data:
            data.setdefault('resolution', get_image_size(filenames[0]))
    
    marker_re = re.compile(rf'^(?P<X>{num})\s+(?P<Y>{num})\s+(?P<Z>{num})\s+(?P<R>\d+)\s+(?P<G>\d+)\s+(?P<B>\d+)\s+(?P<num_measurements>{num})\s+(?P<measurements>.*?)\s*$')
    measurement_re = re.compile(rf'^(?P<image_idx>\d+)\s+(?P<feature_idx>\d+)\s+(?P<X>{num})\s+(?P<Y>{num}).*')
    for i in range(int(total_points)):
        # each point uses a single line
        idx = 5 + int(total_cameras) + i
        match = marker_re.match(lines[idx])
        if not match:
            raise Exception(f'Marker {i} did not match the format specification')
        
        trackers.setdefault(i, {
            'co': tuple(map(float, [match.group('X'), match.group('Y'), match.group('Z')])),
            'rgb': tuple(map(int, [match.group('R'), match.group('G'), match.group('B')])),
        })

        cur = match.group('measurements')
        for m in range(int(match.group('num_measurements'))):
            measurement_match = measurement_re.match(cur)
            if not measurement_match:
                raise Exception(f'Marker {i} did not match measurement {m} format specification')
            # Let the measurement be (mx, my), which is relative to principal point (typically image center)
            # As for the image coordinate system, X-axis points right, and Y-axis points downward, so Z-axis points forward.
            cameras[int(measurement_match.group('image_idx'))]['trackers'].setdefault(i, (float(measurement_match.group('X')), -1 * float(measurement_match.group('Y'))))
            cur = cur[measurement_match.end(len(measurement_match.groups())):].strip()
    
    return data