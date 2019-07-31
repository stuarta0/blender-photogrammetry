import os
import re
import subprocess
import shutil
import platform

import bpy

from ..pmvs.load import prepare_workspace
from ..utils import set_active_collection, get_binpath_for_module, get_binary_path


class PMVSProperties(object):
    def __init__(self, dirpath, level, csize, threshold, wsize, minImageNum, import_points, *args, **kwargs):
        self.dirpath = dirpath 
        self.level = level 
        self.csize = csize 
        self.threshold = threshold 
        self.wsize = wsize 
        self.minImageNum = minImageNum 
        self.import_points = import_points 

def load(properties, data, *args, **kwargs):
    dirpath = bpy.path.abspath(properties.dirpath)
    binpath = get_binpath_for_module(os.path.realpath(__file__))
    env = os.environ.copy()
    if platform.system().lower() == 'windows':
        env.update({
            'PATH': f"{binpath}\lib;{env.get('PATH', '')}",
            'QT_PLUGIN_PATH': f"{binpath}\lib;{env.get('QT_PLUGIN_PATH', '')}"
        })
    
    # running COLMAP requires transforming to PMVS first
    options_path = prepare_workspace(PMVSProperties(dirpath, 0, 2, 0.7, 7, 2, True), data)

    colmap_path = get_binary_path(binpath, 'colmap')
    args = [
        colmap_path,
        'patch_match_stereo',
        '--workspace_path', os.path.dirname(options_path),
        '--workspace_format', 'PMVS',
        '--pmvs_option_name', os.path.basename(options_path),
    ] + (['--PatchMatchStereo.max_image_size', str(properties.max_image_size)] if properties.max_image_size > 0 else [])
    print(' '.join(args))
    retcode = subprocess.call(args, env=env)

    if retcode != 0:
        raise Exception('COLMAP patch_match_stereo failed, see system console for details')

    model = os.path.join(os.path.dirname(options_path), 'reconstruction-colmap.ply')
    args = [
        colmap_path,
        'stereo_fusion',
        '--workspace_path', os.path.dirname(options_path),
        '--workspace_format', 'PMVS',
        '--pmvs_option_name', os.path.basename(options_path),
        '--output_path', model
    ] + (['--StereoFusion.max_image_size', str(properties.max_image_size)] if properties.max_image_size > 0 else [])
    print(' '.join(args))
    retcode = subprocess.call(args, env=env)

    if retcode != 0:
        raise Exception('COLMAP stereo_fusion failed, see system console for details')

    if os.path.exists(model) and properties.import_points:
        set_active_collection(**kwargs)
        bpy.ops.import_mesh.ply(filepath=model)
