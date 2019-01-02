import bpy
import os
import shutil
from math import floor
from mathutils import Matrix


def convert_image(filepath, target):
    """ Creates a scene specifically for saving an image as JPG """
    sc = bpy.data.scenes.new('photogrammetry_helper')
    try:
        img = bpy.data.images.load(filepath)
        r = sc.render
        r.resolution_x = img.size[0]
        r.resolution_y = img.size[1]
        r.resolution_percentage = floor(100 * min(1.0, (3000 / max(r.resolution_x, r.resolution_y))))  # 3000px limit on PMVS
        r.image_settings.file_format = 'JPEG'
        r.image_settings.quality = 100

        sc.display_settings.display_device = 'sRGB'
        img.save_render(target, scene=sc)
        bpy.data.images.remove(img)
    finally:
        # remove the temporary export scene
        bpy.data.scenes.remove(sc)


def load(properties, data, *args, **kwargs):
    """
    Takes the structure calculated from parsing the input and writes to the COLMAP sparse model text format:
    https://colmap.github.io/faq.html#reconstruct-sparse-dense-model-from-known-camera-poses
    """
    dirpath = bpy.path.abspath(properties.dirpath)
    sparse_model_path = os.path.join(dirpath, 'sparse')
    images_path = os.path.join(dirpath, 'images')

    cameras = data['cameras']
    trackers = data['trackers']

    print('output to ' + dirpath)

    if 'resolution' not in data:
        raise Exception('Image resolution must be provided by reader for COLMAP to write correctly')

    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
        os.makedirs(sparse_model_path)
        os.makedirs(images_path)

    # write camera file
    # Camera list with one line of data per camera:
    #   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]
    with open(os.path.join(sparse_model_path, 'cameras.txt'), 'w+') as f:
        # TODO: determine if reducing cameras based on intrinsics leads to better results (https://colmap.github.io/cameras.html)
        # assume camera intrinsics are the same for all cameras
        camera = list(cameras.values())[0]
        f.write('1 RADIAL {res[0]} {res[1]} {f} {pp[0]} {pp[1]} {k[0]} {k[1]}\n'.format(
            res=data['resolution'],
            pp=list(map(lambda x: int(x) / 2, data['resolution'])),
            **camera
        ))
        # f.writelines(['{id} RADIAL {res[0]} {res[1]} {f} {pp[0]} {pp[1]} {k[0]} {k[1]}\n'.format(
        #     id=camera_id,
        #     res=data['resolution'],
        #     pp=list(map(lambda x: int(x) / 2, data['resolution'])),
        #     **camera
        # ) for camera_id, camera in cameras.items() if 'resolution' in data])
    
    # write images file
    # Image list with two lines of data per image:
    #   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME
    #   POINTS2D[] as (X, Y, POINT3D_ID)
    with open(os.path.join(sparse_model_path, 'images.txt'), 'w+') as f:
        for camera_id, camera in cameras.items():
            q = Matrix(camera['R']).to_quaternion()
            f.writelines(['{image_id} {q.w} {q.x} {q.y} {q.z} {t[0]} {t[1]} {t[2]} 1 {relative_filename}\n'.format(
                image_id=camera_id,
                q=q,
                relative_filename=os.path.basename(camera['filename']),
                **camera
            ), '\n'])

    # empty points3D.txt file as per documentation
    with open(os.path.join(sparse_model_path, 'points3D.txt'), 'w+') as f:
        pass

    # copy images over to project folder
    for i, camera in cameras.items():
        shutil.copy(camera['filename'], os.path.join(images_path, os.path.basename(camera['filename'])))
    