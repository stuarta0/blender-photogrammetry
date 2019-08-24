import bpy
import os
import json
from itertools import groupby


def extract(properties, *args, **kargs):
    filepath = bpy.path.abspath(properties.filepath)

    with open(filepath, 'r') as f:
        sfm = json.load(f)

    # TODO: read optional calibration from file
    if not ('views' in sfm and 'intrinsics' in sfm and 'poses' in sfm):
        raise Exception('Not a valid cameras.sfm file, expected object with keys "view", "intrinsics" and "poses".')

    views = sfm['views']
    views_by_pose = dict([(k, list(g)) for k, g in groupby(sorted(views, key=lambda x: x['poseId']), lambda x: x['poseId'])])
    intrinsics = dict([(i['intrinsicId'], i) for i in sfm['intrinsics']])

    cameras = {}
    trackers = {}
    data = {
        'trackers': trackers,
        'cameras': cameras,
    }

    for i, extrinsic in enumerate(sfm['poses']):
        view = views_by_pose[extrinsic['poseId']][0]
        intrinsic = intrinsics[view['intrinsicId']]
        transform = extrinsic['pose']['transform']
        cameras.setdefault(i, {
            'filename': view['path'],
            'f': float(intrinsic['pxFocalLength']),
            'k': tuple(map(float, intrinsic.get('distortionParams', [0, 0, 0]))),
            't': tuple(map(float, transform['center'])),
            'R': tuple([tuple(map(float, transform['rotation'][i:i+3])) for i in range(0, len(transform['rotation']), 3)]),
            'trackers': {},
        })

    return data