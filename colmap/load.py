import os
import re
import subprocess
import shutil
import platform

import bpy

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
    target = 'pmvs' + os.sep
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
    retcode = subprocess.call([
        os.path.join(binpath, 'colmap{}'.format(ext)),
        'patch_match_stereo',
        '--workspace_path', os.path.join(dirpath, target),
        '--workspace_format', 'PMVS',
        '--pmvs_option_name', os.path.basename(options_path),
    ] + ['--PatchMatchStereo.max_image_size', str(properties.max_image_size)] if properties.max_image_size > 0 else [], env=env)

    if retcode != 0:
        raise Exception('COLMAP patch_match_stereo failed, see system console for details')

    model = os.path.join(dirpath, target, 'fused.ply')
    retcode = subprocess.call([
        os.path.join(binpath, 'colmap{}'.format(ext)),
        'stereo_fusion',
        '--workspace_path', os.path.join(dirpath, target),
        '--workspace_format', 'PMVS',
        '--pmvs_option_name', os.path.basename(options_path),
        '--output_path', model
    ] + ['--StereoFusion.max_image_size', properties.max_image_size] if properties.max_image_size > 0 else [], env=env)

    if retcode != 0:
        raise Exception('COLMAP stereo_fusion failed, see system console for details')

    if os.path.exists(model) and properties.import_points:
        bpy.ops.import_mesh.ply(filepath=model)



# def convert_image(filepath, target):
#     """ Creates a scene specifically for saving an image as JPG """
#     sc = bpy.data.scenes.new('photogrammetry_helper')
#     try:
#         img = bpy.data.images.load(filepath)
#         r = sc.render
#         r.resolution_x = img.size[0]
#         r.resolution_y = img.size[1]
#         r.resolution_percentage = floor(100 * min(1.0, (3000 / max(r.resolution_x, r.resolution_y))))  # 3000px limit on PMVS
#         r.image_settings.file_format = 'JPEG'
#         r.image_settings.quality = 100

#         sc.display_settings.display_device = 'sRGB'
#         img.save_render(target, scene=sc)
#         bpy.data.images.remove(img)
#     finally:
#         # remove the temporary export scene
#         bpy.data.scenes.remove(sc)


# def load(properties, data, *args, **kwargs):
#     """
#     Takes the structure calculated from parsing the input and writes to the COLMAP sparse model text format:
#     https://colmap.github.io/faq.html#reconstruct-sparse-dense-model-from-known-camera-poses
#     """
#     dirpath = bpy.path.abspath(properties.dirpath)
#     sparse_model_path = os.path.join(dirpath, 'sparse')
#     images_path = os.path.join(dirpath, 'images')

#     cameras = data['cameras']
#     trackers = data['trackers']

#     print('output to ' + dirpath)

#     if 'resolution' not in data:
#         raise Exception('Image resolution must be provided by reader for COLMAP to write correctly')

#     if not os.path.exists(dirpath):
#         os.makedirs(dirpath)
#         os.makedirs(sparse_model_path)
#         os.makedirs(images_path)

#     # write camera file
#     # Camera list with one line of data per camera:
#     #   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]
#     with open(os.path.join(sparse_model_path, 'cameras.txt'), 'w+') as f:
#         # TODO: determine if reducing cameras based on intrinsics leads to better results (https://colmap.github.io/cameras.html)
#         # assume camera intrinsics are the same for all cameras
#         camera = list(cameras.values())[0]
#         f.write('1 RADIAL {res[0]} {res[1]} {f} {pp[0]} {pp[1]} {k[0]} {k[1]}\n'.format(
#             res=data['resolution'],
#             pp=list(map(lambda x: int(x) / 2, data['resolution'])),
#             **camera
#         ))
#         # f.writelines(['{id} RADIAL {res[0]} {res[1]} {f} {pp[0]} {pp[1]} {k[0]} {k[1]}\n'.format(
#         #     id=camera_id,
#         #     res=data['resolution'],
#         #     pp=list(map(lambda x: int(x) / 2, data['resolution'])),
#         #     **camera
#         # ) for camera_id, camera in cameras.items() if 'resolution' in data])
    
#     # write images file
#     # Image list with two lines of data per image:
#     #   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME
#     #   POINTS2D[] as (X, Y, POINT3D_ID)
#     with open(os.path.join(sparse_model_path, 'images.txt'), 'w+') as f:
#         for camera_id, camera in cameras.items():
#             q = Matrix(camera['R']).to_quaternion()
#             f.writelines(['{image_id} {q.w} {q.x} {q.y} {q.z} {t[0]} {t[1]} {t[2]} 1 {relative_filename}\n'.format(
#                 image_id=camera_id,
#                 q=q,
#                 relative_filename=os.path.basename(camera['filename']),
#                 **camera
#             ), '\n'])

#     # empty points3D.txt file as per documentation
#     with open(os.path.join(sparse_model_path, 'points3D.txt'), 'w+') as f:
#         pass

#     # copy images over to project folder
#     for i, camera in cameras.items():
#         shutil.copy(camera['filename'], os.path.join(images_path, os.path.basename(camera['filename'])))
    