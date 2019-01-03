import os
import re
import subprocess
import shutil
import platform

from ..pmvs.load import prepare_workspace


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
    #def bundle2pmvs(bin_path, bundle_path, target_dir, pmvs_options):
    osname = platform.system().lower()
    dirpath = bpy.path.abspath(properties.dirpath)
    binpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), osname)
    ext = ''
    env = os.environ.copy()

    if osname == 'windows':
        ext = '.exe'
        env.update({
            'PATH': '{SCRIPT_PATH}\lib;{PATH}'.format(SCRIPT_PATH=binpath, PATH=env.get('PATH', '')),
            'QT_PLUGIN_PATH': '{SCRIPT_PATH}\lib;{QT_PLUGIN_PATH}'.format(SCRIPT_PATH=binpath, QT_PLUGIN_PATH=env.get('QT_PLUGIN_PATH', ''))
        })
    
    # running COLMAP requires transforming to PMVS first
    options_path = prepare_workspace(PMVSProperties(dirpath, 0, 2, 0.7, 7, 2, True), data)

    args = [
        os.path.join(binpath, 'colmap{}'.format(ext)),
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
        os.path.join(binpath, 'colmap{}'.format(ext)),
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
        bpy.ops.import_mesh.ply(filepath=model)